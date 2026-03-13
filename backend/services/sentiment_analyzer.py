from transformers import pipeline
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    Analyze sentiment of feedback entries using a pre-trained model
    """

    def __init__(self):
        logger.info("Loading sentiment analysis model...")
        self.classifier = pipeline(
            task="sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            truncation=True,
            max_length=512,
        )

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of a single text.
        Returns dict with 'label' (POSITIVE/NEGATIVE) and 'score'.
        Maps to: positive, neutral, negative
        """
        try:
            result = self.classifier(text[:512])[0]
            label = result["label"].lower()
            score = result["score"]

            # Map to three-way sentiment using confidence threshold
            if label == "positive":
                sentiment = "positive" if score > 0.75 else "neutral"
            else:
                sentiment = "negative" if score > 0.75 else "neutral"

            return {"sentiment": sentiment, "score": float(score), "raw_label": label}
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return {"sentiment": "neutral", "score": 0.5, "raw_label": "unknown"}

    def analyze_batch(
        self, feedback_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Add sentiment to each feedback entry.
        """
        logger.info(f"Analyzing sentiment for {len(feedback_list)} entries...")
        for entry in feedback_list:
            result = self.analyze(entry.get("raw_text", ""))
            entry["sentiment"] = result["sentiment"]
            entry["sentiment_score"] = result["score"]
        logger.info("Sentiment analysis complete.")
        return feedback_list


def aggregate_sentiment_by_theme(
    feedback_list: List[Dict[str, Any]], themes: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
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
