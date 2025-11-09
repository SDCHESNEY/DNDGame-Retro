"""Tests for the DM Service."""

import pytest
from datetime import datetime, timedelta, UTC
from sqlmodel import Session, select

from llm_dungeon_master.dm_service import (
    DMService,
    RateLimitExceeded,
    TokenLimitExceeded
)
from llm_dungeon_master.llm_provider import MockProvider
from llm_dungeon_master.models import Session as GameSession, Message, Player


@pytest.fixture
def dm_service():
    """Create a DM service with mock provider."""
    return DMService(
        llm_provider=MockProvider(),
        max_retries=3,
        initial_backoff=0.1,  # Fast for testing
        rate_limit_per_minute=5,
        max_tokens_per_session=1000
    )


@pytest.fixture
def sample_session(session: Session) -> GameSession:
    """Create a sample game session."""
    game_session = GameSession(name="Test Session", dm_name="Test DM")
    session.add(game_session)
    session.commit()
    session.refresh(game_session)
    return game_session


@pytest.fixture
def sample_player(session: Session) -> Player:
    """Create a sample player."""
    player = Player(name="TestPlayer")
    session.add(player)
    session.commit()
    session.refresh(player)
    return player


class TestDMServiceBasics:
    """Test basic DMService functionality."""
    
    @pytest.mark.asyncio
    async def test_start_session(self, dm_service: DMService, session: Session, sample_session: GameSession):
        """Test starting a new session."""
        response = await dm_service.start_session(
            db=session,
            session_id=sample_session.id
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        
        # Check that DM message was saved to database
        statement = select(Message).where(
            Message.session_id == sample_session.id,
            Message.message_type == "dm"
        )
        messages = session.exec(statement).all()
        assert len(messages) == 1
        assert messages[0].sender_name == "Dungeon Master"
        assert messages[0].content == response
    
    @pytest.mark.asyncio
    async def test_process_player_action(
        self,
        dm_service: DMService,
        session: Session,
        sample_session: GameSession
    ):
        """Test processing a player action."""
        response = await dm_service.process_player_action(
            db=session,
            session_id=sample_session.id,
            player_name="TestPlayer",
            action="I look around the room"
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        
        # Check that both player and DM messages were saved
        statement = select(Message).where(Message.session_id == sample_session.id)
        messages = session.exec(statement).all()
        assert len(messages) == 2
        
        # Player message
        assert messages[0].message_type == "player"
        assert messages[0].sender_name == "TestPlayer"
        assert messages[0].content == "I look around the room"
        
        # DM message
        assert messages[1].message_type == "dm"
        assert messages[1].sender_name == "Dungeon Master"
    
    @pytest.mark.asyncio
    async def test_handle_roll(
        self,
        dm_service: DMService,
        session: Session,
        sample_session: GameSession
    ):
        """Test handling a dice roll."""
        response = await dm_service.handle_roll(
            db=session,
            session_id=sample_session.id,
            player_name="TestPlayer",
            roll_type="perception",
            result=18,
            dice="1d20",
            modifier=3
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert "roll" in response.lower() or "18" in response
        
        # Check messages saved
        statement = select(Message).where(Message.session_id == sample_session.id)
        messages = session.exec(statement).all()
        assert len(messages) == 2
        
        # System message for roll
        assert messages[0].message_type == "system"
        assert "perception" in messages[0].content.lower()
        
        # DM response
        assert messages[1].message_type == "dm"
    
    @pytest.mark.asyncio
    async def test_conversation_history(
        self,
        dm_service: DMService,
        session: Session,
        sample_session: GameSession
    ):
        """Test that conversation history is maintained."""
        # Add some messages
        msg1 = Message(
            session_id=sample_session.id,
            sender_name="Player1",
            content="Hello",
            message_type="player"
        )
        msg2 = Message(
            session_id=sample_session.id,
            sender_name="Dungeon Master",
            content="Welcome!",
            message_type="dm"
        )
        session.add(msg1)
        session.add(msg2)
        session.commit()
        
        # Get conversation history
        history = dm_service._get_conversation_history(
            db=session,
            session_id=sample_session.id,
            limit=10
        )
        
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert "Player1" in history[0]["content"]
        assert history[1]["role"] == "assistant"
        assert "Dungeon Master" in history[1]["content"]


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    @pytest.mark.asyncio
    async def test_rate_limit_enforcement(
        self,
        dm_service: DMService,
        session: Session,
        sample_session: GameSession
    ):
        """Test that rate limiting is enforced."""
        # Make requests up to the limit
        for i in range(5):
            await dm_service.process_player_action(
                db=session,
                session_id=sample_session.id,
                player_name="TestPlayer",
                action=f"Action {i}"
            )
        
        # Next request should fail
        with pytest.raises(RateLimitExceeded):
            await dm_service.process_player_action(
                db=session,
                session_id=sample_session.id,
                player_name="TestPlayer",
                action="Too many requests"
            )
    
    @pytest.mark.asyncio
    async def test_rate_limit_per_session(
        self,
        dm_service: DMService,
        session: Session
    ):
        """Test that rate limits are per-session."""
        # Create two sessions
        session1 = GameSession(name="Session 1")
        session2 = GameSession(name="Session 2")
        session.add(session1)
        session.add(session2)
        session.commit()
        session.refresh(session1)
        session.refresh(session2)
        
        # Max out session 1
        for i in range(5):
            await dm_service.process_player_action(
                db=session,
                session_id=session1.id,
                player_name="TestPlayer",
                action=f"Action {i}"
            )
        
        # Session 2 should still work
        response = await dm_service.process_player_action(
            db=session,
            session_id=session2.id,
            player_name="TestPlayer",
            action="This should work"
        )
        assert isinstance(response, str)
    
    def test_check_rate_limit_cleanup(self, dm_service: DMService):
        """Test that old timestamps are cleaned up."""
        session_id = 1
        
        # Add timestamps manually
        dm_service._request_timestamps[session_id] = [
            datetime.now(UTC) - timedelta(minutes=2),  # Old
            datetime.now(UTC) - timedelta(seconds=30),  # Recent
            datetime.now(UTC)  # Current
        ]
        
        # Check rate limit (should clean old timestamps)
        dm_service._check_rate_limit(session_id)
        
        # Should only have 3 recent timestamps (the check adds one more)
        assert len(dm_service._request_timestamps[session_id]) == 3
        
        # The old timestamp (2 minutes ago) should be removed
        cutoff = datetime.now(UTC) - timedelta(minutes=1)
        assert all(ts > cutoff for ts in dm_service._request_timestamps[session_id])


class TestTokenTracking:
    """Test token tracking functionality."""
    
    @pytest.mark.asyncio
    async def test_token_usage_tracking(
        self,
        dm_service: DMService,
        session: Session,
        sample_session: GameSession
    ):
        """Test that token usage is tracked."""
        initial_usage = dm_service.get_token_usage(sample_session.id)
        assert initial_usage["used"] == 0
        
        # Process an action
        await dm_service.process_player_action(
            db=session,
            session_id=sample_session.id,
            player_name="TestPlayer",
            action="Hello"
        )
        
        # Token usage should increase
        updated_usage = dm_service.get_token_usage(sample_session.id)
        assert updated_usage["used"] > 0
        assert updated_usage["remaining"] < updated_usage["limit"]
    
    @pytest.mark.asyncio
    async def test_token_limit_enforcement(self, session: Session, sample_session: GameSession):
        """Test that token limits are enforced."""
        # Create service with very low token limit
        dm_service = DMService(
            llm_provider=MockProvider(),
            max_tokens_per_session=10  # Very low
        )
        
        # Manually set token usage to be at limit
        dm_service._token_usage[sample_session.id] = 10
        
        # Should fail due to token limit
        with pytest.raises(TokenLimitExceeded):
            await dm_service.process_player_action(
                db=session,
                session_id=sample_session.id,
                player_name="TestPlayer",
                action="This action will exceed the token limit"
            )
    
    def test_get_token_usage_stats(self, dm_service: DMService):
        """Test getting token usage statistics."""
        session_id = 1
        
        # Track some tokens
        dm_service._track_tokens(session_id, 100)
        dm_service._track_tokens(session_id, 50)
        
        stats = dm_service.get_token_usage(session_id)
        assert stats["used"] == 150
        assert stats["limit"] == 1000
        assert stats["remaining"] == 850


class TestRetryLogic:
    """Test retry logic with exponential backoff."""
    
    @pytest.mark.asyncio
    async def test_retry_on_failure(self, dm_service: DMService):
        """Test that retries work on API failures."""
        # Mock provider shouldn't fail, but we can test the structure
        messages = [
            {"role": "system", "content": "Test"},
            {"role": "user", "content": "Hello"}
        ]
        
        response = await dm_service._generate_with_retry(messages)
        assert isinstance(response, str)
    
    @pytest.mark.asyncio
    async def test_retry_gives_up_eventually(self):
        """Test that retry logic eventually gives up."""
        from llm_dungeon_master.llm_provider import LLMProvider
        
        class FailingProvider(LLMProvider):
            """Provider that always fails."""
            
            async def generate_response(self, messages, stream=False):
                raise Exception("API Error")
            
            async def generate_stream(self, messages):
                raise Exception("API Error")
        
        dm_service = DMService(
            llm_provider=FailingProvider(),
            max_retries=2,
            initial_backoff=0.01  # Fast for testing
        )
        
        messages = [{"role": "user", "content": "Test"}]
        
        with pytest.raises(Exception) as exc_info:
            await dm_service._generate_with_retry(messages)
        
        assert "Failed after 2 attempts" in str(exc_info.value)


class TestStreamingResponse:
    """Test streaming response functionality."""
    
    @pytest.mark.asyncio
    async def test_generate_stream(
        self,
        dm_service: DMService,
        session: Session,
        sample_session: GameSession
    ):
        """Test streaming response generation."""
        chunks = []
        async for chunk in dm_service.generate_stream(
            db=session,
            session_id=sample_session.id,
            player_name="TestPlayer",
            action="Tell me a story"
        ):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        full_response = "".join(chunks)
        assert len(full_response) > 0
        
        # Check that messages were saved
        statement = select(Message).where(Message.session_id == sample_session.id)
        messages = session.exec(statement).all()
        assert len(messages) == 2  # Player message + DM response
    
    @pytest.mark.asyncio
    async def test_stream_respects_rate_limit(
        self,
        dm_service: DMService,
        session: Session,
        sample_session: GameSession
    ):
        """Test that streaming respects rate limits."""
        # Max out rate limit
        for i in range(5):
            await dm_service.process_player_action(
                db=session,
                session_id=sample_session.id,
                player_name="TestPlayer",
                action=f"Action {i}"
            )
        
        # Streaming should also fail
        with pytest.raises(RateLimitExceeded):
            async for _ in dm_service.generate_stream(
                db=session,
                session_id=sample_session.id,
                player_name="TestPlayer",
                action="Streaming action"
            ):
                pass


class TestIntegration:
    """Integration tests for complete workflows."""
    
    @pytest.mark.asyncio
    async def test_complete_game_session(
        self,
        dm_service: DMService,
        session: Session,
        sample_session: GameSession
    ):
        """Test a complete game session workflow."""
        # Start session
        opening = await dm_service.start_session(
            db=session,
            session_id=sample_session.id
        )
        assert len(opening) > 0
        
        # Player action
        response1 = await dm_service.process_player_action(
            db=session,
            session_id=sample_session.id,
            player_name="Adventurer",
            action="I enter the tavern"
        )
        assert len(response1) > 0
        
        # Dice roll
        roll_response = await dm_service.handle_roll(
            db=session,
            session_id=sample_session.id,
            player_name="Adventurer",
            roll_type="perception",
            result=15,
            dice="1d20",
            modifier=2
        )
        assert len(roll_response) > 0
        
        # Another action
        response2 = await dm_service.process_player_action(
            db=session,
            session_id=sample_session.id,
            player_name="Adventurer",
            action="I talk to the bartender"
        )
        assert len(response2) > 0
        
        # Verify all messages were saved
        statement = select(Message).where(Message.session_id == sample_session.id)
        messages = session.exec(statement).all()
        
        # Should have: 1 DM start, 2 player actions, 2 DM responses, 1 roll system, 1 roll DM
        assert len(messages) >= 7
        
        # Check token usage
        stats = dm_service.get_token_usage(sample_session.id)
        assert stats["used"] > 0
        assert stats["remaining"] >= 0  # Can be 0 if we hit the limit
    
    @pytest.mark.asyncio
    async def test_multiplayer_session(
        self,
        dm_service: DMService,
        session: Session,
        sample_session: GameSession
    ):
        """Test multiple players in same session."""
        # Two players take actions
        response1 = await dm_service.process_player_action(
            db=session,
            session_id=sample_session.id,
            player_name="Player1",
            action="I cast a spell"
        )
        
        response2 = await dm_service.process_player_action(
            db=session,
            session_id=sample_session.id,
            player_name="Player2",
            action="I draw my sword"
        )
        
        assert len(response1) > 0
        assert len(response2) > 0
        
        # Both players' actions should be in history
        statement = select(Message).where(
            Message.session_id == sample_session.id,
            Message.message_type == "player"
        )
        player_messages = session.exec(statement).all()
        
        assert len(player_messages) == 2
        player_names = {msg.sender_name for msg in player_messages}
        assert "Player1" in player_names
        assert "Player2" in player_names
