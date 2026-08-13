"""Construct the configured model provider without leaking provider dependencies."""

from ordnance_id.config import Settings
from ordnance_id.gateway.base import LLMProvider
from ordnance_id.gateway.providers.anthropic import AnthropicProvider
from ordnance_id.gateway.providers.ollama import OllamaProvider


def get_provider(settings: Settings) -> LLMProvider:
    """Create the provider selected by application settings."""

    if settings.LLM_PROVIDER == "anthropic":
        if settings.ANTHROPIC_API_KEY is None:
            raise ValueError("ANTHROPIC_API_KEY is required for the anthropic provider")
        return AnthropicProvider(
            settings.ANTHROPIC_API_KEY.get_secret_value(), settings.TEXT_MODEL
        )
    if settings.LLM_PROVIDER == "ollama":
        return OllamaProvider(settings.OLLAMA_BASE_URL, settings.TEXT_MODEL)
    raise ValueError("The openai provider is not available in Phase 0")

