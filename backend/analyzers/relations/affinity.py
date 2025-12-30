"""
Party Affinity Matrix - Semantic similarity between parties.
"""
import logging
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from .cohesion import compute_party_centroids

logger = logging.getLogger(__name__)


def compute_party_affinity_matrix(
    df: pd.DataFrame,
    embeddings: np.ndarray,
    party_col: str = 'group'
) -> dict:
    """
    Compute affinity matrix between parties based on semantic similarity.
    """
    centroids = compute_party_centroids(df, embeddings, party_col)
    
    if len(centroids) < 2:
        return {'parties': [], 'matrix': [], 'pairs': []}
    
    parties = sorted([p for p in centroids.keys() if p != 'Unknown Group'])
    n_parties = len(parties)
    
    # Build centroid matrix
    centroid_matrix = np.array([centroids[p] for p in parties])
    
    # Compute similarity matrix
    sim_matrix = cosine_similarity(centroid_matrix)
    
    # Build pairs list (sorted by similarity)
    pairs = []
    for i in range(n_parties):
        for j in range(i + 1, n_parties):
            pairs.append({
                'party1': parties[i],
                'party2': parties[j],
                'similarity': round(float(sim_matrix[i, j]), 4)
            })
    
    pairs.sort(key=lambda x: -x['similarity'])
    
    result = {
        'parties': parties,
        'matrix': [[round(float(sim_matrix[i, j]), 4) for j in range(n_parties)] for i in range(n_parties)],
        'pairs': pairs
    }
    
    logger.info("Computed affinity matrix for %d parties", len(parties))
    return result
