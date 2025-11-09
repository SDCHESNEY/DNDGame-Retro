"""NPC generator with personalities and backgrounds for D&D 5e."""

import secrets
import random
from enum import Enum
from typing import List, Optional, Dict
from dataclasses import dataclass


class NPCRole(str, Enum):
    """NPC role types."""
    MERCHANT = "merchant"
    GUARD = "guard"
    NOBLE = "noble"
    COMMONER = "commoner"
    PRIEST = "priest"
    WARRIOR = "warrior"
    ROGUE = "rogue"
    MAGE = "mage"
    INNKEEPER = "innkeeper"
    BLACKSMITH = "blacksmith"


class Alignment(str, Enum):
    """D&D alignment."""
    LAWFUL_GOOD = "lawful_good"
    NEUTRAL_GOOD = "neutral_good"
    CHAOTIC_GOOD = "chaotic_good"
    LAWFUL_NEUTRAL = "lawful_neutral"
    TRUE_NEUTRAL = "true_neutral"
    CHAOTIC_NEUTRAL = "chaotic_neutral"
    LAWFUL_EVIL = "lawful_evil"
    NEUTRAL_EVIL = "neutral_evil"
    CHAOTIC_EVIL = "chaotic_evil"


@dataclass
class NPCStats:
    """Basic NPC statistics."""
    str: int
    dex: int
    con: int
    int: int
    wis: int
    cha: int
    ac: int
    hp: int
    cr: float


@dataclass
class NPC:
    """A generated NPC."""
    name: str
    race: str
    role: NPCRole
    alignment: Alignment
    personality_traits: List[str]
    ideal: str
    bond: str
    flaw: str
    background: str
    motivation: str
    stats: NPCStats
    description: str


