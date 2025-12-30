"""
Thematic Fingerprint - Compute radar chart data for politicians/parties.

Calculates mean cosine similarity between speaker's embeddings and each cluster centroid.
"""

import logging
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


def compute_thematic_fingerprint(
    df: pd.DataFrame,
    embeddings: np.ndarray,
    cluster_centroids: np.ndarray,
    cluster_labels: dict,
    speaker_col: str = 'deputy',
    party_col: str = 'group'
) -> dict:
    """
    Compute thematic fingerprint (radar chart data) for each politician/party.
    
    Calculates mean cosine similarity between speaker's embeddings and each cluster centroid.
    
    Args:
        df: DataFrame with speeches
        embeddings: Speech embeddings array
        cluster_centroids: Array of cluster centroid vectors (n_clusters x embedding_dim)
        cluster_labels: Dict mapping cluster_id -> label string
        speaker_col: Column containing speaker names
        party_col: Column containing party info
    
    Returns:
        Dict with fingerprints per speaker/party:
        {
            'by_deputy': {deputy: {cluster_id: similarity, ...}, ...},
            'by_party': {party: {cluster_id: similarity, ...}, ...},
            'cluster_labels': {cluster_id: label, ...}
        }
    """
    result = {
        'by_deputy': {},
        'by_party': {},
        'cluster_labels': cluster_labels
    }
    
    n_clusters = len(cluster_centroids)
    
    # Per-deputy fingerprint
    for deputy in df[speaker_col].unique():
        mask = df[speaker_col] == deputy
        if mask.sum() == 0:
            continue
            
        deputy_embeddings = embeddings[mask]
        avg_embedding = np.mean(deputy_embeddings, axis=0).reshape(1, -1)
        
        # Similarity to each cluster centroid
        similarities = cosine_similarity(avg_embedding, cluster_centroids)[0]
        
        result['by_deputy'][deputy] = {
            int(i): round(float(similarities[i]), 4)
            for i in range(n_clusters)
        }
    
    # Per-party fingerprint
    for party in df[party_col].unique():
        if party == 'Unknown Group':
            continue
            
        mask = df[party_col] == party
        if mask.sum() == 0:
            continue
            
        party_embeddings = embeddings[mask]
        avg_embedding = np.mean(party_embeddings, axis=0).reshape(1, -1)
        
        similarities = cosine_similarity(avg_embedding, cluster_centroids)[0]
        
        result['by_party'][party] = {
            int(i): round(float(similarities[i]), 4)
            for i in range(n_clusters)
        }
    
    logger.info(
        "Computed thematic fingerprints for %d deputies and %d parties", 
        len(result['by_deputy']), len(result['by_party'])
    )
    
    return result
