"""Pain-point detection engine."""

from app.analysis.base import AnalysisEngine


class PainPointsEngine(AnalysisEngine):
    """Detect pain points for a topic workspace."""

    analysis_type = "pain_points"
    result_type = "pain_points"
    prompt_template = """You are a market-intelligence analyst.

Topic: {name}
Description: {description}
Keywords: {keywords}
Sources:
{sources}

Identify the top pain points expressed about this topic. Return a single JSON object with exactly these keys:
- "summary": a concise string summarizing the pain points
- "score": a float from 0 to 100 representing overall severity
- "details": an object with key "pain_points" containing a list of objects, each with "title", "description", and "severity" ("low", "medium", or "high")

Respond with valid JSON only."""
