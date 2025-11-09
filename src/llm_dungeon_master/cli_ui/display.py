"""Display utilities for ASCII art and terminal formatting."""

import time
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.layout import Layout
from rich.align import Align

from .colors import ColorScheme, get_color_scheme, Theme


class Display:
    """Terminal display manager for retro CLI interface."""
    
    def __init__(self, color_scheme: ColorScheme = ColorScheme.GREEN_PHOSPHOR):
        """Initialize display with color scheme."""
        self.console = Console()
        self.theme = get_color_scheme(color_scheme)
        self.color_scheme = color_scheme
    
    def clear(self):
        """Clear the terminal screen."""
        self.console.clear()
    
    def print(self, text: str, style: Optional[str] = None, **kwargs):
        """Print text with optional styling."""
        if style:
            self.console.print(text, style=style, **kwargs)
        else:
            self.console.print(text, style=self.theme.text, **kwargs)
    
    def print_panel(self, content: str, title: str = "", style: Optional[str] = None, **kwargs):
        """Print content in a bordered panel."""
        panel_style = style or self.theme.border
        title_style = self.theme.title if title else None
        
        panel = Panel(
            content,
            title=title,
            border_style=panel_style,
            title_align="left",
            **kwargs
        )
        self.console.print(panel)
    
    def print_table(self, table: Table):
        """Print a formatted table."""
        self.console.print(table)
    
    def get_title_ascii(self) -> str:
        """Get ASCII art for title screen."""
        return """
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║   ██████╗ ███╗   ██╗██████╗      ██████╗  █████╗ ███╗   ███╗███████╗    ║
║   ██╔══██╗████╗  ██║██╔══██╗    ██╔════╝ ██╔══██╗████╗ ████║██╔════╝    ║
║   ██║  ██║██╔██╗ ██║██║  ██║    ██║  ███╗███████║██╔████╔██║█████╗      ║
║   ██║  ██║██║╚██╗██║██║  ██║    ██║   ██║██╔══██║██║╚██╔╝██║██╔══╝      ║
║   ██████╔╝██║ ╚████║██████╔╝    ╚██████╔╝██║  ██║██║ ╚═╝ ██║███████╗    ║
║   ╚═════╝ ╚═╝  ╚═══╝╚═════╝      ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝    ║
║                                                                           ║
║                   ~ LLM DUNGEON MASTER ~                                  ║
║              A Retro Text-Based RPG Adventure                             ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""
    
    def get_dragon_ascii(self) -> str:
        """Get ASCII art of a dragon."""
        return """
                                                  __----~~~~~~~~~~~------___
                                   .  .   ~~//====......          __--~ ~~
                   -.            \\_|//     |||\\\\  ~~~~~~::::... /~
                ___-==_       _-~o~  \\/    |||  \\\\            _/~~-
        __---~~~.==~||\\=_    -_--~/_-~|-   |\\\\   \\\\        _/~
    _-~~     .=~    |  \\\\-_    '-~7  /-   /  ||    \\      /
  .~       .~       |   \\\\ -_    /  /-   /   ||      \\   /
 /  ____  /         |     \\\\ ~-_/  /|- _/   .||       \\ /
 |~~    ~~|--~~~~--_ \\     ~==-/   | \\~--===~~        .\\
          '         ~-|      /|    |-~\\~~       __--~~
                      |-~~-_/ |    |   ~\\_   _-~            /\\
                           /  \\     \\__   \\/~                \\__
                       _--~ _/ | .-~~____--~-/                  ~~==.
                      ((->/~   '.|||' -_|    ~~-/ ,              . _||
                                 -_     ~\\      ~~---l__i__i__i--~~_/
                                 _-~-__   ~)  \\--______________--~~
                               //.-~~~-~_--~- |-------~~~~~~~~
                                      //.-~~~--\\
"""
    
    def get_sword_ascii(self) -> str:
        """Get ASCII art of a sword."""
        return '''
            />
           //
          //
         //
        |/
       .|.
       |||
       |||
       |||
       |||
      .||:.
      |||||
      |||||
     .:|||:.
     ||||||
     ||||||
     ||||||
     '""""'
'''
    
    def draw_hp_bar(self, current: int, maximum: int, width: int = 20) -> str:
        """Draw an ASCII HP bar."""
        if maximum == 0:
            percentage = 0
        else:
            percentage = current / maximum
        
        filled = int(width * percentage)
        empty = width - filled
        
        bar = "█" * filled + "░" * empty
        return f"[{bar}] {current}/{maximum}"
    
    def draw_box(self, text: str, width: int = 60) -> str:
        """Draw text in an ASCII box."""
        lines = text.split('\n')
        border = "═" * (width - 2)
        
        result = [f"╔{border}╗"]
        for line in lines:
            padding = width - len(line) - 4
            result.append(f"║ {line}{' ' * padding} ║")
        result.append(f"╚{border}╝")
        
        return '\n'.join(result)
    
    def type_text(self, text: str, delay: float = 0.03):
        """Type out text with a typewriter effect."""
        for char in text:
            self.console.print(char, end="", style=self.theme.text)
            time.sleep(delay)
        self.console.print()  # New line at end
    
    def pause(self, message: str = "\n[Press Enter to continue...]"):
        """Pause and wait for user input."""
        self.console.print(message, style=self.theme.dim)
        input()
    
    def create_menu_table(self, title: str, options: list[tuple[str, str]]) -> Table:
        """Create a formatted menu table.
        
        Args:
            title: Menu title
            options: List of (key, description) tuples
        """
        table = Table(
            title=title,
            title_style=self.theme.title,
            border_style=self.theme.border,
            show_header=False,
            padding=(0, 2),
        )
        
        table.add_column("Key", style=self.theme.primary, no_wrap=True)
        table.add_column("Description", style=self.theme.text)
        
        for key, description in options:
            table.add_row(f"[{key}]", description)
        
        return table
    
    def create_stat_table(self, title: str, stats: dict[str, str]) -> Table:
        """Create a table for displaying character stats."""
        table = Table(
            title=title,
            title_style=self.theme.title,
            border_style=self.theme.border,
            show_header=False,
            padding=(0, 1),
        )
        
        table.add_column("Stat", style=self.theme.secondary, no_wrap=True)
        table.add_column("Value", style=self.theme.primary, justify="right")
        
        for stat, value in stats.items():
            table.add_row(stat, value)
        
        return table
    
    def show_error(self, message: str):
        """Display an error message."""
        self.console.print(f"✗ {message}", style=self.theme.error)
    
    def show_success(self, message: str):
        """Display a success message."""
        self.console.print(f"✓ {message}", style=self.theme.success)
    
    def show_info(self, message: str):
        """Display an info message."""
        self.console.print(f"ℹ {message}", style=self.theme.info)
    
    def show_warning(self, message: str):
        """Display a warning message."""
        self.console.print(f"⚠ {message}", style=self.theme.warning)
