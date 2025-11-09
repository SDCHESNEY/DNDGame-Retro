"""Command parser for natural language game commands."""

import re
from typing import Optional
from enum import Enum


class CommandType(Enum):
    """Types of game commands."""
    ATTACK = "attack"
    CAST = "cast"
    MOVE = "move"
    USE = "use"
    LOOK = "look"
    TALK = "talk"
    INVENTORY = "inventory"
    REST = "rest"
    HELP = "help"
    QUIT = "quit"
    UNKNOWN = "unknown"


class ParsedCommand:
    """Represents a parsed command."""
    
    def __init__(
        self,
        command_type: CommandType,
        target: Optional[str] = None,
        item: Optional[str] = None,
        direction: Optional[str] = None,
        raw_text: str = "",
    ):
        """Initialize parsed command.
        
        Args:
            command_type: Type of command
            target: Target of action (e.g., monster to attack)
            item: Item being used (e.g., spell, potion)
            direction: Direction of movement
            raw_text: Original command text
        """
        self.command_type = command_type
        self.target = target
        self.item = item
        self.direction = direction
        self.raw_text = raw_text
    
    def __repr__(self) -> str:
        """String representation."""
        parts = [f"CommandType.{self.command_type.name}"]
        if self.target:
            parts.append(f"target={self.target}")
        if self.item:
            parts.append(f"item={self.item}")
        if self.direction:
            parts.append(f"direction={self.direction}")
        return f"ParsedCommand({', '.join(parts)})"


class CommandParser:
    """Parser for natural language game commands."""
    
    # Attack synonyms
    ATTACK_PATTERNS = [
        r"^(?:attack|hit|strike|fight|slash|stab)\s+(?:the\s+)?(.+)$",
        r"^(.+)\s+(?:attack|hit|strike)$",
    ]
    
    # Spell casting patterns
    CAST_PATTERNS = [
        r"^(?:cast|use)\s+(.+?)\s+(?:on|at|against)\s+(?:the\s+)?(.+)$",
        r"^(?:cast|use)\s+(.+)$",
    ]
    
    # Movement patterns
    MOVE_PATTERNS = [
        r"^(?:go|move|walk|run|head)\s+(?:to\s+)?(?:the\s+)?(north|south|east|west|up|down|n|s|e|w|u|d)$",
        r"^(north|south|east|west|up|down|n|s|e|w|u|d)$",
    ]
    
    # Item usage patterns
    USE_PATTERNS = [
        r"^(?:use|drink|consume|eat)\s+(?:the\s+)?(.+)$",
    ]
    
    # Looking patterns
    LOOK_PATTERNS = [
        r"^(?:look|examine|inspect)\s+(?:at\s+)?(?:the\s+)?(.+)$",
        r"^(?:look|l)$",
    ]
    
    # Talking patterns
    TALK_PATTERNS = [
        r"^(?:talk|speak|chat)\s+(?:to|with)\s+(?:the\s+)?(.+)$",
    ]
    
    # Simple commands
    SIMPLE_COMMANDS = {
        "inventory": CommandType.INVENTORY,
        "inv": CommandType.INVENTORY,
        "i": CommandType.INVENTORY,
        "rest": CommandType.REST,
        "sleep": CommandType.REST,
        "help": CommandType.HELP,
        "?": CommandType.HELP,
        "quit": CommandType.QUIT,
        "exit": CommandType.QUIT,
        "q": CommandType.QUIT,
    }
    
    # Direction abbreviations
    DIRECTIONS = {
        "n": "north",
        "s": "south",
        "e": "east",
        "w": "west",
        "u": "up",
        "d": "down",
    }
    
    def parse(self, text: str) -> ParsedCommand:
        """Parse a command string.
        
        Args:
            text: Command text to parse
        
        Returns:
            ParsedCommand object
        """
        text = text.strip().lower()
        
        if not text:
            return ParsedCommand(CommandType.UNKNOWN, raw_text=text)
        
        # Check simple commands first
        if text in self.SIMPLE_COMMANDS:
            return ParsedCommand(self.SIMPLE_COMMANDS[text], raw_text=text)
        
        # Try attack patterns
        for pattern in self.ATTACK_PATTERNS:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                target = match.group(1).strip()
                return ParsedCommand(CommandType.ATTACK, target=target, raw_text=text)
        
        # Try spell casting patterns
        for pattern in self.CAST_PATTERNS:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                spell = groups[0].strip()
                target = groups[1].strip() if len(groups) > 1 else None
                return ParsedCommand(
                    CommandType.CAST,
                    item=spell,
                    target=target,
                    raw_text=text,
                )
        
        # Try movement patterns
        for pattern in self.MOVE_PATTERNS:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                direction = match.group(1).strip().lower()
                # Expand abbreviations
                direction = self.DIRECTIONS.get(direction, direction)
                return ParsedCommand(
                    CommandType.MOVE,
                    direction=direction,
                    raw_text=text,
                )
        
        # Try item usage patterns
        for pattern in self.USE_PATTERNS:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                item = match.group(1).strip()
                return ParsedCommand(CommandType.USE, item=item, raw_text=text)
        
        # Try looking patterns
        for pattern in self.LOOK_PATTERNS:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                target = groups[0].strip() if groups and groups[0] else None
                return ParsedCommand(CommandType.LOOK, target=target, raw_text=text)
        
        # Try talking patterns
        for pattern in self.TALK_PATTERNS:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                target = match.group(1).strip()
                return ParsedCommand(CommandType.TALK, target=target, raw_text=text)
        
        # Unknown command
        return ParsedCommand(CommandType.UNKNOWN, raw_text=text)
    
    def get_help_text(self) -> str:
        """Get help text for available commands.
        
        Returns:
            Formatted help text
        """
        return """
Available Commands:
===================

Combat:
  attack <target>     - Attack a creature (e.g., "attack goblin")
  cast <spell>        - Cast a spell (e.g., "cast fireball")
  cast <spell> on <target> - Cast spell on target

Movement:
  north/south/east/west - Move in a direction (or n/s/e/w)
  up/down              - Go up or down (or u/d)

Interaction:
  look                - Look around the current area
  look at <object>    - Examine something closely
  talk to <npc>       - Speak with an NPC
  use <item>          - Use an item from inventory

Character:
  inventory (i)       - View your inventory
  rest                - Take a short or long rest

System:
  help (?)            - Show this help message
  quit (q)            - Exit the game

You can also type naturally! For example:
  "I attack the goblin"
  "Cast magic missile at the orc"
  "Go north"
  "Drink healing potion"
"""


def parse_command(text: str) -> ParsedCommand:
    """Convenience function to parse a command.
    
    Args:
        text: Command text to parse
    
    Returns:
        ParsedCommand object
    """
    parser = CommandParser()
    return parser.parse(text)
