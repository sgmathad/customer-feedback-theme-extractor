from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import numpy as np
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class FeedbackEmbedder:
    """
    Generate embeddings for feedback using sentence transformers
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize with a sentence transformer model

        Args:
            model_name: Name of the sentence-transformers model
        """
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)

    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts

        Args:
            texts: List of feedback text strings

        Returns:
            numpy array of embeddings (n_samples, embedding_dim)
        """
        logger.info(f"Generating embeddings for {len(texts)} texts")
        embeddings = self.model.encode(texts, show_progress_bar=True)
        logger.info(f"Embeddings shape: {embeddings.shape}")
        return embeddings


class FeedbackClusterer:
    """
    Cluster feedback using KMeans
    """

    def __init__(self, min_clusters: int = 3, max_clusters: int = 12):
        """
        Args:
            min_clusters: Minimum number of clusters to consider
            max_clusters: Maximum number of clusters to consider
        """
        self.min_clusters = min_clusters
        self.max_clusters = max_clusters
        self.optimal_k = None
        self.kmeans = None

    def find_optimal_clusters(self, embeddings: np.ndarray) -> int:
        """
        Determine optimal number of clusters using silhouette score

        Args:
            embeddings: Embedding vectors

        Returns:
            Optimal number of clusters
        """
        n_samples = len(embeddings)
        max_k = min(self.max_clusters, n_samples - 1)
        min_k = min(self.min_clusters, max_k)

        if max_k < min_k:
            logger.warning(f"Not enough samples for clustering. Using k=1")
            return 1

        best_score = -1
        best_k = min_k

        logger.info(f"Finding optimal clusters between {min_k} and {max_k}")

        for k in range(min_k, max_k + 1):
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(embeddings)

            # Calculate silhouette score
            score = silhouette_score(embeddings, labels)
            logger.info(f"k={k}, silhouette score={score:.3f}")

            if score > best_score:
                best_score = score
                best_k = k

        logger.info(f"Optimal k={best_k} with silhouette score={best_score:.3f}")
        self.optimal_k = best_k
        return best_k

    def cluster(
        self, embeddings: np.ndarray, n_clusters: int | None = None
    ) -> np.ndarray:
        """
        Cluster embeddings using KMeans

        Args:
            embeddings: Embedding vectors
            n_clusters: Number of clusters (if None, will auto-determine)

        Returns:
            Cluster labels for each sample
        """
        if n_clusters is None:
            n_clusters = self.find_optimal_clusters(embeddings)

        logger.info(f"Clustering with k={n_clusters}")
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = self.kmeans.fit_predict(embeddings)

        # Log cluster sizes
        unique, counts = np.unique(labels, return_counts=True)
        for cluster_id, count in zip(unique, counts):
            logger.info(f"Cluster {cluster_id}: {count} samples")

        return labels


def generate_embeddings_and_cluster(
    feedback_list: List[Dict[str, Any]],
    model_name: str = "all-MiniLM-L6-v2",
    min_clusters: int = 3,
    max_clusters: int = 12,
) -> Tuple[np.ndarray, np.ndarray, List[Dict[str, Any]]]:
    """
    Main pipeline: generate embeddings and cluster feedback

    Args:
        feedback_list: List of feedback dictionaries with 'raw_text' key
        model_name: Sentence transformer model name
        min_clusters: Minimum number of clusters
        max_clusters: Maximum number of clusters

    Returns:
        Tuple of (embeddings, cluster_labels, updated_feedback_list)
    """
    # Extract texts
    texts = [entry["raw_text"] for entry in feedback_list]

    # Generate embeddings
    embedder = FeedbackEmbedder(model_name=model_name)
    embeddings = embedder.generate_embeddings(texts)

    # Cluster
    clusterer = FeedbackClusterer(min_clusters=min_clusters, max_clusters=max_clusters)
    labels = clusterer.cluster(embeddings)

    # Add cluster labels to feedback
    for idx, entry in enumerate(feedback_list):
        entry["cluster"] = int(labels[idx])

    return embeddings, labels, feedback_list


def get_cluster_samples(
    feedback_list: List[Dict[str, Any]], cluster_id: int, n_samples: int = 5
) -> List[str]:
    """
    Get representative samples from a cluster

    Args:
        feedback_list: List of feedback with cluster assignments
        cluster_id: ID of the cluster
        n_samples: Number of samples to return

    Returns:
        List of sample texts from the cluster
    """
    cluster_feedback = [
        entry["raw_text"]
        for entry in feedback_list
        if entry.get("cluster") == cluster_id
    ]

    # Return up to n_samples
    return cluster_feedback[:n_samples]
