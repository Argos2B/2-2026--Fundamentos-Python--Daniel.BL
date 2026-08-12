"""Provider-neutral AI assistant architecture."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class AIRequest:
    question: str
    dataset_context: dict[str, Any] | None = None
    analysis_context: dict[str, Any] | None = None
    include_data_sample: bool = False


@dataclass
class AIResponse:
    success: bool
    message: str
    provider: str


class AIProvider(ABC):
    name = "base"

    @abstractmethod
    def ask(self, request: AIRequest) -> AIResponse:
        ...


class NotConfiguredProvider(AIProvider):
    name = "not_configured"

    def ask(self, request: AIRequest) -> AIResponse:
        return AIResponse(
            success=False,
            message="Asistente IA no configurado. Selecciona un proveedor y guarda una API key en Configuracion > IA.",
            provider=self.name,
        )


class OpenAIProvider(NotConfiguredProvider):
    name = "openai"


class GeminiProvider(NotConfiguredProvider):
    name = "gemini"


class AnthropicProvider(NotConfiguredProvider):
    name = "anthropic"


class CustomProvider(NotConfiguredProvider):
    name = "custom"


class AIManager:
    """Builds structured context and delegates to a configured provider."""

    PROVIDERS = {
        "openai": OpenAIProvider,
        "gemini": GeminiProvider,
        "anthropic": AnthropicProvider,
        "custom": CustomProvider,
    }

    def __init__(self, settings: Any | None = None):
        self.settings = settings

    def provider(self) -> AIProvider:
        provider_name = self._setting("ai_provider", "not_configured")
        provider_cls = self.PROVIDERS.get(provider_name, NotConfiguredProvider)
        api_key = self._setting("ai_api_key", "")
        if not api_key:
            return NotConfiguredProvider()
        return provider_cls()

    def ask(self, question: str, data_manager: Any | None = None) -> AIResponse:
        request = AIRequest(
            question=question,
            dataset_context=self.build_dataset_context(data_manager),
            include_data_sample=bool(self._setting("ai_allow_data_samples", False)),
        )
        return self.provider().ask(request)

    def build_dataset_context(self, data_manager: Any | None) -> dict[str, Any] | None:
        if data_manager is None or not getattr(data_manager, "has_data", lambda: False)():
            return None
        if not bool(self._setting("ai_allow_dataset_context", False)):
            return None
        df = data_manager.df
        context = {
            "dataset": getattr(data_manager, "file_name", "dataset"),
            "rows": len(df),
            "columns": [str(col) for col in df.columns],
            "dtypes": {str(col): str(dtype) for col, dtype in df.dtypes.items()},
            "missing": {str(col): int(value) for col, value in df.isna().sum().items()},
        }
        if bool(self._setting("ai_allow_data_samples", False)):
            context["sample"] = df.head(5).to_dict(orient="records")
        return context

    def _setting(self, key: str, default: Any) -> Any:
        if self.settings is None:
            return default
        return self.settings.get(key, default)
