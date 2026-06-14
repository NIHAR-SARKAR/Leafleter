"""Azure OpenAI provider adapter with comprehensive deployment support.

Supports all Azure-hosted model families and API patterns:

* Legacy Azure OpenAI (pre-v1): ``/openai/deployments/{deployment}/chat/completions``
* Modern Azure OpenAI v1: ``/openai/v1/chat/completions``
* OpenAI Responses API: ``/openai/v1/responses``
* Azure AI Foundry unified inference: ``/chat/completions``

Supported model families include OpenAI GPT-5.x, o-series reasoning, GPT-4.x,
and non-OpenAI models hosted through Azure AI Foundry such as DeepSeek,
Meta Llama, Mistral, Cohere, Phi, NVIDIA Nemotron, Grok, Kimi, Jamba,
MiniMax, and others.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

import httpx

from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.providers.base import BaseProvider, ProviderResponse, ProviderUsage

logger = get_logger(__name__)

DEFAULT_API_VERSION = "2024-12-01-preview"
DEFAULT_RESPONSES_API_VERSION = "2025-04-01-preview"
DEFAULT_TIMEOUT = httpx.Timeout(120.0, connect=10.0)


class AzureAPIPattern(StrEnum):
    """Azure API endpoint patterns."""

    AZURE_OPENAI_LEGACY = "azure_openai_legacy"
    AZURE_OPENAI_V1 = "azure_openai_v1"
    AZURE_RESPONSES = "azure_responses"
    AZURE_AI_FOUNDRY = "azure_ai_foundry"


class AzureOpenAIProvider(BaseProvider):
    """Provider adapter for Azure OpenAI and Azure AI Foundry.

    The adapter automatically selects the correct URL pattern and request body
    shape based on the model/deployment name. Users may override this behavior
    via ``config`` fields such as ``api_pattern`` or ``use_responses_api``.
    """

    provider_type = "azure_openai"
    supports_streaming = True
    supports_structured_output = True
    default_model = "gpt-4.1"

    # Model family registry mapping prefixes to supported API patterns and
    # request/response conventions.
    _MODEL_REGISTRY: dict[str, dict[str, Any]] = {
        # GPT-5.x series
        "gpt-5.5": {
            "patterns": [AzureAPIPattern.AZURE_OPENAI_V1, AzureAPIPattern.AZURE_RESPONSES],
            "default": AzureAPIPattern.AZURE_OPENAI_V1,
            "prefers_developer_role": True,
            "uses_max_completion_tokens": True,
            "supports_reasoning_effort": True,
        },
        "gpt-5.4": {
            "patterns": [AzureAPIPattern.AZURE_OPENAI_V1, AzureAPIPattern.AZURE_RESPONSES],
            "default": AzureAPIPattern.AZURE_OPENAI_V1,
            "prefers_developer_role": True,
            "uses_max_completion_tokens": True,
            "supports_reasoning_effort": True,
        },
        "gpt-5.3-codex": {
            "patterns": [AzureAPIPattern.AZURE_RESPONSES, AzureAPIPattern.AZURE_OPENAI_V1],
            "default": AzureAPIPattern.AZURE_RESPONSES,
            "prefers_developer_role": True,
            "uses_max_completion_tokens": True,
            "supports_reasoning_effort": True,
        },
        "gpt-5.3-chat": {
            "patterns": [AzureAPIPattern.AZURE_OPENAI_V1, AzureAPIPattern.AZURE_RESPONSES],
            "default": AzureAPIPattern.AZURE_OPENAI_V1,
            "prefers_developer_role": True,
            "uses_max_completion_tokens": True,
            "supports_reasoning_effort": True,
        },
        "gpt-5.2-codex": {
            "patterns": [AzureAPIPattern.AZURE_RESPONSES, AzureAPIPattern.AZURE_OPENAI_V1],
            "default": AzureAPIPattern.AZURE_RESPONSES,
            "prefers_developer_role": True,
            "uses_max_completion_tokens": True,
            "supports_reasoning_effort": True,
        },
        "gpt-5.2-chat": {
            "patterns": [AzureAPIPattern.AZURE_OPENAI_V1, AzureAPIPattern.AZURE_RESPONSES],
            "default": AzureAPIPattern.AZURE_OPENAI_V1,
            "prefers_developer_role": True,
            "uses_max_completion_tokens": True,
            "supports_reasoning_effort": True,
        },
        "gpt-5.2": {
            "patterns": [AzureAPIPattern.AZURE_OPENAI_V1, AzureAPIPattern.AZURE_RESPONSES],
            "default": AzureAPIPattern.AZURE_OPENAI_V1,
            "prefers_developer_role": True,
            "uses_max_completion_tokens": True,
            "supports_reasoning_effort": True,
        },
        "gpt-5.1-codex-max": {
            "patterns": [AzureAPIPattern.AZURE_RESPONSES, AzureAPIPattern.AZURE_OPENAI_V1],
            "default": AzureAPIPattern.AZURE_RESPONSES,
            "prefers_developer_role": True,
            "uses_max_completion_tokens": True,
            "supports_reasoning_effort": True,
        },
        "gpt-5.1-codex": {
            "patterns": [AzureAPIPattern.AZURE_RESPONSES, AzureAPIPattern.AZURE_OPENAI_V1],
            "default": AzureAPIPattern.AZURE_RESPONSES,
            "prefers_developer_role": True,
            "uses_max_completion_tokens": True,
            "supports_reasoning_effort": True,
        },
        "gpt-5.1-codex-mini": {
            "patterns": [AzureAPIPattern.AZURE_RESPONSES, AzureAPIPattern.AZURE_OPENAI_V1],
            "default": AzureAPIPattern.AZURE_RESPONSES,
            "prefers_developer_role": True,
            "uses_max_completion_tokens": True,
            "supports_reasoning_effort": True,
        },
        "gpt-5.1-chat": {
            "patterns": [AzureAPIPattern.AZURE_OPENAI_V1, AzureAPIPattern.AZURE_RESPONSES],
            "default": AzureAPIPattern.AZURE_OPENAI_V1,
            "prefers_developer_role": True,
            "uses_max_completion_tokens": True,
            "supports_reasoning_effort": True,
        },
        "gpt-5.1": {
            "patterns": [AzureAPIPattern.AZURE_OPENAI_V1, AzureAPIPattern.AZURE_RESPONSES],
            "default": AzureAPIPattern.AZURE_OPENAI_V1,
            "prefers_developer_role": True,
            "uses_max_completion_tokens": True,
            "supports_reasoning_effort": True,
        },
        "gpt-5-pro": {
            "patterns": [AzureAPIPattern.AZURE_OPENAI_V1, AzureAPIPattern.AZURE_RESPONSES],
            "default": AzureAPIPattern.AZURE_OPENAI_V1,
            "prefers_developer_role": True,
            "uses_max_completion_tokens": True,
            "supports_reasoning_effort": True,
        },
        "gpt-5-codex": {
            "patterns": [AzureAPIPattern.AZURE_RESPONSES, AzureAPIPattern.AZURE_OPENAI_V1],
            "default": AzureAPIPattern.AZURE_RESPONSES,
            "prefers_developer_role": True,
            "uses_max_completion_tokens": True,
            "supports_reasoning_effort": True,
        },
        "gpt-5": {
            "patterns": [AzureAPIPattern.AZURE_OPENAI_V1, AzureAPIPattern.AZURE_RESPONSES],
            "default": AzureAPIPattern.AZURE_OPENAI_V1,
            "prefers_developer_role": True,
            "uses_max_completion_tokens": True,
            "supports_reasoning_effort": True,
        },
        "gpt-5-mini": {
            "patterns": [AzureAPIPattern.AZURE_OPENAI_V1, AzureAPIPattern.AZURE_RESPONSES],
            "default": AzureAPIPattern.AZURE_OPENAI_V1,
            "prefers_developer_role": True,
            "uses_max_completion_tokens": True,
            "supports_reasoning_effort": True,
        },
        "gpt-5-nano": {
            "patterns": [AzureAPIPattern.AZURE_OPENAI_V1, AzureAPIPattern.AZURE_RESPONSES],
            "default": AzureAPIPattern.AZURE_OPENAI_V1,
            "prefers_developer_role": True,
            "uses_max_completion_tokens": True,
            "supports_reasoning_effort": True,
        },
        # o-series reasoning models
        "o4-mini": {
            "patterns": [AzureAPIPattern.AZURE_OPENAI_V1, AzureAPIPattern.AZURE_RESPONSES],
            "default": AzureAPIPattern.AZURE_OPENAI_V1,
            "prefers_developer_role": True,
            "uses_max_completion_tokens": True,
            "supports_reasoning_effort": True,
        },
        "o4": {
            "patterns": [AzureAPIPattern.AZURE_OPENAI_V1, AzureAPIPattern.AZURE_RESPONSES],
            "default": AzureAPIPattern.AZURE_OPENAI_V1,
            "prefers_developer_role": True,
            "uses_max_completion_tokens": True,
            "supports_reasoning_effort": True,
        },
        "o3-pro": {
            "patterns": [AzureAPIPattern.AZURE_OPENAI_V1, AzureAPIPattern.AZURE_RESPONSES],
            "default": AzureAPIPattern.AZURE_OPENAI_V1,
            "prefers_developer_role": True,
            "uses_max_completion_tokens": True,
            "supports_reasoning_effort": True,
        },
        "o3-mini": {
            "patterns": [AzureAPIPattern.AZURE_OPENAI_V1, AzureAPIPattern.AZURE_RESPONSES],
            "default": AzureAPIPattern.AZURE_OPENAI_V1,
            "prefers_developer_role": True,
            "uses_max_completion_tokens": True,
            "supports_reasoning_effort": True,
        },
        "o3": {
            "patterns": [AzureAPIPattern.AZURE_OPENAI_V1, AzureAPIPattern.AZURE_RESPONSES],
            "default": AzureAPIPattern.AZURE_OPENAI_V1,
            "prefers_developer_role": True,
            "uses_max_completion_tokens": True,
            "supports_reasoning_effort": True,
        },
        "o1-mini": {
            "patterns": [AzureAPIPattern.AZURE_OPENAI_V1, AzureAPIPattern.AZURE_RESPONSES],
            "default": AzureAPIPattern.AZURE_OPENAI_V1,
            "prefers_developer_role": True,
            "uses_max_completion_tokens": True,
            "supports_reasoning_effort": False,
        },
        "o1": {
            "patterns": [AzureAPIPattern.AZURE_OPENAI_V1, AzureAPIPattern.AZURE_RESPONSES],
            "default": AzureAPIPattern.AZURE_OPENAI_V1,
            "prefers_developer_role": True,
            "uses_max_completion_tokens": True,
            "supports_reasoning_effort": True,
        },
        # GPT-4.x series
        "gpt-4.1-nano": {
            "patterns": [AzureAPIPattern.AZURE_OPENAI_V1, AzureAPIPattern.AZURE_OPENAI_LEGACY],
            "default": AzureAPIPattern.AZURE_OPENAI_V1,
            "prefers_developer_role": False,
            "uses_max_completion_tokens": False,
            "supports_reasoning_effort": False,
        },
        "gpt-4.1-mini": {
            "patterns": [AzureAPIPattern.AZURE_OPENAI_V1, AzureAPIPattern.AZURE_OPENAI_LEGACY],
            "default": AzureAPIPattern.AZURE_OPENAI_V1,
            "prefers_developer_role": False,
            "uses_max_completion_tokens": False,
            "supports_reasoning_effort": False,
        },
        "gpt-4.1": {
            "patterns": [AzureAPIPattern.AZURE_OPENAI_V1, AzureAPIPattern.AZURE_OPENAI_LEGACY],
            "default": AzureAPIPattern.AZURE_OPENAI_V1,
            "prefers_developer_role": False,
            "uses_max_completion_tokens": False,
            "supports_reasoning_effort": False,
        },
        "gpt-4o-mini": {
            "patterns": [AzureAPIPattern.AZURE_OPENAI_V1, AzureAPIPattern.AZURE_OPENAI_LEGACY],
            "default": AzureAPIPattern.AZURE_OPENAI_V1,
            "prefers_developer_role": False,
            "uses_max_completion_tokens": False,
            "supports_reasoning_effort": False,
        },
        "gpt-4o": {
            "patterns": [AzureAPIPattern.AZURE_OPENAI_V1, AzureAPIPattern.AZURE_OPENAI_LEGACY],
            "default": AzureAPIPattern.AZURE_OPENAI_V1,
            "prefers_developer_role": False,
            "uses_max_completion_tokens": False,
            "supports_reasoning_effort": False,
        },
        "gpt-4-turbo": {
            "patterns": [AzureAPIPattern.AZURE_OPENAI_LEGACY, AzureAPIPattern.AZURE_OPENAI_V1],
            "default": AzureAPIPattern.AZURE_OPENAI_LEGACY,
            "prefers_developer_role": False,
            "uses_max_completion_tokens": False,
            "supports_reasoning_effort": False,
        },
        "gpt-4": {
            "patterns": [AzureAPIPattern.AZURE_OPENAI_LEGACY, AzureAPIPattern.AZURE_OPENAI_V1],
            "default": AzureAPIPattern.AZURE_OPENAI_LEGACY,
            "prefers_developer_role": False,
            "uses_max_completion_tokens": False,
            "supports_reasoning_effort": False,
        },
        # Azure AI Foundry / non-OpenAI models
        "deepseek": {"patterns": [AzureAPIPattern.AZURE_AI_FOUNDRY], "default": AzureAPIPattern.AZURE_AI_FOUNDRY},
        "llama": {"patterns": [AzureAPIPattern.AZURE_AI_FOUNDRY], "default": AzureAPIPattern.AZURE_AI_FOUNDRY},
        "meta-llama": {"patterns": [AzureAPIPattern.AZURE_AI_FOUNDRY], "default": AzureAPIPattern.AZURE_AI_FOUNDRY},
        "mistral": {"patterns": [AzureAPIPattern.AZURE_AI_FOUNDRY], "default": AzureAPIPattern.AZURE_AI_FOUNDRY},
        "cohere": {"patterns": [AzureAPIPattern.AZURE_AI_FOUNDRY], "default": AzureAPIPattern.AZURE_AI_FOUNDRY},
        "phi": {"patterns": [AzureAPIPattern.AZURE_AI_FOUNDRY], "default": AzureAPIPattern.AZURE_AI_FOUNDRY},
        "nemotron": {"patterns": [AzureAPIPattern.AZURE_AI_FOUNDRY], "default": AzureAPIPattern.AZURE_AI_FOUNDRY},
        "grok": {"patterns": [AzureAPIPattern.AZURE_AI_FOUNDRY], "default": AzureAPIPattern.AZURE_AI_FOUNDRY},
        "jamba": {"patterns": [AzureAPIPattern.AZURE_AI_FOUNDRY], "default": AzureAPIPattern.AZURE_AI_FOUNDRY},
        "minimax": {"patterns": [AzureAPIPattern.AZURE_AI_FOUNDRY], "default": AzureAPIPattern.AZURE_AI_FOUNDRY},
        "kimi": {"patterns": [AzureAPIPattern.AZURE_AI_FOUNDRY], "default": AzureAPIPattern.AZURE_AI_FOUNDRY},
        "claude": {"patterns": [AzureAPIPattern.AZURE_AI_FOUNDRY], "default": AzureAPIPattern.AZURE_AI_FOUNDRY},
        "anthropic": {"patterns": [AzureAPIPattern.AZURE_AI_FOUNDRY], "default": AzureAPIPattern.AZURE_AI_FOUNDRY},
        "gpt-oss": {"patterns": [AzureAPIPattern.AZURE_AI_FOUNDRY], "default": AzureAPIPattern.AZURE_AI_FOUNDRY},
        "qwen": {"patterns": [AzureAPIPattern.AZURE_AI_FOUNDRY], "default": AzureAPIPattern.AZURE_AI_FOUNDRY},
        "granite": {"patterns": [AzureAPIPattern.AZURE_AI_FOUNDRY], "default": AzureAPIPattern.AZURE_AI_FOUNDRY},
        "command": {"patterns": [AzureAPIPattern.AZURE_AI_FOUNDRY], "default": AzureAPIPattern.AZURE_AI_FOUNDRY},
        "wizard": {"patterns": [AzureAPIPattern.AZURE_AI_FOUNDRY], "default": AzureAPIPattern.AZURE_AI_FOUNDRY},
        "falcon": {"patterns": [AzureAPIPattern.AZURE_AI_FOUNDRY], "default": AzureAPIPattern.AZURE_AI_FOUNDRY},
        "mamba": {"patterns": [AzureAPIPattern.AZURE_AI_FOUNDRY], "default": AzureAPIPattern.AZURE_AI_FOUNDRY},
        "nous": {"patterns": [AzureAPIPattern.AZURE_AI_FOUNDRY], "default": AzureAPIPattern.AZURE_AI_FOUNDRY},
        "yi": {"patterns": [AzureAPIPattern.AZURE_AI_FOUNDRY], "default": AzureAPIPattern.AZURE_AI_FOUNDRY},
        "baichuan": {"patterns": [AzureAPIPattern.AZURE_AI_FOUNDRY], "default": AzureAPIPattern.AZURE_AI_FOUNDRY},
    }

    def _validate_config(self) -> None:
        """Validate Azure configuration and initialize the HTTP client."""
        self.api_key = self.config.get("api_key", "")
        self.api_base = self.config.get("api_base", "")
        self.api_version = self.config.get("api_version", DEFAULT_API_VERSION)

        self.deployment = self.config.get("deployment", self.default_model)
        self.api_pattern = self.config.get("api_pattern")
        self.use_responses_api = self.config.get("use_responses_api")
        self.model_name = self.config.get("model_name", self.deployment)

        self.responses_api_version = self.config.get(
            "responses_api_version",
            DEFAULT_RESPONSES_API_VERSION,
        )
        self.v1_api_version = self.config.get("v1_api_version", "")

        self.reasoning_effort = self.config.get("reasoning_effort")
        self.verbosity = self.config.get("verbosity")

        if not self.api_key or not self.api_base:
            raise ValueError("Azure OpenAI API key and endpoint are required")

        self._client = httpx.AsyncClient(
            headers={
                "api-key": self.api_key,
                "Content-Type": "application/json",
            },
            timeout=DEFAULT_TIMEOUT,
        )

    async def chat_completion(
        self,
        *,
        messages: list[dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        response_format: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> ProviderResponse:
        """Execute a chat completion request against Azure.

        The URL and payload are chosen automatically based on the model name and
        the provider configuration.
        """
        deployment = model or self.deployment or self.default_model
        config = self._detect_model_config(deployment)
        pattern = self._resolve_pattern(config)

        url = self._get_url(deployment, pattern)
        request_messages = self._build_messages(config, messages)
        payload = self._build_request_body(
            pattern=pattern,
            config=config,
            messages=request_messages,
            deployment=deployment,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
        )

        logger.info(
            "azure_chat_request",
            model=deployment,
            pattern=pattern.value,
            messages=len(messages),
        )

        try:
            response = await self._client.post(url, json=payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "azure_http_error",
                status_code=exc.response.status_code,
                body=exc.response.text,
                pattern=pattern.value,
            )
            raise AppException(
                "Azure AI provider returned an error",
                status_code=exc.response.status_code,
            ) from exc
        except httpx.RequestError as exc:
            logger.error(
                "azure_request_error",
                error=str(exc),
                pattern=pattern.value,
            )
            raise AppException("Failed to reach Azure AI provider") from exc

        data = response.json()
        content, finish_reason = self._parse_response(data, pattern)
        usage = self._parse_usage(data, deployment)

        return ProviderResponse(
            content=content,
            raw_response=data,
            usage=usage,
            finish_reason=finish_reason,
        )

    async def list_models(self) -> list[dict[str, Any]]:
        """Return supported Azure OpenAI / AI Foundry models.

        Azure does not expose a universal model list endpoint, so this returns a
        curated default catalog. Subclasses or future versions can call the Azure
        model listing APIs when available.
        """
        return [
            {"id": "gpt-4.1", "name": "GPT-4.1", "context_window": 128000},
            {"id": "gpt-4.1-mini", "name": "GPT-4.1 Mini", "context_window": 128000},
            {"id": "gpt-4.1-nano", "name": "GPT-4.1 Nano", "context_window": 128000},
            {"id": "gpt-4o", "name": "GPT-4o", "context_window": 128000},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "context_window": 128000},
            {"id": "gpt-4", "name": "GPT-4", "context_window": 8192},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "context_window": 128000},
            {"id": "gpt-5", "name": "GPT-5", "context_window": 128000},
            {"id": "gpt-5-mini", "name": "GPT-5 Mini", "context_window": 128000},
            {"id": "gpt-5-nano", "name": "GPT-5 Nano", "context_window": 128000},
            {"id": "o1", "name": "o1", "context_window": 128000},
            {"id": "o1-mini", "name": "o1-mini", "context_window": 128000},
            {"id": "o3", "name": "o3", "context_window": 128000},
            {"id": "o3-mini", "name": "o3-mini", "context_window": 128000},
            {"id": "o4-mini", "name": "o4-mini", "context_window": 128000},
            {"id": "deepseek-r1", "name": "DeepSeek R1", "context_window": 128000},
            {"id": "llama-3.3-70b", "name": "Meta Llama 3.3 70B", "context_window": 128000},
            {"id": "mistral-large", "name": "Mistral Large", "context_window": 128000},
            {"id": "phi-4", "name": "Phi-4", "context_window": 128000},
        ]

    async def validate_credentials(self) -> bool:
        """Validate credentials by attempting a minimal chat completion."""
        try:
            deployment = self.deployment or self.default_model
            pattern = self._resolve_pattern(self._detect_model_config(deployment))
            url = self._get_url(deployment, pattern)
            body = self._build_request_body(
                pattern=pattern,
                config=self._detect_model_config(deployment),
                messages=self._build_messages(
                    self._detect_model_config(deployment),
                    [{"role": "user", "content": "Hi"}],
                ),
                deployment=deployment,
                temperature=None,
                max_tokens=1,
                response_format=None,
            )
            response = await self._client.post(url, json=body)
            response.raise_for_status()
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("azure_credential_validation_failed", error=str(exc))
            return False

    def _detect_model_config(self, model_or_deployment: str) -> dict[str, Any]:
        """Detect model family configuration from the deployment/model name."""
        if self.api_pattern:
            return {
                "patterns": [AzureAPIPattern(self.api_pattern)],
                "default": AzureAPIPattern(self.api_pattern),
                "prefers_developer_role": False,
                "uses_max_completion_tokens": False,
                "supports_reasoning_effort": False,
            }

        normalized = model_or_deployment.lower().replace("_", "-").replace(" ", "-")

        best_match: str | None = None
        best_len = 0
        for prefix in self._MODEL_REGISTRY:
            prefix_normalized = prefix.lower()
            if normalized.startswith(prefix_normalized) and len(prefix_normalized) > best_len:
                best_match = prefix
                best_len = len(prefix_normalized)

        if best_match:
            return self._MODEL_REGISTRY[best_match]

        for prefix, config in self._MODEL_REGISTRY.items():
            if prefix.lower() in normalized:
                return config

        return {
            "patterns": [AzureAPIPattern.AZURE_OPENAI_LEGACY],
            "default": AzureAPIPattern.AZURE_OPENAI_LEGACY,
            "prefers_developer_role": False,
            "uses_max_completion_tokens": False,
            "supports_reasoning_effort": False,
        }

    def _resolve_pattern(self, config: dict[str, Any]) -> AzureAPIPattern:
        """Resolve the API pattern to use for the request."""
        if self.api_pattern:
            return AzureAPIPattern(self.api_pattern)

        if self.use_responses_api is not None:
            if self.use_responses_api and AzureAPIPattern.AZURE_RESPONSES in config["patterns"]:
                return AzureAPIPattern.AZURE_RESPONSES
            if (
                not self.use_responses_api
                and AzureAPIPattern.AZURE_OPENAI_V1 in config["patterns"]
            ):
                return AzureAPIPattern.AZURE_OPENAI_V1

        return config["default"]

    def _get_url(self, deployment: str, pattern: AzureAPIPattern) -> str:
        """Build the Azure API URL based on the selected pattern."""
        base = self.api_base.rstrip("/")

        if pattern == AzureAPIPattern.AZURE_OPENAI_LEGACY:
            return (
                f"{base}/openai/deployments/{deployment}/chat/completions"
                f"?api-version={self.api_version}"
            )

        if pattern == AzureAPIPattern.AZURE_OPENAI_V1:
            if "/openai/v1" not in base:
                base = f"{base}/openai/v1"
            url = f"{base}/chat/completions"
            if self.v1_api_version:
                url += f"?api-version={self.v1_api_version}"
            return url

        if pattern == AzureAPIPattern.AZURE_RESPONSES:
            if "/openai/v1" not in base:
                base = f"{base}/openai/v1"
            return f"{base}/responses?api-version={self.responses_api_version}"

        if pattern == AzureAPIPattern.AZURE_AI_FOUNDRY:
            if ".services.ai.azure.com" in base or (
                ".azure.com" in base and ".openai.azure.com" not in base
            ):
                return f"{base}/chat/completions"
            if "/openai/v1" not in base:
                base = f"{base}/openai/v1"
            return f"{base}/chat/completions"

        raise AppException(f"Unsupported Azure API pattern: {pattern}")

    def _build_messages(
        self,
        config: dict[str, Any],
        messages: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        """Normalize message roles (system -> developer when required)."""
        prefers_developer = config.get("prefers_developer_role", False)
        normalized: list[dict[str, str]] = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            if prefers_developer and role == "system":
                role = "developer"
            normalized.append({"role": role, "content": content})
        return normalized

    def _build_request_body(
        self,
        *,
        pattern: AzureAPIPattern,
        config: dict[str, Any],
        messages: list[dict[str, str]],
        deployment: str,
        temperature: float | None,
        max_tokens: int | None,
        response_format: dict[str, str] | None,
    ) -> dict[str, Any]:
        """Build the request payload based on the API pattern."""
        if pattern == AzureAPIPattern.AZURE_RESPONSES:
            inputs: list[dict[str, str]] = []
            for message in messages:
                role = message["role"]
                if role in ("system", "developer"):
                    role = "developer"
                inputs.append({"role": role, "content": message["content"]})

            body: dict[str, Any] = {
                "model": deployment,
                "input": inputs,
            }

            if max_tokens is not None and max_tokens > 0:
                body["max_output_tokens"] = max_tokens

            if response_format:
                body["text"] = {"format": response_format}

            if config.get("supports_reasoning_effort") and self.reasoning_effort:
                body["reasoning"] = {"effort": self.reasoning_effort}

            if self.verbosity:
                body["verbosity"] = self.verbosity

            # Strip parameters rejected by the Responses API.
            body.pop("max_tokens", None)
            body.pop("temperature", None)
            body.pop("top_p", None)
            body.pop("frequency_penalty", None)
            body.pop("presence_penalty", None)
            body.pop("messages", None)

            return body

        body = {"messages": messages}

        if pattern in (AzureAPIPattern.AZURE_OPENAI_V1, AzureAPIPattern.AZURE_AI_FOUNDRY):
            body["model"] = deployment

        if temperature is not None:
            body["temperature"] = temperature

        if max_tokens is not None:
            if config.get("uses_max_completion_tokens") and pattern != AzureAPIPattern.AZURE_AI_FOUNDRY:
                body["max_completion_tokens"] = max_tokens
            else:
                body["max_tokens"] = max_tokens

        if response_format:
            body["response_format"] = response_format

        if config.get("supports_reasoning_effort") and self.reasoning_effort:
            body["reasoning_effort"] = self.reasoning_effort

        return body

    def _parse_response(
        self,
        data: dict[str, Any],
        pattern: AzureAPIPattern,
    ) -> tuple[str, str | None]:
        """Extract content and finish reason from an Azure response."""
        if pattern == AzureAPIPattern.AZURE_RESPONSES:
            if "output_text" in data:
                return str(data["output_text"]), data.get("status")

            output = data.get("output", [])
            if output:
                first_output = output[0]
                content_items = first_output.get("content", [])
                if content_items:
                    return str(content_items[0].get("text", "")), data.get("status")
                text = first_output.get("text")
                if text:
                    return str(text), data.get("status")
            return "", data.get("status")

        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        content = message.get("content", "")
        finish_reason = choice.get("finish_reason")
        return content, finish_reason

    def _parse_usage(self, data: dict[str, Any], model: str) -> ProviderUsage:
        """Parse token usage and cost from an Azure response."""
        usage_data = data.get("usage", {})
        input_tokens = usage_data.get("prompt_tokens") or usage_data.get("input_tokens", 0)
        output_tokens = (
            usage_data.get("completion_tokens") or usage_data.get("output_tokens", 0)
        )
        total_tokens = usage_data.get(
            "total_tokens",
            input_tokens + output_tokens,
        )

        return ProviderUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost=self._estimate_cost(
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            ),
            model=model,
            provider_type=self.provider_type,
        )
