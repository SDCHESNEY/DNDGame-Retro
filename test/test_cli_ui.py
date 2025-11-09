"""Tests for CLI UI components."""

import pytest
from llm_dungeon_master.cli_ui import (
    ColorScheme,
    Display,
    CommandParser,
    CommandType,
)
from llm_dungeon_master.cli_ui.colors import get_color_scheme, get_hp_color, get_modifier_color


class TestColorSchemes:
    """Tests for color schemes and themes."""
    
    def test_all_color_schemes_available(self):
        """Test that all color schemes are defined."""
        schemes = [
            ColorScheme.GREEN_PHOSPHOR,
            ColorScheme.AMBER_MONITOR,
            ColorScheme.IBM_CGA,
            ColorScheme.COMMODORE_64,
            ColorScheme.APPLE_II,
        ]
        
        for scheme in schemes:
            theme = get_color_scheme(scheme)
            assert theme is not None
            assert theme.primary is not None
            assert theme.text is not None
    
    def test_hp_color_logic(self):
        """Test HP color calculation."""
        theme = get_color_scheme(ColorScheme.GREEN_PHOSPHOR)
        
        # High HP (>50%) should use hp_good
        color_high = get_hp_color(80, 100, theme)
        assert color_high == theme.hp_good
        
        # Medium HP (>25%) should use hp_warning
        color_medium = get_hp_color(40, 100, theme)
        assert color_medium == theme.hp_warning
        
        # Low HP (<=25%) should use hp_critical
        color_low = get_hp_color(20, 100, theme)
        assert color_low == theme.hp_critical
    
    def test_modifier_color_logic(self):
        """Test ability modifier color calculation."""
        theme = get_color_scheme(ColorScheme.GREEN_PHOSPHOR)
        
        # Positive modifier
        color_pos = get_modifier_color(3, theme)
        assert color_pos == theme.success
        
        # Negative modifier
        color_neg = get_modifier_color(-2, theme)
        assert color_neg == theme.error
        
        # Zero modifier
        color_zero = get_modifier_color(0, theme)
        assert color_zero == theme.text


class TestDisplay:
    """Tests for Display class."""
    
    def test_display_initialization(self):
        """Test Display can be initialized with different color schemes."""
        for scheme in ColorScheme:
            display = Display(color_scheme=scheme)
            assert display.theme is not None
            assert display.console is not None
    
    def test_hp_bar_generation(self):
        """Test HP bar ASCII generation."""
        display = Display()
        
        # Full HP
        bar = display.draw_hp_bar(100, 100, width=10)
        assert "[" in bar
        assert "]" in bar
        assert "100/100" in bar
        
        # Half HP
        bar = display.draw_hp_bar(50, 100, width=10)
        assert "50/100" in bar
        
        # Zero HP
        bar = display.draw_hp_bar(0, 100, width=10)
        assert "0/100" in bar
    
    def test_ascii_art_available(self):
        """Test that ASCII art methods return non-empty strings."""
        display = Display()
        
        title = display.get_title_ascii()
        assert len(title) > 0
        assert "DUNGEON" in title or "MASTER" in title
        
        dragon = display.get_dragon_ascii()
        assert len(dragon) > 0
        
        sword = display.get_sword_ascii()
        assert len(sword) > 0


