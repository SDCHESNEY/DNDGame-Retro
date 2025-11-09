"""Tests for Quality of Life features."""

import pytest
from pathlib import Path
from datetime import datetime, timedelta, UTC
from sqlmodel import create_engine, Session as DBSession, SQLModel
import tempfile
import json

from llm_dungeon_master.models import (
    Session, Player, Character, Message, Roll, CombatEncounter
)
from llm_dungeon_master.qol import (
    SessionStateManager, MessageHistoryManager, StatisticsTracker, AliasManager
)


@pytest.fixture
def db():
    """Create an in-memory database for testing."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    
    with DBSession(engine) as session:
        yield session


@pytest.fixture
def sample_session(db):
    """Create a sample session with data."""
    # Create player
    player = Player(name="test_player")
    db.add(player)
    db.commit()
    db.refresh(player)
    
    # Create character
    character = Character(
        player_id=player.id,
        name="Test Hero",
        race="Human",
        char_class="Fighter",
        level=5,
        max_hp=45,
        current_hp=45,
        strength=16,
        dexterity=14,
        constitution=15,
        intelligence=10,
        wisdom=12,
        charisma=11
    )
    db.add(character)
    db.commit()
    db.refresh(character)
    
    # Create session
    session = Session(name="Test Session")
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # Create messages
    for i in range(10):
        message = Message(
            session_id=session.id,
            sender_name="test_player" if i % 2 == 0 else "DM",
            content=f"Test message {i}",
            message_type="player" if i % 2 == 0 else "dm"
        )
        db.add(message)
    
    # Create rolls
    for i in range(5):
        roll = Roll(
            session_id=session.id,
            character_id=character.id,
            roll_type="attack",
            formula="1d20",
            result=15 + i,
            rolls=f"[{15 + i}]",  # JSON string of rolls
            modifier=3
        )
        db.add(roll)
    
    # Create combat encounter
    encounter = CombatEncounter(
        session_id=session.id,
        name="Test Encounter",
        is_active=False,
        round_number=5
    )
    db.add(encounter)
    
    db.commit()
    
    return session, player, character


# ============================================================================
# Session State Manager Tests
# ============================================================================

class TestSessionStateManager:
    """Tests for session save/load functionality."""
    
    def test_save_session(self, db, sample_session):
        """Test saving session state."""
        session, player, character = sample_session
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionStateManager(db, Path(tmpdir))
            filepath = manager.save_session(session.id)
            
            assert filepath.exists()
            assert filepath.suffix == ".json"
            assert f"session_{session.id}_" in filepath.name
    
    def test_save_session_with_metadata(self, db, sample_session):
        """Test saving with custom metadata."""
        session, player, character = sample_session
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionStateManager(db, Path(tmpdir))
            metadata = {"note": "Important save"}
            filepath = manager.save_session(session.id, metadata)
            
            # Load and check metadata
            with open(filepath) as f:
                data = json.load(f)
            
            assert data["metadata"]["note"] == "Important save"
    
    def test_load_session(self, db, sample_session):
        """Test loading session state."""
        session, player, character = sample_session
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionStateManager(db, Path(tmpdir))
            
            # Save then load
            filepath = manager.save_session(session.id)
            snapshot = manager.load_session(filepath)
            
            assert snapshot.session_id == session.id
            assert snapshot.session_name == session.name
            assert len(snapshot.recent_messages) == 10
    
    def test_list_saves(self, db, sample_session):
        """Test listing save files."""
        session, player, character = sample_session
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionStateManager(db, Path(tmpdir))
            
            # Create multiple saves
            manager.save_session(session.id)
            manager.save_session(session.id)
            
            saves = manager.list_saves(session.id)
            assert len(saves) >= 2
    
    def test_get_save_info(self, db, sample_session):
        """Test getting save file info."""
        session, player, character = sample_session
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionStateManager(db, Path(tmpdir))
            filepath = manager.save_session(session.id)
            
            info = manager.get_save_info(filepath)
            
            assert info["session_id"] == session.id
            assert info["session_name"] == session.name
            assert info["num_messages"] == 10
    
    def test_delete_save(self, db, sample_session):
        """Test deleting a save file."""
        session, player, character = sample_session
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionStateManager(db, Path(tmpdir))
            filepath = manager.save_session(session.id)
            
            assert filepath.exists()
            
            success = manager.delete_save(filepath)
            assert success
            assert not filepath.exists()
    
    def test_auto_save(self, db, sample_session):
        """Test auto-save functionality."""
        session, player, character = sample_session
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionStateManager(db, Path(tmpdir))
            
            # Create multiple auto-saves
            for _ in range(6):
                manager.auto_save(session.id)
            
            saves = [s for s in manager.list_saves(session.id) if "_auto_" in s.name]
            
            # Should keep only 5 most recent
            assert len(saves) <= 5


# ============================================================================
# Message History Manager Tests
# ============================================================================

class TestMessageHistoryManager:
    """Tests for message history functionality."""
    
    def test_get_recent_messages(self, db, sample_session):
        """Test getting recent messages."""
        session, player, character = sample_session
        
        manager = MessageHistoryManager(db)
        messages = manager.get_recent_messages(session.id, limit=5)
        
        assert len(messages) == 5
        # Should be in chronological order
        for i in range(len(messages) - 1):
            assert messages[i].timestamp <= messages[i + 1].timestamp
    
    def test_search_messages(self, db, sample_session):
        """Test searching messages."""
        session, player, character = sample_session
        
        manager = MessageHistoryManager(db)
        messages = manager.search_messages(session.id, "message 5")
        
        assert len(messages) >= 1
        assert "5" in messages[0].content
    
    def test_search_by_sender(self, db, sample_session):
        """Test filtering by sender."""
        session, player, character = sample_session
        
        manager = MessageHistoryManager(db)
        messages = manager.search_messages(session.id, "", sender="DM")
        
        assert all(msg.sender_name == "DM" for msg in messages)
    
    def test_search_by_type(self, db, sample_session):
        """Test filtering by message type."""
        session, player, character = sample_session
        
        manager = MessageHistoryManager(db)
        messages = manager.search_messages(session.id, "", message_type="player")
        
        assert all(msg.message_type == "player" for msg in messages)
    
    def test_get_messages_by_date(self, db, sample_session):
        """Test getting messages by date range."""
        session, player, character = sample_session
        
        manager = MessageHistoryManager(db)
        start_date = datetime.now(UTC) - timedelta(days=1)
        messages = manager.get_messages_by_date(session.id, start_date)
        
        assert len(messages) >= 10
    
    def test_get_message_stats(self, db, sample_session):
        """Test message statistics."""
        session, player, character = sample_session
        
        manager = MessageHistoryManager(db)
        stats = manager.get_message_stats(session.id)
        
        assert stats["total_messages"] == 10
        assert "test_player" in stats["by_sender"]
        assert "DM" in stats["by_sender"]
    
    def test_export_text(self, db, sample_session):
        """Test exporting as text."""
        session, player, character = sample_session
        
        manager = MessageHistoryManager(db)
        text = manager.export_history(session.id, format="text")
        
        assert "test_player" in text
        assert "Test message" in text
    
    def test_export_json(self, db, sample_session):
        """Test exporting as JSON."""
        session, player, character = sample_session
        
        manager = MessageHistoryManager(db)
        json_str = manager.export_history(session.id, format="json")
        
        data = json.loads(json_str)
        assert len(data) == 10
        assert data[0]["sender_name"] in ["test_player", "DM"]
    
    def test_export_markdown(self, db, sample_session):
        """Test exporting as Markdown."""
        session, player, character = sample_session
        
        manager = MessageHistoryManager(db)
        markdown = manager.export_history(session.id, format="markdown")
        
        assert "# Message History" in markdown
        assert "##" in markdown  # Headers for messages
    
    def test_clear_old_messages(self, db, sample_session):
        """Test clearing old messages."""
        session, player, character = sample_session
        
        manager = MessageHistoryManager(db)
        deleted = manager.clear_old_messages(session.id, keep_recent=5)
        
        assert deleted == 5
        
        # Check remaining
        remaining = manager.get_recent_messages(session.id, limit=100)
        assert len(remaining) == 5


# ============================================================================
# Statistics Tracker Tests
# ============================================================================

class TestStatisticsTracker:
    """Tests for statistics tracking."""
    
    def test_get_dice_stats(self, db, sample_session):
        """Test dice rolling statistics."""
        session, player, character = sample_session
        
        tracker = StatisticsTracker(db)
        stats = tracker.get_dice_stats(session_id=session.id)
        
        assert stats["total_rolls"] == 5
        assert stats["average_result"] > 0
    
    def test_get_dice_stats_by_character(self, db, sample_session):
        """Test dice stats filtered by character."""
        session, player, character = sample_session
        
        tracker = StatisticsTracker(db)
        stats = tracker.get_dice_stats(character_id=character.id)
        
        assert stats["total_rolls"] == 5
    
    def test_critical_detection(self, db, sample_session):
        """Test critical hit detection."""
        session, player, character = sample_session
        
        # Add a natural 20
        roll = Roll(
            session_id=session.id,
            character_id=character.id,
            roll_type="attack",
            formula="1d20",
            result=20,
            modifier=0
        )
        db.add(roll)
        db.commit()
        
        tracker = StatisticsTracker(db)
        stats = tracker.get_dice_stats(session_id=session.id)
        
        assert stats["critical_hits"] >= 1
    
    def test_get_combat_stats(self, db, sample_session):
        """Test combat statistics."""
        session, player, character = sample_session
        
        tracker = StatisticsTracker(db)
        stats = tracker.get_combat_stats(session_id=session.id)
        
        assert stats["total_encounters"] == 1
        assert stats["completed_encounters"] == 1
        assert stats["average_rounds"] == 5.0
    
    def test_get_character_stats(self, db, sample_session):
        """Test character-specific statistics."""
        session, player, character = sample_session
        
        tracker = StatisticsTracker(db)
        stats = tracker.get_character_stats(character.id)
        
        assert stats["character_id"] == character.id
        assert stats["name"] == character.name
        assert stats["level"] == 5
        assert stats["dice_stats"]["total_rolls"] == 5
    
    def test_get_session_stats(self, db, sample_session):
        """Test comprehensive session statistics."""
        session, player, character = sample_session
        
        tracker = StatisticsTracker(db)
        stats = tracker.get_session_stats(session.id)
        
        assert stats["session_id"] == session.id
        assert stats["total_messages"] == 10
        assert "dice_stats" in stats
        assert "combat_stats" in stats
    
    def test_get_player_activity(self, db, sample_session):
        """Test player activity tracking."""
        session, player, character = sample_session
        
        tracker = StatisticsTracker(db)
        activity = tracker.get_player_activity(session.id, days=7)
        
        assert activity["period_days"] == 7
        assert activity["total_messages"] >= 10
    
    def test_get_leaderboard_messages(self, db, sample_session):
        """Test message leaderboard."""
        session, player, character = sample_session
        
        tracker = StatisticsTracker(db)
        rankings = tracker.get_leaderboard(session.id, metric="messages")
        
        assert len(rankings) >= 2  # test_player and DM
        assert all("player" in r and "count" in r for r in rankings)
    
    def test_get_leaderboard_rolls(self, db, sample_session):
        """Test roll leaderboard."""
        session, player, character = sample_session
        
        tracker = StatisticsTracker(db)
        rankings = tracker.get_leaderboard(session.id, metric="rolls")
        
        assert len(rankings) >= 1
        assert rankings[0]["count"] == 5
    
    def test_format_stats_report(self, db, sample_session):
        """Test formatting statistics report."""
        session, player, character = sample_session
        
        tracker = StatisticsTracker(db)
        stats = tracker.get_session_stats(session.id)
        report = tracker.format_stats_report(stats)
        
        assert "STATISTICS REPORT" in report
        assert "Session ID" in report
        assert "Dice Statistics" in report


# ============================================================================
# Alias Manager Tests
# ============================================================================

class TestAliasManager:
    """Tests for command alias management."""
    
    def test_default_aliases(self):
        """Test default aliases are loaded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = AliasManager(Path(tmpdir))
            
            assert "n" in manager.aliases
            assert manager.aliases["n"] == "move north"
    
    def test_add_alias(self):
        """Test adding custom alias."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = AliasManager(Path(tmpdir))
            
            success = manager.add_alias("test", "test command")
            assert success
            assert manager.aliases["test"] == "test command"
    
    def test_remove_alias(self):
        """Test removing custom alias."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = AliasManager(Path(tmpdir))
            
            manager.add_alias("custom", "custom command")
            success = manager.remove_alias("custom")
            
            assert success
            assert "custom" not in manager.aliases
    
    def test_cannot_remove_default(self):
        """Test cannot remove default aliases."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = AliasManager(Path(tmpdir))
            
            success = manager.remove_alias("n")
            assert not success
    
    def test_expand_alias(self):
        """Test expanding aliases."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = AliasManager(Path(tmpdir))
            
            expanded = manager.expand_alias("n")
            assert expanded == "move north"
    
    def test_expand_with_arguments(self):
        """Test expanding alias with additional arguments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = AliasManager(Path(tmpdir))
            
            expanded = manager.expand_alias("r 1d6+2")
            assert expanded == "roll 1d6+2"
    
    def test_expand_non_alias(self):
        """Test expanding non-alias command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = AliasManager(Path(tmpdir))
            
            expanded = manager.expand_alias("regular command")
            assert expanded == "regular command"
    
    def test_get_alias(self):
        """Test getting specific alias."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = AliasManager(Path(tmpdir))
            
            command = manager.get_alias("i")
            assert command == "inventory"
    
    def test_list_aliases(self):
        """Test listing all aliases."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = AliasManager(Path(tmpdir))
            
            aliases = manager.list_aliases()
            assert len(aliases) >= 20  # Should have all defaults
    
    def test_list_custom_only(self):
        """Test listing only custom aliases."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = AliasManager(Path(tmpdir))
            
            manager.add_alias("custom1", "command1")
            manager.add_alias("custom2", "command2")
            
            custom = manager.list_aliases(include_defaults=False)
            assert len(custom) == 2
    
    def test_save_and_load_aliases(self):
        """Test persistence of custom aliases."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create and save
            manager1 = AliasManager(Path(tmpdir))
            manager1.add_alias("persist", "persisted command")
            
            # Load in new instance
            manager2 = AliasManager(Path(tmpdir))
            assert manager2.aliases["persist"] == "persisted command"
    
    def test_reset_aliases(self):
        """Test resetting to defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = AliasManager(Path(tmpdir))
            
            manager.add_alias("custom", "custom command")
            manager.reset_aliases()
            
            assert "custom" not in manager.aliases
            assert "n" in manager.aliases  # Default still there
    
    def test_import_aliases(self):
        """Test importing aliases from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # Create import file
            import_file = tmppath / "import.json"
            with open(import_file, 'w') as f:
                json.dump({"imp1": "imported1", "imp2": "imported2"}, f)
            
            # Import
            manager = AliasManager(tmppath)
            count = manager.import_aliases(import_file)
            
            assert count == 2
            assert manager.aliases["imp1"] == "imported1"
    
    def test_export_aliases(self):
        """Test exporting aliases to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            manager = AliasManager(tmppath)
            
            manager.add_alias("exp1", "export1")
            manager.add_alias("exp2", "export2")
            
            export_file = tmppath / "export.json"
            success = manager.export_aliases(export_file, custom_only=True)
            
            assert success
            
            with open(export_file) as f:
                data = json.load(f)
            
            assert "exp1" in data
            assert "n" not in data  # Default should not be in custom-only export
    
    def test_format_aliases(self):
        """Test formatting aliases for display."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = AliasManager(Path(tmpdir))
            
            output = manager.format_aliases()
            
            assert "COMMAND ALIASES" in output
            assert "Movement:" in output
            assert "n" in output
    
    def test_format_aliases_by_category(self):
        """Test formatting specific category."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = AliasManager(Path(tmpdir))
            
            output = manager.format_aliases(category="movement")
            
            assert "movement" in output.lower()
            assert "n" in output


# ============================================================================
# Integration Tests
# ============================================================================

class TestQoLIntegration:
    """Integration tests for QoL features."""
    
    def test_save_and_restore_workflow(self, db, sample_session):
        """Test complete save/load workflow."""
        session, player, character = sample_session
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Save session
            save_manager = SessionStateManager(db, Path(tmpdir))
            filepath = save_manager.save_session(session.id, {"note": "Checkpoint"})
            
            # Load and verify
            snapshot = save_manager.load_session(filepath)
            assert snapshot.session_id == session.id
            assert snapshot.metadata["note"] == "Checkpoint"
    
    def test_history_and_stats_consistency(self, db, sample_session):
        """Test consistency between history and stats."""
        session, player, character = sample_session
        
        history_manager = MessageHistoryManager(db)
        stats_tracker = StatisticsTracker(db)
        
        # Get data from both
        messages = history_manager.get_recent_messages(session.id, limit=100)
        stats = stats_tracker.get_session_stats(session.id)
        
        # Should match
        assert len(messages) == stats["total_messages"]
    
    def test_alias_expansion_in_commands(self):
        """Test using aliases with various commands."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = AliasManager(Path(tmpdir))
            
            # Test movement aliases
            assert manager.expand_alias("n") == "move north"
            assert manager.expand_alias("s") == "move south"
            
            # Test dice aliases
            assert manager.expand_alias("r20") == "roll 1d20"
            assert manager.expand_alias("adv") == "roll 1d20 advantage"
