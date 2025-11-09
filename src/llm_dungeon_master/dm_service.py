"""Dungeon Master service for processing player actions and generating responses."""

import asyncio
from datetime import datetime, timedelta, UTC
from typing import Optional
from sqlmodel import Session as DBSession, select

from .llm_provider import LLMProvider, get_llm_provider
from .prompts import get_dm_system_message, get_start_session_message, format_roll_prompt
from .models import Session, Message


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""
    pass


class TokenLimitExceeded(Exception):
    """Raised when token limit is exceeded."""
    pass


class DMService:
    """Service for managing DM interactions with LLM."""
    
    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        max_retries: int = 3,
        initial_backoff: float = 1.0,
        rate_limit_per_minute: int = 20,
        max_tokens_per_session: int = 100000
    ):
        """Initialize the DM service.
        
        Args:
            llm_provider: LLM provider to use (defaults to configured provider)
            max_retries: Maximum number of retry attempts
            initial_backoff: Initial backoff time in seconds
            rate_limit_per_minute: Maximum requests per minute per session
            max_tokens_per_session: Maximum tokens per session
        """
        self.llm_provider = llm_provider or get_llm_provider()
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.rate_limit_per_minute = rate_limit_per_minute
        self.max_tokens_per_session = max_tokens_per_session
        
        # Track rate limiting per session
        self._request_timestamps: dict[int, list[datetime]] = {}
        self._token_usage: dict[int, int] = {}
    
    def _check_rate_limit(self, session_id: int) -> None:
        """Check if rate limit is exceeded for a session.
        
        Args:
            session_id: Session ID to check
            
        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        now = datetime.now(UTC)
        cutoff = now - timedelta(minutes=1)
        
        # Clean old timestamps
        if session_id in self._request_timestamps:
            self._request_timestamps[session_id] = [
                ts for ts in self._request_timestamps[session_id]
                if ts > cutoff
            ]
        else:
            self._request_timestamps[session_id] = []
        
        # Check limit
        if len(self._request_timestamps[session_id]) >= self.rate_limit_per_minute:
            raise RateLimitExceeded(
                f"Rate limit exceeded: {self.rate_limit_per_minute} requests per minute"
            )
        
        # Record this request
        self._request_timestamps[session_id].append(now)
    
    def _check_token_limit(self, session_id: int) -> None:
        """Check if token limit is exceeded for a session.
        
        Args:
            session_id: Session ID to check
            
        Raises:
            TokenLimitExceeded: If token limit is exceeded
        """
        used_tokens = self._token_usage.get(session_id, 0)
        if used_tokens >= self.max_tokens_per_session:
            raise TokenLimitExceeded(
                f"Token limit exceeded: {used_tokens}/{self.max_tokens_per_session}"
            )
    
    def _track_tokens(self, session_id: int, estimated_tokens: int) -> None:
        """Track token usage for a session.
        
        Args:
            session_id: Session ID
            estimated_tokens: Estimated number of tokens used
        """
        if session_id not in self._token_usage:
            self._token_usage[session_id] = 0
        self._token_usage[session_id] += estimated_tokens
    
    def get_token_usage(self, session_id: int) -> dict[str, int]:
        """Get token usage statistics for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Dictionary with used and remaining tokens
        """
        used = self._token_usage.get(session_id, 0)
        return {
            "used": used,
            "limit": self.max_tokens_per_session,
            "remaining": max(0, self.max_tokens_per_session - used)
        }
    
    async def _generate_with_retry(
        self,
        messages: list[dict[str, str]],
        stream: bool = False
    ) -> str:
        """Generate a response with retry logic and exponential backoff.
        
        Args:
            messages: Conversation history
            stream: Whether to use streaming (not implemented for retry)
            
        Returns:
            Generated response
            
        Raises:
            Exception: If all retries fail
        """
        last_error = None
        backoff = self.initial_backoff
        
        for attempt in range(self.max_retries):
            try:
                response = await self.llm_provider.generate_response(
                    messages=messages,
                    stream=False
                )
                
                if isinstance(response, str):
                    return response
                else:
                    # If we got an iterator somehow, consume it
                    chunks = []
                    async for chunk in response:
                        chunks.append(chunk)
                    return "".join(chunks)
                    
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    # Wait with exponential backoff
                    await asyncio.sleep(backoff)
                    backoff *= 2
        
        # All retries failed
        raise Exception(f"Failed after {self.max_retries} attempts: {last_error}")
    
    def _get_conversation_history(
        self,
        db: DBSession,
        session_id: int,
        limit: int = 20
    ) -> list[dict[str, str]]:
        """Get conversation history for a session.
        
        Args:
            db: Database session
            session_id: Session ID
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of message dictionaries in LLM format
        """
        # Get recent messages
        statement = (
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        messages = db.exec(statement).all()
        
        # Convert to LLM format (oldest first)
        history = []
        for msg in reversed(messages):
            role = "assistant" if msg.message_type == "dm" else "user"
            history.append({
                "role": role,
                "content": f"{msg.sender_name}: {msg.content}"
            })
        
        return history
    
    async def start_session(
        self,
        db: DBSession,
        session_id: int
    ) -> str:
        """Start a new session and generate the opening message.
        
        Args:
            db: Database session
            session_id: Session ID
            
        Returns:
            DM's opening message
            
        Raises:
            RateLimitExceeded: If rate limit is exceeded
            TokenLimitExceeded: If token limit is exceeded
        """
        # Check limits
        self._check_rate_limit(session_id)
        self._check_token_limit(session_id)
        
        # Build messages
        messages = [
            get_dm_system_message(),
            get_start_session_message()
        ]
        
        # Generate response with retry
        response = await self._generate_with_retry(messages)
        
        # Track tokens (rough estimate: 1 token ≈ 4 characters)
        estimated_tokens = sum(len(m["content"]) for m in messages) // 4
        estimated_tokens += len(response) // 4
        self._track_tokens(session_id, estimated_tokens)
        
        # Save DM message to database
        dm_message = Message(
            session_id=session_id,
            sender_name="Dungeon Master",
            content=response,
            message_type="dm"
        )
        db.add(dm_message)
        db.commit()
        
        return response
    
    async def process_player_action(
        self,
        db: DBSession,
        session_id: int,
        player_name: str,
        action: str
    ) -> str:
        """Process a player action and generate DM response.
        
        Args:
            db: Database session
            session_id: Session ID
            player_name: Name of the player
            action: Player's action/message
            
        Returns:
            DM's response
            
        Raises:
            RateLimitExceeded: If rate limit is exceeded
            TokenLimitExceeded: If token limit is exceeded
        """
        # Check limits
        self._check_rate_limit(session_id)
        self._check_token_limit(session_id)
        
        # Save player message
        player_message = Message(
            session_id=session_id,
            sender_name=player_name,
            content=action,
            message_type="player"
        )
        db.add(player_message)
        db.commit()
        
        # Build conversation with history
        messages = [get_dm_system_message()]
        history = self._get_conversation_history(db, session_id)
        messages.extend(history)
        
        # Generate response with retry
        response = await self._generate_with_retry(messages)
        
        # Track tokens
        estimated_tokens = sum(len(m["content"]) for m in messages) // 4
        estimated_tokens += len(response) // 4
        self._track_tokens(session_id, estimated_tokens)
        
        # Save DM message
        dm_message = Message(
            session_id=session_id,
            sender_name="Dungeon Master",
            content=response,
            message_type="dm"
        )
        db.add(dm_message)
        db.commit()
        
        return response
    
    async def handle_roll(
        self,
        db: DBSession,
        session_id: int,
        player_name: str,
        roll_type: str,
        result: int,
        dice: str = "1d20",
        modifier: int = 0
    ) -> str:
        """Handle a dice roll and generate DM response.
        
        Args:
            db: Database session
            session_id: Session ID
            player_name: Name of the player
            roll_type: Type of roll (e.g., "attack", "perception")
            result: Total roll result
            dice: Dice formula used
            modifier: Modifier applied
            
        Returns:
            DM's response to the roll
            
        Raises:
            RateLimitExceeded: If rate limit is exceeded
            TokenLimitExceeded: If token limit is exceeded
        """
        # Check limits
        self._check_rate_limit(session_id)
        self._check_token_limit(session_id)
        
        # Save roll message
        roll_message = Message(
            session_id=session_id,
            sender_name=player_name,
            content=f"Rolled {roll_type}: {result} ({dice} + {modifier})",
            message_type="system"
        )
        db.add(roll_message)
        db.commit()
        
        # Build conversation with roll context
        messages = [get_dm_system_message()]
        history = self._get_conversation_history(db, session_id, limit=10)
        messages.extend(history)
        
        # Add roll prompt
        roll_prompt = format_roll_prompt(roll_type, result, dice, modifier)
        messages.append({"role": "user", "content": roll_prompt})
        
        # Generate response with retry
        response = await self._generate_with_retry(messages)
        
        # Track tokens
        estimated_tokens = sum(len(m["content"]) for m in messages) // 4
        estimated_tokens += len(response) // 4
        self._track_tokens(session_id, estimated_tokens)
        
        # Save DM message
        dm_message = Message(
            session_id=session_id,
            sender_name="Dungeon Master",
            content=response,
            message_type="dm"
        )
        db.add(dm_message)
        db.commit()
        
        return response
    
    async def generate_stream(
        self,
        db: DBSession,
        session_id: int,
        player_name: str,
        action: str
    ):
        """Generate a streaming response for a player action.
        
        Args:
            db: Database session
            session_id: Session ID
            player_name: Name of the player
            action: Player's action/message
            
        Yields:
            Chunks of the DM's response
            
        Raises:
            RateLimitExceeded: If rate limit is exceeded
            TokenLimitExceeded: If token limit is exceeded
        """
        # Check limits
        self._check_rate_limit(session_id)
        self._check_token_limit(session_id)
        
        # Save player message
        player_message = Message(
            session_id=session_id,
            sender_name=player_name,
            content=action,
            message_type="player"
        )
        db.add(player_message)
        db.commit()
        
        # Build conversation with history
        messages = [get_dm_system_message()]
        history = self._get_conversation_history(db, session_id)
        messages.extend(history)
        
        # Generate streaming response
        full_response = []
        async for chunk in self.llm_provider.generate_stream(messages):
            full_response.append(chunk)
            yield chunk
        
        # Track tokens and save complete response
        response_text = "".join(full_response)
        estimated_tokens = sum(len(m["content"]) for m in messages) // 4
        estimated_tokens += len(response_text) // 4
        self._track_tokens(session_id, estimated_tokens)
        
        # Save DM message
        dm_message = Message(
            session_id=session_id,
            sender_name="Dungeon Master",
            content=response_text,
            message_type="dm"
        )
        db.add(dm_message)
        db.commit()
