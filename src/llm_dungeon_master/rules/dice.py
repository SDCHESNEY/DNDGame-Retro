"""Dice rolling and check resolution system."""

import secrets
from enum import Enum
from typing import Optional, NamedTuple
from dataclasses import dataclass
import re


class AdvantageType(Enum):
    """Type of advantage for rolls."""
    DISADVANTAGE = -1
    NORMAL = 0
    ADVANTAGE = 1


class RollResult(NamedTuple):
    """Result of a dice roll."""
    total: int
    rolls: list[int]
    formula: str
    advantage_type: AdvantageType = AdvantageType.NORMAL
    is_critical: bool = False
    is_critical_fail: bool = False


class CheckResult(NamedTuple):
    """Result of an ability check or attack."""
    success: bool
    roll: int
    dc: int
    total: int
    modifier: int
    advantage_type: AdvantageType = AdvantageType.NORMAL
    is_critical: bool = False
    is_critical_fail: bool = False


def roll_die(sides: int) -> int:
    """Roll a single die using cryptographically secure RNG.
    
    Args:
        sides: Number of sides on the die
        
    Returns:
        Random number between 1 and sides (inclusive)
    """
    return secrets.randbelow(sides) + 1


def parse_dice_formula(formula: str) -> tuple[int, int, int]:
    """Parse a dice formula like '2d6+3' or '1d20'.
    
    Args:
        formula: Dice formula string
        
    Returns:
        Tuple of (count, sides, modifier)
        
    Raises:
        ValueError: If formula is invalid
    """
    # Remove whitespace
    formula = formula.replace(" ", "").lower()
    
    # Match patterns like 2d6+3, 1d20-1, d8, etc.
    pattern = r'^(\d*)d(\d+)([+-]\d+)?$'
    match = re.match(pattern, formula)
    
    if not match:
        raise ValueError(f"Invalid dice formula: {formula}")
    
    count_str, sides_str, modifier_str = match.groups()
    
    # Default count is 1 if not specified
    count = int(count_str) if count_str else 1
    sides = int(sides_str)
    modifier = int(modifier_str) if modifier_str else 0
    
    # Validation
    if count < 1 or count > 100:
        raise ValueError(f"Dice count must be between 1 and 100, got {count}")
    if sides < 2 or sides > 1000:
        raise ValueError(f"Die sides must be between 2 and 1000, got {sides}")
    
    return count, sides, modifier


def roll_dice(
    formula: str,
    advantage: AdvantageType = AdvantageType.NORMAL
) -> RollResult:
    """Roll dice according to a formula.
    
    Args:
        formula: Dice formula like '2d6+3' or '1d20'
        advantage: Type of advantage (for d20 rolls)
        
    Returns:
        RollResult with total and individual rolls
        
    Examples:
        >>> result = roll_dice("2d6+3")
        >>> result.total  # Between 5 and 15
        >>> result = roll_dice("1d20", AdvantageType.ADVANTAGE)
    """
    count, sides, modifier = parse_dice_formula(formula)
    
    # Roll the dice
    rolls = [roll_die(sides) for _ in range(count)]
    
    # Handle advantage/disadvantage for d20 rolls
    is_critical = False
    is_critical_fail = False
    
    if sides == 20 and count == 1 and advantage != AdvantageType.NORMAL:
        # Roll a second d20
        second_roll = roll_die(20)
        rolls.append(second_roll)
        
        # Keep the higher or lower roll
        if advantage == AdvantageType.ADVANTAGE:
            kept_roll = max(rolls)
        else:  # DISADVANTAGE
            kept_roll = min(rolls)
        
        # Check for critical
        is_critical = kept_roll == 20
        is_critical_fail = kept_roll == 1
        
        total = kept_roll + modifier
    else:
        # Normal roll - sum all dice
        total = sum(rolls) + modifier
        
        # Check for critical (only on single d20)
        if sides == 20 and count == 1:
            is_critical = rolls[0] == 20
            is_critical_fail = rolls[0] == 1
    
    return RollResult(
        total=total,
        rolls=rolls,
        formula=formula,
        advantage_type=advantage,
        is_critical=is_critical,
        is_critical_fail=is_critical_fail
    )


