"""Audience insights engine."""

from app.analysis.base import AnalysisEngine


class AudienceAnalysisEngine(AnalysisEngine):
    """Analyze audience characteristics and pain points."""

    analysis_type = "audience"
    prompt_template = """Analyze the audience for the topic "{topic_name}".

Description: {description}
Keywords: {keywords}

Sources:
{sources}

Provide:
1. Audience demographics and psychographics.
2. Top 5 pain points.
3. Top 5 unmet needs or desires.
4. Recommended messaging angles.

Include a line starting with "Score: <number>" where the number is audience engagement potential from 0-100.
"""
