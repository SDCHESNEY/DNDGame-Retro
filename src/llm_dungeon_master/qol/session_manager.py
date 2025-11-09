"""Session state management with save/load functionality."""

import json
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime, UTC
from dataclasses import dataclass, asdict
from sqlmodel import Session as DBSession, select

from ..models import Session, Character, Message, SessionPlayer


@dataclass
class SessionSnapshot:
    """A snapshot of session state."""
    session_id: int
    session_name: str
    created_at: str
    saved_at: str
    players: List[Dict]
    characters: List[Dict]
    recent_messages: List[Dict]
    metadata: Dict


class SessionStateManager:
    """Manages session state persistence."""
    
    def __init__(self, db: DBSession, save_dir: Optional[Path] = None):
        """Initialize session state manager.
        
        Args:
            db: Database session
            save_dir: Directory for save files (default: ./saves/)
        """
        self.db = db
        self.save_dir = save_dir or Path("./saves")
        self.save_dir.mkdir(exist_ok=True)
    
    def save_session(self, session_id: int, metadata: Optional[Dict] = None) -> Path:
        """Save complete session state to file.
        
        Args:
            session_id: Session ID to save
            metadata: Optional metadata to include
            
        Returns:
            Path to saved file
        """
        # Get session
        session = self.db.get(Session, session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Get session players
        stmt = select(SessionPlayer).where(SessionPlayer.session_id == session_id)
        session_players = self.db.exec(stmt).all()
        
        players = []
        characters = []
        
        for sp in session_players:
            if sp.player:
                players.append({
                    "id": sp.player.id,
                    "username": sp.player.username,
                    "joined_at": sp.joined_at.isoformat() if sp.joined_at else None
                })
            
            if sp.character:
                characters.append({
                    "id": sp.character.id,
                    "name": sp.character.name,
                    "race": sp.character.race,
                    "char_class": sp.character.char_class,
                    "level": sp.character.level,
                    "current_hp": sp.character.current_hp,
                    "max_hp": sp.character.max_hp
                })
        
        # Get recent messages (last 50)
        stmt = select(Message).where(
            Message.session_id == session_id
        ).order_by(Message.created_at.desc()).limit(50)
        messages = self.db.exec(stmt).all()
        
        recent_messages = [
            {
                "sender": msg.sender_name,
                "content": msg.content,
                "message_type": msg.message_type,
                "timestamp": msg.created_at.isoformat() if msg.created_at else None
            }
            for msg in reversed(list(messages))
        ]
        
        # Create snapshot
        snapshot = SessionSnapshot(
            session_id=session.id,
            session_name=session.name,
            created_at=session.created_at.isoformat() if session.created_at else None,
            saved_at=datetime.now(UTC).isoformat(),
            players=players,
            characters=characters,
            recent_messages=recent_messages,
            metadata=metadata or {}
        )
        
        # Save to file
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        filename = f"session_{session_id}_{timestamp}.json"
        filepath = self.save_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(asdict(snapshot), f, indent=2)
        
        return filepath
    
    def load_session(self, filepath: Path) -> SessionSnapshot:
        """Load session state from file.
        
        Args:
            filepath: Path to save file
            
        Returns:
            SessionSnapshot object
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        return SessionSnapshot(**data)
    
    def list_saves(self, session_id: Optional[int] = None) -> List[Path]:
        """List available save files.
        
        Args:
            session_id: Optional session ID to filter by
            
        Returns:
            List of save file paths
        """
        pattern = f"session_{session_id}_*.json" if session_id else "session_*.json"
        saves = sorted(self.save_dir.glob(pattern), reverse=True)
        return saves
    
    def get_save_info(self, filepath: Path) -> Dict:
        """Get basic info about a save file without loading it.
        
        Args:
            filepath: Path to save file
            
        Returns:
            Dictionary with save file info
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        return {
            "filename": filepath.name,
            "session_id": data.get("session_id"),
            "session_name": data.get("session_name"),
            "saved_at": data.get("saved_at"),
            "num_players": len(data.get("players", [])),
            "num_characters": len(data.get("characters", [])),
            "num_messages": len(data.get("recent_messages", []))
        }
    
    def delete_save(self, filepath: Path) -> bool:
        """Delete a save file.
        
        Args:
            filepath: Path to save file
            
        Returns:
            True if deleted successfully
        """
        try:
            filepath.unlink()
            return True
        except Exception:
            return False
    
    def auto_save(self, session_id: int) -> Optional[Path]:
        """Create an auto-save of the session.
        
        Args:
            session_id: Session ID to auto-save
            
        Returns:
            Path to auto-save file or None if failed
        """
        try:
            # Keep only last 5 auto-saves
            auto_saves = [
                p for p in self.list_saves(session_id)
                if "_auto_" in p.name
            ]
            
            if len(auto_saves) >= 5:
                # Delete oldest
                for old_save in auto_saves[5:]:
                    self.delete_save(old_save)
            
            # Create auto-save with special naming
            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            filename = f"session_{session_id}_auto_{timestamp}.json"
            filepath = self.save_dir / filename
            
            return self.save_session(session_id, {"auto_save": True})
        except Exception:
            return None
