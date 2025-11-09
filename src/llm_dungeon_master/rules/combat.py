"""Combat management system."""

from datetime import datetime, UTC
from typing import Optional, NamedTuple
from enum import Enum
from dataclasses import dataclass
from sqlmodel import Session as DBSession, select

from ..models import Character, Session
from .dice import resolve_attack, roll_damage, roll_die, AdvantageType


class ActionType(Enum):
    """Types of combat actions."""
    ACTION = "action"
    BONUS_ACTION = "bonus_action"
    REACTION = "reaction"
    FREE_ACTION = "free_action"


class AttackResult(NamedTuple):
    """Result of an attack."""
    hit: bool
    damage: int
    is_critical: bool
    attack_roll: int
    target_ac: int
    attacker_name: str
    target_name: str
    

@dataclass
class Combatant:
    """A combatant in combat."""
    character_id: int
    name: str
    initiative: int
    current_hp: int
    max_hp: int
    armor_class: int
    has_acted: bool = False
    has_bonus_action: bool = True
    has_reaction: bool = True
    
    @property
    def is_alive(self) -> bool:
        """Check if combatant is alive."""
        return self.current_hp > 0
    
    @property
    def is_conscious(self) -> bool:
        """Check if combatant is conscious."""
        return self.current_hp > 0


@dataclass
class CombatState:
    """Current state of combat."""
    session_id: int
    round_number: int
    combatants: list[Combatant]
    current_turn_index: int
    combat_log: list[str]
    started_at: datetime
    
    @property
    def current_combatant(self) -> Optional[Combatant]:
        """Get the current combatant."""
        if 0 <= self.current_turn_index < len(self.combatants):
            return self.combatants[self.current_turn_index]
        return None
    
    @property
    def is_combat_over(self) -> bool:
        """Check if combat has ended."""
        alive_combatants = [c for c in self.combatants if c.is_alive]
        return len(alive_combatants) <= 1


