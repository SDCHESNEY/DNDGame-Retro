"""Color schemes and themes for retro terminal interface."""

from dataclasses import dataclass
from enum import Enum
from rich.style import Style


class ColorScheme(Enum):
    """Available retro color schemes."""
    GREEN_PHOSPHOR = "green_phosphor"  # Classic green-on-black terminal
    AMBER_MONITOR = "amber_monitor"    # Amber monochrome
    IBM_CGA = "ibm_cga"                # IBM CGA palette
    COMMODORE_64 = "commodore_64"      # C64 colors
    APPLE_II = "apple_ii"              # Apple II green


@dataclass
class Theme:
    """Color theme configuration."""
    primary: str
    secondary: str
    success: str
    warning: str
    error: str
    info: str
    text: str
    dim: str
    border: str
    title: str
    hp_good: str
    hp_warning: str
    hp_critical: str
    
    def get_style(self, name: str) -> Style:
        """Get Rich Style for a named color."""
        color = getattr(self, name, self.text)
        return Style(color=color)


# Retro color schemes
THEMES = {
    ColorScheme.GREEN_PHOSPHOR: Theme(
        primary="bright_green",
        secondary="green",
        success="bright_green",
        warning="bright_yellow",
        error="bright_red",
        info="bright_cyan",
        text="green",
        dim="dim green",
        border="bright_green",
        title="bold bright_green",
        hp_good="bright_green",
        hp_warning="bright_yellow",
        hp_critical="bright_red",
    ),
    ColorScheme.AMBER_MONITOR: Theme(
        primary="bright_yellow",
        secondary="yellow",
        success="bright_yellow",
        warning="yellow",
        error="red",
        info="bright_yellow",
        text="yellow",
        dim="dim yellow",
        border="bright_yellow",
        title="bold bright_yellow",
        hp_good="bright_yellow",
        hp_warning="yellow",
        hp_critical="red",
    ),
    ColorScheme.IBM_CGA: Theme(
        primary="bright_cyan",
        secondary="cyan",
        success="bright_green",
        warning="bright_yellow",
        error="bright_red",
        info="bright_cyan",
        text="bright_white",
        dim="white",
        border="bright_magenta",
        title="bold bright_cyan",
        hp_good="bright_green",
        hp_warning="bright_yellow",
        hp_critical="bright_red",
    ),
    ColorScheme.COMMODORE_64: Theme(
        primary="bright_blue",
        secondary="blue",
        success="bright_green",
        warning="bright_yellow",
        error="bright_red",
        info="bright_cyan",
        text="bright_blue",
        dim="blue",
        border="bright_white",
        title="bold bright_cyan",
        hp_good="bright_green",
        hp_warning="yellow",
        hp_critical="red",
    ),
    ColorScheme.APPLE_II: Theme(
        primary="bright_green",
        secondary="green",
        success="bright_green",
        warning="bright_yellow",
        error="bright_red",
        info="bright_cyan",
        text="green",
        dim="dim green",
        border="green",
        title="bold bright_green",
        hp_good="bright_green",
        hp_warning="yellow",
        hp_critical="red",
    ),
}


def get_color_scheme(scheme: ColorScheme = ColorScheme.GREEN_PHOSPHOR) -> Theme:
    """Get a color theme by scheme name."""
    return THEMES.get(scheme, THEMES[ColorScheme.GREEN_PHOSPHOR])


def get_hp_color(current_hp: int, max_hp: int, theme: Theme) -> str:
    """Get appropriate HP color based on percentage remaining."""
    if max_hp == 0:
        return theme.hp_critical
    
    percentage = (current_hp / max_hp) * 100
    
    if percentage > 50:
        return theme.hp_good
    elif percentage > 25:
        return theme.hp_warning
    else:
        return theme.hp_critical


def get_modifier_color(modifier: int, theme: Theme) -> str:
    """Get color for ability modifier based on value."""
    if modifier > 0:
        return theme.success
    elif modifier < 0:
        return theme.error
    else:
        return theme.text
