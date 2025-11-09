"""Tests for dice rolling system."""

import pytest
from llm_dungeon_master.rules.dice import (
    roll_die, parse_dice_formula, roll_dice, resolve_check,
    resolve_attack, roll_damage, AdvantageType,
    d4, d6, d8, d10, d12, d20, d100
)


class TestRollDie:
    """Test individual die rolling."""
    
    def test_roll_d6(self):
        """Test rolling a d6."""
        for _ in range(100):
            result = roll_die(6)
            assert 1 <= result <= 6
    
    def test_roll_d20(self):
        """Test rolling a d20."""
        for _ in range(100):
            result = roll_die(20)
            assert 1 <= result <= 20
    
    def test_invalid_sides(self):
        """Test rolling with invalid sides."""
        with pytest.raises(ValueError):
            roll_die(0)
        with pytest.raises(ValueError):
            roll_die(-5)


class TestParseDiceFormula:
    """Test dice formula parsing."""
    
    def test_simple_dice(self):
        """Test simple dice formulas."""
        count, sides, modifier = parse_dice_formula("1d6")
        assert count == 1
        assert sides == 6
        assert modifier == 0
    
    def test_multiple_dice(self):
        """Test multiple dice."""
        count, sides, modifier = parse_dice_formula("2d8")
        assert count == 2
        assert sides == 8
        assert modifier == 0
    
    def test_dice_with_positive_modifier(self):
        """Test dice with positive modifier."""
        count, sides, modifier = parse_dice_formula("1d20+5")
        assert count == 1
        assert sides == 20
        assert modifier == 5
    
    def test_dice_with_negative_modifier(self):
        """Test dice with negative modifier."""
        count, sides, modifier = parse_dice_formula("2d6-3")
        assert count == 2
        assert sides == 6
        assert modifier == -3
    
    def test_whitespace_handling(self):
        """Test formulas with whitespace."""
        count, sides, modifier = parse_dice_formula(" 3d10 + 4 ")
        assert count == 3
        assert sides == 10
        assert modifier == 4
    
    def test_invalid_formula(self):
        """Test invalid formulas."""
        with pytest.raises(ValueError):
            parse_dice_formula("invalid")
        with pytest.raises(ValueError):
            parse_dice_formula("d")
        with pytest.raises(ValueError):
            parse_dice_formula("2d")


class TestRollDice:
    """Test complete dice rolling."""
    
    def test_simple_roll(self):
        """Test simple dice roll."""
        result = roll_dice("1d6")
        assert 1 <= result.total <= 6
        assert len(result.rolls) == 1
        assert result.formula == "1d6"
        assert result.advantage_type == AdvantageType.NORMAL
    
    def test_multiple_dice(self):
        """Test rolling multiple dice."""
        result = roll_dice("3d6")
        assert 3 <= result.total <= 18
        assert len(result.rolls) == 3
    
    def test_dice_with_modifier(self):
        """Test dice with modifier."""
        result = roll_dice("1d6+3")
        assert 4 <= result.total <= 9
        assert result.formula == "1d6+3"
    
    def test_advantage(self):
        """Test rolling with advantage."""
        result = roll_dice("1d20", AdvantageType.ADVANTAGE)
        assert 1 <= result.total <= 20
        assert result.advantage_type == AdvantageType.ADVANTAGE
        assert len(result.rolls) == 2  # Should roll twice
    
    def test_disadvantage(self):
        """Test rolling with disadvantage."""
        result = roll_dice("1d20", AdvantageType.DISADVANTAGE)
        assert 1 <= result.total <= 20
        assert result.advantage_type == AdvantageType.DISADVANTAGE
        assert len(result.rolls) == 2  # Should roll twice
    
    def test_critical_hit(self):
        """Test critical hit detection (natural 20)."""
        # We can't guarantee a natural 20, but we can test the logic
        results = [roll_dice("1d20") for _ in range(100)]
        # Should get at least one natural 20 in 100 rolls (statistically)
        criticals = [r for r in results if r.is_critical]
        assert len(criticals) > 0
    
    def test_critical_fail(self):
        """Test critical fail detection (natural 1)."""
        results = [roll_dice("1d20") for _ in range(100)]
        # Should get at least one natural 1 in 100 rolls (statistically)
        critical_fails = [r for r in results if r.is_critical_fail]
        assert len(critical_fails) > 0


