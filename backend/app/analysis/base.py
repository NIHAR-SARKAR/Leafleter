"""Base analysis engine and shared context."""

from dataclasses import dataclass, field
from typing import Any

from app.core.logging import get_logger
from app.models.topic import Topic
from app.providers.base import BaseProvider, ProviderResponse

logger = get_logger(__name__)


@dataclass
class AnalysisContext:
    """Context passed to analysis engines."""

    topic: Topic
    provider: BaseProvider
    model: str
    sources_text: str = ""
    extra_data: dict[str, Any] = field(default_factory=dict)


class AnalysisEngine:
    """Base class for AI-powered analysis engines."""

    analysis_type: str = ""
    prompt_template: str = ""

    async def analyze(self, context: AnalysisContext) -> dict[str, Any]:
        """Run the analysis and return a structured result."""
        prompt = self._build_prompt(context)
        messages = [
            {"role": "system", "content": "You are a market intelligence analyst."},
            {"role": "user", "content": prompt},
        ]
        try:
            response = await context.provider.chat_completion(
                messages=messages,
                model=context.model,
                temperature=0.3,
                max_tokens=2000,
            )
        except Exception as exc:
            logger.exception(
                "analysis_engine_failed",
                analysis_type=self.analysis_type,
                topic_id=context.topic.id,
                error=str(exc),
            )
            raise

        return self._parse_response(response, context)

    def _build_prompt(self, context: AnalysisContext) -> str:
        """Build the analysis prompt."""
        return self.prompt_template.format(
            topic_name=context.topic.name,
            description=context.topic.description or "",
            keywords=context.topic.keywords or "",
            sources=context.sources_text,
        )

    def _parse_response(
        self, response: ProviderResponse, context: AnalysisContext
    ) -> dict[str, Any]:
        """Parse provider response into a result dict."""
        content = response.content.strip()
        score = self._extract_score(content)
        return {
            "result_type": self.analysis_type,
            "score": score,
            "summary": content[:500],
            "details": {"analysis": content},
            "raw_output": content,
            "usage": response.usage,
        }

    def _extract_score(self, text: str) -> float | None:
        """Attempt to extract a numeric score from 0-100 from the text."""
        import re

        match = re.search(r"score\s*[:=]?\s*(\d+(?:\.\d+)?)", text, re.IGNORECASE)
        if match:
            score = float(match.group(1))
            return max(0.0, min(100.0, score))
        return None
