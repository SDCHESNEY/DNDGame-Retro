"""Screen components for retro CLI interface."""

from typing import Optional
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.columns import Columns
from rich.text import Text

from .display import Display
from .colors import ColorScheme, get_hp_color, get_modifier_color


class TitleScreen:
    """Title screen with ASCII art and menu."""
    
    def __init__(self, display: Display):
        """Initialize title screen."""
        self.display = display
    
    def show(self):
        """Display the title screen."""
        self.display.clear()
        
        # Show title ASCII art with dragon
        title = Text(self.display.get_title_ascii(), style=self.display.theme.title)
        self.display.console.print(title)
        
        # Add dragon decoration
        self.display.console.print("\n")
        dragon = Text(self.display.get_dragon_ascii(), style=self.display.theme.secondary)
        self.display.console.print(dragon)
        
        self.display.pause()


class MainMenu:
    """Main menu screen."""
    
    def __init__(self, display: Display):
        """Initialize main menu."""
        self.display = display
    
    def show(self) -> str:
        """Display main menu and get user choice.
        
        Returns:
            Menu choice key
        """
        self.display.clear()
        
        # Show menu options
        options = [
            ("P", "Play - Start or continue a game session"),
            ("C", "Characters - Manage your characters"),
            ("S", "Sessions - View game sessions"),
            ("T", "Theme - Change color scheme"),
            ("Q", "Quit - Exit the game"),
        ]
        
        table = self.display.create_menu_table("╔═══ MAIN MENU ═══╗", options)
        self.display.console.print("\n")
        self.display.print_table(table)
        self.display.console.print("\n")
        
        # Get choice
        choice = Prompt.ask(
            "Select an option",
            choices=["p", "c", "s", "t", "q"],
            default="p",
            show_choices=False,
        )
        
        return choice.lower()


class CharacterSheetScreen:
    """Character sheet display screen."""
    
    def __init__(self, display: Display):
        """Initialize character sheet screen."""
        self.display = display
    
    def show(self, character: dict):
        """Display a character sheet.
        
        Args:
            character: Character data dictionary
        """
        self.display.clear()
        
        # Title
        name = character.get("name", "Unknown")
        char_class = character.get("character_class", "Unknown")
        level = character.get("level", 1)
        race = character.get("race", "Unknown")
        
        title = f"{name} - Level {level} {race} {char_class}"
        self.display.console.print(f"\n╔{'═' * (len(title) + 2)}╗", style=self.display.theme.border)
        self.display.console.print(f"║ {title} ║", style=self.display.theme.title)
        self.display.console.print(f"╚{'═' * (len(title) + 2)}╝\n", style=self.display.theme.border)
        
        # Combat Stats Section
        hp_current = character.get("hp_current", 0)
        hp_max = character.get("hp_max", 0)
        ac = character.get("armor_class", 10)
        initiative = character.get("initiative_bonus", 0)
        speed = character.get("speed", 30)
        
        # HP Bar with color
        hp_color = get_hp_color(hp_current, hp_max, self.display.theme)
        hp_bar = self.display.draw_hp_bar(hp_current, hp_max, width=30)
        
        combat_stats = {
            "Hit Points": f"[{hp_color}]{hp_bar}[/]",
            "Armor Class": str(ac),
            "Initiative": f"+{initiative}" if initiative >= 0 else str(initiative),
            "Speed": f"{speed} ft",
        }
        
        combat_table = self.display.create_stat_table("⚔ Combat Stats", combat_stats)
        
        # Ability Scores Section
        abilities = {}
        for ability in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]:
            score = character.get(ability, 10)
            modifier = (score - 10) // 2
            mod_str = f"+{modifier}" if modifier >= 0 else str(modifier)
            mod_color = get_modifier_color(modifier, self.display.theme)
            abilities[ability.capitalize()[:3].upper()] = f"{score} ([{mod_color}]{mod_str}[/])"
        
        ability_table = self.display.create_stat_table("📊 Abilities", abilities)
        
        # Skills Section (if present)
        proficiencies = character.get("skill_proficiencies", [])
        if proficiencies:
            skills_str = ", ".join(proficiencies)
            skills_table = Table(
                title="🎯 Proficiencies",
                title_style=self.display.theme.title,
                border_style=self.display.theme.border,
                show_header=False,
            )
            skills_table.add_row(skills_str)
        else:
            skills_table = None
        
        # Equipment Section (if present)
        equipment = character.get("equipment", [])
        if equipment:
            equipment_str = ", ".join(equipment)
            equipment_table = Table(
                title="🎒 Equipment",
                title_style=self.display.theme.title,
                border_style=self.display.theme.border,
                show_header=False,
            )
            equipment_table.add_row(equipment_str)
        else:
            equipment_table = None
        
        # Display in two columns
        left_column = [combat_table, ability_table]
        right_column = []
        
        if skills_table:
            right_column.append(skills_table)
        if equipment_table:
            right_column.append(equipment_table)
        
        # Print tables side by side if we have both columns
        if right_column:
            columns = Columns([Table.grid(*left_column), Table.grid(*right_column)])
            self.display.console.print(columns)
        else:
            for table in left_column:
                self.display.console.print(table)
                self.display.console.print()
        
        # Background Section
        background = character.get("background")
        if background:
            self.display.console.print()
            self.display.print_panel(
                background,
                title="📜 Background",
                style=self.display.theme.secondary,
            )
        
        self.display.pause()


