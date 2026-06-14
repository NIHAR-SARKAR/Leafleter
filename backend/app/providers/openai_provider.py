"""OpenAI provider adapter."""

from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.providers.base import BaseProvider, ProviderResponse, ProviderUsage

logger = get_logger(__name__)

DEFAULT_OPENAI_BASE = "https://api.openai.com/v1"


class OpenAIProvider(BaseProvider):
    """Provider adapter for OpenAI-compatible APIs."""

    provider_type = "openai"

    def _validate_config(self) -> None:
        """Validate that an API key is present."""
        self.api_key = self.config.get("api_key") or settings.OPENAI_API_KEY or ""
        self.api_base = self.config.get("api_base") or DEFAULT_OPENAI_BASE
        if not self.api_key:
            raise ValueError("OpenAI API key is not configured")

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
        """Execute a chat completion request against OpenAI."""
        url = f"{self.api_base.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if response_format is not None:
            payload["response_format"] = response_format
        payload.update(kwargs)

        logger.info(
            "openai_chat_request",
            model=model,
            messages=len(messages),
        )

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "openai_http_error",
                    status_code=exc.response.status_code,
                    body=exc.response.text,
                )
                raise AppException(
                    "AI provider returned an error",
                    status_code=exc.response.status_code,
                ) from exc
            except httpx.RequestError as exc:
                logger.error("openai_request_error", error=str(exc))
                raise AppException("Failed to reach AI provider") from exc

        data = response.json()
        choice = data["choices"][0]
        message = choice.get("message", {})
        content = message.get("content", "")
        finish_reason = choice.get("finish_reason")

        usage_data = data.get("usage", {})
        input_tokens = usage_data.get("prompt_tokens", 0)
        output_tokens = usage_data.get("completion_tokens", 0)
        total_tokens = usage_data.get("total_tokens", input_tokens + output_tokens)

        usage = ProviderUsage(
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

        return ProviderResponse(
            content=content,
            raw_response=data,
            usage=usage,
            finish_reason=finish_reason,
        )

    async def list_models(self) -> list[dict[str, Any]]:
        """List available models from OpenAI."""
        url = f"{self.api_base.rstrip('/')}/models"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                logger.error("openai_list_models_error", error=str(exc))
                return self._default_models()

        data = response.json()
        return [
            {
                "id": m["id"],
                "name": m["id"],
                "context_window": self._estimate_context_window(m["id"]),
            }
            for m in data.get("data", [])
            if "gpt" in m["id"]
        ] or self._default_models()

    async def validate_credentials(self) -> bool:
        """Validate credentials by listing models."""
        try:
            models = await self.list_models()
            return len(models) > 0
        except Exception as exc:
            logger.warning("openai_credential_validation_failed", error=str(exc))
            return False

    def _default_models(self) -> list[dict[str, Any]]:
        """Return default OpenAI models when API listing fails."""
        return [
            {"id": "gpt-4o", "name": "GPT-4o", "context_window": 128000},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "context_window": 128000},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "context_window": 128000},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "context_window": 16385},
        ]

    def _estimate_context_window(self, model_id: str) -> int:
        """Estimate context window from model id."""
        if "gpt-4o" in model_id or "gpt-4-turbo" in model_id:
            return 128000
        if "gpt-3.5" in model_id:
            return 16385
        if "gpt-4" in model_id:
            return 8192
        return 4096

    async def embeddings(
        self,
        *,
        texts: list[str],
        model: str,
        **kwargs: Any,
    ) -> list[list[float]]:
        """Generate embeddings via OpenAI."""
        url = f"{self.api_base.rstrip('/')}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": model, "input": texts, **kwargs}
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
        data = response.json()
        return [item["embedding"] for item in data.get("data", [])]
