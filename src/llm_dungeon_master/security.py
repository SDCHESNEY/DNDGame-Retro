"""Security middleware and utilities for LLM Dungeon Master.

Provides rate limiting, input validation, and security headers.
"""

import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Callable, Dict, Optional

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

from .config import settings


class RateLimiter:
    """Token bucket rate limiter for API endpoints."""
    
    def __init__(self, rate: int = 60, burst: int = 10):
        """Initialize rate limiter.
        
        Args:
            rate: Maximum requests per minute
            burst: Maximum burst size
        """
        self.rate = rate
        self.burst = burst
        self.buckets: Dict[str, Dict] = defaultdict(lambda: {
            "tokens": burst,
            "last_update": time.time()
        })
    
    def is_allowed(self, key: str) -> tuple[bool, Optional[int]]:
        """Check if request is allowed under rate limit.
        
        Args:
            key: Identifier for rate limiting (e.g., IP address, user ID)
            
        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        bucket = self.buckets[key]
        now = time.time()
        
        # Refill tokens based on time elapsed
        elapsed = now - bucket["last_update"]
        bucket["tokens"] = min(
            self.burst,
            bucket["tokens"] + elapsed * (self.rate / 60)
        )
        bucket["last_update"] = now
        
        # Check if request is allowed
        if bucket["tokens"] >= 1:
            bucket["tokens"] -= 1
            return True, None
        else:
            # Calculate retry-after time (ensure at least 1 second)
            retry_after = max(1, int((1 - bucket["tokens"]) / (self.rate / 60)))
            return False, retry_after


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting API requests."""
    
    def __init__(self, app, rate_limiter: Optional[RateLimiter] = None):
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter(
            rate=settings.rate_limit_per_minute,
            burst=settings.rate_limit_burst
        )
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        # Skip rate limiting if disabled
        if not settings.rate_limit_enabled:
            return await call_next(request)
        
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/ready", "/live"]:
            return await call_next(request)
        
        # Get client identifier (IP address)
        client_ip = request.client.host if request.client else "unknown"
        
        # Check rate limit
        allowed, retry_after = self.rate_limiter.is_allowed(client_ip)
        
        if not allowed:
            return JSONResponse(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "retry_after": retry_after
                },
                headers={"Retry-After": str(retry_after)}
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.rate_limiter.rate)
        response.headers["X-RateLimit-Remaining"] = str(int(self.rate_limiter.buckets[client_ip]["tokens"]))
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers to responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Remove server identification
        if "server" in response.headers:
            del response.headers["server"]
        
        return response


def validate_session_id(session_id: int) -> int:
    """Validate session ID.
    
    Args:
        session_id: Session ID to validate
        
    Returns:
        Validated session ID
        
    Raises:
        HTTPException: If session ID is invalid
    """
    if session_id < 1:
        raise HTTPException(status_code=400, detail="Invalid session ID")
    return session_id


def validate_character_id(character_id: int) -> int:
    """Validate character ID.
    
    Args:
        character_id: Character ID to validate
        
    Returns:
        Validated character ID
        
    Raises:
        HTTPException: If character ID is invalid
    """
    if character_id < 1:
        raise HTTPException(status_code=400, detail="Invalid character ID")
    return character_id


def validate_player_id(player_id: int) -> int:
    """Validate player ID.
    
    Args:
        player_id: Player ID to validate
        
    Returns:
        Validated player ID
        
    Raises:
        HTTPException: If player ID is invalid
    """
    if player_id < 1:
        raise HTTPException(status_code=400, detail="Invalid player ID")
    return player_id


def validate_dice_formula(formula: str) -> str:
    """Validate dice formula format.
    
    Args:
        formula: Dice formula (e.g., "1d20", "2d6+5")
        
    Returns:
        Validated formula
        
    Raises:
        HTTPException: If formula is invalid
    """
    import re
    
    # Basic dice formula validation
    pattern = r"^\d+d\d+([+-]\d+)?$"
    if not re.match(pattern, formula.replace(" ", "")):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid dice formula: {formula}. Expected format: XdY or XdY+Z"
        )
    
    return formula


def sanitize_string(text: str, max_length: int = 1000) -> str:
    """Sanitize user input string.
    
    Args:
        text: Input text
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
        
    Raises:
        HTTPException: If text is too long
    """
    if len(text) > max_length:
        raise HTTPException(
            status_code=400,
            detail=f"Text too long. Maximum length: {max_length}"
        )
    
    # Remove null bytes
    text = text.replace("\x00", "")
    
    return text.strip()


class SessionTokenManager:
    """Manage session tokens for reconnection."""
    
    def __init__(self):
        self.tokens: Dict[str, tuple[int, int, datetime]] = {}  # token -> (session_id, player_id, expiry)
    
    def create_token(self, session_id: int, player_id: int) -> str:
        """Create a reconnection token.
        
        Args:
            session_id: Session ID
            player_id: Player ID
            
        Returns:
            Reconnection token
        """
        import secrets
        
        token = secrets.token_urlsafe(32)
        expiry = datetime.now() + timedelta(seconds=settings.session_timeout)
        self.tokens[token] = (session_id, player_id, expiry)
        
        return token
    
    def validate_token(self, token: str) -> Optional[tuple[int, int]]:
        """Validate reconnection token.
        
        Args:
            token: Reconnection token
            
        Returns:
            Tuple of (session_id, player_id) if valid, None otherwise
        """
        if token not in self.tokens:
            return None
        
        session_id, player_id, expiry = self.tokens[token]
        
        # Check if token is expired
        if datetime.now() > expiry:
            del self.tokens[token]
            return None
        
        return session_id, player_id
    
    def revoke_token(self, token: str) -> None:
        """Revoke a reconnection token.
        
        Args:
            token: Token to revoke
        """
        if token in self.tokens:
            del self.tokens[token]
    
    def cleanup_expired_tokens(self) -> int:
        """Remove expired tokens.
        
        Returns:
            Number of tokens removed
        """
        now = datetime.now()
        expired = [
            token for token, (_, _, expiry) in self.tokens.items()
            if now > expiry
        ]
        
        for token in expired:
            del self.tokens[token]
        
        return len(expired)


# Global instances
rate_limiter = RateLimiter()
session_token_manager = SessionTokenManager()
