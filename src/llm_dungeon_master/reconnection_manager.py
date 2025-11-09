"""Reconnection manager for handling player disconnects and reconnects."""

from datetime import datetime, UTC, timedelta
from typing import Optional, Dict
import secrets
import hashlib
from sqlmodel import Session as DBSession, select

from .models import ReconnectionToken, Player, Session as GameSession, SessionPlayer, PlayerPresence


class ReconnectionManager:
    """Manages player reconnection tokens and session restoration."""
    
    def __init__(self, db_session: DBSession):
        self.db = db_session
        self.token_expiry_hours = 24  # Tokens valid for 24 hours
    
    def create_reconnection_token(
        self,
        player_id: int,
        session_id: int
    ) -> str:
        """
        Create a reconnection token for a player in a session.
        
        Args:
            player_id: The player ID
            session_id: The session ID
            
        Returns:
            The reconnection token string
        """
        # Generate a secure random token
        raw_token = secrets.token_urlsafe(32)
        
        # Hash it for storage (additional security layer)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        
        # Check if token already exists for this player/session
        statement = select(ReconnectionToken).where(
            ReconnectionToken.player_id == player_id,
            ReconnectionToken.session_id == session_id,
            ReconnectionToken.is_valid == True
        )
        existing = self.db.exec(statement).first()
        
        if existing:
            # Invalidate old token
            existing.is_valid = False
        
        # Create new token
        expires_at = datetime.now(UTC) + timedelta(hours=self.token_expiry_hours)
        
        token_record = ReconnectionToken(
            player_id=player_id,
            session_id=session_id,
            token=token_hash,
            expires_at=expires_at,
            is_valid=True
        )
        
        self.db.add(token_record)
        self.db.commit()
        
        # Return the unhashed token (only time it's visible)
        return raw_token
    
    def validate_token(self, token: str) -> Optional[ReconnectionToken]:
        """
        Validate a reconnection token.
        
        Args:
            token: The token string
            
        Returns:
            ReconnectionToken if valid, None otherwise
        """
        # Hash the provided token
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Look up token
        statement = select(ReconnectionToken).where(
            ReconnectionToken.token == token_hash,
            ReconnectionToken.is_valid == True
        )
        token_record = self.db.exec(statement).first()
        
        if not token_record:
            return None
        
        # Check if expired
        expires_at = token_record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if datetime.now(UTC) > expires_at:
            token_record.is_valid = False
            self.db.commit()
            return None
        
        return token_record
    
    def handle_reconnection(self, token: str) -> Dict[str, any]:
        """
        Handle a player reconnection using a token.
        
        Args:
            token: The reconnection token
            
        Returns:
            Dictionary with reconnection details and session state
        """
        # Validate token
        token_record = self.validate_token(token)
        
        if not token_record:
            return {
                "success": False,
                "error": "Invalid or expired token"
            }
        
        # Mark token as used
        token_record.used_at = datetime.now(UTC)
        token_record.is_valid = False  # One-time use
        self.db.commit()
        
        # Get player and session details
        player = self.db.get(Player, token_record.player_id)
        session = self.db.get(GameSession, token_record.session_id)
        
        if not player or not session:
            return {
                "success": False,
                "error": "Player or session not found"
            }
        
        # Restore session state
        session_state = self.restore_session_state(
            token_record.player_id,
            token_record.session_id
        )
        
        return {
            "success": True,
            "player_id": token_record.player_id,
            "player_name": player.name,
            "session_id": token_record.session_id,
            "session_name": session.name,
            "session_state": session_state,
            "reconnected_at": datetime.now(UTC)
        }
    
    def restore_session_state(
        self,
        player_id: int,
        session_id: int
    ) -> Dict[str, any]:
        """
        Restore complete session state for a player.
        
        Args:
            player_id: The player ID
            session_id: The session ID
            
        Returns:
            Dictionary with complete session state
        """
        # Get session player info
        statement = select(SessionPlayer).where(
            SessionPlayer.session_id == session_id,
            SessionPlayer.player_id == player_id
        )
        session_player = self.db.exec(statement).first()
        
        if not session_player:
            return {"error": "Player not in session"}
        
        # Get character info if assigned
        character_info = None
        if session_player.character_id:
            from .models import Character
            character = self.db.get(Character, session_player.character_id)
            if character:
                character_info = {
                    "id": character.id,
                    "name": character.name,
                    "class": character.char_class,
                    "level": character.level,
                    "current_hp": character.current_hp,
                    "max_hp": character.max_hp,
                    "armor_class": character.armor_class
                }
        
        # Get current turn state
        from .models import Turn
        turn_statement = select(Turn).where(
            Turn.session_id == session_id
        ).order_by(Turn.turn_order)
        turns = list(self.db.exec(turn_statement).all())
        
        current_turn = None
        for turn in turns:
            if turn.status == "active":
                current_turn = {
                    "character_id": turn.character_id,
                    "character_name": turn.character_name,
                    "round_number": turn.round_number
                }
                break
        
        # Get recent messages
        from .models import Message
        message_statement = select(Message).where(
            Message.session_id == session_id
        ).order_by(Message.created_at.desc()).limit(50)
        messages = list(self.db.exec(message_statement).all())
        
        # Get other players' presence
        presence_statement = select(PlayerPresence).where(
            PlayerPresence.session_id == session_id
        )
        presences = list(self.db.exec(presence_statement).all())
        
        other_players = []
        for presence in presences:
            if presence.player_id != player_id:
                player = self.db.get(Player, presence.player_id)
                if player:
                    other_players.append({
                        "player_id": player.id,
                        "player_name": player.name,
                        "status": presence.status
                    })
        
        return {
            "session_id": session_id,
            "character": character_info,
            "current_turn": current_turn,
            "turn_queue": [
                {
                    "character_id": turn.character_id,
                    "character_name": turn.character_name,
                    "initiative": turn.initiative,
                    "status": turn.status
                }
                for turn in turns
            ],
            "recent_messages": [
                {
                    "sender": msg.sender_name,
                    "content": msg.content,
                    "type": msg.message_type,
                    "timestamp": msg.created_at
                }
                for msg in reversed(messages)  # Oldest first
            ],
            "other_players": other_players,
            "restored_at": datetime.now(UTC)
        }
    
    def cleanup_expired_tokens(self, session_id: Optional[int] = None) -> int:
        """
        Clean up expired reconnection tokens.
        
        Args:
            session_id: Optional session ID to limit cleanup to
            
        Returns:
            Number of tokens cleaned up
        """
        now = datetime.now(UTC)
        
        if session_id:
            statement = select(ReconnectionToken).where(
                ReconnectionToken.session_id == session_id,
                ReconnectionToken.expires_at < now
            )
        else:
            statement = select(ReconnectionToken).where(
                ReconnectionToken.expires_at < now
            )
        
        expired_tokens = list(self.db.exec(statement).all())
        
        for token in expired_tokens:
            self.db.delete(token)
        
        self.db.commit()
        return len(expired_tokens)
    
    def revoke_token(
        self,
        player_id: int,
        session_id: int
    ) -> bool:
        """
        Revoke all tokens for a player in a session.
        
        Returns:
            True if tokens were revoked
        """
        statement = select(ReconnectionToken).where(
            ReconnectionToken.player_id == player_id,
            ReconnectionToken.session_id == session_id,
            ReconnectionToken.is_valid == True
        )
        tokens = list(self.db.exec(statement).all())
        
        for token in tokens:
            token.is_valid = False
        
        self.db.commit()
        return len(tokens) > 0
    
    def get_token_info(self, token: str) -> Optional[Dict[str, any]]:
        """
        Get information about a token without using it.
        
        Returns:
            Dictionary with token info or None if invalid
        """
        token_record = self.validate_token(token)
        
        if not token_record:
            return None
        
        player = self.db.get(Player, token_record.player_id)
        session = self.db.get(GameSession, token_record.session_id)
        
        return {
            "player_id": token_record.player_id,
            "player_name": player.name if player else "Unknown",
            "session_id": token_record.session_id,
            "session_name": session.name if session else "Unknown",
            "created_at": token_record.created_at,
            "expires_at": token_record.expires_at,
            "is_valid": token_record.is_valid,
            "used_at": token_record.used_at
        }
