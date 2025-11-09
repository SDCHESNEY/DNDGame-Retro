"""Presence tracking system for multiplayer sessions."""

from datetime import datetime, UTC, timedelta
from typing import Optional, List, Dict
from sqlmodel import Session as DBSession, select

from .models import PlayerPresence, SessionPlayer, Player


class PresenceStatus:
    """Player presence status constants."""
    ONLINE = "online"
    AWAY = "away"
    OFFLINE = "offline"


class PresenceManager:
    """Manages player presence and connection status."""
    
    def __init__(self, db_session: DBSession):
        self.db = db_session
        self.heartbeat_timeout = 30  # seconds before marking away
        self.offline_timeout = 300  # seconds before marking offline
    
    def track_connection(
        self,
        session_id: int,
        player_id: int,
        connection_id: str
    ) -> PlayerPresence:
        """
        Track a new connection or update existing presence.
        
        Args:
            session_id: The session ID
            player_id: The player ID
            connection_id: Unique connection identifier (WebSocket ID)
            
        Returns:
            PlayerPresence object
        """
        # Check if presence already exists
        statement = select(PlayerPresence).where(
            PlayerPresence.session_id == session_id,
            PlayerPresence.player_id == player_id,
            PlayerPresence.connection_id == connection_id
        )
        presence = self.db.exec(statement).first()
        
        if presence:
            # Update existing presence
            presence.status = PresenceStatus.ONLINE
            presence.last_heartbeat = datetime.now(UTC)
            presence.disconnected_at = None
        else:
            # Create new presence
            presence = PlayerPresence(
                session_id=session_id,
                player_id=player_id,
                connection_id=connection_id,
                status=PresenceStatus.ONLINE,
                last_heartbeat=datetime.now(UTC)
            )
            self.db.add(presence)
        
        self.db.commit()
        self.db.refresh(presence)
        return presence
    
    def update_heartbeat(
        self,
        session_id: int,
        player_id: int,
        connection_id: str
    ) -> bool:
        """
        Update heartbeat timestamp for a connection.
        
        Returns:
            True if updated successfully
        """
        statement = select(PlayerPresence).where(
            PlayerPresence.session_id == session_id,
            PlayerPresence.player_id == player_id,
            PlayerPresence.connection_id == connection_id
        )
        presence = self.db.exec(statement).first()
        
        if not presence:
            return False
        
        presence.last_heartbeat = datetime.now(UTC)
        if presence.status == PresenceStatus.AWAY:
            presence.status = PresenceStatus.ONLINE
        
        self.db.commit()
        return True
    
    def update_status(
        self,
        player_id: int,
        session_id: int,
        status: str
    ) -> bool:
        """
        Manually update player status.
        
        Args:
            player_id: The player ID
            session_id: The session ID
            status: New status (online, away, offline)
            
        Returns:
            True if updated successfully
        """
        statement = select(PlayerPresence).where(
            PlayerPresence.session_id == session_id,
            PlayerPresence.player_id == player_id
        )
        presences = list(self.db.exec(statement).all())
        
        if not presences:
            return False
        
        for presence in presences:
            presence.status = status
            if status == PresenceStatus.OFFLINE:
                presence.disconnected_at = datetime.now(UTC)
        
        self.db.commit()
        return True
    
    def disconnect(
        self,
        session_id: int,
        player_id: int,
        connection_id: str
    ) -> bool:
        """
        Mark a connection as disconnected.
        
        Returns:
            True if updated successfully
        """
        statement = select(PlayerPresence).where(
            PlayerPresence.session_id == session_id,
            PlayerPresence.player_id == player_id,
            PlayerPresence.connection_id == connection_id
        )
        presence = self.db.exec(statement).first()
        
        if not presence:
            return False
        
        presence.status = PresenceStatus.OFFLINE
        presence.disconnected_at = datetime.now(UTC)
        self.db.commit()
        return True
    
    def get_presence_summary(self, session_id: int) -> Dict[str, any]:
        """
        Get presence summary for all players in a session.
        
        Returns:
            Dictionary with player presence information
        """
        # Get all players in session
        session_players_stmt = select(SessionPlayer).where(
            SessionPlayer.session_id == session_id
        )
        session_players = list(self.db.exec(session_players_stmt).all())
        
        players_info = []
        online_count = 0
        away_count = 0
        offline_count = 0
        
        for sp in session_players:
            # Get player details
            player = self.db.get(Player, sp.player_id)
            if not player:
                continue
            
            # Get presence
            presence_stmt = select(PlayerPresence).where(
                PlayerPresence.session_id == session_id,
                PlayerPresence.player_id == sp.player_id
            ).order_by(PlayerPresence.last_heartbeat.desc())
            presence = self.db.exec(presence_stmt).first()
            
            status = PresenceStatus.OFFLINE
            last_seen = None
            connection_duration = None
            
            if presence:
                # Check if heartbeat is stale
                self._update_stale_status(presence)
                status = presence.status
                last_seen = presence.last_heartbeat
                
                if presence.status == PresenceStatus.ONLINE:
                    # Handle both timezone-aware and naive datetimes
                    connected_at = presence.connected_at
                    if connected_at.tzinfo is None:
                        connected_at = connected_at.replace(tzinfo=UTC)
                    connection_duration = (
                        datetime.now(UTC) - connected_at
                    ).total_seconds()
            
            # Count status
            if status == PresenceStatus.ONLINE:
                online_count += 1
            elif status == PresenceStatus.AWAY:
                away_count += 1
            else:
                offline_count += 1
            
            players_info.append({
                "player_id": sp.player_id,
                "player_name": player.name,
                "character_id": sp.character_id,
                "status": status,
                "last_seen": last_seen,
                "connection_duration_seconds": connection_duration
            })
        
        return {
            "session_id": session_id,
            "total_players": len(session_players),
            "online": online_count,
            "away": away_count,
            "offline": offline_count,
            "players": players_info
        }
    
    def check_all_ready(self, session_id: int) -> Dict[str, any]:
        """
        Check if all players are online and ready.
        
        Returns:
            Dictionary with ready status
        """
        summary = self.get_presence_summary(session_id)
        
        all_online = summary["online"] == summary["total_players"]
        
        return {
            "all_online": all_online,
            "online_count": summary["online"],
            "total_count": summary["total_players"],
            "players": summary["players"]
        }
    
    def get_active_connections(self, session_id: int) -> List[PlayerPresence]:
        """Get all active connections for a session."""
        statement = select(PlayerPresence).where(
            PlayerPresence.session_id == session_id,
            PlayerPresence.status.in_([PresenceStatus.ONLINE, PresenceStatus.AWAY])
        )
        return list(self.db.exec(statement).all())
    
    def cleanup_stale_connections(self, session_id: int) -> int:
        """
        Clean up connections that have been offline for too long.
        
        Returns:
            Number of connections cleaned up
        """
        cutoff = datetime.now(UTC) - timedelta(hours=24)
        statement = select(PlayerPresence).where(
            PlayerPresence.session_id == session_id,
            PlayerPresence.status == PresenceStatus.OFFLINE,
            PlayerPresence.disconnected_at < cutoff
        )
        stale_presences = list(self.db.exec(statement).all())
        
        for presence in stale_presences:
            self.db.delete(presence)
        
        self.db.commit()
        return len(stale_presences)
    
    def _update_stale_status(self, presence: PlayerPresence):
        """Update presence status if heartbeat is stale."""
        now = datetime.now(UTC)
        # Handle both timezone-aware and naive datetimes
        last_heartbeat = presence.last_heartbeat
        if last_heartbeat.tzinfo is None:
            last_heartbeat = last_heartbeat.replace(tzinfo=UTC)
        time_since_heartbeat = (now - last_heartbeat).total_seconds()
        
        if time_since_heartbeat > self.offline_timeout:
            if presence.status != PresenceStatus.OFFLINE:
                presence.status = PresenceStatus.OFFLINE
                presence.disconnected_at = now
                self.db.commit()
        elif time_since_heartbeat > self.heartbeat_timeout:
            if presence.status == PresenceStatus.ONLINE:
                presence.status = PresenceStatus.AWAY
                self.db.commit()
    
    def get_player_status(
        self,
        session_id: int,
        player_id: int
    ) -> Optional[str]:
        """Get current status for a player in a session."""
        statement = select(PlayerPresence).where(
            PlayerPresence.session_id == session_id,
            PlayerPresence.player_id == player_id
        ).order_by(PlayerPresence.last_heartbeat.desc())
        
        presence = self.db.exec(statement).first()
        if not presence:
            return PresenceStatus.OFFLINE
        
        self._update_stale_status(presence)
        return presence.status
