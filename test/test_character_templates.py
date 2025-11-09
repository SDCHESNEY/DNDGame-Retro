"""Tests for character class templates."""

import json
import pytest
from pathlib import Path


@pytest.fixture
def templates_dir():
    """Get the templates directory."""
    return Path(__file__).parent.parent / "src" / "llm_dungeon_master" / "templates"


def test_all_templates_exist(templates_dir):
    """Test that all 10 class templates exist."""
    expected_classes = [
        "fighter", "wizard", "rogue", "cleric", "ranger",
        "paladin", "barbarian", "bard", "sorcerer", "warlock"
    ]
    
    for class_name in expected_classes:
        template_path = templates_dir / f"{class_name}.json"
        assert template_path.exists(), f"Template {class_name}.json not found"


def test_fighter_template(templates_dir):
    """Test Fighter template structure and content."""
    with open(templates_dir / "fighter.json") as f:
        template = json.load(f)
    
    assert template["class"] == "Fighter"
    assert template["hit_die"] == "d10"
    assert "Strength" in template["primary_abilities"]
    assert "Strength" in template["saving_throw_proficiencies"]
    assert "Constitution" in template["saving_throw_proficiencies"]
    assert len(template["skill_options"]) > 0
    assert template["skill_choices"] == 2
    assert len(template["level_1_features"]) >= 2
    assert "recommended_stats" in template


def test_wizard_template(templates_dir):
    """Test Wizard template structure and content."""
    with open(templates_dir / "wizard.json") as f:
        template = json.load(f)
    
    assert template["class"] == "Wizard"
    assert template["hit_die"] == "d6"
    assert "Intelligence" in template["primary_abilities"]
    assert "Intelligence" in template["saving_throw_proficiencies"]
    assert "Wisdom" in template["saving_throw_proficiencies"]
    assert "spellcasting" in template
    assert template["spellcasting"]["cantrips_known"] == 3
    assert "1" in template["spellcasting"]["spell_slots"]


def test_rogue_template(templates_dir):
    """Test Rogue template structure and content."""
    with open(templates_dir / "rogue.json") as f:
        template = json.load(f)
    
    assert template["class"] == "Rogue"
    assert template["hit_die"] == "d8"
    assert "Dexterity" in template["primary_abilities"]
    assert template["skill_choices"] == 4  # Rogues get 4 skills
    assert "Thieves' tools" in template["tool_proficiencies"]
    
    # Check for key Rogue features
    feature_names = [f["name"] for f in template["level_1_features"]]
    assert "Sneak Attack" in feature_names
    assert "Expertise" in feature_names


def test_cleric_template(templates_dir):
    """Test Cleric template structure and content."""
    with open(templates_dir / "cleric.json") as f:
        template = json.load(f)
    
    assert template["class"] == "Cleric"
    assert template["hit_die"] == "d8"
    assert "Wisdom" in template["primary_abilities"]
    assert "Wisdom" in template["saving_throw_proficiencies"]
    assert "Charisma" in template["saving_throw_proficiencies"]
    assert "spellcasting" in template
    assert template["spellcasting"]["cantrips_known"] == 3


def test_ranger_template(templates_dir):
    """Test Ranger template structure and content."""
    with open(templates_dir / "ranger.json") as f:
        template = json.load(f)
    
    assert template["class"] == "Ranger"
    assert template["hit_die"] == "d10"
    assert "Dexterity" in template["primary_abilities"] or "Wisdom" in template["primary_abilities"]
    assert template["skill_choices"] == 3
    
    # Check for key Ranger features
    feature_names = [f["name"] for f in template["level_1_features"]]
    assert "Favored Enemy" in feature_names
    assert "Natural Explorer" in feature_names


def test_paladin_template(templates_dir):
    """Test Paladin template structure and content."""
    with open(templates_dir / "paladin.json") as f:
        template = json.load(f)
    
    assert template["class"] == "Paladin"
    assert template["hit_die"] == "d10"
    assert "Strength" in template["primary_abilities"] or "Charisma" in template["primary_abilities"]
    assert "Wisdom" in template["saving_throw_proficiencies"]
    assert "Charisma" in template["saving_throw_proficiencies"]
    
    # Check for key Paladin features
    feature_names = [f["name"] for f in template["level_1_features"]]
    assert "Divine Sense" in feature_names
    assert "Lay on Hands" in feature_names


def test_barbarian_template(templates_dir):
    """Test Barbarian template structure and content."""
    with open(templates_dir / "barbarian.json") as f:
        template = json.load(f)
    
    assert template["class"] == "Barbarian"
    assert template["hit_die"] == "d12"  # Biggest hit die
    assert "Strength" in template["primary_abilities"]
    assert "Strength" in template["saving_throw_proficiencies"]
    assert "Constitution" in template["saving_throw_proficiencies"]
    
    # Check for key Barbarian features
    feature_names = [f["name"] for f in template["level_1_features"]]
    assert "Rage" in feature_names
    assert "Unarmored Defense" in feature_names


