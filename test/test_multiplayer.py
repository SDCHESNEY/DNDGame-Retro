"""Tests for multiplayer functionality."""

import pytest
from datetime import datetime, UTC, timedelta
from sqlmodel import Session, create_engine, SQLModel

from llm_dungeon_master.models import (
    Player, Session as GameSession, Character, SessionPlayer,
    Turn, TurnAction, PlayerPresence, ReconnectionToken
)
from llm_dungeon_master.turn_manager import TurnManager, TurnStatus
from llm_dungeon_master.presence_manager import PresenceManager, PresenceStatus
from llm_dungeon_master.sync_manager import SyncManager, ConflictType, ResolutionStrategy
from llm_dungeon_master.reconnection_manager import ReconnectionManager


@pytest.fixture
def engine():
    """Create a test database engine."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(engine):
    """Create a test database session."""
    with Session(engine) as session:
        yield session


@pytest.fixture
def test_session(db_session):
    """Create a test game session."""
    session = GameSession(name="Test Session", dm_name="Test DM")
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session


@pytest.fixture
def test_players(db_session):
    """Create test players."""
    players = [
        Player(name="Alice"),
        Player(name="Bob"),
        Player(name="Charlie")
    ]
    for player in players:
        db_session.add(player)
    db_session.commit()
    for player in players:
        db_session.refresh(player)
    return players


@pytest.fixture
def test_characters(db_session, test_players):
    """Create test characters."""
    characters = [
        Character(
            player_id=test_players[0].id,
            name="Aragorn",
            race="Human",
            char_class="Fighter",
            initiative_bonus=2,
            strength=16,
            dexterity=14
        ),
        Character(
            player_id=test_players[1].id,
            name="Gandalf",
            race="Human",
            char_class="Wizard",
            initiative_bonus=1,
            intelligence=18,
            wisdom=16
        ),
        Character(
            player_id=test_players[2].id,
            name="Legolas",
            race="Elf",
            char_class="Ranger",
            initiative_bonus=3,
            dexterity=18,
            wisdom=14
        )
    ]
    for char in characters:
        db_session.add(char)
    db_session.commit()
    for char in characters:
        db_session.refresh(char)
    return characters


# Turn Management Tests
class TestTurnManager:
    """Tests for TurnManager."""
    
    def test_start_turn_queue(self, db_session, test_session, test_characters):
        """Test starting a turn queue."""
        turn_manager = TurnManager(db_session)
        char_ids = [c.id for c in test_characters]
        
        turns = turn_manager.start_turn_queue(test_session.id, char_ids)
        
        assert len(turns) == 3
        # Should be ordered by initiative (Legolas, Aragorn, Gandalf)
        assert turns[0].character_name == "Legolas"
        assert turns[0].initiative == 3
        assert turns[0].status == TurnStatus.ACTIVE
        assert turns[1].status == TurnStatus.WAITING
    
    def test_get_current_turn(self, db_session, test_session, test_characters):
        """Test getting current turn."""
        turn_manager = TurnManager(db_session)
        char_ids = [c.id for c in test_characters]
        turn_manager.start_turn_queue(test_session.id, char_ids)
        
        current = turn_manager.get_current_turn(test_session.id)
        
        assert current is not None
        assert current.character_name == "Legolas"
        assert current.status == TurnStatus.ACTIVE
    
    def test_advance_turn(self, db_session, test_session, test_characters):
        """Test advancing to next turn."""
        turn_manager = TurnManager(db_session)
        char_ids = [c.id for c in test_characters]
        turn_manager.start_turn_queue(test_session.id, char_ids)
        
        next_turn = turn_manager.advance_turn(test_session.id)
        
        assert next_turn.character_name == "Aragorn"
        assert next_turn.status == TurnStatus.ACTIVE
        assert next_turn.round_number == 1
    
    def test_advance_turn_wraps_around(self, db_session, test_session, test_characters):
        """Test turn advancement wraps to start."""
        turn_manager = TurnManager(db_session)
        char_ids = [c.id for c in test_characters]
        turn_manager.start_turn_queue(test_session.id, char_ids)
        
        # Advance through all turns
        turn_manager.advance_turn(test_session.id)  # Aragorn
        turn_manager.advance_turn(test_session.id)  # Gandalf
        next_turn = turn_manager.advance_turn(test_session.id)  # Back to Legolas
        
        assert next_turn.character_name == "Legolas"
        assert next_turn.round_number == 2  # New round
    
    def test_set_player_ready(self, db_session, test_session, test_characters):
        """Test marking player as ready."""
        turn_manager = TurnManager(db_session)
        char_ids = [c.id for c in test_characters]
        turns = turn_manager.start_turn_queue(test_session.id, char_ids)
        
        # Mark second character as ready
        success = turn_manager.set_player_ready(test_session.id, turns[1].character_id, True)
        
        assert success
        turns = turn_manager.get_turn_queue(test_session.id)
        # Second turn should be ready
        assert turns[1].status == TurnStatus.READY
    
    def test_check_all_ready(self, db_session, test_session, test_characters):
        """Test checking if all players are ready."""
        turn_manager = TurnManager(db_session)
        char_ids = [c.id for c in test_characters]
        turns = turn_manager.start_turn_queue(test_session.id, char_ids)
        
        # Mark all as ready
        for turn in turns:
            if turn.status == TurnStatus.WAITING:
                turn_manager.set_player_ready(test_session.id, turn.character_id, True)
        
        status = turn_manager.check_all_ready(test_session.id)
        
        assert status["all_ready"] == True
        assert status["ready_count"] == 3
    
    def test_record_action(self, db_session, test_session, test_characters):
        """Test recording a turn action."""
        turn_manager = TurnManager(db_session)
        char_ids = [c.id for c in test_characters]
        turns = turn_manager.start_turn_queue(test_session.id, char_ids)
        
        current = turn_manager.get_current_turn(test_session.id)
        action = turn_manager.record_action(
            test_session.id,
            current.character_id,
            "attack",
            "Attacks the goblin",
            "action"
        )
        
        assert action is not None
        assert action.action_type == "attack"
        assert action.description == "Attacks the goblin"
    
    def test_get_turn_history(self, db_session, test_session, test_characters):
        """Test getting turn history."""
        turn_manager = TurnManager(db_session)
        char_ids = [c.id for c in test_characters]
        turn_manager.start_turn_queue(test_session.id, char_ids)
        
        # Record some actions
        current = turn_manager.get_current_turn(test_session.id)
        turn_manager.record_action(test_session.id, current.character_id, "attack", "Attack 1")
        
        history = turn_manager.get_turn_history(test_session.id)
        
        assert len(history) > 0
        # History is in reverse order (most recent first)
        assert history[0]["character_name"] in ["Legolas", "Aragorn", "Gandalf"]
        # Find the entry with actions
        entry_with_actions = next((h for h in history if len(h["actions"]) > 0), None)
        assert entry_with_actions is not None
        assert len(entry_with_actions["actions"]) == 1


# Presence Management Tests
class TestPresenceManager:
    """Tests for PresenceManager."""
    
    def test_track_connection(self, db_session, test_session, test_players):
        """Test tracking a player connection."""
        presence_manager = PresenceManager(db_session)
        
        presence = presence_manager.track_connection(
            test_session.id,
            test_players[0].id,
            "conn_123"
        )
        
        assert presence is not None
        assert presence.status == PresenceStatus.ONLINE
        assert presence.connection_id == "conn_123"
    
    def test_update_heartbeat(self, db_session, test_session, test_players):
        """Test updating heartbeat."""
        presence_manager = PresenceManager(db_session)
        presence_manager.track_connection(test_session.id, test_players[0].id, "conn_123")
        
        success = presence_manager.update_heartbeat(
            test_session.id,
            test_players[0].id,
            "conn_123"
        )
        
        assert success
    
    def test_disconnect(self, db_session, test_session, test_players):
        """Test disconnecting a player."""
        presence_manager = PresenceManager(db_session)
        presence_manager.track_connection(test_session.id, test_players[0].id, "conn_123")
        
        success = presence_manager.disconnect(
            test_session.id,
            test_players[0].id,
            "conn_123"
        )
        
        assert success
        status = presence_manager.get_player_status(test_session.id, test_players[0].id)
        assert status == PresenceStatus.OFFLINE
    
    def test_get_presence_summary(self, db_session, test_session, test_players):
        """Test getting presence summary."""
        presence_manager = PresenceManager(db_session)
        
        # Add session players
        for player in test_players:
            session_player = SessionPlayer(
                session_id=test_session.id,
                player_id=player.id
            )
            db_session.add(session_player)
        db_session.commit()
        
        # Track some connections
        presence_manager.track_connection(test_session.id, test_players[0].id, "conn_1")
        presence_manager.track_connection(test_session.id, test_players[1].id, "conn_2")
        
        summary = presence_manager.get_presence_summary(test_session.id)
        
        assert summary["total_players"] == 3
        assert summary["online"] >= 2
        assert len(summary["players"]) == 3
    
    def test_check_all_ready(self, db_session, test_session, test_players):
        """Test checking if all online."""
        presence_manager = PresenceManager(db_session)
        
        # Add session players
        for player in test_players:
            session_player = SessionPlayer(
                session_id=test_session.id,
                player_id=player.id
            )
            db_session.add(session_player)
        db_session.commit()
        
        # Connect all players
        for i, player in enumerate(test_players):
            presence_manager.track_connection(
                test_session.id,
                player.id,
                f"conn_{i}"
            )
        
        status = presence_manager.check_all_ready(test_session.id)
        
        assert status["all_online"] == True
        assert status["online_count"] == 3


# Sync Manager Tests
class TestSyncManager:
    """Tests for SyncManager."""
    
    def test_detect_turn_order_violation(self, db_session, test_session, test_characters):
        """Test detecting turn order violations."""
        sync_manager = SyncManager(db_session)
        turn_manager = TurnManager(db_session)
        
        # Start turns
        char_ids = [c.id for c in test_characters]
        turn_manager.start_turn_queue(test_session.id, char_ids)
        
        current = turn_manager.get_current_turn(test_session.id)
        
        # Simulate action from wrong character
        actions = [
            {
                "character_id": test_characters[1].id,  # Not current turn
                "action_type": "attack",
                "timestamp": datetime.now(UTC)
            }
        ]
        
        conflicts = sync_manager.detect_conflicts(test_session.id, actions)
        
        assert len(conflicts) > 0
        assert any(c.conflict_type == ConflictType.TURN_ORDER_VIOLATION for c in conflicts)
    
    def test_check_state_consistency(self, db_session, test_session, test_characters):
        """Test checking state consistency."""
        sync_manager = SyncManager(db_session)
        turn_manager = TurnManager(db_session)
        
        char_ids = [c.id for c in test_characters]
        turn_manager.start_turn_queue(test_session.id, char_ids)
        
        # Correct client state
        client_state = {
            "current_turn_character_id": test_characters[2].id,  # Legolas (highest init)
            "round_number": 1,
            "characters": {}
        }
        
        is_consistent, discrepancies = sync_manager.check_state_consistency(
            test_session.id,
            client_state
        )
        
        assert is_consistent
        assert len(discrepancies) == 0
    
    def test_force_sync(self, db_session, test_session, test_characters):
        """Test forcing synchronization."""
        sync_manager = SyncManager(db_session)
        turn_manager = TurnManager(db_session)
        
        char_ids = [c.id for c in test_characters]
        turn_manager.start_turn_queue(test_session.id, char_ids)
        
        state = sync_manager.force_sync(test_session.id)
        
        assert state["session_id"] == test_session.id
        assert state["current_turn"] is not None
        assert len(state["turn_queue"]) == 3


# Reconnection Manager Tests
class TestReconnectionManager:
    """Tests for ReconnectionManager."""
    
    def test_create_token(self, db_session, test_session, test_players):
        """Test creating a reconnection token."""
        reconnection_manager = ReconnectionManager(db_session)
        
        token = reconnection_manager.create_reconnection_token(
            test_players[0].id,
            test_session.id
        )
        
        assert token is not None
        assert len(token) > 0
    
    def test_validate_token(self, db_session, test_session, test_players):
        """Test validating a token."""
        reconnection_manager = ReconnectionManager(db_session)
        
        token = reconnection_manager.create_reconnection_token(
            test_players[0].id,
            test_session.id
        )
        
        token_record = reconnection_manager.validate_token(token)
        
        assert token_record is not None
        assert token_record.player_id == test_players[0].id
        assert token_record.session_id == test_session.id
    
    def test_handle_reconnection(self, db_session, test_session, test_players, test_characters):
        """Test handling reconnection."""
        reconnection_manager = ReconnectionManager(db_session)
        
        # Add session player
        session_player = SessionPlayer(
            session_id=test_session.id,
            player_id=test_players[0].id,
            character_id=test_characters[0].id
        )
        db_session.add(session_player)
        db_session.commit()
        
        token = reconnection_manager.create_reconnection_token(
            test_players[0].id,
            test_session.id
        )
        
        result = reconnection_manager.handle_reconnection(token)
        
        assert result["success"] == True
        assert result["player_id"] == test_players[0].id
        assert result["session_id"] == test_session.id
        assert "session_state" in result
    
    def test_token_expires(self, db_session, test_session, test_players):
        """Test that expired tokens are invalid."""
        reconnection_manager = ReconnectionManager(db_session)
        
        token = reconnection_manager.create_reconnection_token(
            test_players[0].id,
            test_session.id
        )
        
        # Manually expire the token
        import hashlib
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        from sqlmodel import select
        statement = select(ReconnectionToken).where(ReconnectionToken.token == token_hash)
        token_record = db_session.exec(statement).first()
        token_record.expires_at = datetime.now(UTC) - timedelta(hours=1)
        db_session.commit()
        
        # Should be invalid now
        validated = reconnection_manager.validate_token(token)
        assert validated is None
    
    def test_restore_session_state(self, db_session, test_session, test_players, test_characters):
        """Test restoring session state."""
        reconnection_manager = ReconnectionManager(db_session)
        
        # Add session player
        session_player = SessionPlayer(
            session_id=test_session.id,
            player_id=test_players[0].id,
            character_id=test_characters[0].id
        )
        db_session.add(session_player)
        db_session.commit()
        
        state = reconnection_manager.restore_session_state(
            test_players[0].id,
            test_session.id
        )
        
        assert state["session_id"] == test_session.id
        assert state["character"] is not None
        assert state["character"]["name"] == "Aragorn"
    
    def test_revoke_token(self, db_session, test_session, test_players):
        """Test revoking tokens."""
        reconnection_manager = ReconnectionManager(db_session)
        
        token = reconnection_manager.create_reconnection_token(
            test_players[0].id,
            test_session.id
        )
        
        success = reconnection_manager.revoke_token(
            test_players[0].id,
            test_session.id
        )
        
        assert success
        
        # Token should be invalid now
        validated = reconnection_manager.validate_token(token)
        assert validated is None


# Integration Tests
class TestMultiplayerIntegration:
    """Integration tests for multiplayer features."""
    
    def test_full_turn_cycle(self, db_session, test_session, test_characters):
        """Test a complete turn cycle."""
        turn_manager = TurnManager(db_session)
        char_ids = [c.id for c in test_characters]
        
        # Start turns
        turns = turn_manager.start_turn_queue(test_session.id, char_ids)
        assert len(turns) == 3
        
        # Take actions and advance
        for i in range(3):
            current = turn_manager.get_current_turn(test_session.id)
            turn_manager.record_action(
                test_session.id,
                current.character_id,
                "attack",
                f"Action {i+1}"
            )
            turn_manager.advance_turn(test_session.id)
        
        # Should be back to first character, round 2
        current = turn_manager.get_current_turn(test_session.id)
        assert current.character_name == "Legolas"
        assert current.round_number == 2
    
    def test_presence_with_reconnection(self, db_session, test_session, test_players):
        """Test presence tracking with reconnection."""
        presence_manager = PresenceManager(db_session)
        reconnection_manager = ReconnectionManager(db_session)
        
        # Add session player
        session_player = SessionPlayer(
            session_id=test_session.id,
            player_id=test_players[0].id
        )
        db_session.add(session_player)
        db_session.commit()
        
        # Connect
        presence_manager.track_connection(test_session.id, test_players[0].id, "conn_1")
        
        # Create token
        token = reconnection_manager.create_reconnection_token(
            test_players[0].id,
            test_session.id
        )
        
        # Disconnect
        presence_manager.disconnect(test_session.id, test_players[0].id, "conn_1")
        
        # Reconnect using token
        result = reconnection_manager.handle_reconnection(token)
        assert result["success"] == True
        
        # Track new connection
        presence_manager.track_connection(test_session.id, test_players[0].id, "conn_2")
        
        status = presence_manager.get_player_status(test_session.id, test_players[0].id)
        assert status == PresenceStatus.ONLINE
