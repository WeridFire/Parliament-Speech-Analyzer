"""
Party Cohesion and Centroids - Internal party coherence.
"""
import logging
import numpy as np
import pandas as pd

from backend.config import LEFT_PARTIES, RIGHT_PARTIES, CENTER_PARTIES

logger = logging.getLogger(__name__)


def compute_party_centroids(
    df: pd.DataFrame,
    embeddings: np.ndarray,
    party_col: str = 'group'
) -> dict:
    """Compute the centroid (average embedding) for each party."""
    centroids = {}
    
    for party in df[party_col].unique():
        if party == 'Unknown Group':
            continue
            
        mask = df[party_col] == party
        if mask.sum() == 0:
            continue
            
        party_embeddings = embeddings[mask]
        centroids[party] = np.mean(party_embeddings, axis=0)
    
    return centroids


def compute_party_cohesion(
    df: pd.DataFrame,
    embeddings: np.ndarray,
    party_col: str = 'group'
) -> dict:
    """
    Compute internal cohesion score for each party.
    Higher score = more coherent party line.
    """
    centroids = compute_party_centroids(df, embeddings, party_col)
    result = {}
    
    for party in df[party_col].unique():
        if party == 'Unknown Group' or party not in centroids:
            continue
        
        mask = df[party_col] == party
        party_embeddings = embeddings[mask]
        centroid = centroids[party]
        
        # Compute distances to centroid
        distances = np.linalg.norm(party_embeddings - centroid, axis=1)
        
        avg_distance = float(np.mean(distances))
        std_distance = float(np.std(distances))
        
        # Cohesion score: inverse of avg distance, normalized
        cohesion = 1.0 / (1.0 + avg_distance)
        
        result[party] = {
            'cohesion_score': round(cohesion, 4),
            'avg_distance': round(avg_distance, 4),
            'std_distance': round(std_distance, 4),
            'n_speeches': int(mask.sum()),
            'interpretation': 'compatto' if cohesion > 0.7 else ('frammentato' if cohesion < 0.4 else 'moderato')
        }
    
    logger.info("Computed cohesion for %d parties", len(result))
    return result
