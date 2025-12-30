"""
Thematic Overlap - Bipartisan vs polarized topics.
"""
import logging
import numpy as np
import pandas as pd

from backend.config import LEFT_PARTIES, RIGHT_PARTIES, CENTER_PARTIES

logger = logging.getLogger(__name__)


def categorize_party_coalition(party: str) -> str:
    """Categorize party as left, center, or right."""
    if party in LEFT_PARTIES:
        return 'left'
    elif party in RIGHT_PARTIES:
        return 'right'
    elif party in CENTER_PARTIES:
        return 'center'
    return 'other'


def compute_thematic_overlap(
    df: pd.DataFrame,
    cluster_col: str = 'cluster',
    cluster_labels: dict = None,
    party_col: str = 'group'
) -> dict:
    """
    Analyze thematic overlap between left and right coalitions.
    Identifies bipartisan vs polarized topics.
    """
    labels = cluster_labels or {}
    
    # Add coalition column
    df = df.copy()
    df['_coalition'] = df[party_col].apply(categorize_party_coalition)
    
    result = {}
    
    for cluster in df[cluster_col].unique():
        cluster_df = df[df[cluster_col] == cluster]
        
        # Count by coalition
        coalition_counts = cluster_df['_coalition'].value_counts().to_dict()
        total = len(cluster_df)
        
        left_pct = (coalition_counts.get('left', 0) / total) * 100 if total > 0 else 0
        right_pct = (coalition_counts.get('right', 0) / total) * 100 if total > 0 else 0
        center_pct = (coalition_counts.get('center', 0) / total) * 100 if total > 0 else 0
        
        # Overlap score: higher = more bipartisan
        overlap = min(left_pct, right_pct) * 2  # 0-100 scale
        
        # Classification
        if overlap > 40:
            topic_type = 'bipartisan'
        elif left_pct > 60:
            topic_type = 'left-dominated'
        elif right_pct > 60:
            topic_type = 'right-dominated'
        else:
            topic_type = 'mixed'
        
        result[int(cluster)] = {
            'label': labels.get(cluster, f"Topic {cluster}"),
            'left_pct': round(left_pct, 1),
            'right_pct': round(right_pct, 1),
            'center_pct': round(center_pct, 1),
            'overlap_score': round(overlap, 1),
            'type': topic_type,
            'n_speeches': total
        }
    
    logger.info("Computed thematic overlap for %d clusters", len(result))
    return result