def test_bard_template(templates_dir):
    """Test Bard template structure and content."""
    with open(templates_dir / "bard.json") as f:
        template = json.load(f)
    
    assert template["class"] == "Bard"
    assert template["hit_die"] == "d8"
    assert "Charisma" in template["primary_abilities"]
    assert template["skill_choices"] == 3
    assert "spellcasting" in template
    
    # Check for key Bard features
    feature_names = [f["name"] for f in template["level_1_features"]]
    assert "Bardic Inspiration" in feature_names


def test_sorcerer_template(templates_dir):
    """Test Sorcerer template structure and content."""
    with open(templates_dir / "sorcerer.json") as f:
        template = json.load(f)
    
    assert template["class"] == "Sorcerer"
    assert template["hit_die"] == "d6"
    assert "Charisma" in template["primary_abilities"]
    assert "Constitution" in template["saving_throw_proficiencies"]
    assert "Charisma" in template["saving_throw_proficiencies"]
    assert "spellcasting" in template
    assert template["spellcasting"]["cantrips_known"] == 4  # Most cantrips at level 1
    
    # Check for Sorcerous Origin feature
    feature_names = [f["name"] for f in template["level_1_features"]]
    assert "Sorcerous Origin" in feature_names


def test_warlock_template(templates_dir):
    """Test Warlock template structure and content."""
    with open(templates_dir / "warlock.json") as f:
        template = json.load(f)
    
    assert template["class"] == "Warlock"
    assert template["hit_die"] == "d8"
    assert "Charisma" in template["primary_abilities"]
    assert "Wisdom" in template["saving_throw_proficiencies"]
    assert "Charisma" in template["saving_throw_proficiencies"]
    assert "spellcasting" in template
    assert template["spellcasting"].get("pact_magic") == True
    
    # Check for key Warlock features
    feature_names = [f["name"] for f in template["level_1_features"]]
    assert "Otherworldly Patron" in feature_names


def test_all_templates_have_required_fields(templates_dir):
    """Test that all templates have required fields."""
    required_fields = [
        "class", "description", "hit_die", "primary_abilities",
        "saving_throw_proficiencies", "armor_proficiencies",
        "weapon_proficiencies", "skill_choices", "skill_options",
        "starting_equipment", "level_1_features", "ability_score_priority",
        "recommended_stats"
    ]
    
    class_files = list(templates_dir.glob("*.json"))
    assert len(class_files) == 10, "Should have 10 class templates"
    
    for template_path in class_files:
        with open(template_path) as f:
            template = json.load(f)
        
        for field in required_fields:
            assert field in template, f"{template_path.name} missing field: {field}"


def test_recommended_stats_valid(templates_dir):
    """Test that recommended stats use point buy correctly."""
    point_buy_costs = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}
    
    for template_path in templates_dir.glob("*.json"):
        with open(template_path) as f:
            template = json.load(f)
        
        stats = template["recommended_stats"]
        total_cost = sum(point_buy_costs[score] for score in stats.values())
        
        assert total_cost <= 27, f"{template['class']} recommended stats exceed point buy (cost: {total_cost})"
        
        for ability, score in stats.items():
            assert 8 <= score <= 15, f"{template['class']} has invalid {ability} score: {score}"


def test_hit_die_valid(templates_dir):
    """Test that all hit dice are valid D&D values."""
    valid_hit_dice = ["d6", "d8", "d10", "d12"]
    
    for template_path in templates_dir.glob("*.json"):
        with open(template_path) as f:
            template = json.load(f)
        
        assert template["hit_die"] in valid_hit_dice, \
            f"{template['class']} has invalid hit die: {template['hit_die']}"


def test_saving_throws_valid(templates_dir):
    """Test that all saving throw proficiencies are valid abilities."""
    valid_abilities = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]
    
    for template_path in templates_dir.glob("*.json"):
        with open(template_path) as f:
            template = json.load(f)
        
        saves = template["saving_throw_proficiencies"]
        assert len(saves) == 2, f"{template['class']} should have exactly 2 saving throw proficiencies"
        
        for save in saves:
            assert save in valid_abilities, f"{template['class']} has invalid saving throw: {save}"


def test_spellcaster_templates_have_spell_info(templates_dir):
    """Test that spellcasting classes have spell slot information."""
    spellcasting_classes = ["Wizard", "Cleric", "Bard", "Sorcerer", "Warlock"]
    
    for class_name in spellcasting_classes:
        with open(templates_dir / f"{class_name.lower()}.json") as f:
            template = json.load(f)
        
        assert "spellcasting" in template, f"{class_name} should have spellcasting info"
        assert "cantrips_known" in template["spellcasting"]
        assert "spell_slots" in template["spellcasting"] or "spells_known" in template["spellcasting"]
