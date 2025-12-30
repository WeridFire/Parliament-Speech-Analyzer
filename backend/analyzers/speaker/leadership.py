"""
Topic Leadership - Identify topic leaders based on embedding proximity.
"""
import logging
from collections import defaultdict

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


def compute_topic_leadership(
    df: pd.DataFrame,
    embeddings: np.ndarray,
    cluster_centroids: np.ndarray,
    cluster_labels: dict,
    speaker_col: str = 'deputy',
    cluster_col: str = 'cluster'
) -> dict:
    """
    Identify which speakers are the "leaders" of each topic.
    
    A speaker leads a topic if their average embedding is closest to the centroid.
    
    Returns for each speaker:
    - best_topic: the topic they lead (most representative of)
    - topic_scores: similarity to each cluster centroid
    """
    result = {}
    topic_leaders = defaultdict(list)
    
    for speaker in df[speaker_col].unique():
        mask = df[speaker_col] == speaker
        n_speeches = mask.sum()
        
        if n_speeches < 2:
            continue
        
        speaker_embeddings = embeddings[mask]
        speaker_centroid = np.mean(speaker_embeddings, axis=0).reshape(1, -1)
        
        # Compute similarity to each cluster centroid
        similarities = cosine_similarity(speaker_centroid, cluster_centroids)[0]
        
        best_topic_idx = int(np.argmax(similarities))
        best_similarity = float(similarities[best_topic_idx])
        
        topic_scores = {
            int(i): round(float(similarities[i]), 4)
            for i in range(len(cluster_centroids))
        }
        
        result[speaker] = {
            'best_topic': best_topic_idx,
            'best_topic_label': cluster_labels.get(best_topic_idx, f"Topic {best_topic_idx}"),
            'best_similarity': round(best_similarity, 4),
            'topic_scores': topic_scores,
            'n_speeches': n_speeches
        }
        
        topic_leaders[best_topic_idx].append({
            'speaker': speaker,
            'similarity': best_similarity
        })
    
    # Find top leader for each topic
    cluster_leaders = {}
    for topic_idx, leaders in topic_leaders.items():
        sorted_leaders = sorted(leaders, key=lambda x: -x['similarity'])
        cluster_leaders[int(topic_idx)] = {
            'label': cluster_labels.get(topic_idx, f"Topic {topic_idx}"),
            'top_leaders': sorted_leaders[:5]
        }
    
    logger.info("Computed topic leadership for %d speakers", len(result))
    
    return {
        'by_speaker': result,
        'by_topic': cluster_leaders
    }
