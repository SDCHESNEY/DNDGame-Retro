"""Animation utilities for dice rolls and combat effects."""

import random
import time
from typing import Optional
from rich.live import Live
from rich.text import Text
from rich.panel import Panel

from .display import Display


class DiceAnimation:
    """ASCII animation for dice rolls."""
    
    # ASCII art for each die face
    D20_FACES = {
        1: ["┌─────────┐",
            "│         │",
            "│    ●    │",
            "│         │",
            "└─────────┘"],
        20: ["┌─────────┐",
             "│  ●   ●  │",
             "│  ●●●●●  │",
             "│  ●   ●  │",
             "└─────────┘"],
    }
    
    def __init__(self, display: Display):
        """Initialize dice animation."""
        self.display = display
    
    def _get_dice_art(self, value: int, sides: int = 20) -> list[str]:
        """Get ASCII art for a die showing a specific value.
        
        Args:
            value: Die value to show
            sides: Number of sides on die
        
        Returns:
            List of strings representing die face
        """
        # For d20, use special faces for 1 and 20
        if sides == 20:
            if value == 1:
                return self.D20_FACES[1]
            elif value == 20:
                return self.D20_FACES[20]
        
        # Generic die face
        return [
            "┌─────────┐",
            f"│         │",
            f"│   {value:2d}    │",
            f"│         │",
            "└─────────┘",
        ]
    
    def _get_rolling_art(self) -> list[str]:
        """Get ASCII art for a rolling die."""
        frames = [
            ["┌─────────┐",
             "│  ╱   ╲  │",
             "│ ●  ?  ● │",
             "│  ╲   ╱  │",
             "└─────────┘"],
            ["┌─────────┐",
             "│  ─   ─  │",
             "│ ●  ?  ● │",
             "│  ─   ─  │",
             "└─────────┘"],
            ["┌─────────┐",
             "│  ╲   ╱  │",
             "│ ●  ?  ● │",
             "│  ╱   ╲  │",
             "└─────────┘"],
        ]
        return random.choice(frames)
    
    def roll(
        self,
        sides: int = 20,
        count: int = 1,
        modifier: int = 0,
        label: str = "Roll",
    ) -> int:
        """Animate a dice roll and return result.
        
        Args:
            sides: Number of sides on die
            count: Number of dice to roll
            modifier: Modifier to add to roll
            label: Label for the roll
        
        Returns:
            Total roll result
        """
        # Perform actual roll
        rolls = [random.randint(1, sides) for _ in range(count)]
        total = sum(rolls) + modifier
        
        # Show rolling animation
        with Live(refresh_per_second=10) as live:
            # Rolling phase
            for _ in range(15):
                art = self._get_rolling_art()
                text = Text("\n".join(art), style=self.display.theme.secondary)
                panel = Panel(
                    text,
                    title=f"🎲 {label}",
                    title_align="left",
                    border_style=self.display.theme.border,
                )
                live.update(panel)
                time.sleep(0.1)
            
            # Show result
            if count == 1:
                art = self._get_dice_art(rolls[0], sides)
                result_text = f"\n{rolls[0]}"
            else:
                result_text = f"\n{' + '.join(map(str, rolls))}"
            
            if modifier != 0:
                mod_str = f"+{modifier}" if modifier > 0 else str(modifier)
                result_text += f" {mod_str}"
            
            result_text += f" = {total}"
            
            art = self._get_dice_art(rolls[0], sides) if count == 1 else [
                "┌─────────┐",
                f"│  TOTAL  │",
                f"│   {total:2d}    │",
                f"│         │",
                "└─────────┘",
            ]
            
            text = Text("\n".join(art), style=self.display.theme.primary)
            text.append(result_text, style=self.display.theme.success)
            
            panel = Panel(
                text,
                title=f"🎲 {label}",
                title_align="left",
                border_style=self.display.theme.success,
            )
            live.update(panel)
            time.sleep(1)
        
        return total
    
    def advantage_roll(self, sides: int = 20, modifier: int = 0, label: str = "Advantage Roll") -> int:
        """Roll with advantage (take higher of two rolls).
        
        Args:
            sides: Number of sides on die
            modifier: Modifier to add to roll
            label: Label for the roll
        
        Returns:
            Total roll result (higher roll + modifier)
        """
        roll1 = random.randint(1, sides)
        roll2 = random.randint(1, sides)
        higher = max(roll1, roll2)
        total = higher + modifier
        
        self.display.console.print(
            f"\n🎲 {label}: {roll1} vs {roll2} → Using {higher}",
            style=self.display.theme.primary,
        )
        
        if modifier != 0:
            mod_str = f"+{modifier}" if modifier > 0 else str(modifier)
            self.display.console.print(
                f"   {higher} {mod_str} = {total}",
                style=self.display.theme.success,
            )
        
        return total
    
    def disadvantage_roll(self, sides: int = 20, modifier: int = 0, label: str = "Disadvantage Roll") -> int:
        """Roll with disadvantage (take lower of two rolls).
        
        Args:
            sides: Number of sides on die
            modifier: Modifier to add to roll
            label: Label for the roll
        
        Returns:
            Total roll result (lower roll + modifier)
        """
        roll1 = random.randint(1, sides)
        roll2 = random.randint(1, sides)
        lower = min(roll1, roll2)
        total = lower + modifier
        
        self.display.console.print(
            f"\n🎲 {label}: {roll1} vs {roll2} → Using {lower}",
            style=self.display.theme.primary,
        )
        
        if modifier != 0:
            mod_str = f"+{modifier}" if modifier > 0 else str(modifier)
            self.display.console.print(
                f"   {lower} {mod_str} = {total}",
                style=self.display.theme.warning,
            )
        
        return total


