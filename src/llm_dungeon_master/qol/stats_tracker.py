"""Statistics tracking for gameplay metrics."""

from typing import Dict, List, Optional
from datetime import datetime, UTC, timedelta
from sqlmodel import Session as DBSession, select, func
from collections import defaultdict

from ..models import Roll, CombatEncounter, Message, Character


class StatisticsTracker:
    """Tracks and analyzes gameplay statistics."""
    
    def __init__(self, db: DBSession):
        """Initialize statistics tracker.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def get_dice_stats(
        self,
        session_id: Optional[int] = None,
        character_id: Optional[int] = None
    ) -> Dict:
        """Get dice rolling statistics.
        
        Args:
            session_id: Optional session filter
            character_id: Optional character filter
            
        Returns:
            Dictionary with dice statistics
        """
        conditions = []
        if session_id:
            conditions.append(Roll.session_id == session_id)
        if character_id:
            conditions.append(Roll.character_id == character_id)
        
        if conditions:
            stmt = select(Roll).where(*conditions)
        else:
            stmt = select(Roll)
        
        rolls = list(self.db.exec(stmt).all())
        
        if not rolls:
            return {
                "total_rolls": 0,
                "by_type": {},
                "by_die": {},
                "critical_hits": 0,
                "critical_failures": 0,
                "average_result": 0,
                "highest_roll": 0,
                "lowest_roll": 0
            }
        
        # Count by type
        by_type = defaultdict(int)
        by_die = defaultdict(int)
        critical_hits = 0
        critical_failures = 0
        
        results = []
        
        for roll in rolls:
            by_type[roll.roll_type] += 1
            
            # Parse dice formula to get die type
            if 'd' in roll.formula.lower():
                die_type = roll.formula.lower().split('d')[1].split('+')[0].split('-')[0].strip()
                by_die[f"d{die_type}"] += 1
            
            # Check for crits (d20 rolls)
            if 'd20' in roll.formula.lower():
                if roll.result >= 20:
                    critical_hits += 1
                elif roll.result <= 1:
                    critical_failures += 1
            
            results.append(roll.result)
        
        return {
            "total_rolls": len(rolls),
            "by_type": dict(by_type),
            "by_die": dict(by_die),
            "critical_hits": critical_hits,
            "critical_failures": critical_failures,
            "average_result": sum(results) / len(results) if results else 0,
            "highest_roll": max(results) if results else 0,
            "lowest_roll": min(results) if results else 0
        }
    
    def get_combat_stats(self, session_id: Optional[int] = None) -> Dict:
        """Get combat statistics.
        
        Args:
            session_id: Optional session filter
            
        Returns:
            Dictionary with combat statistics
        """
        if session_id:
            stmt = select(CombatEncounter).where(
                CombatEncounter.session_id == session_id
            )
        else:
            stmt = select(CombatEncounter)
        
        encounters = list(self.db.exec(stmt).all())
        
        if not encounters:
            return {
                "total_encounters": 0,
                "active_encounters": 0,
                "completed_encounters": 0,
                "average_rounds": 0,
                "total_rounds": 0
            }
        
        active = sum(1 for e in encounters if e.is_active)
        completed = len(encounters) - active
        
        rounds = [e.round_number for e in encounters if not e.is_active and e.round_number > 0]
        
        return {
            "total_encounters": len(encounters),
            "active_encounters": active,
            "completed_encounters": completed,
            "average_rounds": sum(rounds) / len(rounds) if rounds else 0,
            "total_rounds": sum(rounds) if rounds else 0
        }
    
    def get_character_stats(self, character_id: int) -> Dict:
        """Get statistics for a specific character.
        
        Args:
            character_id: Character ID
            
        Returns:
            Dictionary with character statistics
        """
        character = self.db.get(Character, character_id)
        if not character:
            return {}
        
        # Get dice rolls
        dice_stats = self.get_dice_stats(character_id=character_id)
        
        # Get messages sent (if character has messages)
        stmt = select(Message).where(Message.sender_name == character.name)
        messages = len(list(self.db.exec(stmt).all()))
        
        return {
            "character_id": character.id,
            "name": character.name,
            "level": character.level,
            "experience": character.experience_points,
            "dice_stats": dice_stats,
            "messages_sent": messages,
            "current_hp": character.current_hp,
            "max_hp": character.max_hp,
            "hp_percentage": (character.current_hp / character.max_hp * 100) if character.max_hp > 0 else 0
        }
    
    def get_session_stats(self, session_id: int) -> Dict:
        """Get comprehensive session statistics.
        
        Args:
            session_id: Session ID
            
        Returns:
            Dictionary with session statistics
        """
        dice_stats = self.get_dice_stats(session_id=session_id)
        combat_stats = self.get_combat_stats(session_id=session_id)
        
        # Get message stats
        stmt = select(Message).where(Message.session_id == session_id)
        messages = list(self.db.exec(stmt).all())
        
        by_sender = defaultdict(int)
        by_type = defaultdict(int)
        
        for msg in messages:
            by_sender[msg.sender_name] += 1
            by_type[msg.message_type] += 1
        
        # Calculate duration
        if messages:
            timestamps = [m.created_at for m in messages if m.created_at]
            if timestamps:
                duration = max(timestamps) - min(timestamps)
                duration_minutes = duration.total_seconds() / 60
            else:
                duration_minutes = 0
        else:
            duration_minutes = 0
        
        return {
            "session_id": session_id,
            "total_messages": len(messages),
            "messages_by_sender": dict(by_sender),
            "messages_by_type": dict(by_type),
            "duration_minutes": duration_minutes,
            "dice_stats": dice_stats,
            "combat_stats": combat_stats
        }
    
    def get_player_activity(
        self,
        session_id: int,
        days: int = 7
    ) -> Dict:
        """Get player activity over time.
        
        Args:
            session_id: Session ID
            days: Number of days to look back
            
        Returns:
            Dictionary with activity data
        """
        cutoff = datetime.now(UTC) - timedelta(days=days)
        
        stmt = select(Message).where(
            Message.session_id == session_id,
            Message.created_at >= cutoff
        ).order_by(Message.created_at)
        
        messages = list(self.db.exec(stmt).all())
        
        # Group by day and sender
        activity_by_day = defaultdict(lambda: defaultdict(int))
        
        for msg in messages:
            if msg.created_at:
                day = msg.created_at.date().isoformat()
                activity_by_day[day][msg.sender_name] += 1
        
        return {
            "period_days": days,
            "cutoff_date": cutoff.isoformat(),
            "activity_by_day": {
                day: dict(senders)
                for day, senders in activity_by_day.items()
            },
            "total_messages": len(messages)
        }
    
    def get_leaderboard(self, session_id: int, metric: str = "messages") -> List[Dict]:
        """Get a leaderboard for a specific metric.
        
        Args:
            session_id: Session ID
            metric: Metric to rank by ('messages', 'rolls', 'crits')
            
        Returns:
            List of rankings
        """
        if metric == "messages":
            stmt = select(Message).where(Message.session_id == session_id)
            items = list(self.db.exec(stmt).all())
            
            counts = defaultdict(int)
            for msg in items:
                counts[msg.sender_name] += 1
            
            rankings = [
                {"player": sender, "count": count}
                for sender, count in sorted(counts.items(), key=lambda x: x[1], reverse=True)
            ]
            
        elif metric == "rolls":
            stmt = select(Roll).where(Roll.session_id == session_id)
            rolls = list(self.db.exec(stmt).all())
            
            counts = defaultdict(int)
            for roll in rolls:
                if roll.character:
                    counts[roll.character.name] += 1
            
            rankings = [
                {"player": name, "count": count}
                for name, count in sorted(counts.items(), key=lambda x: x[1], reverse=True)
            ]
            
        elif metric == "crits":
            stmt = select(Roll).where(
                Roll.session_id == session_id,
                Roll.formula.ilike('%d20%')
            )
            rolls = list(self.db.exec(stmt).all())
            
            counts = defaultdict(int)
            for roll in rolls:
                if roll.result >= 20 and roll.character:
                    counts[roll.character.name] += 1
            
            rankings = [
                {"player": name, "count": count}
                for name, count in sorted(counts.items(), key=lambda x: x[1], reverse=True)
            ]
        
        else:
            rankings = []
        
        return rankings
    
    def format_stats_report(self, stats: Dict) -> str:
        """Format statistics as a readable report.
        
        Args:
            stats: Statistics dictionary
            
        Returns:
            Formatted report string
        """
        lines = ["=== STATISTICS REPORT ===\n"]
        
        if "session_id" in stats:
            lines.append(f"Session ID: {stats['session_id']}")
            lines.append(f"Total Messages: {stats.get('total_messages', 0)}")
            lines.append(f"Duration: {stats.get('duration_minutes', 0):.1f} minutes\n")
        
        if "dice_stats" in stats:
            dice = stats["dice_stats"]
            lines.append("Dice Statistics:")
            lines.append(f"  Total Rolls: {dice.get('total_rolls', 0)}")
            lines.append(f"  Critical Hits: {dice.get('critical_hits', 0)}")
            lines.append(f"  Critical Failures: {dice.get('critical_failures', 0)}")
            lines.append(f"  Average Result: {dice.get('average_result', 0):.2f}\n")
        
        if "combat_stats" in stats:
            combat = stats["combat_stats"]
            lines.append("Combat Statistics:")
            lines.append(f"  Total Encounters: {combat.get('total_encounters', 0)}")
            lines.append(f"  Active: {combat.get('active_encounters', 0)}")
            lines.append(f"  Completed: {combat.get('completed_encounters', 0)}")
            lines.append(f"  Average Rounds: {combat.get('average_rounds', 0):.1f}\n")
        
        return "\n".join(lines)
