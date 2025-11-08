"""Tests for LLM providers."""

import pytest
from llm_dungeon_master.llm_provider import MockProvider, OpenAIProvider, get_llm_provider
from llm_dungeon_master.config import settings


@pytest.mark.asyncio
async def test_mock_provider_generate_response():
    """Test MockProvider generates responses."""
    provider = MockProvider()
    
    messages = [
        {"role": "system", "content": "You are a DM"},
        {"role": "user", "content": "I want to attack the goblin"}
    ]
    
    response = await provider.generate_response(messages)
    
    assert isinstance(response, str)
    assert len(response) > 0
    assert "attack" in response.lower()


@pytest.mark.asyncio
async def test_mock_provider_roll_response():
    """Test MockProvider responds to rolls."""
    provider = MockProvider()
    
    messages = [
        {"role": "user", "content": "I roll for initiative"}
    ]
    
    response = await provider.generate_response(messages)
    
    assert isinstance(response, str)
    assert "roll" in response.lower()


@pytest.mark.asyncio
async def test_mock_provider_look_response():
    """Test MockProvider responds to look/examine."""
    provider = MockProvider()
    
    messages = [
        {"role": "user", "content": "I look around the room"}
    ]
    
    response = await provider.generate_response(messages)
    
    assert isinstance(response, str)
    assert len(response) > 0


@pytest.mark.asyncio
async def test_mock_provider_generic_response():
    """Test MockProvider handles generic messages."""
    provider = MockProvider()
    
    messages = [
        {"role": "user", "content": "I talk to the merchant"}
    ]
    
    response = await provider.generate_response(messages)
    
    assert isinstance(response, str)
    assert len(response) > 0


@pytest.mark.asyncio
async def test_mock_provider_stream():
    """Test MockProvider streaming."""
    provider = MockProvider()
    
    messages = [
        {"role": "user", "content": "Hello"}
    ]
    
    chunks = []
    async for chunk in provider.generate_stream(messages):
        chunks.append(chunk)
    
    assert len(chunks) > 0
    assert all(isinstance(chunk, str) for chunk in chunks)
    
    # Reconstruct the message
    full_response = "".join(chunks).strip()
    assert len(full_response) > 0


def test_get_llm_provider_mock():
    """Test getting mock provider."""
    # Save original setting
    original_provider = settings.llm_provider
    
    try:
        settings.llm_provider = "mock"
        provider = get_llm_provider()
        
        assert isinstance(provider, MockProvider)
    finally:
        settings.llm_provider = original_provider


def test_get_llm_provider_openai():
    """Test getting OpenAI provider."""
    # Save original settings
    original_provider = settings.llm_provider
    original_api_key = settings.openai_api_key
    
    try:
        settings.llm_provider = "openai"
        settings.openai_api_key = "test-key-123"
        
        provider = get_llm_provider()
        
        assert isinstance(provider, OpenAIProvider)
        assert provider.client.api_key == "test-key-123"
    finally:
        settings.llm_provider = original_provider
        settings.openai_api_key = original_api_key


def test_get_llm_provider_openai_no_key():
    """Test that OpenAI provider requires API key."""
    original_provider = settings.llm_provider
    original_api_key = settings.openai_api_key
    
    try:
        settings.llm_provider = "openai"
        settings.openai_api_key = ""
        
        with pytest.raises(ValueError, match="OPENAI_API_KEY must be set"):
            get_llm_provider()
    finally:
        settings.llm_provider = original_provider
        settings.openai_api_key = original_api_key


def test_get_llm_provider_invalid():
    """Test invalid provider raises error."""
    original_provider = settings.llm_provider
    
    try:
        settings.llm_provider = "invalid"
        
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            get_llm_provider()
    finally:
        settings.llm_provider = original_provider


def test_openai_provider_initialization():
    """Test OpenAI provider can be initialized."""
    provider = OpenAIProvider(api_key="test-key", model="gpt-4")
    
    assert provider.model == "gpt-4"
    assert provider.client.api_key == "test-key"
