"""LLM provider abstraction for different AI backends."""

from abc import ABC, abstractmethod
from typing import AsyncIterator
import openai
from .config import settings


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate_response(
        self,
        messages: list[dict[str, str]],
        stream: bool = False
    ) -> str | AsyncIterator[str]:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    async def generate_stream(
        self,
        messages: list[dict[str, str]]
    ) -> AsyncIterator[str]:
        """Generate a streaming response from the LLM."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""
    
    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model
    
    async def generate_response(
        self,
        messages: list[dict[str, str]],
        stream: bool = False
    ) -> str | AsyncIterator[str]:
        """Generate a response from OpenAI."""
        if stream:
            return self.generate_stream(messages)
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.8,
            max_tokens=500
        )
        return response.choices[0].message.content or ""
    
    async def generate_stream(
        self,
        messages: list[dict[str, str]]
    ) -> AsyncIterator[str]:
        """Generate a streaming response from OpenAI."""
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.8,
            max_tokens=500,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class MockProvider(LLMProvider):
    """Mock provider for testing without API costs."""
    
    async def generate_response(
        self,
        messages: list[dict[str, str]],
        stream: bool = False
    ) -> str | AsyncIterator[str]:
        """Generate a mock response."""
        if stream:
            return self.generate_stream(messages)
        
        # Simple mock response based on the last user message
        last_message = messages[-1]["content"] if messages else ""
        
        if "roll" in last_message.lower():
            return "🎲 You rolled a 15! A solid roll. What would you like to do next?"
        elif "attack" in last_message.lower():
            return "⚔️ Your attack strikes true! The goblin staggers back, wounded but still standing."
        elif "look" in last_message.lower() or "examine" in last_message.lower():
            return "🔍 You see a dimly lit chamber with ancient stone walls. Torches flicker on the walls, casting dancing shadows."
        else:
            return f"🎭 The Dungeon Master considers your action: '{last_message}'. The adventure continues..."
    
    async def generate_stream(
        self,
        messages: list[dict[str, str]]
    ) -> AsyncIterator[str]:
        """Generate a mock streaming response."""
        response = await self.generate_response(messages, stream=False)
        
        # Simulate streaming by yielding words
        words = response.split()
        for word in words:
            yield word + " "


def get_llm_provider() -> LLMProvider:
    """Get the configured LLM provider."""
    if settings.llm_provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY must be set when using OpenAI provider")
        return OpenAIProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_model
        )
    elif settings.llm_provider == "mock":
        return MockProvider()
    else:
        raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")
