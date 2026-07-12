from openai import OpenAI
import os
import json
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def generate_recommendations(
    themes: List[Dict],
    overall_sentiment: Dict[str, int],
    api_key: str | None = None,
    n_recommendations: int = 5,
) -> List[Dict[str, str]]:

    client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    theme_summaries = []

    for t in themes:
        counts = t.get("sentiment_counts", {})

        neg = counts.get("negative", 0)
        total = t.get("count", 0)

        neg_pct = round(neg / total * 100) if total else 0

        theme_summaries.append(
            f"- {t['theme_name']} "
            f"({total} mentions, {neg_pct}% negative): "
            f"{t['description']}"
        )

    total_feedback = sum(t.get("count", 0) for t in themes)

    overall_neg_pct = (
        round(overall_sentiment.get("negative", 0) / total_feedback * 100)
        if total_feedback
        else 0
    )

    prompt = f"""
You are a product manager analyzing customer feedback.

Here are the top themes extracted from
{total_feedback} customer feedback entries
({overall_neg_pct}% overall negative sentiment):

{chr(10).join(theme_summaries)}

Based on frequency and negative sentiment,
generate exactly {n_recommendations}
prioritized actionable recommendations.

Rules:
- Plain, non-technical language
- Order highest priority first
- Specific and actionable
- Focus on problems to fix

Return ONLY valid JSON:

[
  {{
    "priority": 1,
    "title": "Short title",
    "description": "Actionable recommendation"
  }}
]
"""

    try:
        response = client.responses.create(
            model="gpt-5-mini",
            input=prompt,
        )

        raw = response.output_text.strip()

        recommendations = json.loads(raw)

        logger.info(f"Generated {len(recommendations)} recommendations")

        return recommendations

    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")

        fallback = []

        sorted_themes = sorted(
            themes,
            key=lambda t: t.get("sentiment_counts", {}).get("negative", 0),
            reverse=True,
        )

        for i, t in enumerate(sorted_themes[:n_recommendations]):
            fallback.append(
                {
                    "priority": i + 1,
                    "title": f"Address {t['theme_name']}",
                    "description": (
                        "This theme has high negative sentiment. "
                        f"Review and improve: {t['description']}"
                    ),
                }
            )

        return fallback
