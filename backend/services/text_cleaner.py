import re
import unicodedata
from typing import List, Dict, Any
import logging
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

logger = logging.getLogger(__name__)


class TextCleaner:
    """
    Clean and normalize feedback text
    """

    def __init__(self, min_length: int = 10, similarity_threshold: float = 0.95):
        self.min_length = min_length
        self.similarity_threshold = similarity_threshold

    def clean_text(self, text: str) -> str:
        """
        Clean and normalize a single text entry
        """
        if not text or not isinstance(text, str):
            return ""

        # Normalize unicode characters
        text = unicodedata.normalize("NFKD", text)

        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)

        # Strip leading/trailing whitespace
        text = text.strip()

        # Remove URLs
        text = re.sub(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
            "",
            text,
        )

        # Remove email addresses (basic PII)
        text = re.sub(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL]", text
        )

        # Remove phone numbers (basic PII)
        text = re.sub(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "[PHONE]", text)

        # Fix common encoding issues
        text = text.replace("â€™", "'")
        text = text.replace('â€"', "-")
        text = text.replace("â€œ", '"')
        text = text.replace("â€", '"')

        return text

    def is_valid_entry(self, text: str) -> bool:
        """
        Check if a text entry is valid (not empty, meets minimum length)
        """
        if not text or len(text.strip()) < self.min_length:
            return False
        return True

    def clean_feedback_list(
        self, feedback_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Clean a list of feedback entries

        Returns:
            Cleaned feedback list with invalid entries removed
        """
        cleaned = []
        removed_count = 0

        for entry in feedback_list:
            original_text = entry.get("raw_text", "")
            cleaned_text = self.clean_text(original_text)

            if self.is_valid_entry(cleaned_text):
                entry["raw_text"] = cleaned_text
                cleaned.append(entry)
            else:
                removed_count += 1

        logger.info(f"Removed {removed_count} invalid entries")
        logger.info(f"Remaining entries: {len(cleaned)}")

        return cleaned

    def deduplicate_by_similarity(
        self, feedback_list: List[Dict[str, Any]], embeddings: np.ndarray
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate feedback based on embedding similarity

        Args:
            feedback_list: List of feedback entries
            embeddings: Pre-computed embeddings for each entry

        Returns:
            Deduplicated feedback list
        """
        if len(feedback_list) == 0:
            return []

        # Compute pairwise similarity
        similarity_matrix = cosine_similarity(embeddings)

        # Mark duplicates
        to_remove = set()
        for i in range(len(similarity_matrix)):
            if i in to_remove:
                continue
            for j in range(i + 1, len(similarity_matrix)):
                if j in to_remove:
                    continue
                if similarity_matrix[i][j] > self.similarity_threshold:
                    to_remove.add(j)

        # Filter out duplicates
        deduplicated = [
            entry for idx, entry in enumerate(feedback_list) if idx not in to_remove
        ]

        logger.info(f"Removed {len(to_remove)} duplicate entries")
        logger.info(f"Remaining unique entries: {len(deduplicated)}")

        return deduplicated

    def process_feedback(
        self, feedback_list: List[Dict[str, Any]], embeddings: np.ndarray | None = None
    ) -> List[Dict[str, Any]]:
        """
        Complete cleaning pipeline

        Args:
            feedback_list: Raw feedback entries
            embeddings: Optional pre-computed embeddings for deduplication

        Returns:
            Cleaned and deduplicated feedback list
        """
        # Clean text
        cleaned = self.clean_feedback_list(feedback_list)

        # Deduplicate if embeddings provided
        if embeddings is not None and len(embeddings) == len(cleaned):
            cleaned = self.deduplicate_by_similarity(cleaned, embeddings)

        return cleaned


def clean_and_prepare_feedback(
    feedback_list: List[Dict[str, Any]],
    embeddings: np.ndarray | None = None,
    min_length: int = 10,
    similarity_threshold: float = 0.95,
) -> List[Dict[str, Any]]:
    """
    Main entry point for text cleaning

    Args:
        feedback_list: Raw feedback entries from parser
        embeddings: Optional embeddings for deduplication
        min_length: Minimum text length to keep
        similarity_threshold: Similarity threshold for deduplication

    Returns:
        Cleaned feedback ready for AI processing
    """
    cleaner = TextCleaner(
        min_length=min_length, similarity_threshold=similarity_threshold
    )
    return cleaner.process_feedback(feedback_list, embeddings)
