from openai import OpenAI
import os
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ThemeGenerator:
    """
    Generate theme names and descriptions using OpenAI.
    """

    def __init__(self, api_key: str | None = None):

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError("OpenAI API key not provided")

        self.client = OpenAI(api_key=self.api_key)

    def generate_theme(
        self,
        samples: List[str],
        cluster_id: int,
    ) -> Dict[str, str]:

        prompt = f"""
Analyze the following customer feedback samples.

Generate:
1. A concise theme name (2-4 words)
2. A one-sentence description

Feedback samples:
{chr(10).join(f"- {sample}" for sample in samples)}

Respond exactly in this format:

Theme Name: <name>
Description: <description>
"""

        try:

            response = self.client.responses.create(
                model="gpt-5-mini",
                input=prompt,
            )

            response_text = response.output_text

            lines = response_text.strip().split("\n")

            theme_name = ""
            description = ""

            for line in lines:
                if line.startswith("Theme Name:"):
                    theme_name = line.replace("Theme Name:", "").strip()

                elif line.startswith("Description:"):
                    description = line.replace("Description:", "").strip()

            if not theme_name:
                theme_name = f"Theme {cluster_id + 1}"

            if not description:
                description = "A group of related customer feedback"

            logger.info(f"Cluster {cluster_id}: {theme_name}")

            return {
                "theme_name": theme_name,
                "description": description,
            }

        except Exception as e:

            logger.error(f"Error generating theme for cluster {cluster_id}: {e}")

            return {
                "theme_name": f"Theme {cluster_id + 1}",
                "description": "Unable to generate description",
            }


def generate_themes(
    feedback_list: List[Dict[str, Any]], api_key: str | None = None
) -> List[Dict[str, Any]]:
    """
    Generate themes for all clusters in feedback

    Args:
        feedback_list: List of feedback with cluster assignments
        api_key: Anthropic API key

    Returns:
        List of theme metadata dicts with keys:
        - cluster_id
        - theme_name
        - description
        - count
        - percentage
    """

    generator = ThemeGenerator(api_key=api_key)

    # Get unique clusters
    clusters = set(entry.get("cluster", 0) for entry in feedback_list)
    total_count = len(feedback_list)

    themes = []

    for cluster_id in sorted(clusters):
        # Get samples from this cluster
        cluster_feedback = [
            entry["raw_text"]
            for entry in feedback_list
            if entry.get("cluster") == cluster_id
        ]

        # Get representative samples (up to 5)
        samples = cluster_feedback[:5]

        # Generate theme
        theme = generator.generate_theme(samples, cluster_id)

        # Add metadata
        count = len(cluster_feedback)
        percentage = (count / total_count) * 100

        themes.append(
            {
                "cluster_id": cluster_id,
                "theme_name": theme["theme_name"],
                "description": theme["description"],
                "count": count,
                "percentage": round(percentage, 1),
            }
        )

        logger.info(
            f"Theme {cluster_id}: {theme['theme_name']} ({count} mentions, {percentage:.1f}%)"
        )

    # Sort by count (descending)
    themes.sort(key=lambda x: x["count"], reverse=True)

    return themes


def add_themes_to_feedback(
    feedback_list: List[Dict[str, Any]], themes: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Add theme names to feedback entries

    Args:
        feedback_list: List of feedback with cluster assignments
        themes: List of theme metadata

    Returns:
        Updated feedback list with theme names
    """
    # Create cluster to theme mapping
    cluster_to_theme = {theme["cluster_id"]: theme["theme_name"] for theme in themes}

    # Add theme names
    for entry in feedback_list:
        cluster_id = entry.get("cluster", 0)
        entry["theme_name"] = cluster_to_theme.get(
            cluster_id, f"Theme {cluster_id + 1}"
        )

    return feedback_list
