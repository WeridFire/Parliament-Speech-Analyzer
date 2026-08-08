"""
Pipeline Core Functions - Reusable NLP analysis components.

- Embedding generation with SentenceTransformers
- Dimensionality reduction (PCA / t-SNE)
- K-Means clustering

Heavy libraries are imported lazily so that importing this module (which the
test suite and the CLI do constantly) does not drag in torch.
"""

import logging
from typing import Optional

import numpy as np

from backend.config import EMBEDDING_MODEL, REDUCTION_METHOD, TSNE_PERPLEXITY

logger = logging.getLogger(__name__)

# The model is ~500 MB to load. The pipeline needs it twice (speech texts, then
# topic descriptions), and used to construct it separately each time - including
# when the embeddings had come from cache and no model was needed at all.
_model_cache: dict[str, object] = {}


def get_embedding_model(model_name: str = EMBEDDING_MODEL):
    """Load a sentence-transformers model once per process."""
    if model_name not in _model_cache:
        from sentence_transformers import SentenceTransformer

        logger.info("Loading embedding model: %s", model_name)
        _model_cache[model_name] = SentenceTransformer(model_name)

    return _model_cache[model_name]


def generate_embeddings(texts: list, model_name: str = EMBEDDING_MODEL) -> np.ndarray:
    """
    Generate sentence embeddings using a multilingual transformer model.

    Args:
        texts: List of texts to encode
        model_name: Name of the sentence-transformers model

    Returns:
        NumPy array of shape (n_texts, embedding_dim)
    """
    model = get_embedding_model(model_name)

    logger.info("Generating embeddings for %d texts...", len(texts))
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)

    logger.debug("Embeddings shape: %s", embeddings.shape)
    return embeddings


def reduce_dimensions(
    embeddings: np.ndarray,
    method: Optional[str] = None,
    n_components: int = 2,
    perplexity: Optional[int] = None,
) -> np.ndarray:
    """
    Reduce embedding dimensions for visualization.

    Args:
        embeddings: High-dimensional embeddings array
        method: 'pca' or 'tsne' (defaults to REDUCTION_METHOD from config)
        n_components: Target dimensions (default 2)
        perplexity: t-SNE perplexity (defaults to TSNE_PERPLEXITY from config)

    Returns:
        Reduced embeddings array
    """
    method = (method or REDUCTION_METHOD).lower()
    perplexity = perplexity if perplexity is not None else TSNE_PERPLEXITY

    logger.info("Reducing dimensions using %s...", method.upper())

    if embeddings.size == 0 or embeddings.ndim < 2 or embeddings.shape[0] == 0:
        logger.warning("Cannot reduce dimensions: empty or invalid embeddings array")
        return np.array([]).reshape(0, n_components)

    if method == "pca":
        from sklearn.decomposition import PCA

        reducer = PCA(n_components=n_components, random_state=42)
        reduced = reducer.fit_transform(embeddings)
        logger.info("PCA explained variance: %.2f%%", sum(reducer.explained_variance_ratio_) * 100)
        return reduced

    if method == "tsne":
        if embeddings.shape[1] > 50:
            logger.debug("Pre-reducing with PCA for t-SNE...")
            from sklearn.decomposition import PCA

            embeddings = PCA(n_components=50, random_state=42).fit_transform(embeddings)

        from sklearn.manifold import TSNE

        reducer = TSNE(
            n_components=n_components,
            perplexity=min(perplexity, len(embeddings) - 1),
            random_state=42,
        )
        return reducer.fit_transform(embeddings)

    raise ValueError(f"Unknown reduction method: {method}")


def apply_clustering(embeddings: np.ndarray, n_clusters: int = 5) -> np.ndarray:
    """
    Apply K-Means clustering to embeddings.

    Args:
        embeddings: Embeddings array
        n_clusters: Number of clusters

    Returns:
        Cluster labels array
    """
    logger.info("Clustering with K-Means (k=%d)...", n_clusters)

    from sklearn.cluster import KMeans

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(embeddings)

    unique, counts = np.unique(labels, return_counts=True)
    for cluster, count in zip(unique, counts):
        logger.debug("Cluster %d: %d speeches", cluster, count)

    return labels
