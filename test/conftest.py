"""Test configuration and fixtures."""

import pytest
from sqlmodel import SQLModel, create_engine, Session
from fastapi.testclient import TestClient

from llm_dungeon_master.server import app
from llm_dungeon_master.models import Player, Session as GameSession, Character, Message


@pytest.fixture(name="engine")
def engine_fixture():
    """Create a test database engine."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="session")
def session_fixture(engine):
    """Create a test database session."""
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture():
    """Create a test client for the FastAPI app."""
    with TestClient(app) as client:
        yield client


@pytest.fixture(name="sample_player")
def sample_player_fixture(session):
    """Create a sample player for testing."""
    player = Player(name="Test Player")
    session.add(player)
    session.commit()
    session.refresh(player)
    return player


@pytest.fixture(name="sample_session")
def sample_session_fixture(session):
    """Create a sample game session for testing."""
    game_session = GameSession(name="Test Session", dm_name="Test DM")
    session.add(game_session)
    session.commit()
    session.refresh(game_session)
    return game_session


@pytest.fixture(name="sample_character")
def sample_character_fixture(session, sample_player):
    """Create a sample character for testing."""
    character = Character(
        player_id=sample_player.id,
        name="Test Character",
        race="Human",
        char_class="Fighter",
        level=1,
        max_hp=10,
        current_hp=10,
        armor_class=15
    )
    session.add(character)
    session.commit()
    session.refresh(character)
    return character