class CombatAnimation:
    """ASCII animations for combat effects."""
    
    def __init__(self, display: Display):
        """Initialize combat animation."""
        self.display = display
    
    def attack_animation(self, attacker: str, target: str):
        """Show attack animation.
        
        Args:
            attacker: Name of attacker
            target: Name of target
        """
        frames = [
            f"{attacker} ─→     {target}",
            f"{attacker}  ─→    {target}",
            f"{attacker}   ─→   {target}",
            f"{attacker}    ─→  {target}",
            f"{attacker}     ─→ {target}",
            f"{attacker}      ⚔ {target}",
        ]
        
        with Live(refresh_per_second=10) as live:
            for frame in frames:
                text = Text(frame, style=self.display.theme.primary)
                live.update(text)
                time.sleep(0.1)
    
    def spell_animation(self, caster: str, target: str, spell_name: str):
        """Show spell casting animation.
        
        Args:
            caster: Name of caster
            target: Name of target
            spell_name: Name of spell
        """
        frames = [
            f"{caster} ✨         {target}",
            f"{caster}  ✨✨       {target}",
            f"{caster}   ✨✨✨     {target}",
            f"{caster}    ✨✨✨✨   {target}",
            f"{caster}     💥💥💥  {target}",
        ]
        
        with Live(refresh_per_second=8) as live:
            for frame in frames:
                text = Text(f"{spell_name}:", style=self.display.theme.info)
                text.append(f"\n{frame}", style=self.display.theme.secondary)
                live.update(text)
                time.sleep(0.15)
    
    def critical_hit_flash(self):
        """Flash the screen for a critical hit."""
        flash_frames = ["💥", "✨", "⚡", "💥", "✨"]
        
        with Live(refresh_per_second=10) as live:
            for frame in flash_frames:
                text = Text(
                    f"\n\n{'  ' * 10}{frame * 5}\n"
                    f"{'  ' * 8}CRITICAL HIT!\n"
                    f"{'  ' * 10}{frame * 5}\n",
                    style=self.display.theme.warning,
                )
                live.update(text)
                time.sleep(0.15)
    
    def healing_animation(self, target: str):
        """Show healing animation.
        
        Args:
            target: Name of creature being healed
        """
        frames = [
            f"    ✨    \n   {target}",
            f"   ✨✨   \n   {target}",
            f"  ✨✨✨  \n   {target}",
            f" ✨✨✨✨ \n   {target}",
            f"    💚    \n   {target}",
        ]
        
        with Live(refresh_per_second=8) as live:
            for frame in frames:
                text = Text(frame, style=self.display.theme.success)
                live.update(text)
                time.sleep(0.15)
    
    def death_animation(self, creature: str):
        """Show death animation.
        
        Args:
            creature: Name of creature dying
        """
        frames = [
            f"{creature} 🧍",
            f"{creature} 🧎",
            f"{creature} 💀",
            f"        💀 {creature}",
        ]
        
        with Live(refresh_per_second=4) as live:
            for frame in frames:
                text = Text(frame, style=self.display.theme.dim)
                live.update(text)
                time.sleep(0.3)
