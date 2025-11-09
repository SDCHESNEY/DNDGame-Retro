"""Tests for condition management system."""

import pytest
from llm_dungeon_master.rules.conditions import (
    ConditionManager, ConditionType, DurationType, Condition
)


class TestConditionType:
    """Test condition type enum."""
    
    def test_condition_descriptions(self):
        """Test that all conditions have descriptions."""
        for condition in ConditionType:
            assert len(condition.description) > 0


class TestConditionManager:
    """Test condition manager functionality."""
    
    def test_apply_condition(self):
        """Test applying a condition."""
        manager = ConditionManager()
        
        condition = manager.apply_condition(
            character_id=1,
            character_name="Fighter",
            condition_type=ConditionType.POISONED,
            source="Goblin Arrow",
            duration_type=DurationType.ROUNDS,
            duration_value=3
        )
        
        assert condition.condition_type == ConditionType.POISONED
        assert condition.source == "Goblin Arrow"
        assert condition.rounds_remaining == 3
    
    def test_get_conditions(self):
        """Test getting character conditions."""
        manager = ConditionManager()
        
        manager.apply_condition(
            1, "Fighter", ConditionType.POISONED, "Trap",
            DurationType.ROUNDS, 2
        )
        
        char_conditions = manager.get_conditions(1)
        assert char_conditions is not None
        assert char_conditions.character_id == 1
        assert len(char_conditions.active_conditions) == 1
    
    def test_has_condition(self):
        """Test checking if character has a condition."""
        manager = ConditionManager()
        
        manager.apply_condition(
            1, "Fighter", ConditionType.BLINDED, "Flash Spell",
            DurationType.ROUNDS, 1
        )
        
        char_conditions = manager.get_conditions(1)
        assert char_conditions.has_condition(ConditionType.BLINDED)
        assert not char_conditions.has_condition(ConditionType.POISONED)
    
    def test_remove_condition(self):
        """Test removing a condition."""
        manager = ConditionManager()
        
        manager.apply_condition(
            1, "Fighter", ConditionType.PRONE, "Tripped",
            DurationType.UNTIL_DISPELLED
        )
        
        success = manager.remove_condition(1, ConditionType.PRONE)
        assert success
        
        char_conditions = manager.get_conditions(1)
        assert not char_conditions.has_condition(ConditionType.PRONE)
    
    def test_remove_nonexistent_condition(self):
        """Test removing a condition that doesn't exist."""
        manager = ConditionManager()
        
        success = manager.remove_condition(1, ConditionType.STUNNED)
        assert not success
    
    def test_advance_round(self):
        """Test advancing conditions by one round."""
        manager = ConditionManager()
        
        manager.apply_condition(
            1, "Fighter", ConditionType.FRIGHTENED, "Dragon Presence",
            DurationType.ROUNDS, 2
        )
        
        # Advance one round
        expired = manager.advance_round(1)
        assert len(expired) == 0  # Should not expire yet
        
        char_conditions = manager.get_conditions(1)
        condition = char_conditions.get_condition(ConditionType.FRIGHTENED)
        assert condition.rounds_remaining == 1
        
        # Advance another round - expires when reaching 0
        expired = manager.advance_round(1)
        assert len(expired) == 1  # Expires when reaching 0
        
        char_conditions = manager.get_conditions(1)
        assert not char_conditions.has_condition(ConditionType.FRIGHTENED)
    
    def test_multiple_conditions(self):
        """Test managing multiple conditions on one character."""
        manager = ConditionManager()
        
        manager.apply_condition(
            1, "Fighter", ConditionType.POISONED, "Snake Bite",
            DurationType.ROUNDS, 5
        )
        manager.apply_condition(
            1, "Fighter", ConditionType.PRONE, "Knocked Down",
            DurationType.UNTIL_DISPELLED
        )
        
        char_conditions = manager.get_conditions(1)
        assert len(char_conditions.active_conditions) == 2
        assert char_conditions.has_condition(ConditionType.POISONED)
        assert char_conditions.has_condition(ConditionType.PRONE)
    
    def test_condition_stacking_duration(self):
        """Test that applying same condition extends duration."""
        manager = ConditionManager()
        
        manager.apply_condition(
            1, "Fighter", ConditionType.RESTRAINED, "Web Spell",
            DurationType.ROUNDS, 2
        )
        
        # Apply same condition with longer duration
        manager.apply_condition(
            1, "Fighter", ConditionType.RESTRAINED, "Net",
            DurationType.ROUNDS, 5
        )
        
        char_conditions = manager.get_conditions(1)
        condition = char_conditions.get_condition(ConditionType.RESTRAINED)
        assert condition.rounds_remaining == 5  # Should use longer duration
    
    def test_until_save_duration(self):
        """Test condition with save-ended duration."""
        manager = ConditionManager()
        
        condition = manager.apply_condition(
            1, "Fighter", ConditionType.CHARMED, "Charm Person",
            DurationType.UNTIL_SAVE, save_dc=15, save_ability="Wis"
        )
        
        assert condition.save_dc == 15
        assert condition.save_ability == "Wis"
        assert not condition.is_expired
    
    def test_permanent_condition(self):
        """Test permanent condition."""
        manager = ConditionManager()
        
        condition = manager.apply_condition(
            1, "Fighter", ConditionType.PETRIFIED, "Basilisk Gaze",
            DurationType.PERMANENT
        )
        
        assert not condition.is_expired
        # Advance rounds shouldn't expire it
        for _ in range(10):
            manager.advance_round(1)
        
        char_conditions = manager.get_conditions(1)
        assert char_conditions.has_condition(ConditionType.PETRIFIED)
    
    def test_clear_all_conditions(self):
        """Test clearing all conditions."""
        manager = ConditionManager()
        
        manager.apply_condition(
            1, "Fighter", ConditionType.POISONED, "Trap",
            DurationType.ROUNDS, 3
        )
        manager.apply_condition(
            1, "Fighter", ConditionType.FRIGHTENED, "Fear Spell",
            DurationType.ROUNDS, 2
        )
        
        count = manager.clear_all_conditions(1)
        assert count == 2
        
        char_conditions = manager.get_conditions(1)
        assert len(char_conditions.active_conditions) == 0


