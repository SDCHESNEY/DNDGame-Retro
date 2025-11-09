"""Character creation and management."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from sqlmodel import Session as DBSession

from .models import (
    Character, CharacterSpell, CharacterFeature, 
    CharacterEquipment, CharacterProficiency
)


class ValidationError(Exception):
    """Raised when character validation fails."""
    pass


class CharacterBuilder:
    """Build and validate D&D 5e characters."""
    
    ABILITY_SCORES = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
    POINT_BUY_COSTS = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}
    MAX_POINT_BUY = 27
    
    # Experience required for each level
    LEVEL_XP = {
        1: 0, 2: 300, 3: 900, 4: 2700, 5: 6500,
        6: 14000, 7: 23000, 8: 34000, 9: 48000, 10: 64000,
        11: 85000, 12: 100000, 13: 120000, 14: 140000, 15: 165000,
        16: 195000, 17: 225000, 18: 265000, 19: 305000, 20: 355000
    }
    
    # Proficiency bonus by level
    PROFICIENCY_BONUS = {
        1: 2, 2: 2, 3: 2, 4: 2, 5: 3, 6: 3, 7: 3, 8: 3,
        9: 4, 10: 4, 11: 4, 12: 4, 13: 5, 14: 5, 15: 5, 16: 5,
        17: 6, 18: 6, 19: 6, 20: 6
    }
    
    def __init__(self, db: DBSession):
        self.db = db
        self.templates_dir = Path(__file__).parent / "templates"
    
    def load_template(self, class_name: str) -> Dict:
        """Load a character class template."""
        template_path = self.templates_dir / f"{class_name.lower()}.json"
        if not template_path.exists():
            raise ValueError(f"Template for class '{class_name}' not found")
        
        with open(template_path, 'r') as f:
            return json.load(f)
    
    def list_available_classes(self) -> List[str]:
        """List all available character classes."""
        if not self.templates_dir.exists():
            return []
        
        classes = []
        for file in self.templates_dir.glob("*.json"):
            classes.append(file.stem.capitalize())
        return sorted(classes)
    
    def calculate_point_buy_cost(self, scores: Dict[str, int]) -> int:
        """Calculate the point buy cost for a set of ability scores."""
        total_cost = 0
        for ability in self.ABILITY_SCORES:
            score = scores.get(ability, 10)
            if score < 8 or score > 15:
                raise ValidationError(f"{ability.capitalize()} score {score} is out of range (8-15)")
            total_cost += self.POINT_BUY_COSTS[score]
        return total_cost
    
    def validate_point_buy(self, scores: Dict[str, int]) -> Tuple[bool, str]:
        """Validate that ability scores follow point buy rules."""
        try:
            cost = self.calculate_point_buy_cost(scores)
            if cost > self.MAX_POINT_BUY:
                return False, f"Point buy cost {cost} exceeds maximum of {self.MAX_POINT_BUY}"
            return True, f"Valid point buy (cost: {cost}/{self.MAX_POINT_BUY})"
        except ValidationError as e:
            return False, str(e)
    
    def calculate_modifier(self, score: int) -> int:
        """Calculate ability modifier from score."""
        return (score - 10) // 2
    
    def calculate_hp(self, char_class: str, level: int, constitution_modifier: int) -> int:
        """Calculate hit points for a character."""
        template = self.load_template(char_class)
        hit_die = template["hit_die"]
        
        # Parse hit die (e.g., "d10" -> 10)
        die_size = int(hit_die[1:])
        
        # Max HP at level 1, then average of die for subsequent levels
        if level == 1:
            return die_size + constitution_modifier
        else:
            # Level 1: max die + con mod
            # Levels 2+: (average of die + con mod) per level
            avg_roll = (die_size // 2) + 1
            return die_size + constitution_modifier + ((avg_roll + constitution_modifier) * (level - 1))
    
    def calculate_armor_class(self, dexterity_modifier: int, armor_type: Optional[str] = None) -> int:
        """Calculate armor class."""
        if armor_type is None:
            # Unarmored: 10 + Dex
            return 10 + dexterity_modifier
        elif armor_type == "leather":
            return 11 + dexterity_modifier
        elif armor_type == "scale mail":
            return 14 + min(dexterity_modifier, 2)  # Medium armor caps Dex at +2
        elif armor_type == "chain mail":
            return 16
        else:
            return 10 + dexterity_modifier
    
    def create_from_template(
        self,
        player_id: int,
        name: str,
        race: str,
        char_class: str,
        ability_scores: Dict[str, int],
        background: Optional[str] = None,
        skills: Optional[List[str]] = None
    ) -> Character:
        """Create a character from a class template."""
        # Load template
        template = self.load_template(char_class)
        
        # Validate point buy
        is_valid, message = self.validate_point_buy(ability_scores)
        if not is_valid:
            raise ValidationError(f"Invalid ability scores: {message}")
        
        # Calculate derived stats
        con_mod = self.calculate_modifier(ability_scores["constitution"])
        dex_mod = self.calculate_modifier(ability_scores["dexterity"])
        
        max_hp = self.calculate_hp(char_class, 1, con_mod)
        armor_class = self.calculate_armor_class(dex_mod)
        
        # Create character
        character = Character(
            player_id=player_id,
            name=name,
            race=race,
            char_class=char_class,
            background=background,
            level=1,
            strength=ability_scores["strength"],
            dexterity=ability_scores["dexterity"],
            constitution=ability_scores["constitution"],
            intelligence=ability_scores["intelligence"],
            wisdom=ability_scores["wisdom"],
            charisma=ability_scores["charisma"],
            max_hp=max_hp,
            current_hp=max_hp,
            armor_class=armor_class,
            initiative_bonus=dex_mod,
            proficiency_bonus=2,
            experience_points=0
        )
        
        # Set spell slots for spellcasters
        if "spellcasting" in template:
            spell_info = template["spellcasting"]
            for level, slots in spell_info.get("spell_slots", {}).items():
                setattr(character, f"spell_slots_{level}", slots)
                setattr(character, f"current_spell_slots_{level}", slots)
        
        self.db.add(character)
        self.db.commit()
        self.db.refresh(character)
        
        # Add class features
        for feature in template.get("level_1_features", []):
            char_feature = CharacterFeature(
                character_id=character.id,
                feature_name=feature["name"],
                feature_type="class_feature",
                source=f"{char_class} 1",
                description=feature["description"]
            )
            self.db.add(char_feature)
        
        # Add proficiencies
        for save in template.get("saving_throw_proficiencies", []):
            prof = CharacterProficiency(
                character_id=character.id,
                proficiency_type="saving_throw",
                proficiency_name=save,
                source="Class"
            )
            self.db.add(prof)
        
        # Add armor proficiencies
        for armor in template.get("armor_proficiencies", []):
            prof = CharacterProficiency(
                character_id=character.id,
                proficiency_type="armor",
                proficiency_name=armor,
                source="Class"
            )
            self.db.add(prof)
        
        # Add weapon proficiencies
        for weapon in template.get("weapon_proficiencies", []):
            prof = CharacterProficiency(
                character_id=character.id,
                proficiency_type="weapon",
                proficiency_name=weapon,
                source="Class"
            )
            self.db.add(prof)
        
        # Add skills if provided
        if skills:
            for skill in skills:
                prof = CharacterProficiency(
                    character_id=character.id,
                    proficiency_type="skill",
                    proficiency_name=skill,
                    source="Class"
                )
                self.db.add(prof)
        
        self.db.commit()
        
        return character
    
    def validate_character(self, character: Character) -> Tuple[bool, List[str]]:
        """Validate a character's stats and configuration."""
        errors = []
        
        # Check ability scores are in valid range
        for ability in self.ABILITY_SCORES:
            score = getattr(character, ability)
            if score < 3 or score > 20:
                errors.append(f"{ability.capitalize()} score {score} is out of valid range (3-20)")
        
        # Check level is valid
        if character.level < 1 or character.level > 20:
            errors.append(f"Level {character.level} is invalid (must be 1-20)")
        
        # Check HP is positive
        if character.max_hp <= 0:
            errors.append(f"Maximum HP must be positive (got {character.max_hp})")
        
        if character.current_hp < 0:
            errors.append(f"Current HP cannot be negative (got {character.current_hp})")
        
        # Check AC is reasonable
        if character.armor_class < 5 or character.armor_class > 30:
            errors.append(f"Armor Class {character.armor_class} seems unreasonable")
        
        # Check proficiency bonus matches level
        expected_prof = self.PROFICIENCY_BONUS.get(character.level, 2)
        if character.proficiency_bonus != expected_prof:
            errors.append(f"Proficiency bonus should be {expected_prof} for level {character.level}")
        
        return len(errors) == 0, errors
    
    def apply_level_up(self, character: Character) -> Character:
        """Apply level up to a character."""
        # Check if character has enough XP
        new_level = character.level + 1
        if new_level > 20:
            raise ValidationError("Character is already at maximum level (20)")
        
        required_xp = self.LEVEL_XP.get(new_level, 0)
        if character.experience_points < required_xp:
            raise ValidationError(
                f"Not enough XP to level up. Need {required_xp}, have {character.experience_points}"
            )
        
        # Load template for HP calculation
        template = self.load_template(character.char_class)
        hit_die = template["hit_die"]
        die_size = int(hit_die[1:])
        avg_roll = (die_size // 2) + 1
        
        con_mod = self.calculate_modifier(character.constitution)
        hp_gain = avg_roll + con_mod
        
        # Apply level up
        character.level = new_level
        character.max_hp += hp_gain
        character.current_hp += hp_gain
        character.proficiency_bonus = self.PROFICIENCY_BONUS[new_level]
        
        # Update spell slots for spellcasters (would need level-based template data)
        
        self.db.add(character)
        self.db.commit()
        self.db.refresh(character)
        
        return character
    
    def get_character_summary(self, character: Character) -> Dict:
        """Get a summary of character stats and features."""
        # Calculate modifiers
        modifiers = {
            ability: self.calculate_modifier(getattr(character, ability))
            for ability in self.ABILITY_SCORES
        }
        
        # Get proficiencies
        proficiencies = {
            "skills": [],
            "saving_throws": [],
            "weapons": [],
            "armor": [],
            "tools": [],
            "languages": []
        }
        
        for prof in character.proficiencies:
            prof_type = prof.proficiency_type
            if prof_type == "skill":
                proficiencies["skills"].append(prof.proficiency_name)
            elif prof_type == "saving_throw":
                proficiencies["saving_throws"].append(prof.proficiency_name)
            elif prof_type == "weapon":
                proficiencies["weapons"].append(prof.proficiency_name)
            elif prof_type == "armor":
                proficiencies["armor"].append(prof.proficiency_name)
            elif prof_type == "tool":
                proficiencies["tools"].append(prof.proficiency_name)
            elif prof_type == "language":
                proficiencies["languages"].append(prof.proficiency_name)
        
        # Get features
        features = [
            {"name": f.feature_name, "description": f.description, "source": f.source}
            for f in character.features
        ]
        
        # Get spells
        spells = [
            {"name": s.spell_name, "level": s.spell_level, "prepared": s.is_prepared}
            for s in character.spells
        ]
        
        return {
            "id": character.id,
            "name": character.name,
            "race": character.race,
            "class": character.char_class,
            "level": character.level,
            "background": character.background,
            "xp": character.experience_points,
            "hp": {"current": character.current_hp, "max": character.max_hp},
            "ac": character.armor_class,
            "initiative": character.initiative_bonus,
            "speed": character.speed,
            "proficiency_bonus": character.proficiency_bonus,
            "ability_scores": {
                ability: {
                    "score": getattr(character, ability),
                    "modifier": modifiers[ability]
                }
                for ability in self.ABILITY_SCORES
            },
            "proficiencies": proficiencies,
            "features": features,
            "spells": spells,
            "spell_slots": {
                str(i): {
                    "max": getattr(character, f"spell_slots_{i}"),
                    "current": getattr(character, f"current_spell_slots_{i}")
                }
                for i in range(1, 10)
                if getattr(character, f"spell_slots_{i}") > 0
            }
        }
