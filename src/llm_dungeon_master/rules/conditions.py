"""Status effects and condition management system."""

from datetime import datetime, UTC
from typing import Optional
from enum import Enum
from dataclasses import dataclass, field


class ConditionType(Enum):
    """D&D 5e condition types."""
    BLINDED = "blinded"
    CHARMED = "charmed"
    DEAFENED = "deafened"
    FRIGHTENED = "frightened"
    GRAPPLED = "grappled"
    INCAPACITATED = "incapacitated"
    INVISIBLE = "invisible"
    PARALYZED = "paralyzed"
    PETRIFIED = "petrified"
    POISONED = "poisoned"
    PRONE = "prone"
    RESTRAINED = "restrained"
    STUNNED = "stunned"
    UNCONSCIOUS = "unconscious"
    EXHAUSTION = "exhaustion"
    
    @property
    def description(self) -> str:
        """Get condition description."""
        descriptions = {
            ConditionType.BLINDED: "Cannot see; auto-fail Perception checks; attacks have disadvantage; attacks against have advantage",
            ConditionType.CHARMED: "Cannot attack charmer or target with harmful effects; charmer has advantage on social checks",
            ConditionType.DEAFENED: "Cannot hear; auto-fail hearing-based Perception checks",
            ConditionType.FRIGHTENED: "Disadvantage on ability checks and attacks while source is in sight; cannot willingly move closer",
            ConditionType.GRAPPLED: "Speed is 0; ends if grappler is incapacitated or moved away",
            ConditionType.INCAPACITATED: "Cannot take actions or reactions",
            ConditionType.INVISIBLE: "Impossible to see without magic; attacks have advantage; attacks against have disadvantage",
            ConditionType.PARALYZED: "Incapacitated; can't move or speak; auto-fail Str/Dex saves; attacks have advantage; hits within 5ft are crits",
            ConditionType.PETRIFIED: "Transformed to stone; incapacitated; can't move or speak; unaware; resistant to all damage; immune to poison/disease",
            ConditionType.POISONED: "Disadvantage on attack rolls and ability checks",
            ConditionType.PRONE: "Disadvantage on attack rolls; attacks within 5ft have advantage; attacks beyond 5ft have disadvantage; costs half movement to stand",
            ConditionType.RESTRAINED: "Speed is 0; attacks have disadvantage; attacks against have advantage; disadvantage on Dex saves",
            ConditionType.STUNNED: "Incapacitated; can't move; can speak falteringly; auto-fail Str/Dex saves; attacks against have advantage",
            ConditionType.UNCONSCIOUS: "Incapacitated; can't move or speak; unaware; drops held items; falls prone; auto-fail Str/Dex saves; attacks have advantage; hits within 5ft are crits",
            ConditionType.EXHAUSTION: "Six levels of exhaustion with increasing penalties",
        }
        return descriptions.get(self, "Unknown condition")


class DurationType(Enum):
    """Types of condition duration."""
    INSTANT = "instant"  # Ends immediately
    ROUNDS = "rounds"  # Ends after N rounds
    MINUTES = "minutes"  # Ends after N minutes
    HOURS = "hours"  # Ends after N hours
    UNTIL_SAVE = "until_save"  # Ends on successful save
    UNTIL_DISPELLED = "until_dispelled"  # Requires dispel magic
    PERMANENT = "permanent"  # Permanent until removed


@dataclass
class Condition:
    """A condition applied to a character."""
    condition_type: ConditionType
    source: str
    duration_type: DurationType
    duration_value: int = 0
    rounds_remaining: Optional[int] = None
    save_dc: Optional[int] = None
    save_ability: Optional[str] = None
    applied_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    @property
    def is_expired(self) -> bool:
        """Check if condition has expired."""
        if self.duration_type == DurationType.INSTANT:
            return True
        if self.duration_type == DurationType.ROUNDS and self.rounds_remaining is not None:
            return self.rounds_remaining <= 0
        if self.duration_type in (DurationType.PERMANENT, DurationType.UNTIL_DISPELLED):
            return False
        return False
    
    @property
    def description(self) -> str:
        """Get condition description."""
        desc = f"{self.condition_type.value.title()}: {self.condition_type.description}"
        
        if self.duration_type == DurationType.ROUNDS and self.rounds_remaining:
            desc += f" (Ends in {self.rounds_remaining} rounds)"
        elif self.duration_type == DurationType.UNTIL_SAVE and self.save_dc:
            desc += f" (DC {self.save_dc} {self.save_ability or 'save'} to end)"
        elif self.duration_type == DurationType.PERMANENT:
            desc += " (Permanent)"
        
        desc += f" [Source: {self.source}]"
        return desc


