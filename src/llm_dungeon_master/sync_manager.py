"""Synchronization manager for handling conflicts in multiplayer sessions."""

from datetime import datetime, UTC
from typing import Optional, List, Dict, Tuple
from sqlmodel import Session as DBSession, select
from enum import Enum

from .models import Turn, TurnAction, Character, Session


class ConflictType(str, Enum):
    """Types of conflicts that can occur."""
    SIMULTANEOUS_ACTION = "simultaneous_action"  # Multiple players act at once
    INITIATIVE_DISPUTE = "initiative_dispute"  # Initiative order conflict
    RESOURCE_CONFLICT = "resource_conflict"  # Multiple players use same resource
    STATE_MISMATCH = "state_mismatch"  # Client/server state differs
    TURN_ORDER_VIOLATION = "turn_order_violation"  # Acting out of turn


class ResolutionStrategy(str, Enum):
    """Strategies for resolving conflicts."""
    FIRST_COME_FIRST_SERVE = "first_come_first_serve"  # First action wins
    INITIATIVE_ORDER = "initiative_order"  # Higher initiative wins
    DM_DECISION = "dm_decision"  # DM must decide
    REROLL = "reroll"  # Re-roll to decide
    CANCEL_ALL = "cancel_all"  # Cancel all conflicting actions


class ConflictResolution:
    """Represents a conflict and its resolution."""
    
    def __init__(
        self,
        conflict_id: str,
        conflict_type: ConflictType,
        session_id: int,
        involved_character_ids: List[int],
        description: str,
        timestamp: datetime
    ):
        self.conflict_id = conflict_id
        self.conflict_type = conflict_type
        self.session_id = session_id
        self.involved_character_ids = involved_character_ids
        self.description = description
        self.timestamp = timestamp
        self.resolution_strategy: Optional[ResolutionStrategy] = None
        self.resolved_at: Optional[datetime] = None
        self.winner_character_id: Optional[int] = None
        self.resolution_notes: Optional[str] = None


