"""Tests for security middleware and utilities."""

import time
import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

from llm_dungeon_master.security import (
    RateLimiter,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    validate_session_id,
    validate_character_id,
    validate_player_id,
    validate_dice_formula,
    sanitize_string,
    SessionTokenManager,
)


class TestRateLimiter:
    """Test RateLimiter class."""
    
    def test_rate_limiter_creation(self):
        """Test creating a RateLimiter."""
        limiter = RateLimiter(rate=60, burst=10)
        assert limiter.rate == 60
        assert limiter.burst == 10
    
    def test_rate_limiter_allows_initial_requests(self):
        """Test that initial requests are allowed."""
        limiter = RateLimiter(rate=60, burst=10)
        
        allowed, retry_after = limiter.is_allowed("test-key")
        assert allowed is True
        assert retry_after is None
    
    def test_rate_limiter_enforces_burst_limit(self):
        """Test that burst limit is enforced."""
        limiter = RateLimiter(rate=60, burst=5)
        
        # Use up all burst tokens
        for _ in range(5):
            allowed, _ = limiter.is_allowed("test-key")
            assert allowed is True
        
        # Next request should be denied
        allowed, retry_after = limiter.is_allowed("test-key")
        assert allowed is False
        assert retry_after is not None
        assert retry_after > 0
    
    def test_rate_limiter_tokens_refill(self):
        """Test that tokens refill over time."""
        limiter = RateLimiter(rate=120, burst=2)  # 2 tokens/second
        
        # Use both tokens
        limiter.is_allowed("test-key")
        limiter.is_allowed("test-key")
        
        # Should be denied immediately
        allowed, _ = limiter.is_allowed("test-key")
        assert allowed is False
        
        # Wait for refill
        time.sleep(1.1)
        
        # Should be allowed again
        allowed, _ = limiter.is_allowed("test-key")
        assert allowed is True
    
    def test_rate_limiter_different_keys(self):
        """Test that different keys have separate limits."""
        limiter = RateLimiter(rate=60, burst=1)
        
        # Use up key1
        limiter.is_allowed("key1")
        allowed1, _ = limiter.is_allowed("key1")
        assert allowed1 is False
        
        # key2 should still be allowed
        allowed2, _ = limiter.is_allowed("key2")
        assert allowed2 is True


class TestRateLimitMiddleware:
    """Test RateLimitMiddleware class."""
    
    @pytest.mark.asyncio
    async def test_middleware_allows_requests_under_limit(self):
        """Test middleware allows requests under rate limit."""
        limiter = RateLimiter(rate=60, burst=10)
        middleware = RateLimitMiddleware(Mock(), limiter)
        
        request = Mock(spec=Request)
        request.url.path = "/api/test"
        request.client.host = "127.0.0.1"
        
        async def call_next(req):
            response = Mock()
            response.headers = {}
            return response
        
        response = await middleware.dispatch(request, call_next)
        assert response is not None
    
    @pytest.mark.asyncio
    async def test_middleware_blocks_requests_over_limit(self):
        """Test middleware blocks requests over rate limit."""
        limiter = RateLimiter(rate=60, burst=1)
        middleware = RateLimitMiddleware(Mock(), limiter)
        
        request = Mock(spec=Request)
        request.url.path = "/api/test"
        request.client.host = "127.0.0.1"
        
        async def call_next(req):
            response = Mock()
            response.headers = {}
            return response
        
        # First request should succeed
        await middleware.dispatch(request, call_next)
        
        # Second request should be rate limited
        response = await middleware.dispatch(request, call_next)
        assert isinstance(response, JSONResponse)
        assert response.status_code == 429
    
    @pytest.mark.asyncio
    async def test_middleware_skips_health_checks(self):
        """Test middleware skips rate limiting for health checks."""
        limiter = RateLimiter(rate=60, burst=0)  # No burst tokens
        middleware = RateLimitMiddleware(Mock(), limiter)
        
        request = Mock(spec=Request)
        request.url.path = "/health"
        request.client.host = "127.0.0.1"
        
        async def call_next(req):
            response = Mock()
            response.headers = {}
            return response
        
        # Should succeed even with no burst tokens
        response = await middleware.dispatch(request, call_next)
        assert not isinstance(response, JSONResponse) or response.status_code != 429
    
    @pytest.mark.asyncio
    async def test_middleware_disabled(self):
        """Test middleware can be disabled."""
        with patch('llm_dungeon_master.security.settings') as mock_settings:
            mock_settings.rate_limit_enabled = False
            
            limiter = RateLimiter(rate=60, burst=0)
            middleware = RateLimitMiddleware(Mock(), limiter)
            
            request = Mock(spec=Request)
            request.url.path = "/api/test"
            request.client.host = "127.0.0.1"
            
            async def call_next(req):
                response = Mock()
                response.headers = {}
                return response
            
            # Should succeed even with no burst tokens
            response = await middleware.dispatch(request, call_next)
            assert response is not None