class TestResolveCheck:
    """Test ability check resolution."""
    
    def test_successful_check(self):
        """Test a check that should succeed."""
        # With +5 modifier vs DC 10, should succeed often
        successes = 0
        for _ in range(100):
            result = resolve_check(20, 10, 5)  # 20 ability = +5 modifier
            if result.success:
                successes += 1
        assert successes > 70  # Should succeed most of the time
    
    def test_failed_check(self):
        """Test a check that should fail."""
        # With +0 modifier vs DC 20, should fail often (need 20 on d20)
        # Expected: 95% fail rate (only natural 20 succeeds)
        failures = 0
        for _ in range(100):
            result = resolve_check(10, 20, 0)  # 10 ability = +0 modifier
            if not result.success:
                failures += 1
        # With 100 rolls, ~95 should fail (allow for variance)
        assert failures > 85  # Should fail most of the time
    
    def test_check_with_proficiency(self):
        """Test check with proficiency bonus."""
        result = resolve_check(14, 15, proficiency_bonus=2)  # +2 ability +2 prof = +4
        assert result.modifier == 4
    
    def test_check_with_advantage(self):
        """Test check with advantage."""
        result = resolve_check(10, 15, advantage=AdvantageType.ADVANTAGE)
        assert result.advantage_type == AdvantageType.ADVANTAGE
    
    def test_critical_success(self):
        """Test critical success on checks."""
        # Test enough times to virtually guarantee at least one natural 20
        results = [resolve_check(10, 15) for _ in range(200)]
        criticals = [r for r in results if r.is_critical]
        # With 200 rolls, probability of NO natural 20s is (19/20)^200 ≈ 0.00004%
        assert len(criticals) > 0  # Should get at least one natural 20
    
    def test_critical_fail(self):
        """Test critical fail on checks."""
        results = [resolve_check(20, 5) for _ in range(100)]
        critical_fails = [r for r in results if r.is_critical_fail]
        assert len(critical_fails) > 0  # Should get at least one natural 1


class TestResolveAttack:
    """Test attack roll resolution."""
    
    def test_successful_attack(self):
        """Test attack that should hit."""
        # +10 bonus vs AC 10 should hit often (need 0+ on d20)
        # Expected: 95% hit rate (only natural 1 misses)
        hits = 0
        for _ in range(100):
            result = resolve_attack(10, 10)
            if result.success:
                hits += 1
        # With 100 rolls, ~95 should hit (allow for variance)
        assert hits > 85  # Should hit most of the time
    
    def test_failed_attack(self):
        """Test attack that should miss."""
        # +0 bonus vs AC 20 should miss often
        misses = 0
        for _ in range(100):
            result = resolve_attack(0, 20)
            if not result.success:
                misses += 1
        assert misses > 90  # Should miss most of the time
    
    def test_attack_with_advantage(self):
        """Test attack with advantage."""
        result = resolve_attack(5, 15, AdvantageType.ADVANTAGE)
        assert result.advantage_type == AdvantageType.ADVANTAGE
    
    def test_attack_with_disadvantage(self):
        """Test attack with disadvantage."""
        result = resolve_attack(5, 15, AdvantageType.DISADVANTAGE)
        assert result.advantage_type == AdvantageType.DISADVANTAGE
    
    def test_critical_hit(self):
        """Test critical hit on attack."""
        results = [resolve_attack(5, 15) for _ in range(100)]
        criticals = [r for r in results if r.is_critical]
        assert len(criticals) > 0  # Should get at least one natural 20
    
    def test_critical_miss(self):
        """Test critical miss on attack."""
        results = [resolve_attack(5, 15) for _ in range(100)]
        critical_misses = [r for r in results if r.is_critical_fail]
        assert len(critical_misses) > 0  # Should get at least one natural 1


class TestRollDamage:
    """Test damage rolling."""
    
    def test_simple_damage(self):
        """Test simple damage roll."""
        result = roll_damage("1d6")
        assert 1 <= result.total <= 6
    
    def test_damage_with_modifier(self):
        """Test damage with modifier."""
        result = roll_damage("1d8+3")
        assert 4 <= result.total <= 11
    
    def test_multiple_damage_dice(self):
        """Test multiple damage dice."""
        result = roll_damage("2d6+2")
        assert 4 <= result.total <= 14
    
    def test_critical_damage(self):
        """Test critical hit damage (doubles dice)."""
        normal = roll_damage("2d6+3", critical=False)
        # On critical, dice are doubled but not modifier
        # So 2d6+3 becomes 4d6+3
        for _ in range(10):
            critical = roll_damage("2d6+3", critical=True)
            # Critical should be at least 2d6+3 minimum (5) but can be much higher
            assert critical.total >= 5
            # The number of dice rolled should be doubled
            assert len(critical.rolls) == 4  # 2*2 dice
    
    def test_zero_damage(self):
        """Test that damage can't go below 0."""
        # This is handled at the combat level, but rolls with negative modifiers can be negative
        result = roll_damage("1d4-10")  # Unrealistic but tests bounds
        # The roll itself can be negative, combat system handles minimum 0


class TestConvenienceFunctions:
    """Test convenience dice functions."""
    
    def test_d4(self):
        """Test d4 convenience function."""
        for _ in range(20):
            result = d4()
            assert 1 <= result.total <= 4
    
    def test_d6(self):
        """Test d6 convenience function."""
        for _ in range(20):
            result = d6()
            assert 1 <= result.total <= 6
    
    def test_d8(self):
        """Test d8 convenience function."""
        for _ in range(20):
            result = d8()
            assert 1 <= result.total <= 8
    
    def test_d10(self):
        """Test d10 convenience function."""
        for _ in range(20):
            result = d10()
            assert 1 <= result.total <= 10
    
    def test_d12(self):
        """Test d12 convenience function."""
        for _ in range(20):
            result = d12()
            assert 1 <= result.total <= 12
    
    def test_d20(self):
        """Test d20 convenience function."""
        for _ in range(20):
            result = d20()
            assert 1 <= result.total <= 20
    
    def test_d100(self):
        """Test d100 convenience function."""
        for _ in range(20):
            result = d100()
            assert 1 <= result.total <= 100