class CombatScreen:
    """Combat encounter display screen."""
    
    def __init__(self, display: Display):
        """Initialize combat screen."""
        self.display = display
    
    def show_initiative_order(self, combatants: list[dict]):
        """Display initiative order.
        
        Args:
            combatants: List of combatant dictionaries with name, initiative, hp
        """
        self.display.clear()
        
        self.display.console.print("\n╔═════════════════════════╗", style=self.display.theme.border)
        self.display.console.print("║   INITIATIVE ORDER   ║", style=self.display.theme.title)
        self.display.console.print("╚═════════════════════════╝\n", style=self.display.theme.border)
        
        table = Table(
            border_style=self.display.theme.border,
            show_header=True,
            header_style=self.display.theme.primary,
        )
        
        table.add_column("Init", justify="center", style=self.display.theme.secondary)
        table.add_column("Combatant", style=self.display.theme.text)
        table.add_column("HP", justify="right")
        
        for combatant in combatants:
            name = combatant.get("name", "Unknown")
            initiative = combatant.get("initiative", 0)
            hp_current = combatant.get("hp_current", 0)
            hp_max = combatant.get("hp_max", 0)
            
            hp_color = get_hp_color(hp_current, hp_max, self.display.theme)
            hp_display = f"[{hp_color}]{hp_current}/{hp_max}[/]"
            
            table.add_row(str(initiative), name, hp_display)
        
        self.display.print_table(table)
        self.display.console.print()
    
    def show_combat_action(
        self,
        attacker: str,
        action: str,
        target: Optional[str] = None,
        result: Optional[str] = None,
    ):
        """Display a combat action.
        
        Args:
            attacker: Name of attacking creature
            action: Action description
            target: Target name (optional)
            result: Result description (optional)
        """
        # Build action message
        message = f"{attacker} {action}"
        if target:
            message += f" {target}"
        
        self.display.console.print(f"\n⚔  {message}", style=self.display.theme.primary)
        
        if result:
            self.display.console.print(f"   → {result}", style=self.display.theme.secondary)
    
    def show_damage(self, target: str, damage: int, damage_type: str = ""):
        """Display damage dealt.
        
        Args:
            target: Name of target
            damage: Amount of damage
            damage_type: Type of damage (optional)
        """
        damage_str = f"{damage} damage"
        if damage_type:
            damage_str += f" ({damage_type})"
        
        self.display.console.print(
            f"   💥 {target} takes {damage_str}!",
            style=self.display.theme.error,
        )
    
    def show_healing(self, target: str, healing: int):
        """Display healing received.
        
        Args:
            target: Name of target
            healing: Amount healed
        """
        self.display.console.print(
            f"   ✨ {target} heals {healing} HP!",
            style=self.display.theme.success,
        )
    
    def show_miss(self, attacker: str, target: str):
        """Display a miss.
        
        Args:
            attacker: Name of attacker
            target: Name of target
        """
        self.display.console.print(
            f"   ○ {attacker}'s attack misses {target}!",
            style=self.display.theme.dim,
        )
    
    def show_death(self, creature: str):
        """Display creature death.
        
        Args:
            creature: Name of creature
        """
        self.display.console.print(
            f"\n   💀 {creature} has fallen!",
            style=self.display.theme.warning,
        )
    
    def prompt_action(self) -> str:
        """Prompt for combat action.
        
        Returns:
            Action string
        """
        return Prompt.ask(
            "\n[bold]Your action[/bold]",
            default="attack",
        )
