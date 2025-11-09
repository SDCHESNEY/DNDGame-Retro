"""Encounter generator with CR balancing for D&D 5e."""

import secrets
from enum import Enum
from typing import List, Dict, Optional
from dataclasses import dataclass


class EncounterDifficulty(str, Enum):
    """Encounter difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    DEADLY = "deadly"


class Environment(str, Enum):
    """Environment types for encounters."""
    DUNGEON = "dungeon"
    FOREST = "forest"
    MOUNTAINS = "mountains"
    SWAMP = "swamp"
    DESERT = "desert"
    URBAN = "urban"
    UNDERDARK = "underdark"
    COASTAL = "coastal"


@dataclass
class Monster:
    """A monster in an encounter."""
    name: str
    cr: float
    xp: int
    count: int
    hp: int
    ac: int
    description: str


@dataclass
class Encounter:
    """A generated encounter."""
    monsters: List[Monster]
    total_xp: int
    adjusted_xp: int
    difficulty: EncounterDifficulty
    environment: Environment
    description: str
    treasure_cr: float  # Average CR for treasure calculation


class EncounterGenerator:
    """Generates balanced encounters for D&D 5e."""
    
    # XP thresholds by character level
    XP_THRESHOLDS = {
        1: {"easy": 25, "medium": 50, "hard": 75, "deadly": 100},
        2: {"easy": 50, "medium": 100, "hard": 150, "deadly": 200},
        3: {"easy": 75, "medium": 150, "hard": 225, "deadly": 400},
        4: {"easy": 125, "medium": 250, "hard": 375, "deadly": 500},
        5: {"easy": 250, "medium": 500, "hard": 750, "deadly": 1100},
        6: {"easy": 300, "medium": 600, "hard": 900, "deadly": 1400},
        7: {"easy": 350, "medium": 750, "hard": 1100, "deadly": 1700},
        8: {"easy": 450, "medium": 900, "hard": 1400, "deadly": 2100},
        9: {"easy": 550, "medium": 1100, "hard": 1600, "deadly": 2400},
        10: {"easy": 600, "medium": 1200, "hard": 1900, "deadly": 2800},
        11: {"easy": 800, "medium": 1600, "hard": 2400, "deadly": 3600},
        12: {"easy": 1000, "medium": 2000, "hard": 3000, "deadly": 4500},
        13: {"easy": 1100, "medium": 2200, "hard": 3400, "deadly": 5100},
        14: {"easy": 1250, "medium": 2500, "hard": 3800, "deadly": 5700},
        15: {"easy": 1400, "medium": 2800, "hard": 4300, "deadly": 6400},
        16: {"easy": 1600, "medium": 3200, "hard": 4800, "deadly": 7200},
        17: {"easy": 2000, "medium": 3900, "hard": 5900, "deadly": 8800},
        18: {"easy": 2100, "medium": 4200, "hard": 6300, "deadly": 9500},
        19: {"easy": 2400, "medium": 4900, "hard": 7300, "deadly": 10900},
        20: {"easy": 2800, "medium": 5700, "hard": 8500, "deadly": 12700},
    }
    
    # CR to XP mapping
    CR_XP = {
        0: 10, 0.125: 25, 0.25: 50, 0.5: 100,
        1: 200, 2: 450, 3: 700, 4: 1100, 5: 1800,
        6: 2300, 7: 2900, 8: 3900, 9: 5000, 10: 5900,
        11: 7200, 12: 8400, 13: 10000, 14: 11500, 15: 13000,
        16: 15000, 17: 18000, 18: 20000, 19: 22000, 20: 25000,
        21: 33000, 22: 41000, 23: 50000, 24: 62000, 25: 75000,
        26: 90000, 27: 105000, 28: 120000, 29: 135000, 30: 155000,
    }
    
    # Monster lists by environment and CR
    MONSTERS = {
        Environment.DUNGEON: [
            {"name": "Kobold", "cr": 0.125, "hp": 5, "ac": 12, "desc": "Small reptilian humanoid"},
            {"name": "Goblin", "cr": 0.25, "hp": 7, "ac": 15, "desc": "Small, sneaky humanoid"},
            {"name": "Skeleton", "cr": 0.25, "hp": 13, "ac": 13, "desc": "Undead warrior"},
            {"name": "Zombie", "cr": 0.25, "hp": 22, "ac": 8, "desc": "Shambling undead"},
            {"name": "Orc", "cr": 0.5, "hp": 15, "ac": 13, "desc": "Savage warrior"},
            {"name": "Hobgoblin", "cr": 0.5, "hp": 11, "ac": 18, "desc": "Disciplined soldier"},
            {"name": "Gnoll", "cr": 0.5, "hp": 22, "ac": 15, "desc": "Hyena-like humanoid"},
            {"name": "Bugbear", "cr": 1, "hp": 27, "ac": 16, "desc": "Large, hairy goblinoid"},
            {"name": "Ghoul", "cr": 1, "hp": 22, "ac": 12, "desc": "Flesh-eating undead"},
            {"name": "Ogre", "cr": 2, "hp": 59, "ac": 11, "desc": "Large, brutish giant"},
            {"name": "Minotaur", "cr": 3, "hp": 76, "ac": 14, "desc": "Bull-headed humanoid"},
            {"name": "Troll", "cr": 5, "hp": 84, "ac": 15, "desc": "Regenerating giant"},
        ],
        Environment.FOREST: [
            {"name": "Wolf", "cr": 0.25, "hp": 11, "ac": 13, "desc": "Pack predator"},
            {"name": "Goblin", "cr": 0.25, "hp": 7, "ac": 15, "desc": "Forest raider"},
            {"name": "Pixie", "cr": 0.25, "hp": 1, "ac": 15, "desc": "Tiny fey trickster"},
            {"name": "Satyr", "cr": 0.5, "hp": 31, "ac": 14, "desc": "Fey reveler"},
            {"name": "Dryad", "cr": 1, "hp": 22, "ac": 11, "desc": "Tree spirit"},
            {"name": "Werewolf", "cr": 3, "hp": 58, "ac": 12, "desc": "Shapeshifting lycanthrope"},
            {"name": "Owlbear", "cr": 3, "hp": 59, "ac": 13, "desc": "Bear-owl hybrid"},
            {"name": "Treant", "cr": 9, "hp": 138, "ac": 16, "desc": "Ancient tree guardian"},
        ],
        Environment.MOUNTAINS: [
            {"name": "Giant Eagle", "cr": 1, "hp": 26, "ac": 13, "desc": "Majestic bird"},
            {"name": "Griffon", "cr": 2, "hp": 59, "ac": 12, "desc": "Lion-eagle hybrid"},
            {"name": "Stone Giant", "cr": 7, "hp": 126, "ac": 17, "desc": "Mountain-dwelling giant"},
            {"name": "Frost Giant", "cr": 8, "hp": 138, "ac": 15, "desc": "Ice-wielding giant"},
            {"name": "Fire Giant", "cr": 9, "hp": 162, "ac": 18, "desc": "Forge master giant"},
            {"name": "Roc", "cr": 11, "hp": 248, "ac": 15, "desc": "Colossal bird"},
            {"name": "Adult Red Dragon", "cr": 17, "hp": 256, "ac": 19, "desc": "Fire-breathing terror"},
        ],
    }
    
    def __init__(self):
        """Initialize the encounter generator."""
        pass
    
    def calculate_xp_budget(
        self,
        party_levels: List[int],
        difficulty: EncounterDifficulty
    ) -> int:
        """Calculate XP budget for an encounter."""
        total_xp = 0
        for level in party_levels:
            level = min(20, max(1, level))  # Clamp to 1-20
            total_xp += self.XP_THRESHOLDS[level][difficulty.value]
        return total_xp
    
    def get_xp_multiplier(self, monster_count: int, party_size: int) -> float:
        """Get XP multiplier based on number of monsters."""
        # Adjust for party size
        if party_size < 3:
            adjustment = 1
        elif party_size > 5:
            adjustment = -1
        else:
            adjustment = 0
        
        # Base multipliers
        if monster_count == 1:
            multiplier = 1.0
        elif monster_count == 2:
            multiplier = 1.5
        elif monster_count <= 6:
            multiplier = 2.0
        elif monster_count <= 10:
            multiplier = 2.5
        elif monster_count <= 14:
            multiplier = 3.0
        else:
            multiplier = 4.0
        
        # Apply adjustment
        adjustments = {-1: 0.5, 0: 1.0, 1: 1.5}
        return multiplier * adjustments.get(adjustment, 1.0)
    
    def generate_encounter(
        self,
        party_levels: List[int],
        difficulty: EncounterDifficulty,
        environment: Environment = Environment.DUNGEON
    ) -> Encounter:
        """Generate a balanced encounter."""
        xp_budget = self.calculate_xp_budget(party_levels, difficulty)
        party_size = len(party_levels)
        
        # Get available monsters for environment
        monsters_data = self.MONSTERS.get(environment, self.MONSTERS[Environment.DUNGEON])
        
        # Filter monsters by CR (not too far above party level)
        avg_level = sum(party_levels) / len(party_levels)
        max_cr = avg_level + 4
        suitable_monsters = [m for m in monsters_data if m["cr"] <= max_cr]
        
        if not suitable_monsters:
            suitable_monsters = monsters_data
        
        # Try to build encounter
        max_attempts = 100
        best_encounter = None
        best_diff = float('inf')
        
        for _ in range(max_attempts):
            monsters = []
            total_xp = 0
            
            # Decide number of monsters (1-6 typically)
            num_monsters = secrets.choice([1, 1, 2, 2, 3, 3, 4, 5, 6])
            
            for _ in range(num_monsters):
                monster_data = secrets.choice(suitable_monsters)
                cr = monster_data["cr"]
                xp = self.CR_XP.get(cr, 100)
                
                # Decide count (usually 1, sometimes 2-4 for weak monsters)
                if cr < 0.5:
                    count = secrets.choice([1, 1, 2, 2, 3, 4])
                elif cr < 2:
                    count = secrets.choice([1, 1, 1, 2, 2])
                else:
                    count = 1
                
                monsters.append({
                    "data": monster_data,
                    "count": count,
                    "xp": xp
                })
                total_xp += xp * count
            
            # Calculate adjusted XP
            total_monsters = sum(m["count"] for m in monsters)
            multiplier = self.get_xp_multiplier(total_monsters, party_size)
            adjusted_xp = int(total_xp * multiplier)
            
            # Check if this is closer to budget
            diff = abs(adjusted_xp - xp_budget)
            if diff < best_diff:
                best_diff = diff
                best_encounter = (monsters, total_xp, adjusted_xp)
            
            # If close enough, use it
            if adjusted_xp >= xp_budget * 0.7 and adjusted_xp <= xp_budget * 1.3:
                break
        
        # Build final encounter
        monsters, total_xp, adjusted_xp = best_encounter
        
        encounter_monsters = []
        total_cr = 0
        for m in monsters:
            data = m["data"]
            monster = Monster(
                name=data["name"],
                cr=data["cr"],
                xp=m["xp"],
                count=m["count"],
                hp=data["hp"],
                ac=data["ac"],
                description=data["desc"]
            )
            encounter_monsters.append(monster)
            total_cr += data["cr"] * m["count"]
        
        # Generate description
        monster_names = ", ".join(
            f"{m.count}x {m.name}" if m.count > 1 else m.name
            for m in encounter_monsters
        )
        
        env_descriptions = {
            Environment.DUNGEON: "in a torch-lit corridor",
            Environment.FOREST: "among ancient trees",
            Environment.MOUNTAINS: "on a rocky precipice",
            Environment.SWAMP: "in murky waters",
            Environment.DESERT: "under the scorching sun",
            Environment.URBAN: "in a shadowy alley",
            Environment.UNDERDARK: "in the depths below",
            Environment.COASTAL: "by the crashing waves",
        }
        
        description = f"You encounter {monster_names} {env_descriptions.get(environment, 'nearby')}."
        
        return Encounter(
            monsters=encounter_monsters,
            total_xp=total_xp,
            adjusted_xp=adjusted_xp,
            difficulty=difficulty,
            environment=environment,
            description=description,
            treasure_cr=total_cr / len(encounter_monsters) if encounter_monsters else 1
        )
    
    def format_encounter(self, encounter: Encounter) -> str:
        """Format an encounter for display."""
        lines = []
        lines.append(f"=== {encounter.difficulty.value.upper()} ENCOUNTER ===")
        lines.append(f"Environment: {encounter.environment.value.title()}")
        lines.append(f"XP: {encounter.total_xp} (Adjusted: {encounter.adjusted_xp})")
        lines.append("")
        lines.append(encounter.description)
        lines.append("")
        lines.append("Monsters:")
        for monster in encounter.monsters:
            count_str = f"{monster.count}x " if monster.count > 1 else ""
            lines.append(f"  {count_str}{monster.name} (CR {monster.cr})")
            lines.append(f"    HP: {monster.hp}, AC: {monster.ac}, XP: {monster.xp}")
            lines.append(f"    {monster.description}")
        
        return "\n".join(lines)
