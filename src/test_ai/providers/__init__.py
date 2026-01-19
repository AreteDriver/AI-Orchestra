"""Multi-Provider AI Support.

Provides a unified interface for multiple AI providers (OpenAI, Anthropic, etc.)
with automatic fallback and provider-agnostic operations.
"""

from .base import (
    Provider,
    ProviderConfig,
    ProviderType,
    CompletionRequest,
    CompletionResponse,
    ProviderError,
    ProviderNotConfiguredError,
    RateLimitError,
)
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .manager import (
    ProviderManager,
    get_provider,
    get_manager,
    list_providers,
    reset_manager,
)

__all__ = [
    # Base classes
    "Provider",
    "ProviderConfig",
    "ProviderType",
    "CompletionRequest",
    "CompletionResponse",
    "ProviderError",
    "ProviderNotConfiguredError",
    "RateLimitError",
    # Implementations
    "OpenAIProvider",
    "AnthropicProvider",
    # Manager
    "ProviderManager",
    "get_provider",
    "get_manager",
    "list_providers",
    "reset_manager",
]
