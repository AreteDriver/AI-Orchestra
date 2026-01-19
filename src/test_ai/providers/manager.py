"""Provider manager for multi-provider support."""

from __future__ import annotations

import logging
from typing import Any

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


logger = logging.getLogger(__name__)

# Global manager instance
_manager: ProviderManager | None = None


class ProviderManager:
    """Manages multiple AI providers with fallback support.

    Provides a unified interface for:
    - Registering and configuring providers
    - Automatic fallback when a provider fails
    - Provider-agnostic completions
    """

    PROVIDER_CLASSES: dict[ProviderType, type[Provider]] = {
        ProviderType.OPENAI: OpenAIProvider,
        ProviderType.ANTHROPIC: AnthropicProvider,
    }

    def __init__(self):
        """Initialize provider manager."""
        self._providers: dict[str, Provider] = {}
        self._default_provider: str | None = None
        self._fallback_order: list[str] = []

    def register(
        self,
        name: str,
        provider: Provider | None = None,
        config: ProviderConfig | None = None,
        provider_type: ProviderType | None = None,
        api_key: str | None = None,
        set_default: bool = False,
    ) -> Provider:
        """Register a provider.

        Args:
            name: Name to register provider under
            provider: Pre-configured provider instance
            config: Provider configuration
            provider_type: Type of provider to create
            api_key: API key for the provider
            set_default: Whether to set as default provider

        Returns:
            Registered provider

        Raises:
            ValueError: If neither provider nor provider_type specified
        """
        if provider is not None:
            self._providers[name] = provider
        elif provider_type is not None:
            if provider_type not in self.PROVIDER_CLASSES:
                raise ValueError(f"Unknown provider type: {provider_type}")

            provider_class = self.PROVIDER_CLASSES[provider_type]

            if config is None:
                config = ProviderConfig(provider_type=provider_type, api_key=api_key)

            self._providers[name] = provider_class(config=config)
        elif config is not None:
            if config.provider_type not in self.PROVIDER_CLASSES:
                raise ValueError(f"Unknown provider type: {config.provider_type}")

            provider_class = self.PROVIDER_CLASSES[config.provider_type]
            self._providers[name] = provider_class(config=config)
        else:
            raise ValueError("Must specify provider, provider_type, or config")

        if set_default or self._default_provider is None:
            self._default_provider = name

        if name not in self._fallback_order:
            self._fallback_order.append(name)

        return self._providers[name]

    def unregister(self, name: str) -> None:
        """Unregister a provider.

        Args:
            name: Provider name to unregister
        """
        if name in self._providers:
            del self._providers[name]

        if name in self._fallback_order:
            self._fallback_order.remove(name)

        if self._default_provider == name:
            self._default_provider = (
                self._fallback_order[0] if self._fallback_order else None
            )

    def get(self, name: str) -> Provider | None:
        """Get a provider by name.

        Args:
            name: Provider name

        Returns:
            Provider or None if not found
        """
        return self._providers.get(name)

    def get_default(self) -> Provider | None:
        """Get the default provider.

        Returns:
            Default provider or None if none registered
        """
        if self._default_provider:
            return self._providers.get(self._default_provider)
        return None

    def set_default(self, name: str) -> None:
        """Set the default provider.

        Args:
            name: Provider name

        Raises:
            ValueError: If provider not registered
        """
        if name not in self._providers:
            raise ValueError(f"Provider not registered: {name}")
        self._default_provider = name

    def set_fallback_order(self, order: list[str]) -> None:
        """Set the fallback order for providers.

        Args:
            order: List of provider names in fallback order

        Raises:
            ValueError: If any provider not registered
        """
        for name in order:
            if name not in self._providers:
                raise ValueError(f"Provider not registered: {name}")
        self._fallback_order = order.copy()

    def list_providers(self) -> list[str]:
        """List registered provider names.

        Returns:
            List of provider names
        """
        return list(self._providers.keys())

    def list_configured(self) -> list[str]:
        """List providers that are properly configured.

        Returns:
            List of configured provider names
        """
        return [
            name
            for name, provider in self._providers.items()
            if provider.is_configured()
        ]

    def complete(
        self,
        request: CompletionRequest,
        provider_name: str | None = None,
        use_fallback: bool = True,
    ) -> CompletionResponse:
        """Generate a completion using registered providers.

        Args:
            request: Completion request
            provider_name: Specific provider to use (None = default)
            use_fallback: Whether to try fallback providers on failure

        Returns:
            Completion response

        Raises:
            ProviderNotConfiguredError: If no providers configured
            ProviderError: If all providers fail
        """
        if not self._providers:
            raise ProviderNotConfiguredError("No providers registered")

        # Determine provider order
        if provider_name:
            providers_to_try = [provider_name]
            if use_fallback:
                providers_to_try.extend(
                    [p for p in self._fallback_order if p != provider_name]
                )
        elif self._default_provider:
            providers_to_try = [self._default_provider]
            if use_fallback:
                providers_to_try.extend(
                    [p for p in self._fallback_order if p != self._default_provider]
                )
        else:
            providers_to_try = self._fallback_order.copy()

        last_error: Exception | None = None

        for name in providers_to_try:
            provider = self._providers.get(name)
            if not provider:
                continue

            try:
                logger.debug(f"Attempting completion with provider: {name}")
                return provider.complete(request)
            except RateLimitError as e:
                logger.warning(f"Rate limit hit for {name}: {e}")
                last_error = e
                if not use_fallback:
                    raise
            except ProviderError as e:
                logger.warning(f"Provider {name} failed: {e}")
                last_error = e
                if not use_fallback:
                    raise
            except Exception as e:
                logger.error(f"Unexpected error from {name}: {e}")
                last_error = e
                if not use_fallback:
                    raise ProviderError(f"Provider error: {e}")

        raise ProviderError(f"All providers failed. Last error: {last_error}")

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        provider_name: str | None = None,
        use_fallback: bool = True,
        **kwargs: Any,
    ) -> str:
        """Convenience method for simple text generation.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            model: Model to use
            provider_name: Specific provider to use
            use_fallback: Whether to try fallback providers
            **kwargs: Additional request parameters

        Returns:
            Generated text
        """
        request = CompletionRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            **kwargs,
        )
        response = self.complete(
            request, provider_name=provider_name, use_fallback=use_fallback
        )
        return response.content

    def health_check(self, provider_name: str | None = None) -> dict[str, bool]:
        """Check health of providers.

        Args:
            provider_name: Specific provider to check (None = all)

        Returns:
            Dict mapping provider names to health status
        """
        if provider_name:
            provider = self._providers.get(provider_name)
            if provider:
                return {provider_name: provider.health_check()}
            return {provider_name: False}

        return {name: provider.health_check() for name, provider in self._providers.items()}


def get_manager() -> ProviderManager:
    """Get the global provider manager instance.

    Returns:
        Global ProviderManager instance
    """
    global _manager
    if _manager is None:
        _manager = ProviderManager()
    return _manager


def reset_manager() -> None:
    """Reset the global provider manager instance."""
    global _manager
    _manager = None


def get_provider(name: str | None = None) -> Provider | None:
    """Get a provider from the global manager.

    Args:
        name: Provider name (None = default)

    Returns:
        Provider or None if not found
    """
    manager = get_manager()
    if name:
        return manager.get(name)
    return manager.get_default()


def list_providers() -> list[str]:
    """List registered providers in the global manager.

    Returns:
        List of provider names
    """
    return get_manager().list_providers()
