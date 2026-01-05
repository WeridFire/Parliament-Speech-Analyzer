"""
Pipeline Core Functions - Reusable NLP analysis components.

This module provides the core functions for speech analysis:
- Embedding generation with SentenceTransformers
- Dimensionality reduction (PCA/t-SNE)
- K-Means clustering

These functions are used by export_data.py for the full analysis pipeline.
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd
import numpy as np
import pandas as pd
# Lazy imports for heavy libraries
# from sentence_transformers import SentenceTransformer
# from sklearn.decomposition import PCA
# from sklearn.manifold import TSNE
# from sklearn.cluster import KMeans

logger = logging.getLogger(__name__)


def generate_embeddings(
    texts: list, 
    model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"
) -> np.ndarray:
    """
    Generate sentence embeddings using a multilingual transformer model.
    
    Args:
        texts: List of texts to encode
        model_name: Name of the sentence-transformers model
    
    Returns:
        NumPy array of shape (n_texts, embedding_dim)
    """
    logger.info("Loading embedding model: %s", model_name)
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name)
    
    logger.info("Generating embeddings for %d texts...", len(texts))
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    
    logger.debug("Embeddings shape: %s", embeddings.shape)
    return embeddings


def reduce_dimensions(
    embeddings: np.ndarray,
    method: str = "pca",
    n_components: int = 2,
    perplexity: int = 30
) -> np.ndarray:
    """
    Reduce embedding dimensions for visualization.
    
    Args:
        embeddings: High-dimensional embeddings array
        method: 'pca' or 'tsne'
        n_components: Target dimensions (default 2)
        perplexity: t-SNE perplexity parameter
    
    Returns:
        Reduced embeddings array
    """
    logger.info("Reducing dimensions using %s...", method.upper())
    
    # Guard against empty arrays
    if embeddings.size == 0 or len(embeddings.shape) < 2 or embeddings.shape[0] == 0:
        logger.warning("Cannot reduce dimensions: empty or invalid embeddings array")
        return np.array([]).reshape(0, n_components)
    
    if method.lower() == "pca":
        from sklearn.decomposition import PCA
        reducer = PCA(n_components=n_components, random_state=42)
        reduced = reducer.fit_transform(embeddings)
        explained_var = sum(reducer.explained_variance_ratio_) * 100
        logger.info("PCA explained variance: %.2f%%", explained_var)
        
    elif method.lower() == "tsne":
        # Pre-reduce with PCA for efficiency
        if embeddings.shape[1] > 50:
            logger.debug("Pre-reducing with PCA for t-SNE...")
            from sklearn.decomposition import PCA
            pca = PCA(n_components=50, random_state=42)
            embeddings = pca.fit_transform(embeddings)
        
        from sklearn.manifold import TSNE
        reducer = TSNE(
            n_components=n_components,
            perplexity=min(perplexity, len(embeddings) - 1),
            random_state=42,
            n_iter=1000
        )
        reduced = reducer.fit_transform(embeddings)
    else:
        raise ValueError(f"Unknown reduction method: {method}")
    
    logger.debug("Reduced dimensions: %s", reduced.shape)
    return reduced


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
    
    # Log distribution
    unique, counts = np.unique(labels, return_counts=True)
    for cluster, count in zip(unique, counts):
        logger.debug("Cluster %d: %d speeches", cluster, count)
    
    return labels
