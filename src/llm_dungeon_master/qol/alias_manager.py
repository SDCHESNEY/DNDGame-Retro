"""Command alias management for shortcuts."""

import json
from pathlib import Path
from typing import Dict, Optional, List


class AliasManager:
    """Manages command aliases and shortcuts."""
    
    # Default aliases
    DEFAULT_ALIASES = {
        # Movement
        "n": "move north",
        "s": "move south",
        "e": "move east",
        "w": "move west",
        "ne": "move northeast",
        "nw": "move northwest",
        "se": "move southeast",
        "sw": "move southwest",
        "u": "move up",
        "d": "move down",
        
        # Common actions
        "i": "inventory",
        "inv": "inventory",
        "l": "look",
        "ex": "examine",
        "atk": "attack",
        "def": "defend",
        
        # Dice shortcuts
        "r": "roll",
        "r20": "roll 1d20",
        "adv": "roll 1d20 advantage",
        "dis": "roll 1d20 disadvantage",
        
        # Character shortcuts
        "hp": "status hp",
        "ac": "status ac",
        "stats": "character stats",
        "char": "character show",
        
        # Session shortcuts
        "save": "session save",
        "load": "session load",
        "exit": "session end",
        "quit": "session end",
        
        # Help shortcuts
        "h": "help",
        "?": "help",
        "??": "help all",
    }
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize alias manager.
        
        Args:
            config_dir: Directory for alias config (default: ~/.dndgame/)
        """
        self.config_dir = config_dir or Path.home() / ".dndgame"
        self.config_dir.mkdir(exist_ok=True)
        self.alias_file = self.config_dir / "aliases.json"
        
        # Load aliases
        self.aliases = self.DEFAULT_ALIASES.copy()
        self.load_aliases()
    
    def load_aliases(self):
        """Load custom aliases from config file."""
        if self.alias_file.exists():
            try:
                with open(self.alias_file, 'r') as f:
                    custom = json.load(f)
                    self.aliases.update(custom)
            except Exception:
                pass
    
    def save_aliases(self):
        """Save custom aliases to config file."""
        # Only save non-default aliases
        custom = {
            k: v for k, v in self.aliases.items()
            if k not in self.DEFAULT_ALIASES or v != self.DEFAULT_ALIASES.get(k)
        }
        
        with open(self.alias_file, 'w') as f:
            json.dump(custom, f, indent=2)
    
    def add_alias(self, alias: str, command: str) -> bool:
        """Add or update an alias.
        
        Args:
            alias: Alias shortcut
            command: Full command
            
        Returns:
            True if added successfully
        """
        self.aliases[alias.lower()] = command
        self.save_aliases()
        return True
    
    def remove_alias(self, alias: str) -> bool:
        """Remove a custom alias.
        
        Args:
            alias: Alias to remove
            
        Returns:
            True if removed
        """
        alias = alias.lower()
        
        # Don't allow removing default aliases
        if alias in self.DEFAULT_ALIASES and self.aliases.get(alias) == self.DEFAULT_ALIASES[alias]:
            return False
        
        if alias in self.aliases:
            del self.aliases[alias]
            self.save_aliases()
            return True
        
        return False
    
    def expand_alias(self, command: str) -> str:
        """Expand an alias to its full command.
        
        Args:
            command: Command (may be an alias)
            
        Returns:
            Expanded command
        """
        parts = command.split(None, 1)
        if not parts:
            return command
        
        first_word = parts[0].lower()
        rest = parts[1] if len(parts) > 1 else ""
        
        if first_word in self.aliases:
            expanded = self.aliases[first_word]
            if rest:
                # If alias has parameters, append them
                return f"{expanded} {rest}"
            return expanded
        
        return command
    
    def get_alias(self, alias: str) -> Optional[str]:
        """Get the command for an alias.
        
        Args:
            alias: Alias to look up
            
        Returns:
            Command or None if not found
        """
        return self.aliases.get(alias.lower())
    
    def list_aliases(self, include_defaults: bool = True) -> Dict[str, str]:
        """List all aliases.
        
        Args:
            include_defaults: Whether to include default aliases
            
        Returns:
            Dictionary of aliases
        """
        if include_defaults:
            return self.aliases.copy()
        else:
            return {
                k: v for k, v in self.aliases.items()
                if k not in self.DEFAULT_ALIASES or v != self.DEFAULT_ALIASES.get(k)
            }
    
    def reset_aliases(self):
        """Reset to default aliases only."""
        self.aliases = self.DEFAULT_ALIASES.copy()
        if self.alias_file.exists():
            self.alias_file.unlink()
    
    def import_aliases(self, filepath: Path) -> int:
        """Import aliases from a file.
        
        Args:
            filepath: Path to alias file
            
        Returns:
            Number of aliases imported
        """
        try:
            with open(filepath, 'r') as f:
                imported = json.load(f)
            
            count = 0
            for alias, command in imported.items():
                if isinstance(command, str):
                    self.add_alias(alias, command)
                    count += 1
            
            return count
        except Exception:
            return 0
    
    def export_aliases(self, filepath: Path, custom_only: bool = True) -> bool:
        """Export aliases to a file.
        
        Args:
            filepath: Path to save aliases
            custom_only: Only export custom (non-default) aliases
            
        Returns:
            True if exported successfully
        """
        try:
            aliases = self.list_aliases(include_defaults=not custom_only)
            
            with open(filepath, 'w') as f:
                json.dump(aliases, f, indent=2)
            
            return True
        except Exception:
            return False
    
    def format_aliases(self, category: Optional[str] = None) -> str:
        """Format aliases for display.
        
        Args:
            category: Optional category filter
            
        Returns:
            Formatted alias list
        """
        lines = ["=== COMMAND ALIASES ===\n"]
        
        categories = {
            "movement": ["n", "s", "e", "w", "ne", "nw", "se", "sw", "u", "d"],
            "actions": ["i", "inv", "l", "ex", "atk", "def"],
            "dice": ["r", "r20", "adv", "dis"],
            "character": ["hp", "ac", "stats", "char"],
            "session": ["save", "load", "exit", "quit"],
            "help": ["h", "?", "??"]
        }
        
        if category and category in categories:
            lines.append(f"{category.title()} Aliases:")
            for alias in categories[category]:
                if alias in self.aliases:
                    lines.append(f"  {alias:10} -> {self.aliases[alias]}")
        else:
            for cat_name, aliases in categories.items():
                lines.append(f"\n{cat_name.title()}:")
                for alias in aliases:
                    if alias in self.aliases:
                        lines.append(f"  {alias:10} -> {self.aliases[alias]}")
            
            # Show custom aliases
            custom = self.list_aliases(include_defaults=False)
            if custom:
                lines.append("\nCustom:")
                for alias, command in sorted(custom.items()):
                    if alias not in sum(categories.values(), []):
                        lines.append(f"  {alias:10} -> {command}")
        
        lines.append(f"\nTotal: {len(self.aliases)} aliases")
        return "\n".join(lines)