class SyncManager:
    """Manages synchronization and conflict resolution."""
    
    def __init__(self, db_session: DBSession):
        self.db = db_session
        self.active_conflicts: Dict[str, ConflictResolution] = {}
    
    def detect_conflicts(
        self,
        session_id: int,
        actions: List[Dict[str, any]]
    ) -> List[ConflictResolution]:
        """
        Detect conflicts in a set of actions.
        
        Args:
            session_id: The session ID
            actions: List of action dictionaries with character_id, action_type, etc.
            
        Returns:
            List of detected conflicts
        """
        conflicts = []
        
        # Check for simultaneous actions from different players
        action_times = {}
        for action in actions:
            char_id = action.get("character_id")
            timestamp = action.get("timestamp", datetime.now(UTC))
            
            if char_id in action_times:
                # Potential simultaneous action
                time_diff = abs((timestamp - action_times[char_id]).total_seconds())
                if time_diff < 1.0:  # Within 1 second = simultaneous
                    conflict = ConflictResolution(
                        conflict_id=f"conflict_{session_id}_{len(conflicts)}",
                        conflict_type=ConflictType.SIMULTANEOUS_ACTION,
                        session_id=session_id,
                        involved_character_ids=[char_id],
                        description=f"Character {char_id} attempted multiple actions simultaneously",
                        timestamp=timestamp
                    )
                    conflicts.append(conflict)
            else:
                action_times[char_id] = timestamp
        
        # Check for turn order violations
        current_turn = self._get_current_turn(session_id)
        if current_turn:
            for action in actions:
                char_id = action.get("character_id")
                if char_id != current_turn.character_id:
                    conflict = ConflictResolution(
                        conflict_id=f"conflict_{session_id}_{len(conflicts)}",
                        conflict_type=ConflictType.TURN_ORDER_VIOLATION,
                        session_id=session_id,
                        involved_character_ids=[char_id, current_turn.character_id],
                        description=f"Character {char_id} acted out of turn (current: {current_turn.character_id})",
                        timestamp=datetime.now(UTC)
                    )
                    conflicts.append(conflict)
        
        # Check for resource conflicts (e.g., two players targeting same item)
        targets = {}
        for action in actions:
            target = action.get("target")
            char_id = action.get("character_id")
            if target and target in targets:
                conflict = ConflictResolution(
                    conflict_id=f"conflict_{session_id}_{len(conflicts)}",
                    conflict_type=ConflictType.RESOURCE_CONFLICT,
                    session_id=session_id,
                    involved_character_ids=[char_id, targets[target]],
                    description=f"Multiple characters targeting {target}",
                    timestamp=datetime.now(UTC)
                )
                conflicts.append(conflict)
            elif target:
                targets[target] = char_id
        
        # Store active conflicts
        for conflict in conflicts:
            self.active_conflicts[conflict.conflict_id] = conflict
        
        return conflicts
    
    def resolve_conflict(
        self,
        conflict_id: str,
        strategy: ResolutionStrategy,
        winner_character_id: Optional[int] = None,
        notes: Optional[str] = None
    ) -> bool:
        """
        Resolve a conflict using the specified strategy.
        
        Args:
            conflict_id: The conflict ID to resolve
            strategy: The resolution strategy to use
            winner_character_id: Optional winning character ID
            notes: Optional resolution notes
            
        Returns:
            True if resolved successfully
        """
        conflict = self.active_conflicts.get(conflict_id)
        if not conflict:
            return False
        
        conflict.resolution_strategy = strategy
        conflict.resolved_at = datetime.now(UTC)
        conflict.resolution_notes = notes
        
        if strategy == ResolutionStrategy.INITIATIVE_ORDER:
            # Use initiative order to determine winner
            winner_character_id = self._resolve_by_initiative(
                conflict.session_id,
                conflict.involved_character_ids
            )
        elif strategy == ResolutionStrategy.REROLL:
            # Simulate a reroll (random selection)
            import secrets
            winner_character_id = secrets.choice(conflict.involved_character_ids)
        elif strategy == ResolutionStrategy.FIRST_COME_FIRST_SERVE:
            # First character ID wins (assuming list is in order)
            winner_character_id = conflict.involved_character_ids[0]
        
        conflict.winner_character_id = winner_character_id
        
        # Remove from active conflicts
        del self.active_conflicts[conflict_id]
        
        return True
    
    def get_sync_stats(self, session_id: int) -> Dict[str, any]:
        """
        Get synchronization statistics for a session.
        
        Returns:
            Dictionary with sync stats
        """
        # Count active conflicts
        session_conflicts = [
            c for c in self.active_conflicts.values()
            if c.session_id == session_id
        ]
        
        # Count by type
        conflict_types = {}
        for conflict in session_conflicts:
            ct = conflict.conflict_type
            conflict_types[ct] = conflict_types.get(ct, 0) + 1
        
        return {
            "session_id": session_id,
            "active_conflicts": len(session_conflicts),
            "conflicts_by_type": conflict_types,
            "conflicts": [
                {
                    "conflict_id": c.conflict_id,
                    "type": c.conflict_type,
                    "involved_characters": c.involved_character_ids,
                    "description": c.description,
                    "timestamp": c.timestamp,
                    "resolved": c.resolved_at is not None
                }
                for c in session_conflicts
            ]
        }
    
    def check_state_consistency(
        self,
        session_id: int,
        client_state: Dict[str, any]
    ) -> Tuple[bool, List[str]]:
        """
        Check if client state matches server state.
        
        Args:
            session_id: The session ID
            client_state: Dictionary with client's view of game state
            
        Returns:
            Tuple of (is_consistent, list_of_discrepancies)
        """
        discrepancies = []
        
        # Check current turn
        current_turn = self._get_current_turn(session_id)
        client_turn_id = client_state.get("current_turn_character_id")
        
        if current_turn:
            if client_turn_id != current_turn.character_id:
                discrepancies.append(
                    f"Turn mismatch: client={client_turn_id}, server={current_turn.character_id}"
                )
        
        # Check round number
        if current_turn:
            client_round = client_state.get("round_number")
            if client_round != current_turn.round_number:
                discrepancies.append(
                    f"Round mismatch: client={client_round}, server={current_turn.round_number}"
                )
        
        # Check character HP
        client_characters = client_state.get("characters", {})
        for char_id_str, client_char in client_characters.items():
            char_id = int(char_id_str)
            server_char = self.db.get(Character, char_id)
            if server_char:
                client_hp = client_char.get("current_hp")
                if client_hp != server_char.current_hp:
                    discrepancies.append(
                        f"HP mismatch for character {char_id}: client={client_hp}, server={server_char.current_hp}"
                    )
        
        is_consistent = len(discrepancies) == 0
        return is_consistent, discrepancies
    
    def force_sync(self, session_id: int) -> Dict[str, any]:
        """
        Force synchronization by returning authoritative server state.
        
        Returns:
            Dictionary with complete server state
        """
        # Get current turn
        current_turn = self._get_current_turn(session_id)
        
        # Get all turns
        turns_stmt = select(Turn).where(
            Turn.session_id == session_id
        ).order_by(Turn.turn_order)
        turns = list(self.db.exec(turns_stmt).all())
        
        # Get session details
        session = self.db.get(Session, session_id)
        
        return {
            "session_id": session_id,
            "session_name": session.name if session else "Unknown",
            "current_turn": {
                "character_id": current_turn.character_id if current_turn else None,
                "character_name": current_turn.character_name if current_turn else None,
                "round_number": current_turn.round_number if current_turn else 1
            } if current_turn else None,
            "turn_queue": [
                {
                    "character_id": turn.character_id,
                    "character_name": turn.character_name,
                    "initiative": turn.initiative,
                    "status": turn.status,
                    "turn_order": turn.turn_order
                }
                for turn in turns
            ],
            "timestamp": datetime.now(UTC)
        }
    
    def _get_current_turn(self, session_id: int) -> Optional[Turn]:
        """Get the current active turn."""
        statement = select(Turn).where(
            Turn.session_id == session_id,
            Turn.status == "active"
        )
        return self.db.exec(statement).first()
    
    def _resolve_by_initiative(
        self,
        session_id: int,
        character_ids: List[int]
    ) -> Optional[int]:
        """Resolve conflict by initiative order."""
        highest_initiative = -1
        winner_id = None
        
        for char_id in character_ids:
            statement = select(Turn).where(
                Turn.session_id == session_id,
                Turn.character_id == char_id
            )
            turn = self.db.exec(statement).first()
            
            if turn and turn.initiative > highest_initiative:
                highest_initiative = turn.initiative
                winner_id = char_id
        
        return winner_id
