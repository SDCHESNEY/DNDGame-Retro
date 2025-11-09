"""Location generator for D&D 5e campaigns."""

import secrets
import random
from enum import Enum
from typing import List, Dict, Optional
from dataclasses import dataclass


class LocationType(str, Enum):
    """Types of locations."""
    DUNGEON = "dungeon"
    SETTLEMENT = "settlement"
    WILDERNESS = "wilderness"
    TAVERN = "tavern"
    SHOP = "shop"
    TEMPLE = "temple"


class DungeonTheme(str, Enum):
    """Dungeon themes."""
    CRYPT = "crypt"
    MINE = "mine"
    FORTRESS = "fortress"
    CAVE = "cave"
    TEMPLE = "temple"
    TOWER = "tower"


@dataclass
class Room:
    """A room in a location."""
    name: str
    description: str
    features: List[str]
    connections: List[str]
    hazards: List[str]
    treasure: bool


@dataclass
class Location:
    """A generated location."""
    name: str
    type: LocationType
    description: str
    rooms: List[Room]
    atmosphere: str
    notable_features: List[str]
    inhabitants: List[str]
    hooks: List[str]  # Adventure hooks


class LocationGenerator:
    """Generates locations for D&D 5e campaigns."""
    
    # Dungeon room names by theme
    DUNGEON_ROOMS = {
        DungeonTheme.CRYPT: [
            "Burial Chamber", "Hall of Tombs", "Ossuary", "Funeral Chapel",
            "Catacombs", "Crypt Keeper's Office", "Bone Pit", "Memorial Hall"
        ],
        DungeonTheme.MINE: [
            "Shaft Entrance", "Ore Processing Room", "Cart Rails", "Excavation Site",
            "Collapsed Tunnel", "Storage Chamber", "Foreman's Office", "Smelting Room"
        ],
        DungeonTheme.FORTRESS: [
            "Guard Room", "Barracks", "Armory", "War Room", "Throne Room",
            "Dungeon Cells", "Courtyard", "Keep Tower", "Kitchen"
        ],
        DungeonTheme.CAVE: [
            "Cavern Entrance", "Underground Lake", "Stalactite Gallery", "Crystal Grotto",
            "Narrow Passage", "Mushroom Forest", "Bat Colony", "Echoing Chamber"
        ],
        DungeonTheme.TEMPLE: [
            "Sanctuary", "Meditation Chamber", "Library", "High Priest's Quarters",
            "Offering Room", "Prayer Hall", "Relic Chamber", "Bell Tower"
        ],
        DungeonTheme.TOWER: [
            "Entry Hall", "Library", "Laboratory", "Summoning Circle", "Observatory",
            "Wizard's Study", "Storage Room", "Rooftop Terrace"
        ],
    }
    
    # Room features
    ROOM_FEATURES = {
        DungeonTheme.CRYPT: [
            "Sarcophagi line the walls",
            "Ancient burial urns on pedestals",
            "Faded frescoes depict funeral rites",
            "Cobwebs cover everything",
            "Dusty air with smell of decay",
        ],
        DungeonTheme.MINE: [
            "Mining tools scattered about",
            "Cart tracks run through the room",
            "Support beams creak ominously",
            "Ore veins visible in walls",
            "Dim crystals provide faint light",
        ],
        DungeonTheme.FORTRESS: [
            "Arrow slits in thick walls",
            "Weapon racks along the walls",
            "Banners hang from ceiling",
            "Heavy oak doors reinforced with iron",
            "Murder holes in the ceiling",
        ],
        DungeonTheme.CAVE: [
            "Natural rock formations",
            "Underground stream flows through",
            "Bioluminescent fungi grow here",
            "Dripping water echoes",
            "Uneven, slippery floor",
        ],
        DungeonTheme.TEMPLE: [
            "Altar at the far end",
            "Religious symbols adorn walls",
            "Incense burners release fragrant smoke",
            "Stained glass windows",
            "Kneeling cushions arranged in rows",
        ],
        DungeonTheme.TOWER: [
            "Spiral staircase to next level",
            "Bookshelves filled with tomes",
            "Magical runes glow faintly",
            "Arcane apparatus on tables",
            "Large windows overlooking landscape",
        ],
    }
    
    # Hazards
    HAZARDS = [
        "Pit trap (10 ft deep)",
        "Poisoned needle trap",
        "Collapsing ceiling",
        "Slippery floor",
        "Noxious gas",
        "Swinging blade trap",
        "Pressure plate triggering arrows",
        "Unstable floor (may collapse)",
    ]
    
    # Settlement names
    SETTLEMENT_PREFIXES = [
        "New", "Old", "North", "South", "East", "West", "High", "Low",
        "Green", "Red", "White", "Black", "Silver", "Golden"
    ]
    
    SETTLEMENT_SUFFIXES = [
        "haven", "town", "ville", "bridge", "ford", "field", "wood",
        "port", "dale", "castle", "keep", "watch"
    ]
    
    # Settlement features
    SETTLEMENT_FEATURES = [
        "Market square with weekly bazaar",
        "Ancient stone walls surround the settlement",
        "Notable temple to a major deity",
        "Thriving merchant district",
        "Underground sewers rumored to hold secrets",
        "Famous tavern known throughout the region",
        "Powerful wizard's tower on the outskirts",
        "Well-maintained roads and infrastructure",
    ]
    
    # Wilderness features
    WILDERNESS_FEATURES = {
        "forest": [
            "Ancient trees tower overhead",
            "Thick underbrush limits visibility",
            "Animal trails crisscross the area",
            "Babbling brook runs through",
            "Mysterious stone circle in a clearing",
        ],
        "mountains": [
            "Jagged peaks loom above",
            "Treacherous paths wind upward",
            "Mountain goats leap between crags",
            "Eagle nests visible on cliff faces",
            "Cave entrance in mountainside",
        ],
        "swamp": [
            "Murky water obscures depth",
            "Gnarled cypress trees rise from water",
            "Thick fog reduces visibility",
            "Strange sounds echo through mist",
            "Patches of quicksand dot the area",
        ],
    }
    
    # Adventure hooks
    ADVENTURE_HOOKS = [
        "Locals report strange noises at night",
        "A valuable item has been stolen",
        "Someone has gone missing",
        "Monsters have been spotted nearby",
        "An ancient prophecy mentions this place",
        "A rival adventuring party seeks the same goal",
        "The local lord offers a reward",
        "A map shows hidden treasure here",
    ]
    
    def __init__(self):
        """Initialize the location generator."""
        pass
    
    def generate_dungeon(
        self,
        theme: Optional[DungeonTheme] = None,
        num_rooms: int = 6
    ) -> Location:
        """Generate a dungeon."""
        if theme is None:
            theme = secrets.choice(list(DungeonTheme))
        
        # Generate name
        prefixes = ["The", "Ancient", "Lost", "Forgotten", "Dark", "Cursed"]
        suffixes = ["Depths", "Halls", "Ruins", "Sanctum", "Domain", "Lair"]
        name = f"{secrets.choice(prefixes)} {theme.value.title()} {secrets.choice(suffixes)}"
        
        # Generate rooms
        room_names = random.sample(self.DUNGEON_ROOMS[theme], min(num_rooms, len(self.DUNGEON_ROOMS[theme])))
        rooms = []
        
        for i, room_name in enumerate(room_names):
            # Pick features
            features = random.sample(
                self.ROOM_FEATURES[theme],
                k=secrets.randbelow(3) + 2
            )
            
            # Connections
            connections = []
            if i > 0:
                connections.append(f"Passage to {room_names[i-1]}")
            if i < len(room_names) - 1:
                connections.append(f"Door to {room_names[i+1]}")
            
            # Random connections to other rooms
            if i > 1 and secrets.randbelow(100) < 30:
                other_room = secrets.choice(room_names[:i-1])
                connections.append(f"Secret passage to {other_room}")
            
            # Hazards (33% chance)
            hazards = []
            if secrets.randbelow(100) < 33:
                hazards.append(secrets.choice(self.HAZARDS))
            
            # Treasure (50% chance)
            has_treasure = secrets.randbelow(100) < 50
            
            # Description
            desc = f"A {room_name.lower()} with {features[0].lower()}."
            
            rooms.append(Room(
                name=room_name,
                description=desc,
                features=features,
                connections=connections,
                hazards=hazards,
                treasure=has_treasure
            ))
        
        # Overall description
        atmospheres = {
            DungeonTheme.CRYPT: "musty and cold, filled with the silence of the dead",
            DungeonTheme.MINE: "echoing with distant drips, air thick with dust",
            DungeonTheme.FORTRESS: "imposing and militaristic, designed for defense",
            DungeonTheme.CAVE: "damp and natural, shaped by ages of water flow",
            DungeonTheme.TEMPLE: "reverent and sacred, though long abandoned",
            DungeonTheme.TOWER: "arcane and mysterious, crackling with residual magic",
        }
        
        description = f"A {theme.value} {atmospheres[theme]}"
        atmosphere = atmospheres[theme]
        
        # Notable features
        notable_features = [
            f"Built {secrets.choice(['centuries', 'millennia'])} ago",
            f"Contains {secrets.choice(['ancient', 'powerful', 'cursed'])} artifacts",
            f"Home to {secrets.choice(['undead', 'monsters', 'cultists', 'bandits'])}",
        ]
        
        # Inhabitants
        inhabitants = [
            secrets.choice(["Skeletons", "Zombies", "Goblins", "Orcs", "Cultists"])
        ]
        
        # Hooks
        hooks = random.sample(self.ADVENTURE_HOOKS, k=2)
        
        return Location(
            name=name,
            type=LocationType.DUNGEON,
            description=description,
            rooms=rooms,
            atmosphere=atmosphere,
            notable_features=notable_features,
            inhabitants=inhabitants,
            hooks=hooks
        )
    
    def generate_settlement(self, size: str = "town") -> Location:
        """Generate a settlement."""
        # Generate name
        prefix = secrets.choice(self.SETTLEMENT_PREFIXES)
        suffix = secrets.choice(self.SETTLEMENT_SUFFIXES)
        name = f"{prefix}{suffix}"
        
        # Notable locations within settlement
        locations = [
            "The Town Square", "The Market", "The Tavern", "The Inn",
            "The Temple", "The Blacksmith", "The General Store", "The Town Hall"
        ]
        
        rooms = []
        for loc in locations:
            desc = f"A bustling {loc.lower()} in the heart of {name}"
            features = [secrets.choice(self.SETTLEMENT_FEATURES)]
            
            rooms.append(Room(
                name=loc,
                description=desc,
                features=features,
                connections=[f"Streets lead to other parts of {name}"],
                hazards=[],
                treasure=False
            ))
        
        # Description
        sizes = {
            "village": "small village with a few dozen residents",
            "town": "modest town with several hundred residents",
            "city": "large city with thousands of residents",
        }
        description = f"A {sizes.get(size, sizes['town'])}"
        
        atmosphere = secrets.choice([
            "friendly and welcoming to travelers",
            "bustling with trade and commerce",
            "quiet and peaceful",
            "tense due to recent troubles",
        ])
        
        # Features
        notable_features = random.sample(self.SETTLEMENT_FEATURES, k=3)
        
        # Inhabitants
        inhabitants = ["Humans", "Elves", "Dwarves", "Halflings", "Various races"]
        
        # Hooks
        hooks = random.sample(self.ADVENTURE_HOOKS, k=2)
        
        return Location(
            name=name,
            type=LocationType.SETTLEMENT,
            description=description,
            rooms=rooms,
            atmosphere=atmosphere,
            notable_features=notable_features,
            inhabitants=inhabitants,
            hooks=hooks
        )
    
    def generate_wilderness(self, terrain: str = "forest") -> Location:
        """Generate a wilderness area."""
        # Generate name
        adjectives = ["Dark", "Ancient", "Wild", "Mystic", "Haunted", "Verdant"]
        terrains = {"forest": "Forest", "mountains": "Mountains", "swamp": "Swamp"}
        name = f"The {secrets.choice(adjectives)} {terrains.get(terrain, 'Forest')}"
        
        # Areas within wilderness
        area_names = [
            "Clearing", "Overlook", "Grove", "Path Junction",
            "Stream Crossing", "Rock Formation"
        ]
        
        rooms = []
        features_list = self.WILDERNESS_FEATURES.get(terrain, self.WILDERNESS_FEATURES["forest"])
        
        for area in area_names:
            features = random.sample(features_list, k=2)
            desc = f"A natural {area.lower()} with {features[0].lower()}"
            
            rooms.append(Room(
                name=area,
                description=desc,
                features=features,
                connections=["Trails lead in multiple directions"],
                hazards=[],
                treasure=secrets.randbelow(100) < 20  # 20% chance
            ))
        
        # Description
        description = f"A {terrain} area {features_list[0].lower()}"
        atmosphere = secrets.choice([
            "eerily quiet and still",
            "filled with natural sounds",
            "wild and untamed",
            "peaceful and serene",
        ])
        
        # Features
        notable_features = random.sample(features_list, k=3)
        
        # Inhabitants
        wildlife = {
            "forest": ["Wolves", "Bears", "Deer", "Wild boars"],
            "mountains": ["Mountain goats", "Eagles", "Mountain lions"],
            "swamp": ["Crocodiles", "Snakes", "Giant frogs"],
        }
        inhabitants = wildlife.get(terrain, wildlife["forest"])
        
        # Hooks
        hooks = random.sample(self.ADVENTURE_HOOKS, k=2)
        
        return Location(
            name=name,
            type=LocationType.WILDERNESS,
            description=description,
            rooms=rooms,
            atmosphere=atmosphere,
            notable_features=notable_features,
            inhabitants=inhabitants,
            hooks=hooks
        )
    
    def format_location(self, location: Location) -> str:
        """Format location for display."""
        lines = []
        lines.append(f"=== {location.name.upper()} ===")
        lines.append(f"Type: {location.type.value.title()}")
        lines.append("")
        lines.append(f"Description: {location.description}")
        lines.append(f"Atmosphere: {location.atmosphere}")
        lines.append("")
        
        lines.append("Notable Features:")
        for feature in location.notable_features:
            lines.append(f"  • {feature}")
        lines.append("")
        
        lines.append("Inhabitants:")
        for inhabitant in location.inhabitants:
            lines.append(f"  • {inhabitant}")
        lines.append("")
        
        lines.append(f"Areas/Rooms ({len(location.rooms)}):")
        for i, room in enumerate(location.rooms, 1):
            lines.append(f"\n{i}. {room.name}")
            lines.append(f"   {room.description}")
            
            if room.features:
                lines.append("   Features:")
                for feature in room.features:
                    lines.append(f"     • {feature}")
            
            if room.hazards:
                lines.append("   Hazards:")
                for hazard in room.hazards:
                    lines.append(f"     ⚠ {hazard}")
            
            if room.treasure:
                lines.append("   💎 Contains treasure!")
        
        lines.append("\nAdventure Hooks:")
        for hook in location.hooks:
            lines.append(f"  • {hook}")
        
        return "\n".join(lines)
