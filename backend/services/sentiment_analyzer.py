from openai import OpenAI
import os
from typing import Dict, Any, List
import json
import logging

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    Analyze sentiment using an LLM API.
    """

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def analyze(self, text: str) -> Dict[str, Any]:
        try:
            response = self.client.responses.create(
                model="gpt-5-mini",
                input=f"""
Classify the sentiment of this customer feedback.

Return ONLY valid JSON:

{{
    "sentiment": "positive|neutral|negative",
    "score": 0.0-1.0
}}

Feedback:
{text}
""",
            )

            result = json.loads(response.output_text)

            return {
                "sentiment": result["sentiment"],
                "score": float(result["score"]),
            }

        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return {
                "sentiment": "neutral",
                "score": 0.5,
            }

    def analyze_batch(
        self,
        feedback_list: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        logger.info(f"Analyzing sentiment for {len(feedback_list)} entries...")

        for entry in feedback_list:
            result = self.analyze(entry.get("raw_text", ""))

            entry["sentiment"] = result["sentiment"]
            entry["sentiment_score"] = result["score"]

        return feedback_list


def aggregate_sentiment_by_theme(
    feedback_list: List[Dict[str, Any]], themes: List[Dict[str, Any]]
) -> Any:
    """
    Aggregate sentiment counts per theme and attach to theme metadata.
    """
    cluster_to_theme_idx = {t["cluster_id"]: i for i, t in enumerate(themes)}

    for entry in feedback_list:
        cluster_id = entry.get("cluster", 0)
        theme_idx = cluster_to_theme_idx.get(cluster_id)
        if theme_idx is None:
            continue
        theme = themes[theme_idx]
        if "sentiment_counts" not in theme:
            theme["sentiment_counts"] = {"positive": 0, "neutral": 0, "negative": 0}
        sentiment = entry.get("sentiment", "neutral")
        theme["sentiment_counts"][sentiment] = (
            theme["sentiment_counts"].get(sentiment, 0) + 1
        )

    # Compute overall sentiment breakdown across all feedback
    overall = {"positive": 0, "neutral": 0, "negative": 0}
    for entry in feedback_list:
        s = entry.get("sentiment", "neutral")
        overall[s] = overall.get(s, 0) + 1

    return themes, overall


def run_sentiment_analysis(
    feedback_list: List[Dict[str, Any]], themes: List[Dict[str, Any]]
) -> tuple:
    """
    Main entry: run sentiment analysis and aggregate by theme.
    Returns (updated_feedback_list, updated_themes, overall_sentiment)
    """
    analyzer = SentimentAnalyzer()
    feedback_list = analyzer.analyze_batch(feedback_list)
    themes, overall_sentiment = aggregate_sentiment_by_theme(feedback_list, themes)
    return feedback_list, themes, overall_sentiment
