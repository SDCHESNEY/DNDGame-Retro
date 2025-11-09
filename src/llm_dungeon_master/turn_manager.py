"""Turn management system for multiplayer sessions."""

from datetime import datetime, UTC
from typing import Optional, List, Dict
from sqlmodel import Session as DBSession, select
from enum import Enum

from .models import Turn, TurnAction, SessionPlayer, Character, CombatEncounter


class TurnStatus(str, Enum):
    """Status of a turn."""
    WAITING = "waiting"  # Waiting for turn
    ACTIVE = "active"  # Currently taking turn
    READY = "ready"  # Ready for next turn
    COMPLETED = "completed"  # Turn finished
    SKIPPED = "skipped"  # Turn was skipped


class TurnManager:
    """Manages turn-based gameplay in multiplayer sessions."""
    
    def __init__(self, db_session: DBSession):
        self.db = db_session
    
    def start_turn_queue(
        self,
        session_id: int,
        player_character_ids: List[int],
        combat_encounter_id: Optional[int] = None
    ) -> List[Turn]:
        """
        Start a turn queue for a session.
        
        Args:
            session_id: The session ID
            player_character_ids: List of character IDs to include
            combat_encounter_id: Optional combat encounter ID
            
        Returns:
            List of Turn objects in initiative order
        """
        # If combat encounter provided, use combat initiative
        if combat_encounter_id:
            encounter = self.db.get(CombatEncounter, combat_encounter_id)
            if not encounter or not encounter.is_active:
                raise ValueError(f"Combat encounter {combat_encounter_id} not found or inactive")
            
            # Get combatants in initiative order
            combatants = sorted(
                encounter.combatants,
                key=lambda c: c.initiative,
                reverse=True
            )
            
            # Create turns from combatants
            turns = []
            for order, combatant in enumerate(combatants):
                turn = Turn(
                    session_id=session_id,
                    character_id=combatant.character_id,
                    character_name=combatant.name,
                    turn_order=order,
                    initiative=combatant.initiative,
                    status=TurnStatus.ACTIVE if order == 0 else TurnStatus.WAITING,
                    combat_encounter_id=combat_encounter_id,
                    is_npc=combatant.is_npc
                )
                self.db.add(turn)
                turns.append(turn)
            
            self.db.commit()
            return turns
        
        # Non-combat turn order (use dexterity or simple order)
        characters = []
        for char_id in player_character_ids:
            char = self.db.get(Character, char_id)
            if char:
                characters.append(char)
        
        # Sort by initiative bonus (dexterity modifier)
        characters.sort(
            key=lambda c: c.initiative_bonus,
            reverse=True
        )
        
        # Create turns
        turns = []
        for order, character in enumerate(characters):
            turn = Turn(
                session_id=session_id,
                character_id=character.id,
                character_name=character.name,
                turn_order=order,
                initiative=character.initiative_bonus,
                status=TurnStatus.ACTIVE if order == 0 else TurnStatus.WAITING,
                is_npc=False
            )
            self.db.add(turn)
            turns.append(turn)
        
        self.db.commit()
        return turns
    
    def get_current_turn(self, session_id: int) -> Optional[Turn]:
        """Get the current active turn for a session."""
        statement = select(Turn).where(
            Turn.session_id == session_id,
            Turn.status == TurnStatus.ACTIVE
        )
        return self.db.exec(statement).first()
    
    def get_turn_queue(self, session_id: int) -> List[Turn]:
        """Get all turns for a session in order."""
        statement = select(Turn).where(
            Turn.session_id == session_id
        ).order_by(Turn.turn_order)
        return list(self.db.exec(statement).all())
    
    def advance_turn(self, session_id: int) -> Turn:
        """
        Advance to the next turn in the queue.
        
        Returns:
            The newly active Turn
        """
        # Get current turn
        current = self.get_current_turn(session_id)
        if not current:
            raise ValueError(f"No active turn for session {session_id}")
        
        # Mark current turn as completed
        current.status = TurnStatus.COMPLETED
        current.ended_at = datetime.now(UTC)
        
        # Get all turns in order
        turns = self.get_turn_queue(session_id)
        
        # Find next turn
        current_index = None
        for i, turn in enumerate(turns):
            if turn.id == current.id:
                current_index = i
                break
        
        if current_index is None:
            raise ValueError("Current turn not found in queue")
        
        # Wrap around to start if at end
        next_index = (current_index + 1) % len(turns)
        next_turn = turns[next_index]
        
        # If we've wrapped around, increment round
        if next_index == 0:
            # Reset all turns and increment round
            for turn in turns:
                if turn.status == TurnStatus.COMPLETED:
                    turn.status = TurnStatus.WAITING
                    turn.round_number += 1
                    turn.started_at = None
                    turn.ended_at = None
        
        # Activate next turn
        next_turn.status = TurnStatus.ACTIVE
        next_turn.started_at = datetime.now(UTC)
        
        self.db.commit()
        self.db.refresh(next_turn)
        return next_turn
    
    def set_player_ready(self, session_id: int, character_id: int, ready: bool = True) -> bool:
        """
        Mark a player as ready for their turn.
        
        Returns:
            True if status updated successfully
        """
        statement = select(Turn).where(
            Turn.session_id == session_id,
            Turn.character_id == character_id
        )
        turn = self.db.exec(statement).first()
        
        if not turn:
            return False
        
        if ready:
            if turn.status == TurnStatus.WAITING:
                turn.status = TurnStatus.READY
        else:
            if turn.status == TurnStatus.READY:
                turn.status = TurnStatus.WAITING
        
        self.db.commit()
        return True
    
    def check_all_ready(self, session_id: int) -> Dict[str, any]:
        """
        Check if all players are ready.
        
        Returns:
            Dictionary with ready status and player details
        """
        turns = self.get_turn_queue(session_id)
        
        ready_count = sum(
            1 for turn in turns
            if turn.status in [TurnStatus.READY, TurnStatus.ACTIVE]
        )
        
        return {
            "all_ready": ready_count == len(turns),
            "ready_count": ready_count,
            "total_count": len(turns),
            "players": [
                {
                    "character_id": turn.character_id,
                    "character_name": turn.character_name,
                    "status": turn.status,
                    "is_ready": turn.status in [TurnStatus.READY, TurnStatus.ACTIVE]
                }
                for turn in turns
            ]
        }
    
    def record_action(
        self,
        session_id: int,
        character_id: int,
        action_type: str,
        description: str,
        cost: Optional[str] = None
    ) -> TurnAction:
        """Record an action taken during a turn."""
        # Get current turn for this character
        statement = select(Turn).where(
            Turn.session_id == session_id,
            Turn.character_id == character_id,
            Turn.status == TurnStatus.ACTIVE
        )
        turn = self.db.exec(statement).first()
        
        if not turn:
            raise ValueError(f"No active turn for character {character_id}")
        
        action = TurnAction(
            turn_id=turn.id,
            action_type=action_type,
            description=description,
            cost=cost or "action"
        )
        self.db.add(action)
        self.db.commit()
        self.db.refresh(action)
        return action
    
    def get_turn_history(
        self,
        session_id: int,
        limit: int = 50
    ) -> List[Dict[str, any]]:
        """Get recent turn history with actions."""
        statement = select(Turn).where(
            Turn.session_id == session_id
        ).order_by(Turn.round_number.desc(), Turn.turn_order.desc()).limit(limit)
        
        turns = list(self.db.exec(statement).all())
        
        history = []
        for turn in turns:
            # Get actions for this turn
            action_stmt = select(TurnAction).where(
                TurnAction.turn_id == turn.id
            ).order_by(TurnAction.timestamp)
            actions = list(self.db.exec(action_stmt).all())
            
            history.append({
                "character_name": turn.character_name,
                "round": turn.round_number,
                "status": turn.status,
                "started_at": turn.started_at,
                "ended_at": turn.ended_at,
                "actions": [
                    {
                        "type": action.action_type,
                        "description": action.description,
                        "cost": action.cost,
                        "timestamp": action.timestamp
                    }
                    for action in actions
                ]
            })
        
        return history
    
    def skip_turn(self, session_id: int, character_id: int) -> Turn:
        """Skip a character's turn."""
        statement = select(Turn).where(
            Turn.session_id == session_id,
            Turn.character_id == character_id,
            Turn.status == TurnStatus.ACTIVE
        )
        turn = self.db.exec(statement).first()
        
        if not turn:
            raise ValueError(f"No active turn for character {character_id}")
        
        turn.status = TurnStatus.SKIPPED
        turn.ended_at = datetime.now(UTC)
        self.db.commit()
        
        # Advance to next turn
        return self.advance_turn(session_id)
    
    def end_turn_queue(self, session_id: int):
        """End all turns for a session."""
        turns = self.get_turn_queue(session_id)
        for turn in turns:
            if turn.status != TurnStatus.COMPLETED:
                turn.status = TurnStatus.COMPLETED
                turn.ended_at = datetime.now(UTC)
        self.db.commit()
