"""Tests for character API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from llm_dungeon_master.server import app, get_db
from llm_dungeon_master.models import Player, Character


@pytest.fixture
def db():
    """Create a test database."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def client(db):
    """Create a test client with database override."""
    def get_test_db():
        yield db
    
    app.dependency_overrides[get_db] = get_test_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def test_player(db):
    """Create a test player."""
    player = Player(name="Test Player")
    db.add(player)
    db.commit()
    db.refresh(player)
    return player


def test_list_character_classes(client):
    """Test listing available character classes."""
    response = client.get("/api/characters/classes")
    
    assert response.status_code == 200
    data = response.json()
    assert "classes" in data
    assert len(data["classes"]) == 10
    assert "Fighter" in data["classes"]
    assert "Wizard" in data["classes"]


def test_create_character_basic(client, test_player):
    """Test creating a basic character."""
    character_data = {
        "player_id": test_player.id,
        "name": "Test Character",
        "race": "Human",
        "char_class": "Fighter",
        "level": 1,
        "strength": 15,
        "dexterity": 14,
        "constitution": 13,
        "intelligence": 12,
        "wisdom": 10,
        "charisma": 8
    }
    
    response = client.post("/api/characters", json=character_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Character"
    assert data["char_class"] == "Fighter"
    assert data["level"] == 1
    assert data["strength"] == 15


def test_get_character(client, test_player, db):
    """Test getting a specific character."""
    character = Character(
        player_id=test_player.id,
        name="Get Test",
        race="Elf",
        char_class="Wizard",
        level=1,
        strength=8,
        dexterity=14,
        constitution=13,
        intelligence=15,
        wisdom=12,
        charisma=10,
        max_hp=8,
        current_hp=8,
        armor_class=12
    )
    db.add(character)
    db.commit()
    db.refresh(character)
    
    response = client.get(f"/api/characters/{character.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Get Test"
    assert data["char_class"] == "Wizard"


def test_get_character_not_found(client):
    """Test getting a non-existent character."""
    response = client.get("/api/characters/999")
    
    assert response.status_code == 404


def test_list_characters(client, test_player, db):
    """Test listing all characters."""
    # Create multiple characters
    for i in range(3):
        character = Character(
            player_id=test_player.id,
            name=f"Character {i}",
            race="Human",
            char_class="Fighter",
            level=1,
            strength=10,
            dexterity=10,
            constitution=10,
            intelligence=10,
            wisdom=10,
            charisma=10,
            max_hp=10,
            current_hp=10,
            armor_class=10
        )
        db.add(character)
    db.commit()
    
    response = client.get("/api/characters")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3


def test_list_characters_by_player(client, test_player, db):
    """Test listing characters filtered by player."""
    # Create a second player
    other_player = Player(name="Other Player")
    db.add(other_player)
    db.commit()
    db.refresh(other_player)
    
    # Create characters for both players
    for player in [test_player, other_player]:
        character = Character(
            player_id=player.id,
            name=f"Character for {player.name}",
            race="Human",
            char_class="Fighter",
            level=1,
            strength=10,
            dexterity=10,
            constitution=10,
            intelligence=10,
            wisdom=10,
            charisma=10,
            max_hp=10,
            current_hp=10,
            armor_class=10
        )
        db.add(character)
    db.commit()
    
    response = client.get(f"/api/characters?player_id={test_player.id}")
    
    assert response.status_code == 200
    data = response.json()
    # Should only get characters for test_player
    for char in data:
        assert char["player_id"] == test_player.id


def test_update_character(client, test_player, db):
    """Test updating a character."""
    character = Character(
        player_id=test_player.id,
        name="Update Test",
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
        armor_class=16
    )
    db.add(character)
    db.commit()
    db.refresh(character)
    
    update_data = {
        "player_id": test_player.id,
        "name": "Update Test",
        "race": "Human",
        "char_class": "Fighter",
        "level": 2,
        "strength": 15,
        "dexterity": 14,
        "constitution": 13,
        "intelligence": 12,
        "wisdom": 10,
        "charisma": 8
    }
    
    response = client.put(f"/api/characters/{character.id}", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["level"] == 2


def test_delete_character(client, test_player, db):
    """Test deleting a character."""
    character = Character(
        player_id=test_player.id,
        name="Delete Test",
        race="Human",
        char_class="Fighter",
        level=1,
        strength=10,
        dexterity=10,
        constitution=10,
        intelligence=10,
        wisdom=10,
        charisma=10,
        max_hp=10,
        current_hp=10,
        armor_class=10
    )
    db.add(character)
    db.commit()
    db.refresh(character)
    
    response = client.delete(f"/api/characters/{character.id}")
    
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]
    
    # Verify character is deleted
    response = client.get(f"/api/characters/{character.id}")
    assert response.status_code == 404


def test_create_character_from_template(client, test_player):
    """Test creating a character from a class template."""
    params = {
        "player_id": test_player.id,
        "name": "Template Fighter",
        "race": "Human",
        "char_class": "Fighter",
        "strength": 15,
        "dexterity": 13,
        "constitution": 14,
        "intelligence": 8,
        "wisdom": 10,
        "charisma": 12,
        "background": "Soldier"
    }
    
    response = client.post("/api/characters/from-template", params=params)
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Template Fighter"
    assert data["char_class"] == "Fighter"
    assert data["background"] == "Soldier"
    assert data["proficiency_bonus"] == 2
    assert data["max_hp"] > 0


def test_create_character_from_template_invalid_point_buy(client, test_player):
    """Test creating a character with invalid point buy."""
    params = {
        "player_id": test_player.id,
        "name": "Invalid Character",
        "race": "Human",
        "char_class": "Fighter",
        "strength": 20,  # Invalid
        "dexterity": 20,
        "constitution": 20,
        "intelligence": 20,
        "wisdom": 20,
        "charisma": 20
    }
    
    response = client.post("/api/characters/from-template", params=params)
    
    assert response.status_code == 400
    assert "Invalid ability scores" in response.json()["detail"] or "out of range" in response.json()["detail"]


def test_get_character_summary(client, test_player, db):
    """Test getting a character summary."""
    from llm_dungeon_master.character_builder import CharacterBuilder
    
    builder = CharacterBuilder(db)
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
        ability_scores=ability_scores
    )
    
    response = client.get(f"/api/characters/{character.id}/summary")
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Summary Test"
    assert data["class"] == "Fighter"
    assert "ability_scores" in data
    assert "proficiencies" in data
    assert "features" in data
    assert data["ability_scores"]["strength"]["score"] == 15
    assert data["ability_scores"]["strength"]["modifier"] == 2


def test_validate_character_valid(client, test_player, db):
    """Test validating a valid character."""
    character = Character(
        player_id=test_player.id,
        name="Valid Character",
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
        proficiency_bonus=2
    )
    db.add(character)
    db.commit()
    db.refresh(character)
    
    response = client.post(f"/api/characters/{character.id}/validate")
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] == True
    assert len(data["errors"]) == 0


def test_validate_character_invalid(client, test_player, db):
    """Test validating an invalid character."""
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
    db.refresh(character)
    
    response = client.post(f"/api/characters/{character.id}/validate")
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] == False
    assert len(data["errors"]) > 0


def test_level_up_character(client, test_player, db):
    """Test leveling up a character."""
    character = Character(
        player_id=test_player.id,
        name="Level Up Test",
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
    
    response = client.post(f"/api/characters/{character.id}/level-up")
    
    assert response.status_code == 200
    data = response.json()
    assert data["level"] == 2
    assert data["max_hp"] > 11


def test_level_up_character_insufficient_xp(client, test_player, db):
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
        experience_points=100  # Not enough
    )
    db.add(character)
    db.commit()
    db.refresh(character)
    
    response = client.post(f"/api/characters/{character.id}/level-up")
    
    assert response.status_code == 400
    assert "Not enough XP" in response.json()["detail"]