@dataclass
class CharacterConditions:
    """All conditions affecting a character."""
    character_id: int
    character_name: str
    conditions: list[Condition] = field(default_factory=list)
    
    def has_condition(self, condition_type: ConditionType) -> bool:
        """Check if character has a specific condition."""
        return any(c.condition_type == condition_type and not c.is_expired for c in self.conditions)
    
    def get_condition(self, condition_type: ConditionType) -> Optional[Condition]:
        """Get a specific condition if present."""
        for condition in self.conditions:
            if condition.condition_type == condition_type and not condition.is_expired:
                return condition
        return None
    
    @property
    def active_conditions(self) -> list[Condition]:
        """Get all active conditions."""
        return [c for c in self.conditions if not c.is_expired]
    
    @property
    def is_incapacitated(self) -> bool:
        """Check if character is incapacitated."""
        incapacitating = {
            ConditionType.INCAPACITATED,
            ConditionType.PARALYZED,
            ConditionType.PETRIFIED,
            ConditionType.STUNNED,
            ConditionType.UNCONSCIOUS
        }
        return any(c.condition_type in incapacitating for c in self.active_conditions)
    
    @property
    def can_take_actions(self) -> bool:
        """Check if character can take actions."""
        return not self.is_incapacitated
    
    @property
    def can_move(self) -> bool:
        """Check if character can move."""
        if self.is_incapacitated:
            return False
        immobilizing = {ConditionType.GRAPPLED, ConditionType.RESTRAINED, ConditionType.PARALYZED}
        return not any(c.condition_type in immobilizing for c in self.active_conditions)