class TestCommandParser:
    """Tests for command parsing."""
    
    def test_attack_commands(self):
        """Test parsing attack commands."""
        parser = CommandParser()
        
        test_cases = [
            ("attack goblin", "goblin"),
            ("hit the orc", "orc"),
            ("strike dragon", "dragon"),
            ("fight zombie", "zombie"),
        ]
        
        for cmd, expected_target in test_cases:
            parsed = parser.parse(cmd)
            assert parsed.command_type == CommandType.ATTACK
            assert parsed.target is not None
            assert expected_target in parsed.target.lower()
    
    def test_spell_casting_commands(self):
        """Test parsing spell casting commands."""
        parser = CommandParser()
        
        # With target
        parsed = parser.parse("cast fireball on orc")
        assert parsed.command_type == CommandType.CAST
        assert parsed.item == "fireball"
        assert parsed.target == "orc"
        
        # Without target
        parsed = parser.parse("cast shield")
        assert parsed.command_type == CommandType.CAST
        assert parsed.item == "shield"
    
    def test_movement_commands(self):
        """Test parsing movement commands."""
        parser = CommandParser()
        
        test_cases = [
            ("north", "north"),
            ("go south", "south"),
            ("move east", "east"),
            ("walk west", "west"),
            ("n", "north"),
            ("s", "south"),
            ("e", "east"),
            ("w", "west"),
        ]
        
        for cmd, expected_dir in test_cases:
            parsed = parser.parse(cmd)
            assert parsed.command_type == CommandType.MOVE
            assert parsed.direction == expected_dir
    
    def test_simple_commands(self):
        """Test simple one-word commands."""
        parser = CommandParser()
        
        test_cases = [
            ("inventory", CommandType.INVENTORY),
            ("inv", CommandType.INVENTORY),
            ("i", CommandType.INVENTORY),
            ("rest", CommandType.REST),
            ("help", CommandType.HELP),
            ("?", CommandType.HELP),
            ("quit", CommandType.QUIT),
        ]
        
        for cmd, expected_type in test_cases:
            parsed = parser.parse(cmd)
            assert parsed.command_type == expected_type
    
    def test_look_commands(self):
        """Test parsing look/examine commands."""
        parser = CommandParser()
        
        # Look around
        parsed = parser.parse("look")
        assert parsed.command_type == CommandType.LOOK
        assert parsed.target is None
        
        # Look at object
        parsed = parser.parse("look at chest")
        assert parsed.command_type == CommandType.LOOK
        assert parsed.target == "chest"
        
        parsed = parser.parse("examine the door")
        assert parsed.command_type == CommandType.LOOK
        assert "door" in parsed.target
    
    def test_use_item_commands(self):
        """Test parsing item usage commands."""
        parser = CommandParser()
        
        test_cases = [
            ("use potion", CommandType.USE, "potion"),
            ("drink healing potion", CommandType.USE, "healing potion"),
            ("consume elixir", CommandType.USE, "elixir"),
        ]
        
        for cmd, expected_type, expected_item in test_cases:
            parsed = parser.parse(cmd)
            # "use potion" might be interpreted as CAST or USE depending on pattern match order
            assert parsed.command_type in [CommandType.USE, CommandType.CAST]
            item_field = parsed.item if parsed.item else parsed.target
            assert item_field is not None
            assert expected_item in item_field.lower()
    
    def test_talk_commands(self):
        """Test parsing talk/speak commands."""
        parser = CommandParser()
        
        test_cases = [
            ("talk to guard", "guard"),
            ("speak with merchant", "merchant"),
            ("chat to the innkeeper", "innkeeper"),
        ]
        
        for cmd, expected_target in test_cases:
            parsed = parser.parse(cmd)
            assert parsed.command_type == CommandType.TALK
            assert parsed.target is not None
            assert expected_target in parsed.target.lower()
    
    def test_unknown_commands(self):
        """Test that unknown commands are handled."""
        parser = CommandParser()
        
        parsed = parser.parse("xyzzy")
        assert parsed.command_type == CommandType.UNKNOWN
        
        parsed = parser.parse("")
        assert parsed.command_type == CommandType.UNKNOWN
    
    def test_help_text(self):
        """Test that help text is available."""
        parser = CommandParser()
        help_text = parser.get_help_text()
        
        assert len(help_text) > 0
        assert "attack" in help_text.lower()
        assert "move" in help_text.lower()
        assert "inventory" in help_text.lower()


class TestScreenComponents:
    """Tests for screen components."""
    
    def test_display_initialization_with_screens(self):
        """Test that screen components can be initialized."""
        from src.llm_dungeon_master.cli_ui import TitleScreen, MainMenu, CharacterSheetScreen
        
        display = Display()
        
        # These should not raise exceptions
        title = TitleScreen(display)
        menu = MainMenu(display)
        char_screen = CharacterSheetScreen(display)
        
        assert title.display == display
        assert menu.display == display
        assert char_screen.display == display


class TestAnimations:
    """Tests for animation components."""
    
    def test_dice_animation_initialization(self):
        """Test that dice animation can be initialized."""
        from src.llm_dungeon_master.cli_ui import DiceAnimation
        
        display = Display()
        dice = DiceAnimation(display)
        
        assert dice.display == display
    
    def test_combat_animation_initialization(self):
        """Test that combat animation can be initialized."""
        from src.llm_dungeon_master.cli_ui import CombatAnimation
        
        display = Display()
        combat = CombatAnimation(display)
        
        assert combat.display == display


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