class CombatManager:
    """Manager for combat encounters."""
    
    def __init__(self):
        """Initialize combat manager."""
        self._active_combats: dict[int, CombatState] = {}
    
    def start_combat(
        self,
        db: DBSession,
        session_id: int,
        character_ids: list[int]
    ) -> CombatState:
        """Start a new combat encounter.
        
        Args:
            db: Database session
            session_id: Session ID
            character_ids: List of character IDs to include
            
        Returns:
            CombatState with initiative order
        """
        # Get characters from database
        statement = select(Character).where(Character.id.in_(character_ids))
        characters = db.exec(statement).all()
        
        # Roll initiative for each character
        combatants = []
        for char in characters:
            # Roll initiative (d20 + Dex modifier)
            dex_modifier = (char.dexterity - 10) // 2
            initiative = roll_die(20) + dex_modifier
            
            combatant = Combatant(
                character_id=char.id,
                name=char.name,
                initiative=initiative,
                current_hp=char.current_hp,
                max_hp=char.max_hp,
                armor_class=char.armor_class
            )
            combatants.append(combatant)
        
        # Sort by initiative (highest first)
        combatants.sort(key=lambda c: c.initiative, reverse=True)
        
        # Create combat state
        combat_state = CombatState(
            session_id=session_id,
            round_number=1,
            combatants=combatants,
            current_turn_index=0,
            combat_log=[f"Combat started! Initiative order: {', '.join(f'{c.name} ({c.initiative})' for c in combatants)}"],
            started_at=datetime.now(UTC)
        )
        
        # Store active combat
        self._active_combats[session_id] = combat_state
        
        return combat_state
    
    def get_combat(self, session_id: int) -> Optional[CombatState]:
        """Get active combat for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            CombatState if combat is active, None otherwise
        """
        return self._active_combats.get(session_id)
    
    def next_turn(self, session_id: int) -> Optional[CombatState]:
        """Advance to the next turn.
        
        Args:
            session_id: Session ID
            
        Returns:
            Updated CombatState or None if no active combat
        """
        combat = self._active_combats.get(session_id)
        if not combat:
            return None
        
        # Reset current combatant's actions
        current = combat.current_combatant
        if current:
            current.has_acted = False
            current.has_bonus_action = True
            current.has_reaction = True
        
        # Move to next combatant
        combat.current_turn_index += 1
        
        # If we've gone through all combatants, start new round
        if combat.current_turn_index >= len(combat.combatants):
            combat.current_turn_index = 0
            combat.round_number += 1
            combat.combat_log.append(f"--- Round {combat.round_number} ---")
        
        # Skip defeated combatants
        while combat.current_combatant and not combat.current_combatant.is_alive:
            combat.current_turn_index += 1
            if combat.current_turn_index >= len(combat.combatants):
                combat.current_turn_index = 0
                combat.round_number += 1
                combat.combat_log.append(f"--- Round {combat.round_number} ---")
        
        # Check if combat is over
        if combat.is_combat_over:
            alive = [c for c in combat.combatants if c.is_alive]
            if alive:
                combat.combat_log.append(f"Combat ended! {alive[0].name} is victorious!")
            else:
                combat.combat_log.append("Combat ended! All combatants defeated.")
            del self._active_combats[session_id]
        
        return combat
    
    def resolve_attack(
        self,
        session_id: int,
        attacker_id: int,
        target_id: int,
        attack_bonus: int,
        damage_formula: str,
        advantage: AdvantageType = AdvantageType.NORMAL
    ) -> Optional[AttackResult]:
        """Resolve an attack between two combatants.
        
        Args:
            session_id: Session ID
            attacker_id: Attacker character ID
            target_id: Target character ID
            attack_bonus: Attack bonus to add to roll
            damage_formula: Damage dice formula
            advantage: Type of advantage
            
        Returns:
            AttackResult or None if combat not active
        """
        combat = self._active_combats.get(session_id)
        if not combat:
            return None
        
        # Find attacker and target
        attacker = next((c for c in combat.combatants if c.character_id == attacker_id), None)
        target = next((c for c in combat.combatants if c.character_id == target_id), None)
        
        if not attacker or not target:
            return None
        
        # Resolve attack roll
        attack_check = resolve_attack(attack_bonus, target.armor_class, advantage)
        
        damage = 0
        if attack_check.success:
            # Roll damage
            damage_roll = roll_damage(damage_formula, attack_check.is_critical)
            damage = max(0, damage_roll.total)  # Minimum 0 damage
            
            # Apply damage
            target.current_hp = max(0, target.current_hp - damage)
            
            # Log the attack
            if attack_check.is_critical:
                combat.combat_log.append(
                    f"🎯 CRITICAL HIT! {attacker.name} hits {target.name} for {damage} damage! "
                    f"({target.current_hp}/{target.max_hp} HP remaining)"
                )
            else:
                combat.combat_log.append(
                    f"⚔️ {attacker.name} hits {target.name} for {damage} damage! "
                    f"({target.current_hp}/{target.max_hp} HP remaining)"
                )
            
            # Check if target is defeated
            if not target.is_alive:
                combat.combat_log.append(f"💀 {target.name} has been defeated!")
        else:
            # Miss
            if attack_check.is_critical_fail:
                combat.combat_log.append(f"💥 {attacker.name} critically misses {target.name}!")
            else:
                combat.combat_log.append(f"⚫ {attacker.name} misses {target.name}.")
        
        return AttackResult(
            hit=attack_check.success,
            damage=damage,
            is_critical=attack_check.is_critical,
            attack_roll=attack_check.roll,
            target_ac=target.armor_class,
            attacker_name=attacker.name,
            target_name=target.name
        )
    
    def apply_damage(
        self,
        session_id: int,
        character_id: int,
        damage: int
    ) -> bool:
        """Apply damage to a character.
        
        Args:
            session_id: Session ID
            character_id: Character ID
            damage: Damage amount
            
        Returns:
            True if character is still alive, False otherwise
        """
        combat = self._active_combats.get(session_id)
        if not combat:
            return False
        
        # Find character
        character = next((c for c in combat.combatants if c.character_id == character_id), None)
        if not character:
            return False
        
        # Apply damage
        character.current_hp = max(0, character.current_hp - damage)
        
        # Log
        combat.combat_log.append(
            f"{character.name} takes {damage} damage! "
            f"({character.current_hp}/{character.max_hp} HP remaining)"
        )
        
        if not character.is_alive:
            combat.combat_log.append(f"💀 {character.name} has been defeated!")
        
        return character.is_alive
    
    def apply_healing(
        self,
        session_id: int,
        character_id: int,
        healing: int
    ) -> bool:
        """Apply healing to a character.
        
        Args:
            session_id: Session ID
            character_id: Character ID
            healing: Healing amount
            
        Returns:
            True if successful, False otherwise
        """
        combat = self._active_combats.get(session_id)
        if not combat:
            return False
        
        # Find character
        character = next((c for c in combat.combatants if c.character_id == character_id), None)
        if not character:
            return False
        
        # Apply healing
        old_hp = character.current_hp
        character.current_hp = min(character.max_hp, character.current_hp + healing)
        actual_healing = character.current_hp - old_hp
        
        # Log
        combat.combat_log.append(
            f"💚 {character.name} heals {actual_healing} HP! "
            f"({character.current_hp}/{character.max_hp} HP)"
        )
        
        return True
    
    def end_combat(self, session_id: int) -> bool:
        """End combat for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if combat was ended, False if no active combat
        """
        if session_id in self._active_combats:
            combat = self._active_combats[session_id]
            combat.combat_log.append("Combat ended by DM.")
            del self._active_combats[session_id]
            return True
        return False
    
    def get_initiative_order(self, session_id: int) -> list[dict]:
        """Get the initiative order for display.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of combatant info dictionaries
        """
        combat = self._active_combats.get(session_id)
        if not combat:
            return []
        
        return [
            {
                "name": c.name,
                "initiative": c.initiative,
                "hp": f"{c.current_hp}/{c.max_hp}",
                "ac": c.armor_class,
                "is_current": combat.current_combatant == c,
                "is_alive": c.is_alive
            }
            for c in combat.combatants
        ]
