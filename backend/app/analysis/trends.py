"""Trend analysis engine."""

from app.analysis.base import AnalysisEngine


class TrendAnalysisEngine(AnalysisEngine):
    """Identify emerging trends from collected data."""

    analysis_type = "trends"
    prompt_template = """Identify emerging trends for the topic "{topic_name}".

Description: {description}
Keywords: {keywords}

Sources:
{sources}

Provide:
1. Top 5 emerging trends.
2. Trend velocity (rising/stable/declining) for each.
3. Evidence supporting each trend.

Format your answer with a line starting with "Score: <number>" where the number is the overall trend momentum from 0-100.
"""
