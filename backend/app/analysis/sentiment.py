"""Sentiment analysis engine."""

from app.analysis.base import AnalysisEngine


class SentimentAnalysisEngine(AnalysisEngine):
    """Analyze overall sentiment of collected data."""

    analysis_type = "sentiment"
    prompt_template = """Analyze the overall sentiment for the topic "{topic_name}".

Description: {description}
Keywords: {keywords}

Sources:
{sources}

Provide:
1. An overall sentiment score from 0 (very negative) to 100 (very positive).
2. A summary of key emotional themes.
3. Notable positive and negative mentions.

Format your answer with a line starting with "Score: <number>".
"""
