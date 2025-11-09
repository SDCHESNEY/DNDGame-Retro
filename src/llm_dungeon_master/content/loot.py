"""Loot generator with treasure tables for D&D 5e."""

import secrets
from enum import Enum
from typing import List, Optional
from dataclasses import dataclass


class TreasureType(str, Enum):
    """Types of treasure."""
    INDIVIDUAL = "individual"
    HOARD = "hoard"


class MagicItemRarity(str, Enum):
    """Magic item rarity levels."""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    VERY_RARE = "very_rare"
    LEGENDARY = "legendary"


@dataclass
class Currency:
    """Currency amounts."""
    copper: int = 0
    silver: int = 0
    electrum: int = 0
    gold: int = 0
    platinum: int = 0
    
    def total_gold(self) -> float:
        """Convert all currency to gold value."""
        return (
            self.copper * 0.01 +
            self.silver * 0.1 +
            self.electrum * 0.5 +
            self.gold * 1.0 +
            self.platinum * 10.0
        )


@dataclass
class MagicItem:
    """A magic item."""
    name: str
    rarity: MagicItemRarity
    description: str
    type: str  # weapon, armor, potion, scroll, wondrous


@dataclass
class Treasure:
    """Generated treasure."""
    currency: Currency
    gems: List[str]
    art_objects: List[str]
    magic_items: List[MagicItem]
    treasure_type: TreasureType
    total_value: float