class TestSecurityHeadersMiddleware:
    """Test SecurityHeadersMiddleware class."""
    
    @pytest.mark.asyncio
    async def test_middleware_adds_security_headers(self):
        """Test middleware adds security headers."""
        middleware = SecurityHeadersMiddleware(Mock())
        
        request = Mock(spec=Request)
        
        async def call_next(req):
            response = Mock()
            response.headers = {}
            return response
        
        response = await middleware.dispatch(request, call_next)
        
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"
        assert "X-XSS-Protection" in response.headers
        assert "Strict-Transport-Security" in response.headers
    
    @pytest.mark.asyncio
    async def test_middleware_removes_server_header(self):
        """Test middleware removes server identification header."""
        middleware = SecurityHeadersMiddleware(Mock())
        
        request = Mock(spec=Request)
        
        async def call_next(req):
            response = Mock()
            response.headers = {"server": "uvicorn"}
            return response
        
        response = await middleware.dispatch(request, call_next)
        assert "server" not in response.headers


class TestInputValidation:
    """Test input validation functions."""
    
    def test_validate_session_id_valid(self):
        """Test validating valid session IDs."""
        assert validate_session_id(1) == 1
        assert validate_session_id(100) == 100
    
    def test_validate_session_id_invalid(self):
        """Test validating invalid session IDs."""
        with pytest.raises(HTTPException) as exc_info:
            validate_session_id(0)
        assert exc_info.value.status_code == 400
        
        with pytest.raises(HTTPException):
            validate_session_id(-1)
    
    def test_validate_character_id_valid(self):
        """Test validating valid character IDs."""
        assert validate_character_id(1) == 1
        assert validate_character_id(50) == 50
    
    def test_validate_character_id_invalid(self):
        """Test validating invalid character IDs."""
        with pytest.raises(HTTPException) as exc_info:
            validate_character_id(0)
        assert exc_info.value.status_code == 400
    
    def test_validate_player_id_valid(self):
        """Test validating valid player IDs."""
        assert validate_player_id(1) == 1
        assert validate_player_id(25) == 25
    
    def test_validate_player_id_invalid(self):
        """Test validating invalid player IDs."""
        with pytest.raises(HTTPException) as exc_info:
            validate_player_id(0)
        assert exc_info.value.status_code == 400
    
    def test_validate_dice_formula_valid(self):
        """Test validating valid dice formulas."""
        assert validate_dice_formula("1d20") == "1d20"
        assert validate_dice_formula("2d6+5") == "2d6+5"
        assert validate_dice_formula("3d8-2") == "3d8-2"
        assert validate_dice_formula("1d20") == "1d20"
    
    def test_validate_dice_formula_with_spaces(self):
        """Test dice formulas with spaces are accepted."""
        assert validate_dice_formula("1d20 + 5") == "1d20 + 5"
    
    def test_validate_dice_formula_invalid(self):
        """Test validating invalid dice formulas."""
        with pytest.raises(HTTPException) as exc_info:
            validate_dice_formula("invalid")
        assert exc_info.value.status_code == 400
        
        with pytest.raises(HTTPException):
            validate_dice_formula("d20")  # Missing count
        
        with pytest.raises(HTTPException):
            validate_dice_formula("1d")  # Missing sides
    
    def test_sanitize_string_valid(self):
        """Test sanitizing valid strings."""
        assert sanitize_string("Hello, world!") == "Hello, world!"
        assert sanitize_string("  spaces  ") == "spaces"
    
    def test_sanitize_string_removes_null_bytes(self):
        """Test that null bytes are removed."""
        result = sanitize_string("test\x00string")
        assert "\x00" not in result
        assert result == "teststring"
    
    def test_sanitize_string_too_long(self):
        """Test that too-long strings are rejected."""
        long_string = "a" * 1001
        with pytest.raises(HTTPException) as exc_info:
            sanitize_string(long_string, max_length=1000)
        assert exc_info.value.status_code == 400
    
    def test_sanitize_string_custom_max_length(self):
        """Test custom max length."""
        short_string = "test"
        assert sanitize_string(short_string, max_length=10) == "test"
        
        with pytest.raises(HTTPException):
            sanitize_string(short_string, max_length=3)


