"""Opportunity detection engine."""

from app.analysis.base import AnalysisEngine


class OpportunitiesEngine(AnalysisEngine):
    """Detect market opportunities for a topic workspace."""

    analysis_type = "opportunities"
    result_type = "opportunities"
    prompt_template = """You are a market-intelligence analyst.

Topic: {name}
Description: {description}
Keywords: {keywords}
Sources:
{sources}

Identify the top market opportunities related to this topic. Return a single JSON object with exactly these keys:
- "summary": a concise string summarizing the opportunities
- "score": a float from 0 to 100 representing overall opportunity potential
- "details": an object with key "opportunities" containing a list of objects, each with "title", "description", and "potential" ("low", "medium", or "high")

Respond with valid JSON only."""