class TestConditionEffects:
    """Test condition mechanical effects."""
    
    def test_incapacitated_check(self):
        """Test incapacitation detection."""
        manager = ConditionManager()
        
        manager.apply_condition(
            1, "Fighter", ConditionType.STUNNED, "Monk Ability",
            DurationType.ROUNDS, 1
        )
        
        char_conditions = manager.get_conditions(1)
        assert char_conditions.is_incapacitated
        assert not char_conditions.can_take_actions
    
    def test_movement_restriction(self):
        """Test movement restriction."""
        manager = ConditionManager()
        
        manager.apply_condition(
            1, "Fighter", ConditionType.GRAPPLED, "Monster Grab",
            DurationType.UNTIL_DISPELLED
        )
        
        char_conditions = manager.get_conditions(1)
        assert not char_conditions.can_move
    
    def test_check_condition_effects_blinded(self):
        """Test blinded condition effects."""
        manager = ConditionManager()
        
        manager.apply_condition(
            1, "Fighter", ConditionType.BLINDED, "Darkness",
            DurationType.ROUNDS, 1
        )
        
        effects = manager.check_condition_effects(1)
        assert effects["attack_disadvantage"]
        assert effects["attacks_against_advantage"]
    
    def test_check_condition_effects_poisoned(self):
        """Test poisoned condition effects."""
        manager = ConditionManager()
        
        manager.apply_condition(
            1, "Fighter", ConditionType.POISONED, "Poison",
            DurationType.ROUNDS, 10
        )
        
        effects = manager.check_condition_effects(1)
        assert effects["attack_disadvantage"]
    
    def test_check_condition_effects_invisible(self):
        """Test invisible condition effects."""
        manager = ConditionManager()
        
        manager.apply_condition(
            1, "Rogue", ConditionType.INVISIBLE, "Invisibility Spell",
            DurationType.ROUNDS, 10
        )
        
        effects = manager.check_condition_effects(1)
        assert effects["attack_advantage"]
        assert effects["attacks_against_disadvantage"]
    
    def test_check_condition_effects_prone(self):
        """Test prone condition effects."""
        manager = ConditionManager()
        
        manager.apply_condition(
            1, "Fighter", ConditionType.PRONE, "Knocked Down",
            DurationType.UNTIL_DISPELLED
        )
        
        effects = manager.check_condition_effects(1)
        assert effects["attack_disadvantage"]
        assert effects["is_prone"]
    
    def test_check_condition_effects_restrained(self):
        """Test restrained condition effects."""
        manager = ConditionManager()
        
        manager.apply_condition(
            1, "Fighter", ConditionType.RESTRAINED, "Entangle",
            DurationType.ROUNDS, 3
        )
        
        effects = manager.check_condition_effects(1)
        assert effects["attack_disadvantage"]
        assert effects["attacks_against_advantage"]
        assert effects["save_disadvantage"]
        assert effects["speed_modifier"] == -999
    
    def test_check_condition_effects_paralyzed(self):
        """Test paralyzed condition effects."""
        manager = ConditionManager()
        
        manager.apply_condition(
            1, "Fighter", ConditionType.PARALYZED, "Hold Person",
            DurationType.ROUNDS, 1
        )
        
        effects = manager.check_condition_effects(1)
        assert effects["auto_fail_str_saves"]
        assert effects["auto_fail_dex_saves"]
        assert effects["attacks_against_advantage"]
        assert not effects["can_take_actions"]
    
    def test_check_condition_effects_unconscious(self):
        """Test unconscious condition effects."""
        manager = ConditionManager()
        
        manager.apply_condition(
            1, "Fighter", ConditionType.UNCONSCIOUS, "Sleep Spell",
            DurationType.ROUNDS, 1
        )
        
        effects = manager.check_condition_effects(1)
        assert effects["auto_fail_str_saves"]
        assert effects["auto_fail_dex_saves"]
        assert effects["attacks_against_advantage"]
        assert effects["is_prone"]
        assert not effects["can_take_actions"]
    
    def test_multiple_condition_effects(self):
        """Test effects of multiple conditions."""
        manager = ConditionManager()
        
        manager.apply_condition(
            1, "Fighter", ConditionType.POISONED, "Poison",
            DurationType.ROUNDS, 10
        )
        manager.apply_condition(
            1, "Fighter", ConditionType.RESTRAINED, "Net",
            DurationType.ROUNDS, 3
        )
        
        effects = manager.check_condition_effects(1)
        assert effects["attack_disadvantage"]  # From both
        assert effects["attacks_against_advantage"]  # From restrained
        assert effects["save_disadvantage"]  # From restrained
        assert "poisoned" in effects["active_conditions"]
        assert "restrained" in effects["active_conditions"]
    
    def test_no_conditions_effects(self):
        """Test effects when no conditions are active."""
        manager = ConditionManager()
        
        effects = manager.check_condition_effects(999)  # Non-existent character
        assert effects == {}


class TestConditionDescription:
    """Test condition description formatting."""
    
    def test_round_duration_description(self):
        """Test description with round duration."""
        condition = Condition(
            condition_type=ConditionType.STUNNED,
            source="Monk",
            duration_type=DurationType.ROUNDS,
            duration_value=2,
            rounds_remaining=2
        )
        
        desc = condition.description
        assert "Stunned" in desc
        assert "2 rounds" in desc
        assert "Monk" in desc
    
    def test_save_duration_description(self):
        """Test description with save duration."""
        condition = Condition(
            condition_type=ConditionType.FRIGHTENED,
            source="Dragon",
            duration_type=DurationType.UNTIL_SAVE,
            save_dc=15,
            save_ability="Wis"
        )
        
        desc = condition.description
        assert "Frightened" in desc
        assert "DC 15" in desc
        assert "Wis" in desc
        assert "Dragon" in desc
    
    def test_permanent_duration_description(self):
        """Test description with permanent duration."""
        condition = Condition(
            condition_type=ConditionType.PETRIFIED,
            source="Medusa",
            duration_type=DurationType.PERMANENT
        )
        
        desc = condition.description
        assert "Petrified" in desc
        assert "Permanent" in desc
        assert "Medusa" in desc
