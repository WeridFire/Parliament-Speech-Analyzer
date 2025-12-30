"""
Consistency Index - Thematic consistency over time.
"""
import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def compute_consistency_index(
    df: pd.DataFrame,
    embeddings: np.ndarray,
    speaker_col: str = 'deputy'
) -> dict:
    """
    Compute thematic consistency for each speaker.
    
    Lower variance = more consistent
    Returns score 0-100 where 100 = maximally consistent.
    """
    result = {}
    
    # Compute variance baseline across all embeddings
    global_variance = np.mean(np.var(embeddings, axis=0))
    
    for speaker in df[speaker_col].unique():
        mask = df[speaker_col] == speaker
        n_speeches = mask.sum()
        
        if n_speeches < 3:
            continue
        
        speaker_embeddings = embeddings[mask]
        
        # Compute variance of speaker's embeddings
        speaker_variance = np.mean(np.var(speaker_embeddings, axis=0))
        
        # Convert to consistency score (0-100)
        # Higher score = lower variance = more consistent
        if global_variance > 0:
            relative_variance = speaker_variance / global_variance
            consistency_score = max(0, min(100, (1 - relative_variance) * 100 + 50))
        else:
            consistency_score = 50
        
        # Classification
        if consistency_score > 70:
            classification = 'very_consistent'
        elif consistency_score > 50:
            classification = 'consistent'
        elif consistency_score > 30:
            classification = 'variable'
        else:
            classification = 'inconsistent'
        
        result[speaker] = {
            'score': round(consistency_score, 1),
            'variance': round(float(speaker_variance), 6),
            'classification': classification,
            'n_speeches': n_speeches
        }
    
    logger.info("Computed consistency index for %d speakers", len(result))
    return result
