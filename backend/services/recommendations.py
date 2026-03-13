import anthropic
import os
import json
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def generate_recommendations(
    themes: List[Dict[str, Any]],
    overall_sentiment: Dict[str, int],
    api_key: str | None = None,
    n_recommendations: int = 5,
) -> List[Dict[str, str]]:
    """
    Generate prioritized "What to Fix First" recommendations using Claude.

    Weighs high-frequency themes with negative sentiment most heavily.

    Returns a list of dicts: {title, description, priority (1=highest)}
    """
    client = anthropic.Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))

    # Build a concise summary of themes for the prompt
    theme_summaries = []
    for t in themes:
        counts = t.get("sentiment_counts", {})
        neg = counts.get("negative", 0)
        total = t.get("count", 0)
        neg_pct = round(neg / total * 100) if total else 0
        theme_summaries.append(
            f"- {t['theme_name']} ({total} mentions, {neg_pct}% negative): {t['description']}"
        )

    total_feedback = sum(t.get("count", 0) for t in themes)
    overall_neg_pct = (
        round(overall_sentiment.get("negative", 0) / total_feedback * 100)
        if total_feedback
        else 0
    )

    prompt = f"""You are a product manager analyzing customer feedback. 
Here are the top themes extracted from {total_feedback} customer feedback entries ({overall_neg_pct}% overall negative sentiment):

{chr(10).join(theme_summaries)}

Based on frequency and negative sentiment, generate exactly {n_recommendations} prioritized, actionable recommendations for the product team.

Rules:
- Write in plain, non-technical language that any stakeholder can understand
- Order from highest to lowest priority (most urgent first)
- Each recommendation should be specific and actionable, not vague
- Focus on problems to fix, not just observations

Respond ONLY with a valid JSON array (no markdown, no preamble) in this exact format:
[
  {{"priority": 1, "title": "Short title (5 words max)", "description": "1-2 sentence actionable recommendation."}},
  ...
]"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = getattr(message.content[0], "text").strip()
        # Strip possible markdown fences
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        recommendations = json.loads(raw)
        logger.info(f"Generated {len(recommendations)} recommendations")
        return recommendations
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        # Fallback: derive simple recommendations from top negative themes
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
                    "description": f"This theme has high negative sentiment. Review and improve: {t['description']}",
                }
            )
        return fallback
