"""SWOT analysis engine."""

from app.analysis.base import AnalysisEngine


class SWOTAnalysisEngine(AnalysisEngine):
    """Generate SWOT analysis."""

    analysis_type = "swot"
    prompt_template = """Generate a SWOT analysis for the topic "{topic_name}".

Description: {description}
Keywords: {keywords}

Sources:
{sources}

Provide:
1. Strengths
2. Weaknesses
3. Opportunities
4. Threats

Format each section as a bullet list. Include a line starting with "Score: <number>" representing overall strategic opportunity from 0-100.
"""