class NPCGenerator:
    """Generates NPCs with personalities and backgrounds."""
    
    # Name components
    FIRST_NAMES = {
        "human": ["Aric", "Brom", "Cedric", "Daria", "Elena", "Finn", "Gwen", "Hector"],
        "elf": ["Aelrindel", "Elara", "Faelyn", "Galadriel", "Ilthraniel", "Laucian"],
        "dwarf": ["Baern", "Dolgrin", "Eberk", "Fargrim", "Grudda", "Helga", "Thorgrim"],
        "halfling": ["Alton", "Bree", "Cade", "Merric", "Portia", "Shaena", "Vani"],
        "half-orc": ["Dench", "Feng", "Gell", "Holg", "Imsh", "Keth", "Mhurren"],
        "tiefling": ["Akta", "Damakos", "Ekemon", "Kallista", "Morthos", "Rieta"],
    }
    
    LAST_NAMES = {
        "human": ["Thornheart", "Blackwood", "Silverhand", "Ironforge", "Stormwind"],
        "elf": ["Moonwhisper", "Starweaver", "Nightbreeze", "Dawnblade"],
        "dwarf": ["Ironfoot", "Stonefist", "Hammerfall", "Steelbeard"],
        "halfling": ["Goodbarrel", "Tealeaf", "Thorngage", "Brushgather"],
        "half-orc": ["Ironjaw", "Skullsplitter", "Bonecrusher", "Grimfang"],
        "tiefling": ["Shadowhorn", "Hellspark", "Darkflame", "Nightshade"],
    }
    
    # Personality traits
    PERSONALITY_TRAITS = [
        "I always have a plan for when things go wrong",
        "I am incredibly slow to trust",
        "I love a good insult, even one directed at me",
        "I'm always polite and respectful",
        "I'm haunted by memories I can't forget",
        "I judge others harshly, and myself even more severely",
        "I can find common ground with anyone",
        "I speak very slowly and deliberately",
        "I'm always picking things up, examining them",
        "I laugh heartily at any joke",
    ]
    
    IDEALS = {
        "good": [
            "Respect: People deserve to be treated with dignity",
            "Charity: I help those in need",
            "Greater Good: My gifts are for the benefit of all",
        ],
        "neutral": [
            "Independence: I must prove that I can handle myself",
            "Balance: The natural order must be preserved",
            "Knowledge: The path to power lies in understanding",
        ],
        "evil": [
            "Power: I will do whatever it takes to become powerful",
            "Greed: I will do whatever it takes to become wealthy",
            "Domination: Others must do as I command",
        ],
    }
    
    BONDS = [
        "I would die to recover an ancient artifact",
        "My family means everything to me",
        "I owe my life to someone who saved me",
        "I'm trying to pay off an old debt",
        "I seek revenge against those who wronged me",
        "I protect those who cannot protect themselves",
    ]
    
    FLAWS = [
        "I turn tail and run when things look bad",
        "I have a weakness for the vices of the city",
        "I'm convinced that no one could ever fool me",
        "I'm too greedy for my own good",
        "I have trouble keeping my true feelings hidden",
        "I'd rather kill someone than argue with them",
    ]
    
    BACKGROUNDS = {
        NPCRole.MERCHANT: "Has traveled far and wide selling goods, knows trade routes and market prices",
        NPCRole.GUARD: "Trained in city watch, maintains order and investigates crimes",
        NPCRole.NOBLE: "Born into privilege, knows courtly manners and political intrigue",
        NPCRole.COMMONER: "Simple folk trying to make an honest living",
        NPCRole.PRIEST: "Devoted to a deity, provides spiritual guidance and healing",
        NPCRole.WARRIOR: "Veteran of many battles, skilled in combat and tactics",
        NPCRole.ROGUE: "Lived on the streets, skilled in stealth and deception",
        NPCRole.MAGE: "Studied arcane arts, seeks magical knowledge and power",
        NPCRole.INNKEEPER: "Welcomes travelers, hears all the local gossip and rumors",
        NPCRole.BLACKSMITH: "Master craftsman, creates and repairs weapons and armor",
    }
    
    MOTIVATIONS = {
        NPCRole.MERCHANT: "Seeks profit and new trade opportunities",
        NPCRole.GUARD: "Maintains law and order, protects the innocent",
        NPCRole.NOBLE: "Increases family prestige and political power",
        NPCRole.COMMONER: "Provides for family and stays safe",
        NPCRole.PRIEST: "Spreads faith and helps those in need",
        NPCRole.WARRIOR: "Seeks glory in battle and honor",
        NPCRole.ROGUE: "Survives by wit and cunning",
        NPCRole.MAGE: "Pursues arcane knowledge and power",
        NPCRole.INNKEEPER: "Provides comfort to travelers and hears their stories",
        NPCRole.BLACKSMITH: "Creates quality work and masters the craft",
    }
    
    # Race descriptions
    RACE_DESCRIPTIONS = {
        "human": "average height with varied features",
        "elf": "tall and graceful with pointed ears",
        "dwarf": "stout and sturdy with a thick beard",
        "halfling": "short and nimble with friendly demeanor",
        "half-orc": "muscular with greenish skin and tusks",
        "tiefling": "otherworldly with horns and tail",
    }
    
    def __init__(self):
        """Initialize the NPC generator."""
        pass
    
    def roll_stat(self) -> int:
        """Roll 4d6 drop lowest for ability score."""
        rolls = sorted([secrets.randbelow(6) + 1 for _ in range(4)])
        return sum(rolls[1:])  # Drop lowest
    
    def generate_stats(self, role: NPCRole) -> NPCStats:
        """Generate stats appropriate for NPC role."""
        # Base stats
        stats = {
            "str": self.roll_stat(),
            "dex": self.roll_stat(),
            "con": self.roll_stat(),
            "int": self.roll_stat(),
            "wis": self.roll_stat(),
            "cha": self.roll_stat(),
        }
        
        # Boost primary stats based on role
        primary_stats = {
            NPCRole.WARRIOR: ["str", "con"],
            NPCRole.GUARD: ["str", "dex"],
            NPCRole.ROGUE: ["dex", "cha"],
            NPCRole.MAGE: ["int", "wis"],
            NPCRole.PRIEST: ["wis", "cha"],
            NPCRole.MERCHANT: ["cha", "int"],
            NPCRole.NOBLE: ["cha", "int"],
            NPCRole.COMMONER: ["con", "wis"],
            NPCRole.INNKEEPER: ["cha", "wis"],
            NPCRole.BLACKSMITH: ["str", "con"],
        }
        
        for stat in primary_stats.get(role, []):
            stats[stat] = max(stats[stat], 14)
        
        # Calculate derived stats
        con_mod = (stats["con"] - 10) // 2
        dex_mod = (stats["dex"] - 10) // 2
        
        # Base AC and HP by role
        ac_by_role = {
            NPCRole.WARRIOR: 16,
            NPCRole.GUARD: 15,
            NPCRole.ROGUE: 14,
            NPCRole.MAGE: 12,
            NPCRole.PRIEST: 13,
            NPCRole.MERCHANT: 11,
            NPCRole.NOBLE: 12,
            NPCRole.COMMONER: 10,
            NPCRole.INNKEEPER: 11,
            NPCRole.BLACKSMITH: 13,
        }
        
        hp_by_role = {
            NPCRole.WARRIOR: 30,
            NPCRole.GUARD: 25,
            NPCRole.ROGUE: 20,
            NPCRole.MAGE: 15,
            NPCRole.PRIEST: 20,
            NPCRole.MERCHANT: 15,
            NPCRole.NOBLE: 12,
            NPCRole.COMMONER: 10,
            NPCRole.INNKEEPER: 15,
            NPCRole.BLACKSMITH: 25,
        }
        
        cr_by_role = {
            NPCRole.WARRIOR: 2,
            NPCRole.GUARD: 1,
            NPCRole.ROGUE: 1,
            NPCRole.MAGE: 2,
            NPCRole.PRIEST: 1,
            NPCRole.MERCHANT: 0.25,
            NPCRole.NOBLE: 0.125,
            NPCRole.COMMONER: 0,
            NPCRole.INNKEEPER: 0.25,
            NPCRole.BLACKSMITH: 0.5,
        }
        
        ac = ac_by_role.get(role, 10) + max(0, dex_mod)
        hp = hp_by_role.get(role, 10) + max(0, con_mod * 2)
        cr = cr_by_role.get(role, 0)
        
        return NPCStats(
            str=stats["str"],
            dex=stats["dex"],
            con=stats["con"],
            int=stats["int"],
            wis=stats["wis"],
            cha=stats["cha"],
            ac=ac,
            hp=hp,
            cr=cr
        )
    
    def generate_npc(
        self,
        role: Optional[NPCRole] = None,
        race: Optional[str] = None
    ) -> NPC:
        """Generate a complete NPC."""
        # Random role if not specified
        if role is None:
            role = secrets.choice(list(NPCRole))
        
        # Random race if not specified
        if race is None:
            race = secrets.choice(list(self.FIRST_NAMES.keys()))
        
        # Generate name
        first_name = secrets.choice(self.FIRST_NAMES[race])
        last_name = secrets.choice(self.LAST_NAMES[race])
        name = f"{first_name} {last_name}"
        
        # Random alignment
        alignment = secrets.choice(list(Alignment))
        
        # Pick personality traits (2)
        personality_traits = random.sample(self.PERSONALITY_TRAITS, 2)
        
        # Pick ideal based on alignment
        if "good" in alignment.value:
            ideal_list = self.IDEALS["good"]
        elif "evil" in alignment.value:
            ideal_list = self.IDEALS["evil"]
        else:
            ideal_list = self.IDEALS["neutral"]
        ideal = secrets.choice(ideal_list)
        
        # Pick bond and flaw
        bond = secrets.choice(self.BONDS)
        flaw = secrets.choice(self.FLAWS)
        
        # Background and motivation
        background = self.BACKGROUNDS[role]
        motivation = self.MOTIVATIONS[role]
        
        # Generate stats
        stats = self.generate_stats(role)
        
        # Generate description
        race_desc = self.RACE_DESCRIPTIONS[race]
        age_desc = secrets.choice(["young", "middle-aged", "elderly"])
        physical_features = secrets.choice([
            "with distinctive scars",
            "with piercing eyes",
            "with a warm smile",
            "with weathered features",
            "with elegant bearing",
            "with nervous mannerisms",
        ])
        
        description = f"A {age_desc} {race} {race_desc} {physical_features}"
        
        return NPC(
            name=name,
            race=race,
            role=role,
            alignment=alignment,
            personality_traits=personality_traits,
            ideal=ideal,
            bond=bond,
            flaw=flaw,
            background=background,
            motivation=motivation,
            stats=stats,
            description=description
        )
    
    def format_npc(self, npc: NPC) -> str:
        """Format NPC for display."""
        lines = []
        lines.append(f"=== {npc.name.upper()} ===")
        lines.append(f"{npc.race.title()} {npc.role.value.title()}")
        lines.append(f"Alignment: {npc.alignment.value.replace('_', ' ').title()}")
        lines.append("")
        lines.append(npc.description)
        lines.append("")
        
        # Stats
        lines.append("Ability Scores:")
        lines.append(f"  STR: {npc.stats.str}, DEX: {npc.stats.dex}, CON: {npc.stats.con}")
        lines.append(f"  INT: {npc.stats.int}, WIS: {npc.stats.wis}, CHA: {npc.stats.cha}")
        lines.append(f"  AC: {npc.stats.ac}, HP: {npc.stats.hp}, CR: {npc.stats.cr}")
        lines.append("")
        
        # Personality
        lines.append("Personality:")
        for trait in npc.personality_traits:
            lines.append(f"  • {trait}")
        lines.append("")
        
        lines.append(f"Ideal: {npc.ideal}")
        lines.append(f"Bond: {npc.bond}")
        lines.append(f"Flaw: {npc.flaw}")
        lines.append("")
        
        lines.append(f"Background: {npc.background}")
        lines.append(f"Motivation: {npc.motivation}")
        
        return "\n".join(lines)
