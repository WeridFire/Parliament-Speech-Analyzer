"""
Party Affinity Matrix - Semantic similarity between parties.

Cosine similarity between party centroids in the centred embedding space; see
`cohesion.py` for why the centring matters. Values now range over the full
-1..1 scale instead of 0.81-0.99, so the heatmap can show differences.
"""
import logging

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from .cohesion import MIN_PARTY_SPEECHES, compute_party_centroids

logger = logging.getLogger(__name__)


def compute_party_affinity_matrix(
    df: pd.DataFrame,
    embeddings: np.ndarray,
    party_col: str = 'group'
) -> dict:
    """
    Returns:
        {'parties': [...], 'matrix': [[...]], 'pairs': [{party1, party2, similarity}],
         'range': [min, max]}   range of the off-diagonal values, for the colour scale
    """
    centroids = compute_party_centroids(df, embeddings, party_col, min_speeches=MIN_PARTY_SPEECHES)

    if len(centroids) < 2:
        return {'parties': [], 'matrix': [], 'pairs': [], 'range': [0, 0]}

    parties = sorted(centroids)
    sim_matrix = cosine_similarity(np.array([centroids[p] for p in parties]))
    n_parties = len(parties)

    pairs = [
        {'party1': parties[i], 'party2': parties[j], 'similarity': round(float(sim_matrix[i, j]), 4)}
        for i in range(n_parties)
        for j in range(i + 1, n_parties)
    ]
    pairs.sort(key=lambda x: -x['similarity'])

    off_diagonal = sim_matrix[~np.eye(n_parties, dtype=bool)]

    logger.info("Computed affinity matrix for %d parties", n_parties)
    return {
        'parties': parties,
        'matrix': [[round(float(v), 4) for v in row] for row in sim_matrix],
        'pairs': pairs,
        'range': [round(float(off_diagonal.min()), 4), round(float(off_diagonal.max()), 4)],
    }
