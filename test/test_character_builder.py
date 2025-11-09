"""Tests for character builder functionality."""

import pytest
from sqlmodel import Session, create_engine, SQLModel
from llm_dungeon_master.models import Player, Character
from llm_dungeon_master.character_builder import CharacterBuilder, ValidationError


@pytest.fixture
def db():
    """Create a test database."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def test_player(db):
    """Create a test player."""
    player = Player(name="Test Player")
    db.add(player)
    db.commit()
    db.refresh(player)
    return player


@pytest.fixture
def builder(db):
    """Create a character builder."""
    return CharacterBuilder(db)


def test_list_available_classes(builder):
    """Test listing available character classes."""
    classes = builder.list_available_classes()
    
    assert len(classes) == 10
    assert "Fighter" in classes
    assert "Wizard" in classes
    assert "Rogue" in classes
    assert "Cleric" in classes
    assert "Ranger" in classes
    assert "Paladin" in classes
    assert "Barbarian" in classes
    assert "Bard" in classes
    assert "Sorcerer" in classes
    assert "Warlock" in classes


def test_load_template(builder):
    """Test loading a character class template."""
    template = builder.load_template("Fighter")
    
    assert template["class"] == "Fighter"
    assert template["hit_die"] == "d10"
    assert "Strength" in template["saving_throw_proficiencies"]
    assert len(template["level_1_features"]) > 0


def test_load_invalid_template(builder):
    """Test loading a non-existent template."""
    with pytest.raises(ValueError, match="Template for class 'InvalidClass' not found"):
        builder.load_template("InvalidClass")


def test_calculate_point_buy_cost(builder):
    """Test calculating point buy cost."""
    scores = {
        "strength": 15,
        "dexterity": 14,
        "constitution": 13,
        "intelligence": 12,
        "wisdom": 10,
        "charisma": 8
    }
    
    cost = builder.calculate_point_buy_cost(scores)
    expected = 9 + 7 + 5 + 4 + 2 + 0  # 27
    assert cost == expected


def test_validate_point_buy_valid(builder):
    """Test validating valid point buy scores."""
    scores = {
        "strength": 15,
        "dexterity": 14,
        "constitution": 13,
        "intelligence": 12,
        "wisdom": 10,
        "charisma": 8
    }
    
    is_valid, message = builder.validate_point_buy(scores)
    assert is_valid
    assert "27/27" in message


def test_validate_point_buy_too_expensive(builder):
    """Test validating point buy scores that are too expensive."""
    scores = {
        "strength": 15,
        "dexterity": 15,
        "constitution": 15,
        "intelligence": 15,
        "wisdom": 15,
        "charisma": 15
    }
    
    is_valid, message = builder.validate_point_buy(scores)
    assert not is_valid
    assert "exceeds maximum" in message


def test_validate_point_buy_out_of_range(builder):
    """Test validating point buy scores outside valid range."""
    scores = {
        "strength": 20,  # Too high
        "dexterity": 14,
        "constitution": 13,
        "intelligence": 12,
        "wisdom": 10,
        "charisma": 8
    }
    
    is_valid, message = builder.validate_point_buy(scores)
    assert not is_valid
    assert "out of range" in message


def test_calculate_modifier(builder):
    """Test calculating ability modifiers."""
    assert builder.calculate_modifier(10) == 0
    assert builder.calculate_modifier(8) == -1
    assert builder.calculate_modifier(15) == 2
    assert builder.calculate_modifier(20) == 5
    assert builder.calculate_modifier(3) == -4


def test_calculate_hp_level_1(builder):
    """Test calculating HP at level 1."""
    # Fighter with d10, Con 14 (+2 mod)
    hp = builder.calculate_hp("Fighter", 1, 2)
    assert hp == 12  # 10 + 2


def test_calculate_hp_higher_level(builder):
    """Test calculating HP at higher levels."""
    # Fighter with d10, Con 14 (+2 mod), level 5
    hp = builder.calculate_hp("Fighter", 5, 2)
    # Level 1: 10 + 2 = 12
    # Levels 2-5: (6 + 2) * 4 = 32
    # Total: 44
    assert hp == 44


def test_calculate_armor_class_unarmored(builder):
    """Test calculating AC without armor."""
    ac = builder.calculate_armor_class(2)  # Dex +2
    assert ac == 12  # 10 + 2


def test_calculate_armor_class_leather(builder):
    """Test calculating AC with leather armor."""
    ac = builder.calculate_armor_class(3, "leather")
    assert ac == 14  # 11 + 3


def test_calculate_armor_class_medium_armor(builder):
    """Test calculating AC with medium armor (caps Dex at +2)."""
    ac = builder.calculate_armor_class(4, "scale mail")
    assert ac == 16  # 14 + min(4, 2)


def test_calculate_armor_class_heavy_armor(builder):
    """Test calculating AC with heavy armor (no Dex bonus)."""
    ac = builder.calculate_armor_class(3, "chain mail")
    assert ac == 16  # Fixed AC


def test_create_fighter_from_template(builder, test_player, db):
    """Test creating a Fighter character from template."""
    ability_scores = {
        "strength": 15,
        "dexterity": 13,
        "constitution": 14,
        "intelligence": 8,
        "wisdom": 10,
        "charisma": 12
    }
    
    character = builder.create_from_template(
        player_id=test_player.id,
        name="Test Fighter",
        race="Human",
        char_class="Fighter",
        ability_scores=ability_scores,
        background="Soldier"
    )
    
    assert character.name == "Test Fighter"
    assert character.race == "Human"
    assert character.char_class == "Fighter"
    assert character.level == 1
    assert character.strength == 15
    assert character.proficiency_bonus == 2
    assert character.max_hp == 12  # d10 + Con mod (+2)
    assert character.current_hp == 12
    
    # Check that features were added
    assert len(character.features) > 0
    feature_names = [f.feature_name for f in character.features]
    assert "Fighting Style" in feature_names or "Second Wind" in feature_names
    
    # Check that proficiencies were added
    assert len(character.proficiencies) > 0


def test_create_wizard_from_template(builder, test_player, db):
    """Test creating a Wizard character from template."""
    ability_scores = {
        "strength": 8,
        "dexterity": 13,
        "constitution": 14,
        "intelligence": 15,
        "wisdom": 12,
        "charisma": 10
    }
    
    character = builder.create_from_template(
        player_id=test_player.id,
        name="Test Wizard",
        race="Elf",
        char_class="Wizard",
        ability_scores=ability_scores
    )
    
    assert character.name == "Test Wizard"
    assert character.char_class == "Wizard"
    assert character.max_hp == 8  # d6 + Con mod (+2)
    
    # Wizard should have spell slots
    assert character.spell_slots_1 == 2
    assert character.current_spell_slots_1 == 2


def test_create_character_invalid_point_buy(builder, test_player):
    """Test creating a character with invalid point buy."""
    ability_scores = {
        "strength": 20,  # Too high
        "dexterity": 20,
        "constitution": 20,
        "intelligence": 20,
        "wisdom": 20,
        "charisma": 20
    }
    
    with pytest.raises(ValidationError, match="Invalid ability scores"):
        builder.create_from_template(
            player_id=test_player.id,
            name="Invalid Character",
            race="Human",
            char_class="Fighter",
            ability_scores=ability_scores
        )


def test_validate_character_valid(builder, test_player, db):
    """Test validating a valid character."""
    character = Character(
        player_id=test_player.id,
        name="Valid Character",
        race="Human",
        char_class="Fighter",
        level=5,
        strength=15,
        dexterity=14,
        constitution=13,
        intelligence=12,
        wisdom=10,
        charisma=8,
        max_hp=44,
        current_hp=44,
        armor_class=16,
        proficiency_bonus=3  # Correct for level 5
    )
    db.add(character)
    db.commit()
    
    is_valid, errors = builder.validate_character(character)
    assert is_valid
    assert len(errors) == 0


def test_validate_character_invalid_ability_score(builder, test_player, db):
    """Test validating a character with invalid ability score."""
    character = Character(
        player_id=test_player.id,
        name="Invalid Character",
        race="Human",
        char_class="Fighter",
        level=1,
        strength=25,  # Too high
        dexterity=14,
        constitution=13,
        intelligence=12,
        wisdom=10,
        charisma=8,
        max_hp=10,
        current_hp=10,
        armor_class=10,
        proficiency_bonus=2
    )
    db.add(character)
    db.commit()
    
    is_valid, errors = builder.validate_character(character)
    assert not is_valid
    assert any("Strength" in error for error in errors)


def test_validate_character_invalid_proficiency(builder, test_player, db):
    """Test validating a character with incorrect proficiency bonus."""
    character = Character(
        player_id=test_player.id,
        name="Invalid Character",
        race="Human",
        char_class="Fighter",
        level=5,
        strength=15,
        dexterity=14,
        constitution=13,
        intelligence=12,
        wisdom=10,
        charisma=8,
        max_hp=44,
        current_hp=44,
        armor_class=16,
        proficiency_bonus=2  # Should be 3 for level 5
    )
    db.add(character)
    db.commit()
    
    is_valid, errors = builder.validate_character(character)
    assert not is_valid
    assert any("Proficiency bonus" in error for error in errors)


def test_apply_level_up(builder, test_player, db):
    """Test leveling up a character."""
    character = Character(
        player_id=test_player.id,
        name="Level Up Character",
        race="Human",
        char_class="Fighter",
        level=1,
        strength=15,
        dexterity=14,
        constitution=13,
        intelligence=12,
        wisdom=10,
        charisma=8,
        max_hp=11,
        current_hp=11,
        armor_class=16,
        proficiency_bonus=2,
        experience_points=300  # Enough for level 2
    )
    db.add(character)
    db.commit()
    db.refresh(character)
    
    original_hp = character.max_hp
    leveled_up = builder.apply_level_up(character)
    
    assert leveled_up.level == 2
    assert leveled_up.proficiency_bonus == 2  # Still 2 at level 2
    assert leveled_up.max_hp > original_hp


def test_apply_level_up_insufficient_xp(builder, test_player, db):
    """Test leveling up without enough XP."""
    character = Character(
        player_id=test_player.id,
        name="Low XP Character",
        race="Human",
        char_class="Fighter",
        level=1,
        strength=15,
        dexterity=14,
        constitution=13,
        intelligence=12,
        wisdom=10,
        charisma=8,
        max_hp=11,
        current_hp=11,
        armor_class=16,
        proficiency_bonus=2,
        experience_points=100  # Not enough for level 2 (need 300)
    )
    db.add(character)
    db.commit()
    db.refresh(character)
    
    with pytest.raises(ValidationError, match="Not enough XP"):
        builder.apply_level_up(character)


def test_apply_level_up_max_level(builder, test_player, db):
    """Test leveling up at max level."""
    character = Character(
        player_id=test_player.id,
        name="Max Level Character",
        race="Human",
        char_class="Fighter",
        level=20,
        strength=15,
        dexterity=14,
        constitution=13,
        intelligence=12,
        wisdom=10,
        charisma=8,
        max_hp=100,
        current_hp=100,
        armor_class=16,
        proficiency_bonus=6,
        experience_points=999999
    )
    db.add(character)
    db.commit()
    db.refresh(character)
    
    with pytest.raises(ValidationError, match="already at maximum level"):
        builder.apply_level_up(character)


def test_get_character_summary(builder, test_player, db):
    """Test getting a character summary."""
    ability_scores = {
        "strength": 15,
        "dexterity": 14,
        "constitution": 13,
        "intelligence": 12,
        "wisdom": 10,
        "charisma": 8
    }
    
    character = builder.create_from_template(
        player_id=test_player.id,
        name="Summary Test",
        race="Human",
        char_class="Fighter",
        ability_scores=ability_scores,
        background="Soldier"
    )
    
    summary = builder.get_character_summary(character)
    
    assert summary["name"] == "Summary Test"
    assert summary["class"] == "Fighter"
    assert summary["level"] == 1
    assert summary["background"] == "Soldier"
    assert summary["ability_scores"]["strength"]["score"] == 15
    assert summary["ability_scores"]["strength"]["modifier"] == 2
    assert "proficiencies" in summary
    assert "features" in summary
