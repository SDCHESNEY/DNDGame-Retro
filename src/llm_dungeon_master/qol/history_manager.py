"""Message history management with search and scrollback."""

from typing import List, Optional, Dict
from datetime import datetime, UTC
from sqlmodel import Session as DBSession, select, or_, and_

from ..models import Message


class MessageHistoryManager:
    """Manages message history with search capabilities."""
    
    def __init__(self, db: DBSession):
        """Initialize history manager.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def get_recent_messages(
        self,
        session_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Message]:
        """Get recent messages with pagination.
        
        Args:
            session_id: Session ID
            limit: Maximum number of messages
            offset: Offset for pagination
            
        Returns:
            List of messages
        """
        stmt = select(Message).where(
            Message.session_id == session_id
        ).order_by(Message.created_at.desc()).offset(offset).limit(limit)
        
        messages = self.db.exec(stmt).all()
        return list(reversed(list(messages)))
    
    def search_messages(
        self,
        session_id: int,
        query: str,
        sender: Optional[str] = None,
        message_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Message]:
        """Search messages by content, sender, or type.
        
        Args:
            session_id: Session ID
            query: Search query (searches in content)
            sender: Optional sender filter
            message_type: Optional message type filter
            limit: Maximum results
            
        Returns:
            List of matching messages
        """
        conditions = [Message.session_id == session_id]
        
        # Search in content
        if query:
            conditions.append(Message.content.ilike(f"%{query}%"))
        
        # Filter by sender
        if sender:
            conditions.append(Message.sender_name == sender)
        
        # Filter by type
        if message_type:
            conditions.append(Message.message_type == message_type)
        
        stmt = select(Message).where(
            and_(*conditions)
        ).order_by(Message.created_at.desc()).limit(limit)
        
        messages = self.db.exec(stmt).all()
        return list(reversed(list(messages)))
    
    def get_messages_by_date(
        self,
        session_id: int,
        start_date: datetime,
        end_date: Optional[datetime] = None
    ) -> List[Message]:
        """Get messages within a date range.
        
        Args:
            session_id: Session ID
            start_date: Start of date range
            end_date: End of date range (default: now)
            
        Returns:
            List of messages
        """
        end_date = end_date or datetime.now(UTC)
        
        stmt = select(Message).where(
            and_(
                Message.session_id == session_id,
                Message.created_at >= start_date,
                Message.created_at <= end_date
            )
        ).order_by(Message.created_at)
        
        return list(self.db.exec(stmt).all())
    
    def get_conversation_context(
        self,
        session_id: int,
        around_message_id: int,
        context_size: int = 10
    ) -> List[Message]:
        """Get messages around a specific message (for context).
        
        Args:
            session_id: Session ID
            around_message_id: Message ID to get context around
            context_size: Number of messages before and after
            
        Returns:
            List of messages with context
        """
        # Get the target message first
        target = self.db.get(Message, around_message_id)
        if not target or target.session_id != session_id:
            return []
        
        # Get messages before
        stmt_before = select(Message).where(
            and_(
                Message.session_id == session_id,
                Message.created_at < target.created_at
            )
        ).order_by(Message.created_at.desc()).limit(context_size)
        before = list(reversed(list(self.db.exec(stmt_before).all())))
        
        # Get messages after
        stmt_after = select(Message).where(
            and_(
                Message.session_id == session_id,
                Message.created_at > target.created_at
            )
        ).order_by(Message.created_at).limit(context_size)
        after = list(self.db.exec(stmt_after).all())
        
        return before + [target] + after
    
    def get_message_stats(self, session_id: int) -> Dict:
        """Get statistics about messages in a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Dictionary with message statistics
        """
        stmt = select(Message).where(Message.session_id == session_id)
        messages = self.db.exec(stmt).all()
        
        if not messages:
            return {
                "total_messages": 0,
                "by_sender": {},
                "by_type": {},
                "first_message": None,
                "last_message": None
            }
        
        # Count by sender
        by_sender = {}
        by_type = {}
        
        for msg in messages:
            by_sender[msg.sender_name] = by_sender.get(msg.sender_name, 0) + 1
            by_type[msg.message_type] = by_type.get(msg.message_type, 0) + 1
        
        messages_list = list(messages)
        first = min(messages_list, key=lambda m: m.created_at)
        last = max(messages_list, key=lambda m: m.created_at)
        
        return {
            "total_messages": len(messages_list),
            "by_sender": by_sender,
            "by_type": by_type,
            "first_message": first.created_at.isoformat() if first.created_at else None,
            "last_message": last.created_at.isoformat() if last.created_at else None
        }
    
    def export_history(
        self,
        session_id: int,
        format: str = "text"
    ) -> str:
        """Export message history in various formats.
        
        Args:
            session_id: Session ID
            format: Export format ('text', 'json', 'markdown')
            
        Returns:
            Formatted history string
        """
        messages = self.get_recent_messages(session_id, limit=1000)
        
        if format == "json":
            import json
            return json.dumps([
                {
                    "id": msg.id,
                    "sender": msg.sender_name,
                    "content": msg.content,
                    "type": msg.message_type,
                    "timestamp": msg.created_at.isoformat() if msg.created_at else None
                }
                for msg in messages
            ], indent=2)
        
        elif format == "markdown":
            lines = ["# Message History\n"]
            for msg in messages:
                timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S") if msg.created_at else "Unknown"
                lines.append(f"## {msg.sender_name} ({timestamp})")
                lines.append(f"*Type: {msg.message_type}*\n")
                lines.append(msg.content)
                lines.append("\n---\n")
            return "\n".join(lines)
        
        else:  # text
            lines = []
            for msg in messages:
                timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S") if msg.created_at else "Unknown"
                lines.append(f"[{timestamp}] {msg.sender_name}: {msg.content}")
            return "\n".join(lines)
    
    def clear_old_messages(
        self,
        session_id: int,
        keep_recent: int = 100
    ) -> int:
        """Clear old messages, keeping only recent ones.
        
        Args:
            session_id: Session ID
            keep_recent: Number of recent messages to keep
            
        Returns:
            Number of messages deleted
        """
        # Get all messages
        stmt = select(Message).where(
            Message.session_id == session_id
        ).order_by(Message.created_at.desc())
        messages = list(self.db.exec(stmt).all())
        
        # Keep only recent
        to_delete = messages[keep_recent:]
        
        for msg in to_delete:
            self.db.delete(msg)
        
        self.db.commit()
        return len(to_delete)