def resolve_check(
    ability_score: int,
    dc: int,
    proficiency_bonus: int = 0,
    advantage: AdvantageType = AdvantageType.NORMAL
) -> CheckResult:
    """Resolve an ability check.
    
    Args:
        ability_score: The ability score (e.g., Strength = 14)
        dc: Difficulty class to beat
        proficiency_bonus: Proficiency bonus if applicable
        advantage: Type of advantage
        
    Returns:
        CheckResult with success/failure and details
    """
    # Calculate modifier from ability score
    ability_modifier = (ability_score - 10) // 2
    total_modifier = ability_modifier + proficiency_bonus
    
    # Roll d20
    roll_result = roll_dice("1d20", advantage)
    
    # Calculate total
    total = roll_result.total + total_modifier
    
    # Determine success (natural 1 always fails, natural 20 always succeeds)
    if roll_result.is_critical_fail:
        success = False
    elif roll_result.is_critical:
        success = True
    else:
        success = total >= dc
    
    return CheckResult(
        success=success,
        roll=roll_result.rolls[0] if len(roll_result.rolls) == 1 else max(roll_result.rolls) if advantage == AdvantageType.ADVANTAGE else min(roll_result.rolls),
        dc=dc,
        total=total,
        modifier=total_modifier,
        advantage_type=advantage,
        is_critical=roll_result.is_critical,
        is_critical_fail=roll_result.is_critical_fail
    )


def resolve_attack(
    attack_bonus: int,
    target_ac: int,
    advantage: AdvantageType = AdvantageType.NORMAL
) -> CheckResult:
    """Resolve an attack roll.
    
    Args:
        attack_bonus: Total attack bonus (ability + proficiency + misc)
        target_ac: Target's armor class
        advantage: Type of advantage
        
    Returns:
        CheckResult with hit/miss and details
    """
    # Roll d20
    roll_result = roll_dice("1d20", advantage)
    
    # Calculate total
    total = roll_result.total + attack_bonus
    
    # Determine hit (natural 1 always misses, natural 20 always hits)
    if roll_result.is_critical_fail:
        success = False
    elif roll_result.is_critical:
        success = True
    else:
        success = total >= target_ac
    
    return CheckResult(
        success=success,
        roll=roll_result.rolls[0] if len(roll_result.rolls) == 1 else max(roll_result.rolls) if advantage == AdvantageType.ADVANTAGE else min(roll_result.rolls),
        dc=target_ac,
        total=total,
        modifier=attack_bonus,
        advantage_type=advantage,
        is_critical=roll_result.is_critical,
        is_critical_fail=roll_result.is_critical_fail
    )


def roll_damage(
    damage_formula: str,
    critical: bool = False
) -> RollResult:
    """Roll damage dice.
    
    Args:
        damage_formula: Damage formula like '1d8+3' or '2d6'
        critical: Whether this is a critical hit (doubles dice)
        
    Returns:
        RollResult with damage total
        
    Examples:
        >>> result = roll_damage("1d8+3")
        >>> result.total  # Between 4 and 11
        >>> result = roll_damage("2d6+3", critical=True)
        >>> result.total  # 4d6+3 (dice doubled, not modifier)
    """
    count, sides, modifier = parse_dice_formula(damage_formula)
    
    # Double dice on critical (not modifier)
    if critical:
        count *= 2
    
    # Roll all dice
    rolls = [roll_die(sides) for _ in range(count)]
    total = sum(rolls) + modifier
    
    return RollResult(
        total=total,
        rolls=rolls,
        formula=f"{count}d{sides}{modifier:+d}" if modifier else f"{count}d{sides}",
        is_critical=critical
    )


# Convenient d20 functions
def d20(advantage: AdvantageType = AdvantageType.NORMAL) -> RollResult:
    """Roll a d20."""
    return roll_dice("1d20", advantage)


def d4(count: int = 1) -> RollResult:
    """Roll d4(s)."""
    return roll_dice(f"{count}d4")


def d6(count: int = 1) -> RollResult:
    """Roll d6(s)."""
    return roll_dice(f"{count}d6")


def d8(count: int = 1) -> RollResult:
    """Roll d8(s)."""
    return roll_dice(f"{count}d8")


def d10(count: int = 1) -> RollResult:
    """Roll d10(s)."""
    return roll_dice(f"{count}d10")


def d12(count: int = 1) -> RollResult:
    """Roll d12(s)."""
    return roll_dice(f"{count}d12")


def d100() -> RollResult:
    """Roll d100 (percentile)."""
    return roll_dice("1d100")
