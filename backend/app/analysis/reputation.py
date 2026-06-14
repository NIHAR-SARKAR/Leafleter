"""Brand reputation scoring engine."""

from app.analysis.base import AnalysisEngine


class ReputationAnalysisEngine(AnalysisEngine):
    """Score brand reputation from collected mentions."""

    analysis_type = "reputation"
    prompt_template = """Score the brand reputation for "{topic_name}".

Description: {description}
Keywords: {keywords}

Sources:
{sources}

Provide:
1. A reputation score from 0-100.
2. Key reputation drivers.
3. Risk areas and recommendations.

Format your answer with a line starting with "Score: <number>".
"""
