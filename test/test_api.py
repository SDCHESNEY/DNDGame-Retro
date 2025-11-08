"""Tests for FastAPI server endpoints."""

import pytest
from fastapi.testclient import TestClient

from llm_dungeon_master.server import app


client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert data["version"] == "0.1.0"


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_create_session():
    """Test creating a session."""
    response = client.post(
        "/api/sessions",
        json={"name": "Test Adventure", "dm_name": "Test DM"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Adventure"
    assert data["dm_name"] == "Test DM"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data


def test_list_sessions():
    """Test listing sessions."""
    # Create a session first
    client.post(
        "/api/sessions",
        json={"name": "Session 1", "dm_name": "DM 1"}
    )
    
    response = client.get("/api/sessions")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_session():
    """Test getting a specific session."""
    # Create a session first
    create_response = client.post(
        "/api/sessions",
        json={"name": "Specific Session", "dm_name": "Specific DM"}
    )
    session_id = create_response.json()["id"]
    
    response = client.get(f"/api/sessions/{session_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == session_id
    assert data["name"] == "Specific Session"


def test_get_nonexistent_session():
    """Test getting a session that doesn't exist."""
    response = client.get("/api/sessions/99999")
    
    assert response.status_code == 404


def test_create_player():
    """Test creating a player."""
    response = client.post(
        "/api/players",
        json={"name": "Test Player"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Player"
    assert "id" in data
    assert "created_at" in data


def test_list_players():
    """Test listing players."""
    # Create a player first
    client.post("/api/players", json={"name": "Player 1"})
    
    response = client.get("/api/players")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_create_character():
    """Test creating a character."""
    # Create a player first
    player_response = client.post("/api/players", json={"name": "Test Player"})
    player_id = player_response.json()["id"]
    
    response = client.post(
        "/api/characters",
        json={
            "player_id": player_id,
            "name": "Test Character",
            "race": "Elf",
            "char_class": "Ranger",
            "level": 1,
            "strength": 12,
            "dexterity": 16,
            "constitution": 14,
            "intelligence": 10,
            "wisdom": 14,
            "charisma": 10
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Character"
    assert data["race"] == "Elf"
    assert data["char_class"] == "Ranger"
    assert data["level"] == 1
    assert data["dexterity"] == 16
    assert "id" in data


def test_list_characters():
    """Test listing characters."""
    # Create a player and character first
    player_response = client.post("/api/players", json={"name": "Test Player"})
    player_id = player_response.json()["id"]
    
    client.post(
        "/api/characters",
        json={
            "player_id": player_id,
            "name": "Character 1",
            "race": "Human",
            "char_class": "Fighter"
        }
    )
    
    response = client.get("/api/characters")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_list_characters_by_player():
    """Test listing characters filtered by player."""
    # Create two players
    player1_response = client.post("/api/players", json={"name": "Player 1"})
    player1_id = player1_response.json()["id"]
    
    player2_response = client.post("/api/players", json={"name": "Player 2"})
    player2_id = player2_response.json()["id"]
    
    # Create characters for player 1
    client.post(
        "/api/characters",
        json={
            "player_id": player1_id,
            "name": "Char 1",
            "race": "Human",
            "char_class": "Fighter"
        }
    )
    
    # Create character for player 2
    client.post(
        "/api/characters",
        json={
            "player_id": player2_id,
            "name": "Char 2",
            "race": "Elf",
            "char_class": "Wizard"
        }
    )
    
    # Get characters for player 1 only
    response = client.get(f"/api/characters?player_id={player1_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert all(char["player_id"] == player1_id for char in data)


def test_get_messages():
    """Test getting messages for a session."""
    # Create a session first
    session_response = client.post(
        "/api/sessions",
        json={"name": "Test Session", "dm_name": "Test DM"}
    )
    session_id = session_response.json()["id"]
    
    response = client.get(f"/api/sessions/{session_id}/messages")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_create_message():
    """Test creating a message."""
    # Create a session first
    session_response = client.post(
        "/api/sessions",
        json={"name": "Test Session", "dm_name": "Test DM"}
    )
    session_id = session_response.json()["id"]
    
    response = client.post(
        f"/api/sessions/{session_id}/messages",
        json={
            "sender_name": "Test Player",
            "content": "I want to explore the dungeon",
            "message_type": "player"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["sender_name"] == "Test Player"
    assert data["content"] == "I want to explore the dungeon"
    assert data["message_type"] == "player"
    assert data["session_id"] == session_id


def test_create_multiple_message_types():
    """Test creating different types of messages."""
    # Create a session
    session_response = client.post(
        "/api/sessions",
        json={"name": "Test Session", "dm_name": "Test DM"}
    )
    session_id = session_response.json()["id"]
    
    # Create different message types
    message_types = ["player", "dm", "system"]
    
    for msg_type in message_types:
        response = client.post(
            f"/api/sessions/{session_id}/messages",
            json={
                "sender_name": f"Sender-{msg_type}",
                "content": f"Test {msg_type} message",
                "message_type": msg_type
            }
        )
        assert response.status_code == 200
    
    # Get all messages
    response = client.get(f"/api/sessions/{session_id}/messages")
    messages = response.json()
    
    assert len(messages) >= 3
    assert all(any(msg["message_type"] == mt for msg in messages) for mt in message_types)
