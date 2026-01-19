"""OpenAI API client wrapper with sync and async support."""

from typing import Optional, List, Dict
from openai import OpenAI, AsyncOpenAI

from test_ai.config import get_settings
from test_ai.utils.retry import with_retry, async_with_retry
from test_ai.api_clients.resilience import resilient_call, resilient_call_async


class OpenAIClient:
    """Wrapper for OpenAI API with sync and async support.

    Provides both synchronous and asynchronous methods for API calls.
    Async methods are suffixed with '_async' (e.g., generate_completion_async).
    """

    def __init__(self):
        settings = get_settings()
        self.client = OpenAI(api_key=settings.openai_api_key)
        self._async_client: Optional[AsyncOpenAI] = None

    @property
    def async_client(self) -> AsyncOpenAI:
        """Lazy-load async client on first access."""
        if self._async_client is None:
            settings = get_settings()
            self._async_client = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._async_client

    def generate_completion(
        self,
        prompt: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Generate a completion from a prompt."""
        messages: List[Dict[str, str]] = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        return self._call_api(model, messages, temperature, max_tokens)

    @resilient_call("openai")
    @with_retry(max_retries=3, base_delay=1.0, max_delay=30.0)
    def _call_api(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: Optional[int],
    ) -> str:
        """Make the actual API call with retry logic and resilience."""
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    def summarize_text(self, text: str, max_length: int = 500) -> str:
        """Summarize text using GPT."""
        prompt = f"Please provide a concise summary (max {max_length} words) of the following text:\n\n{text}"
        return self.generate_completion(
            prompt=prompt,
            system_prompt="You are a helpful assistant that creates clear, concise summaries.",
        )

    def generate_sop(self, task_description: str) -> str:
        """Generate a Standard Operating Procedure."""
        prompt = f"Create a detailed Standard Operating Procedure (SOP) for: {task_description}"
        return self.generate_completion(
            prompt=prompt,
            system_prompt="You are an expert at creating clear, detailed Standard Operating Procedures.",
        )

    # -------------------------------------------------------------------------
    # Async Methods
    # -------------------------------------------------------------------------

    async def generate_completion_async(
        self,
        prompt: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Generate a completion from a prompt (async)."""
        messages: List[Dict[str, str]] = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        return await self._call_api_async(model, messages, temperature, max_tokens)

    @resilient_call_async("openai")
    @async_with_retry(max_retries=3, base_delay=1.0, max_delay=30.0)
    async def _call_api_async(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: Optional[int],
    ) -> str:
        """Make the actual API call with retry logic and resilience (async)."""
        response = await self.async_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    async def summarize_text_async(self, text: str, max_length: int = 500) -> str:
        """Summarize text using GPT (async)."""
        prompt = f"Please provide a concise summary (max {max_length} words) of the following text:\n\n{text}"
        return await self.generate_completion_async(
            prompt=prompt,
            system_prompt="You are a helpful assistant that creates clear, concise summaries.",
        )

    async def generate_sop_async(self, task_description: str) -> str:
        """Generate a Standard Operating Procedure (async)."""
        prompt = f"Create a detailed Standard Operating Procedure (SOP) for: {task_description}"
        return await self.generate_completion_async(
            prompt=prompt,
            system_prompt="You are an expert at creating clear, detailed Standard Operating Procedures.",
        )
