import re
import random
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Basic PII patterns to redact before surfacing quotes
PII_PATTERNS = [
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "[EMAIL]"),
    (re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"), "[PHONE]"),
    (re.compile(r"\b(?:\d[ -]?){13,16}\b"), "[CARD]"),
    (
        re.compile(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b"),
        "[NAME]",
    ),  # simple two-word proper names
]


def _redact_pii(text: str) -> str:
    for pattern, replacement in PII_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _diversity_score(candidate: str, selected: List[str]) -> float:
    """
    Simple heuristic: prefer quotes that share fewer words with already-selected ones.
    Returns a score between 0 (identical) and 1 (totally different).
    """
    if not selected:
        return 1.0
    candidate_words = set(candidate.lower().split())
    scores = []
    for s in selected:
        s_words = set(s.lower().split())
        union = candidate_words | s_words
        if not union:
            scores.append(0.0)
        else:
            intersection = candidate_words & s_words
            scores.append(1 - len(intersection) / len(union))
    return min(scores)  # be conservative — pick the worst overlap


def select_quotes_for_theme(
    cluster_feedback: List[Dict[str, Any]],
    n_quotes: int = 5,
    min_length: int = 30,
    max_length: int = 300,
) -> List[Dict[str, Any]]:
    """
    Select diverse, PII-free representative quotes from a cluster.

    Returns a list of dicts: {text, sentiment}
    """
    # Filter by length
    candidates = [
        e
        for e in cluster_feedback
        if min_length <= len(e.get("raw_text", "")) <= max_length
    ]

    # Fall back to whatever we have if not enough
    if not candidates:
        candidates = cluster_feedback

    # Shuffle for variety, then greedily pick diverse quotes
    random.shuffle(candidates)
    selected = []
    for entry in candidates:
        text = _redact_pii(entry.get("raw_text", "").strip())
        if not text:
            continue
        if _diversity_score(text, [q["text"] for q in selected]) > 0.4:
            selected.append(
                {
                    "text": text,
                    "sentiment": entry.get("sentiment", "neutral"),
                }
            )
        if len(selected) >= n_quotes:
            break

    # Pad if not enough diverse quotes
    if len(selected) < n_quotes:
        for entry in candidates:
            if len(selected) >= n_quotes:
                break
            text = _redact_pii(entry.get("raw_text", "").strip())
            if text and not any(q["text"] == text for q in selected):
                selected.append(
                    {
                        "text": text,
                        "sentiment": entry.get("sentiment", "neutral"),
                    }
                )

    return selected[:n_quotes]


def add_quotes_to_themes(
    feedback_list: List[Dict[str, Any]],
    themes: List[Dict[str, Any]],
    n_quotes: int = 5,
) -> List[Dict[str, Any]]:
    """
    Attach representative quotes to each theme dict.
    """
    for theme in themes:
        cluster_id = theme["cluster_id"]
        cluster_feedback = [e for e in feedback_list if e.get("cluster") == cluster_id]
        theme["quotes"] = select_quotes_for_theme(cluster_feedback, n_quotes=n_quotes)
        logger.info(
            f"Theme '{theme['theme_name']}': selected {len(theme['quotes'])} quotes"
        )
    return themes
