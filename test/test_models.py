"""Tests for database models."""

import pytest
from datetime import datetime
from sqlmodel import Session, select

from llm_dungeon_master.models import Player, Session as GameSession, Character, Message, SessionPlayer


def test_create_player(session: Session):
    """Test creating a player."""
    player = Player(name="Aragorn")
    session.add(player)
    session.commit()
    session.refresh(player)
    
    assert player.id is not None
    assert player.name == "Aragorn"
    assert isinstance(player.created_at, datetime)


def test_create_game_session(session: Session):
    """Test creating a game session."""
    game_session = GameSession(name="Test Adventure", dm_name="Dungeon Master")
    session.add(game_session)
    session.commit()
    session.refresh(game_session)
    
    assert game_session.id is not None
    assert game_session.name == "Test Adventure"
    assert game_session.dm_name == "Dungeon Master"
    assert game_session.is_active is True
    assert isinstance(game_session.created_at, datetime)


def test_create_character(session: Session, sample_player: Player):
    """Test creating a character."""
    character = Character(
        player_id=sample_player.id,
        name="Gandalf",
        race="Human",
        char_class="Wizard",
        level=5,
        strength=10,
        dexterity=14,
        constitution=12,
        intelligence=18,
        wisdom=16,
        charisma=14,
        max_hp=30,
        current_hp=25,
        armor_class=13
    )
    session.add(character)
    session.commit()
    session.refresh(character)
    
    assert character.id is not None
    assert character.name == "Gandalf"
    assert character.player_id == sample_player.id
    assert character.char_class == "Wizard"
    assert character.level == 5
    assert character.intelligence == 18
    assert character.max_hp == 30
    assert character.current_hp == 25


def test_character_relationship(session: Session, sample_player: Player):
    """Test character-player relationship."""
    character = Character(
        player_id=sample_player.id,
        name="Legolas",
        race="Elf",
        char_class="Ranger",
        level=1,
        max_hp=10,
        current_hp=10,
        armor_class=14
    )
    session.add(character)
    session.commit()
    
    # Query player and check characters
    statement = select(Player).where(Player.id == sample_player.id)
    player = session.exec(statement).first()
    
    assert player is not None
    assert len(player.characters) > 0


def test_create_message(session: Session, sample_session: GameSession):
    """Test creating a message."""
    message = Message(
        session_id=sample_session.id,
        sender_name="Player 1",
        content="I want to roll for initiative!",
        message_type="player"
    )
    session.add(message)
    session.commit()
    session.refresh(message)
    
    assert message.id is not None
    assert message.session_id == sample_session.id
    assert message.sender_name == "Player 1"
    assert message.content == "I want to roll for initiative!"
    assert message.message_type == "player"
    assert isinstance(message.created_at, datetime)


def test_message_types(session: Session, sample_session: GameSession):
    """Test different message types."""
    types = ["player", "dm", "system"]
    
    for msg_type in types:
        message = Message(
            session_id=sample_session.id,
            sender_name=f"Sender-{msg_type}",
            content=f"Test message of type {msg_type}",
            message_type=msg_type
        )
        session.add(message)
    
    session.commit()
    
    # Query messages
    statement = select(Message).where(Message.session_id == sample_session.id)
    messages = session.exec(statement).all()
    
    assert len(messages) == 3
    assert all(msg.message_type in types for msg in messages)


def test_session_player_link(session: Session, sample_player: Player, sample_session: GameSession, sample_character: Character):
    """Test session-player many-to-many relationship."""
    session_player = SessionPlayer(
        session_id=sample_session.id,
        player_id=sample_player.id,
        character_id=sample_character.id
    )
    session.add(session_player)
    session.commit()
    session.refresh(session_player)
    
    assert session_player.id is not None
    assert session_player.session_id == sample_session.id
    assert session_player.player_id == sample_player.id
    assert session_player.character_id == sample_character.id
    assert isinstance(session_player.joined_at, datetime)


def test_character_default_stats(session: Session, sample_player: Player):
    """Test character default stats."""
    character = Character(
        player_id=sample_player.id,
        name="Default Character",
        race="Human",
        char_class="Fighter"
    )
    session.add(character)
    session.commit()
    session.refresh(character)
    
    # Check defaults
    assert character.level == 1
    assert character.strength == 10
    assert character.dexterity == 10
    assert character.constitution == 10
    assert character.intelligence == 10
    assert character.wisdom == 10
    assert character.charisma == 10
    assert character.max_hp == 10
    assert character.current_hp == 10
    assert character.armor_class == 10
