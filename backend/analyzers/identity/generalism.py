"""
Generalism Index - Compute entropy-based specialization score.

Shannon entropy of topic distribution, normalized to 0-100:
- 100 = perfectly generalist (equal distribution across all topics)
- 0 = monotematic (speaks only about one topic)
"""

import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def compute_generalism_index(
    df: pd.DataFrame,
    cluster_col: str = 'cluster',
    speaker_col: str = 'deputy',
    party_col: str = 'group'
) -> dict:
    """
    Compute generalism index based on topic entropy.
    
    Shannon entropy of topic distribution, normalized to 0-100:
    - 100 = perfectly generalist (equal distribution across all topics)
    - 0 = monotematic (speaks only about one topic)
    
    Args:
        df: DataFrame with speeches
        cluster_col: Column with cluster assignments
        speaker_col: Column with speaker names
        party_col: Column with party names
    
    Returns:
        {
            'by_deputy': {deputy: {score, dominant_topic, n_topics}, ...},
            'by_party': {party: {score, dominant_topic, n_topics}, ...}
        }
    """
    result = {
        'by_deputy': {},
        'by_party': {}
    }
    
    n_clusters = df[cluster_col].nunique()
    max_entropy = np.log2(n_clusters) if n_clusters > 1 else 1
    
    # Per-deputy
    for speaker in df[speaker_col].unique():
        speaker_df = df[df[speaker_col] == speaker]
        if len(speaker_df) < 2:
            continue
            
        topic_counts = speaker_df[cluster_col].value_counts()
        proportions = topic_counts.values / topic_counts.sum()
        
        # Shannon entropy
        entropy = -np.sum(proportions * np.log2(proportions + 1e-10))
        normalized_score = (entropy / max_entropy) * 100 if max_entropy > 0 else 0
        
        dominant_topic = int(topic_counts.idxmax())
        n_topics_used = len(topic_counts)
        
        result['by_deputy'][speaker] = {
            'score': round(float(normalized_score), 1),
            'dominant_topic': dominant_topic,
            'n_topics': n_topics_used,
            'n_speeches': len(speaker_df),
            'classification': _classify_generalism(normalized_score)
        }
    
    # Per-party
    for party in df[party_col].unique():
        if party == 'Unknown Group':
            continue
            
        party_df = df[df[party_col] == party]
        if len(party_df) < 2:
            continue
            
        topic_counts = party_df[cluster_col].value_counts()
        proportions = topic_counts.values / topic_counts.sum()
        
        entropy = -np.sum(proportions * np.log2(proportions + 1e-10))
        normalized_score = (entropy / max_entropy) * 100 if max_entropy > 0 else 0
        
        dominant_topic = int(topic_counts.idxmax())
        
        result['by_party'][party] = {
            'score': round(float(normalized_score), 1),
            'dominant_topic': dominant_topic,
            'n_topics': len(topic_counts),
            'n_speeches': len(party_df),
            'classification': _classify_generalism(normalized_score)
        }
    
    logger.info(
        "Computed generalism index for %d deputies and %d parties",
        len(result['by_deputy']), len(result['by_party'])
    )
    
    return result


def _classify_generalism(score: float) -> str:
    """Classify generalism score into category."""
    if score > 70:
        return 'generalista'
    elif score < 30:
        return 'specialista'
    else:
        return 'bilanciato'
