"""Tests for prompt templates."""

from llm_dungeon_master.prompts import (
    get_dm_system_message,
    get_start_session_message,
    format_roll_prompt,
    format_combat_start,
    format_combat_round,
    SYSTEM_PROMPT,
    START_SESSION_PROMPT
)


def test_get_dm_system_message():
    """Test getting the DM system message."""
    message = get_dm_system_message()
    
    assert isinstance(message, dict)
    assert message["role"] == "system"
    assert message["content"] == SYSTEM_PROMPT
    assert "Dungeon Master" in message["content"]
    assert "D&D" in message["content"]


def test_get_start_session_message():
    """Test getting the start session message."""
    message = get_start_session_message()
    
    assert isinstance(message, dict)
    assert message["role"] == "assistant"
    assert message["content"] == START_SESSION_PROMPT
    assert len(message["content"]) > 0


def test_format_roll_prompt():
    """Test formatting a roll prompt."""
    prompt = format_roll_prompt(
        roll_type="attack roll",
        result=18,
        dice="1d20",
        modifier=5
    )
    
    assert isinstance(prompt, str)
    assert "attack roll" in prompt
    assert "18" in prompt
    assert "1d20" in prompt
    assert "5" in prompt


def test_format_combat_start():
    """Test formatting combat start prompt."""
    combatants = ["Aragorn", "Legolas", "Goblin 1", "Goblin 2"]
    prompt = format_combat_start(combatants)
    
    assert isinstance(prompt, str)
    assert "Combat" in prompt or "combat" in prompt
    assert all(name in prompt for name in combatants)
    assert "initiative" in prompt.lower()


def test_format_combat_round():
    """Test formatting combat round prompt."""
    prompt = format_combat_round(
        round_num=3,
        current="Aragorn",
        hp_status="Aragorn: 25/30, Goblin: 5/10"
    )
    
    assert isinstance(prompt, str)
    assert "3" in prompt
    assert "Aragorn" in prompt
    assert "25/30" in prompt


def test_system_prompt_content():
    """Test that system prompt has required content."""
    assert "Dungeon Master" in SYSTEM_PROMPT
    assert "D&D" in SYSTEM_PROMPT
    assert "5e" in SYSTEM_PROMPT or "5th Edition" in SYSTEM_PROMPT


def test_start_session_prompt_content():
    """Test that start session prompt is engaging."""
    assert len(START_SESSION_PROMPT) > 50
    assert "?" in START_SESSION_PROMPT  # Should ask what players want to do