class TestSessionTokenManager:
    """Test SessionTokenManager class."""
    
    def test_session_token_manager_creation(self):
        """Test creating a SessionTokenManager."""
        manager = SessionTokenManager()
        assert manager is not None
        assert hasattr(manager, 'create_token')
        assert hasattr(manager, 'validate_token')
    
    def test_create_token(self):
        """Test creating a reconnection token."""
        manager = SessionTokenManager()
        
        token = manager.create_token(session_id=1, player_id=5)
        assert token is not None
        assert len(token) > 20  # Should be a long random string
    
    def test_validate_token_valid(self):
        """Test validating a valid token."""
        manager = SessionTokenManager()
        
        token = manager.create_token(session_id=1, player_id=5)
        result = manager.validate_token(token)
        
        assert result is not None
        session_id, player_id = result
        assert session_id == 1
        assert player_id == 5
    
    def test_validate_token_invalid(self):
        """Test validating an invalid token."""
        manager = SessionTokenManager()
        
        result = manager.validate_token("invalid-token")
        assert result is None
    
    def test_validate_token_expired(self):
        """Test that expired tokens are rejected."""
        with patch('llm_dungeon_master.security.settings') as mock_settings:
            mock_settings.session_timeout = -1  # Negative timeout = immediate expiry
            
            manager = SessionTokenManager()
            token = manager.create_token(session_id=1, player_id=5)
            
            # Token should be immediately expired
            result = manager.validate_token(token)
            assert result is None
    
    def test_revoke_token(self):
        """Test revoking a token."""
        manager = SessionTokenManager()
        
        token = manager.create_token(session_id=1, player_id=5)
        
        # Token should be valid before revocation
        assert manager.validate_token(token) is not None
        
        # Revoke token
        manager.revoke_token(token)
        
        # Token should be invalid after revocation
        assert manager.validate_token(token) is None
    
    def test_cleanup_expired_tokens(self):
        """Test cleaning up expired tokens."""
        with patch('llm_dungeon_master.security.settings') as mock_settings:
            mock_settings.session_timeout = -1  # Immediate expiry
            
            manager = SessionTokenManager()
            
            # Create some tokens that expire immediately
            manager.create_token(session_id=1, player_id=1)
            manager.create_token(session_id=2, player_id=2)
            manager.create_token(session_id=3, player_id=3)
            
            # Cleanup should remove all expired tokens
            removed = manager.cleanup_expired_tokens()
            assert removed == 3
    
    def test_tokens_are_unique(self):
        """Test that each token is unique."""
        manager = SessionTokenManager()
        
        token1 = manager.create_token(session_id=1, player_id=1)
        token2 = manager.create_token(session_id=1, player_id=1)
        
        assert token1 != token2


class TestSecurityIntegration:
    """Integration tests for security features."""
    
    def test_rate_limiter_and_validation_together(self):
        """Test rate limiter works with input validation."""
        limiter = RateLimiter(rate=60, burst=5)
        
        # Validate inputs
        session_id = validate_session_id(1)
        character_id = validate_character_id(5)
        
        # Check rate limit
        allowed, _ = limiter.is_allowed(f"user-{session_id}")
        assert allowed is True
    
    def test_all_validators_work(self):
        """Test all input validators work correctly."""
        # Valid inputs
        assert validate_session_id(1) == 1
        assert validate_character_id(1) == 1
        assert validate_player_id(1) == 1
        assert validate_dice_formula("1d20") == "1d20"
        assert sanitize_string("test") == "test"
        
        # Invalid inputs
        with pytest.raises(HTTPException):
            validate_session_id(0)
        with pytest.raises(HTTPException):
            validate_character_id(-1)
        with pytest.raises(HTTPException):
            validate_player_id(0)
        with pytest.raises(HTTPException):
            validate_dice_formula("invalid")
        with pytest.raises(HTTPException):
            sanitize_string("a" * 10000)
