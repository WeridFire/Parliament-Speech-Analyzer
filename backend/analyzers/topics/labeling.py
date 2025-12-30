"""
Topic Labeling - Generate human-readable labels from keywords.
"""
import logging

import pandas as pd

from .extraction import extract_cluster_topics

logger = logging.getLogger(__name__)


def label_cluster(keywords: list[str]) -> str:
    """Generate a human-readable label from keywords."""
    if not keywords:
        return "Unknown"
    
    # Take first 2-3 keywords
    label_words = keywords[:min(3, len(keywords))]
    return " / ".join(word.title() for word in label_words)


def get_cluster_labels(df: pd.DataFrame, cluster_col: str = 'cluster', text_col: str = 'cleaned_text') -> dict:
    """
    Get human-readable labels for all clusters.
    
    Returns dict mapping cluster_id -> label string
    """
    topics = extract_cluster_topics(df, text_col=text_col, cluster_col=cluster_col)
    
    labels = {}
    for cluster_id, keywords in topics.items():
        labels[int(cluster_id)] = label_cluster(keywords)
    
    logger.info("Generated labels for %d clusters", len(labels))
    return labels