class ConditionManager:
    """Manager for character conditions."""
    
    def __init__(self):
        """Initialize condition manager."""
        self._character_conditions: dict[int, CharacterConditions] = {}
    
    def apply_condition(
        self,
        character_id: int,
        character_name: str,
        condition_type: ConditionType,
        source: str,
        duration_type: DurationType,
        duration_value: int = 0,
        save_dc: Optional[int] = None,
        save_ability: Optional[str] = None
    ) -> Condition:
        """Apply a condition to a character.
        
        Args:
            character_id: Character ID
            character_name: Character name
            condition_type: Type of condition
            source: Source of condition
            duration_type: How long it lasts
            duration_value: Duration value (rounds, minutes, etc.)
            save_dc: DC for saves to end condition
            save_ability: Ability for saves (Str, Dex, Con, etc.)
            
        Returns:
            Applied Condition
        """
        # Get or create character conditions
        if character_id not in self._character_conditions:
            self._character_conditions[character_id] = CharacterConditions(
                character_id=character_id,
                character_name=character_name
            )
        
        char_conditions = self._character_conditions[character_id]
        
        # Create condition
        condition = Condition(
            condition_type=condition_type,
            source=source,
            duration_type=duration_type,
            duration_value=duration_value,
            rounds_remaining=duration_value if duration_type == DurationType.ROUNDS else None,
            save_dc=save_dc,
            save_ability=save_ability
        )
        
        # Check if condition already exists
        existing = char_conditions.get_condition(condition_type)
        if existing and not existing.is_expired:
            # Update duration if new one is longer
            if (condition.duration_type == DurationType.ROUNDS and 
                existing.duration_type == DurationType.ROUNDS and
                existing.rounds_remaining is not None and
                condition.rounds_remaining is not None):
                if condition.rounds_remaining > existing.rounds_remaining:
                    existing.rounds_remaining = condition.rounds_remaining
        else:
            # Add new condition
            char_conditions.conditions.append(condition)
        
        return condition
    
    def remove_condition(
        self,
        character_id: int,
        condition_type: ConditionType
    ) -> bool:
        """Remove a condition from a character.
        
        Args:
            character_id: Character ID
            condition_type: Type of condition to remove
            
        Returns:
            True if condition was removed, False if not found
        """
        if character_id not in self._character_conditions:
            return False
        
        char_conditions = self._character_conditions[character_id]
        condition = char_conditions.get_condition(condition_type)
        
        if condition:
            char_conditions.conditions.remove(condition)
            return True
        
        return False
    
    def get_conditions(self, character_id: int) -> Optional[CharacterConditions]:
        """Get all conditions for a character.
        
        Args:
            character_id: Character ID
            
        Returns:
            CharacterConditions or None if not found
        """
        return self._character_conditions.get(character_id)
    
    def advance_round(self, character_id: int) -> list[Condition]:
        """Advance conditions by one round.
        
        Args:
            character_id: Character ID
            
        Returns:
            List of conditions that expired this round
        """
        if character_id not in self._character_conditions:
            return []
        
        char_conditions = self._character_conditions[character_id]
        expired = []
        
        for condition in char_conditions.conditions:
            if condition.duration_type == DurationType.ROUNDS and condition.rounds_remaining is not None:
                condition.rounds_remaining -= 1
                if condition.is_expired:
                    expired.append(condition)
        
        # Remove expired conditions
        char_conditions.conditions = [c for c in char_conditions.conditions if not c.is_expired]
        
        return expired
    
    def check_condition_effects(self, character_id: int) -> dict[str, any]:
        """Get all mechanical effects of active conditions.
        
        Args:
            character_id: Character ID
            
        Returns:
            Dictionary of condition effects
        """
        char_conditions = self.get_conditions(character_id)
        if not char_conditions:
            return {}
        
        effects = {
            "can_take_actions": char_conditions.can_take_actions,
            "can_move": char_conditions.can_move,
            "is_incapacitated": char_conditions.is_incapacitated,
            "attack_advantage": False,
            "attack_disadvantage": False,
            "attacks_against_advantage": False,
            "attacks_against_disadvantage": False,
            "save_advantage": False,
            "save_disadvantage": False,
            "auto_fail_str_saves": False,
            "auto_fail_dex_saves": False,
            "speed_modifier": 0,
            "is_prone": False,
            "active_conditions": [c.condition_type.value for c in char_conditions.active_conditions]
        }
        
        # Apply condition effects
        for condition in char_conditions.active_conditions:
            ct = condition.condition_type
            
            if ct == ConditionType.BLINDED:
                effects["attack_disadvantage"] = True
                effects["attacks_against_advantage"] = True
            
            elif ct == ConditionType.FRIGHTENED:
                effects["attack_disadvantage"] = True
            
            elif ct == ConditionType.INVISIBLE:
                effects["attack_advantage"] = True
                effects["attacks_against_disadvantage"] = True
            
            elif ct == ConditionType.PARALYZED:
                effects["auto_fail_str_saves"] = True
                effects["auto_fail_dex_saves"] = True
                effects["attacks_against_advantage"] = True
            
            elif ct == ConditionType.POISONED:
                effects["attack_disadvantage"] = True
            
            elif ct == ConditionType.PRONE:
                effects["attack_disadvantage"] = True
                effects["is_prone"] = True
            
            elif ct == ConditionType.RESTRAINED:
                effects["attack_disadvantage"] = True
                effects["attacks_against_advantage"] = True
                effects["save_disadvantage"] = True
                effects["speed_modifier"] = -999  # Speed is 0
            
            elif ct == ConditionType.STUNNED:
                effects["auto_fail_str_saves"] = True
                effects["auto_fail_dex_saves"] = True
                effects["attacks_against_advantage"] = True
            
            elif ct == ConditionType.UNCONSCIOUS:
                effects["auto_fail_str_saves"] = True
                effects["auto_fail_dex_saves"] = True
                effects["attacks_against_advantage"] = True
                effects["is_prone"] = True
            
            elif ct in (ConditionType.GRAPPLED, ConditionType.RESTRAINED):
                effects["speed_modifier"] = -999  # Speed is 0
        
        return effects
    
    def clear_all_conditions(self, character_id: int) -> int:
        """Clear all conditions from a character.
        
        Args:
            character_id: Character ID
            
        Returns:
            Number of conditions cleared
        """
        if character_id not in self._character_conditions:
            return 0
        
        char_conditions = self._character_conditions[character_id]
        count = len(char_conditions.active_conditions)
        char_conditions.conditions.clear()
        
        return count