class LootGenerator:
    """Generates treasure based on D&D 5e treasure tables."""
    
    # Individual treasure by CR (dice rolls in gold pieces)
    INDIVIDUAL_TREASURE = {
        (0, 4): {"cp": (5, 6), "ep": None, "sp": None, "gp": None, "pp": None},
        (5, 10): {"cp": (4, 6), "ep": (3, 6), "sp": None, "gp": None, "pp": None},
        (11, 16): {"cp": None, "ep": (3, 6), "sp": (2, 6), "gp": (3, 6), "pp": None},
        (17, 30): {"cp": None, "ep": None, "sp": None, "gp": (2, 6), "pp": (3, 6)},
    }
    
    # Gem values
    GEM_VALUES = [10, 50, 100, 500, 1000, 5000]
    
    GEMS = {
        10: ["Azurite", "Banded agate", "Blue quartz", "Eye agate", "Hematite", 
             "Lapis lazuli", "Malachite", "Moss agate", "Obsidian", "Rhodochrosite"],
        50: ["Bloodstone", "Carnelian", "Chalcedony", "Chrysoprase", "Citrine",
             "Jasper", "Moonstone", "Onyx", "Quartz", "Sardonyx"],
        100: ["Amber", "Amethyst", "Chrysoberyl", "Coral", "Garnet",
              "Jade", "Jet", "Pearl", "Spinel", "Tourmaline"],
        500: ["Alexandrite", "Aquamarine", "Black pearl", "Blue spinel", "Peridot",
              "Topaz"],
        1000: ["Black opal", "Blue sapphire", "Emerald", "Fire opal", "Opal",
               "Star ruby", "Star sapphire", "Yellow sapphire"],
        5000: ["Black sapphire", "Diamond", "Jacinth", "Ruby"],
    }
    
    ART_OBJECTS = {
        25: ["Silver ewer", "Carved bone statuette", "Small gold bracelet",
             "Cloth-of-gold vestments", "Black velvet mask with gems"],
        250: ["Gold ring set with gems", "Small gold idol", "Gold dragon comb",
              "Carved ivory statuette", "Silver necklace with a pendant"],
        750: ["Silver chalice with moonstones", "Gold music box", "Jeweled anklet",
              "Embroidered silk robe", "Large gold bracelet"],
        2500: ["Jeweled gold crown", "Jeweled platinum ring", "Gold cup set with emeralds",
               "Gold jewelry box with platinum filigree", "Painted gold war mask"],
    }
    
    # Magic items by rarity
    MAGIC_ITEMS = {
        MagicItemRarity.COMMON: [
            {"name": "Potion of Healing", "type": "potion", "desc": "Restores 2d4+2 HP"},
            {"name": "Spell Scroll (Cantrip)", "type": "scroll", "desc": "Contains a cantrip"},
            {"name": "Potion of Climbing", "type": "potion", "desc": "Grants climbing speed"},
        ],
        MagicItemRarity.UNCOMMON: [
            {"name": "Bag of Holding", "type": "wondrous", "desc": "Holds 500 lbs in extradimensional space"},
            {"name": "+1 Weapon", "type": "weapon", "desc": "+1 to attack and damage rolls"},
            {"name": "Cloak of Protection", "type": "wondrous", "desc": "+1 to AC and saving throws"},
            {"name": "Potion of Greater Healing", "type": "potion", "desc": "Restores 4d4+4 HP"},
            {"name": "Boots of Elvenkind", "type": "wondrous", "desc": "Advantage on Stealth checks"},
        ],
        MagicItemRarity.RARE: [
            {"name": "+2 Weapon", "type": "weapon", "desc": "+2 to attack and damage rolls"},
            {"name": "Ring of Spell Storing", "type": "wondrous", "desc": "Stores up to 5 spell levels"},
            {"name": "Cloak of Displacement", "type": "wondrous", "desc": "Attackers have disadvantage"},
            {"name": "Flame Tongue", "type": "weapon", "desc": "Deals +2d6 fire damage"},
        ],
        MagicItemRarity.VERY_RARE: [
            {"name": "+3 Weapon", "type": "weapon", "desc": "+3 to attack and damage rolls"},
            {"name": "Ring of Telekinesis", "type": "wondrous", "desc": "Cast telekinesis at will"},
            {"name": "Armor of Invulnerability", "type": "armor", "desc": "Grants resistance to all damage"},
        ],
        MagicItemRarity.LEGENDARY: [
            {"name": "Vorpal Sword", "type": "weapon", "desc": "Decapitates on natural 20"},
            {"name": "Ring of Three Wishes", "type": "wondrous", "desc": "Grants three wishes"},
            {"name": "Holy Avenger", "type": "weapon", "desc": "+3 weapon, bonus vs fiends/undead"},
        ],
    }
    
    def __init__(self):
        """Initialize the loot generator."""
        pass
    
    def roll_dice(self, num_dice: int, die_size: int) -> int:
        """Roll dice and return the sum."""
        return sum(secrets.randbelow(die_size) + 1 for _ in range(num_dice))
    
    def generate_individual_treasure(self, cr: float) -> Treasure:
        """Generate individual treasure for a monster."""
        # Find appropriate CR range
        treasure_data = None
        for cr_range, data in self.INDIVIDUAL_TREASURE.items():
            if cr_range[0] <= cr <= cr_range[1]:
                treasure_data = data
                break
        
        if not treasure_data:
            # Default to highest range for high CR
            treasure_data = self.INDIVIDUAL_TREASURE[(17, 30)]
        
        # Roll for currency
        currency = Currency()
        if treasure_data["cp"]:
            currency.copper = self.roll_dice(*treasure_data["cp"])
        if treasure_data["sp"]:
            currency.silver = self.roll_dice(*treasure_data["sp"])
        if treasure_data["ep"]:
            currency.electrum = self.roll_dice(*treasure_data["ep"])
        if treasure_data["gp"]:
            currency.gold = self.roll_dice(*treasure_data["gp"])
        if treasure_data["pp"]:
            currency.platinum = self.roll_dice(*treasure_data["pp"])
        
        return Treasure(
            currency=currency,
            gems=[],
            art_objects=[],
            magic_items=[],
            treasure_type=TreasureType.INDIVIDUAL,
            total_value=currency.total_gold()
        )
    
    def generate_hoard_treasure(self, cr: float) -> Treasure:
        """Generate hoard treasure for a significant encounter."""
        # Base currency based on CR
        currency = Currency()
        
        if cr <= 4:
            currency.copper = self.roll_dice(6, 6) * 100
            currency.silver = self.roll_dice(3, 6) * 100
            currency.gold = self.roll_dice(2, 6) * 10
        elif cr <= 10:
            currency.copper = self.roll_dice(2, 6) * 100
            currency.silver = self.roll_dice(2, 6) * 1000
            currency.gold = self.roll_dice(6, 6) * 100
            currency.platinum = self.roll_dice(3, 6) * 10
        elif cr <= 16:
            currency.gold = self.roll_dice(4, 6) * 1000
            currency.platinum = self.roll_dice(5, 6) * 100
        else:
            currency.gold = self.roll_dice(12, 6) * 1000
            currency.platinum = self.roll_dice(8, 6) * 1000
        
        # Add gems
        gems = []
        num_gems = secrets.randbelow(6) + 1
        for _ in range(num_gems):
            # Pick gem value based on CR
            if cr <= 4:
                value = secrets.choice([10, 50])
            elif cr <= 10:
                value = secrets.choice([50, 100])
            elif cr <= 16:
                value = secrets.choice([100, 500, 1000])
            else:
                value = secrets.choice([1000, 5000])
            
            gem = secrets.choice(self.GEMS[value])
            gems.append(f"{gem} ({value} gp)")
        
        # Add art objects
        art_objects = []
        num_art = secrets.randbelow(4) + 1
        for _ in range(num_art):
            # Pick art value based on CR
            if cr <= 4:
                value = 25
            elif cr <= 10:
                value = 250
            elif cr <= 16:
                value = 750
            else:
                value = 2500
            
            art = secrets.choice(self.ART_OBJECTS[value])
            art_objects.append(f"{art} ({value} gp)")
        
        # Add magic items based on CR
        magic_items = []
        num_items = 0
        
        if cr <= 4:
            if secrets.randbelow(100) < 50:  # 50% chance
                num_items = secrets.randbelow(2) + 1
                rarity = MagicItemRarity.COMMON
        elif cr <= 10:
            num_items = secrets.randbelow(3) + 1
            rarity = secrets.choice([MagicItemRarity.UNCOMMON, MagicItemRarity.UNCOMMON, MagicItemRarity.RARE])
        elif cr <= 16:
            num_items = secrets.randbelow(4) + 1
            rarity = secrets.choice([MagicItemRarity.RARE, MagicItemRarity.RARE, MagicItemRarity.VERY_RARE])
        else:
            num_items = secrets.randbelow(5) + 2
            rarity = secrets.choice([MagicItemRarity.VERY_RARE, MagicItemRarity.LEGENDARY])
        
        for _ in range(num_items):
            item_data = secrets.choice(self.MAGIC_ITEMS[rarity])
            magic_items.append(MagicItem(
                name=item_data["name"],
                rarity=rarity,
                description=item_data["desc"],
                type=item_data["type"]
            ))
        
        # Calculate total value
        total_value = currency.total_gold()
        total_value += sum(int(g.split("(")[1].split(" ")[0]) for g in gems)
        total_value += sum(int(a.split("(")[1].split(" ")[0]) for a in art_objects)
        
        return Treasure(
            currency=currency,
            gems=gems,
            art_objects=art_objects,
            magic_items=magic_items,
            treasure_type=TreasureType.HOARD,
            total_value=total_value
        )
    
    def generate_treasure(self, cr: float, is_hoard: bool = False) -> Treasure:
        """Generate treasure for a given CR."""
        if is_hoard:
            return self.generate_hoard_treasure(cr)
        else:
            return self.generate_individual_treasure(cr)
    
    def format_treasure(self, treasure: Treasure) -> str:
        """Format treasure for display."""
        lines = []
        lines.append(f"=== {treasure.treasure_type.value.upper()} TREASURE ===")
        lines.append(f"Total Value: {treasure.total_value:.2f} gp")
        lines.append("")
        
        # Currency
        if any([treasure.currency.copper, treasure.currency.silver, treasure.currency.electrum,
                treasure.currency.gold, treasure.currency.platinum]):
            lines.append("Currency:")
            if treasure.currency.copper:
                lines.append(f"  {treasure.currency.copper} cp")
            if treasure.currency.silver:
                lines.append(f"  {treasure.currency.silver} sp")
            if treasure.currency.electrum:
                lines.append(f"  {treasure.currency.electrum} ep")
            if treasure.currency.gold:
                lines.append(f"  {treasure.currency.gold} gp")
            if treasure.currency.platinum:
                lines.append(f"  {treasure.currency.platinum} pp")
            lines.append("")
        
        # Gems
        if treasure.gems:
            lines.append("Gems:")
            for gem in treasure.gems:
                lines.append(f"  {gem}")
            lines.append("")
        
        # Art objects
        if treasure.art_objects:
            lines.append("Art Objects:")
            for art in treasure.art_objects:
                lines.append(f"  {art}")
            lines.append("")
        
        # Magic items
        if treasure.magic_items:
            lines.append("Magic Items:")
            for item in treasure.magic_items:
                lines.append(f"  {item.name} ({item.rarity.value.replace('_', ' ').title()})")
                lines.append(f"    Type: {item.type.title()}")
                lines.append(f"    {item.description}")
        
        return "\n".join(lines)
