"""
Relations Analyzer - Analyze relationships and affinities between parties.

This module provides:
- Party Affinity Matrix (cosine similarity heatmap)
- Party Cohesion Score (internal coherence)
- Thematic Overlap (bipartisan vs polarized topics)
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from backend.config import LEFT_PARTIES, RIGHT_PARTIES, CENTER_PARTIES

logger = logging.getLogger(__name__)


def compute_party_centroids(
    df: pd.DataFrame,
    embeddings: np.ndarray,
    party_col: str = 'group'
) -> dict[str, np.ndarray]:
    """
    Compute the centroid (average embedding) for each party.
    
    Returns dict mapping party_name -> centroid vector
    """
    centroids = {}
    
    for party in df[party_col].unique():
        if party == 'Unknown Group':
            continue
        
        party_mask = df[party_col] == party
        party_embeddings = embeddings[party_mask]
        
        if len(party_embeddings) > 0:
            centroids[party] = np.mean(party_embeddings, axis=0)
    
    return centroids


def compute_party_affinity_matrix(
    df: pd.DataFrame,
    embeddings: np.ndarray,
    party_col: str = 'group'
) -> dict:
    """
    Compute affinity matrix between parties based on semantic similarity.
    
    Uses cosine similarity between party centroids to measure
    how semantically similar parties are in their discourse.
    
    Returns:
        {
            'parties': [party1, party2, ...],
            'matrix': [[sim11, sim12, ...], [sim21, sim22, ...], ...],
            'pairs': [{party1, party2, similarity}, ...]  # sorted by similarity
        }
    """
    centroids = compute_party_centroids(df, embeddings, party_col)
    
    if len(centroids) < 2:
        logger.warning("Need at least 2 parties for affinity matrix")
        return {'parties': [], 'matrix': [], 'pairs': []}
    
    parties = sorted(centroids.keys())
    n_parties = len(parties)
    
    # Stack centroids into matrix
    centroid_matrix = np.array([centroids[p] for p in parties])
    
    # Compute pairwise cosine similarity
    similarity_matrix = cosine_similarity(centroid_matrix)
    
    # Round for JSON
    matrix = [[round(float(similarity_matrix[i, j]), 4) 
               for j in range(n_parties)] 
              for i in range(n_parties)]
    
    # Extract pairs for easier visualization
    pairs = []
    for i in range(n_parties):
        for j in range(i + 1, n_parties):
            pairs.append({
                'party1': parties[i],
                'party2': parties[j],
                'similarity': round(float(similarity_matrix[i, j]), 4)
            })
    
    pairs.sort(key=lambda x: -x['similarity'])
    
    logger.info("Computed affinity matrix for %d parties", n_parties)
    
    return {
        'parties': parties,
        'matrix': matrix,
        'pairs': pairs
    }


def compute_party_cohesion(
    df: pd.DataFrame,
    embeddings: np.ndarray,
    party_col: str = 'group'
) -> dict:
    """
    Compute internal cohesion score for each party.
    
    Measures how tightly clustered a party's members are around the centroid.
    Higher score = more coherent party line.
    
    Returns:
        {
            party: {
                'cohesion_score': 0-100 (higher = more compact),
                'variance': raw variance value,
                'n_members': number of unique speakers,
                'n_speeches': number of speeches
            },
            ...
        }
    """
    centroids = compute_party_centroids(df, embeddings, party_col)
    result = {}
    
    # Collect all variances to normalize
    all_variances = []
    party_raw_data = {}
    
    for party in df[party_col].unique():
        if party == 'Unknown Group' or party not in centroids:
            continue
        
        party_mask = df[party_col] == party
        party_embeddings = embeddings[party_mask]
        
        if len(party_embeddings) < 2:
            continue
        
        centroid = centroids[party]
        
        # Compute distances from centroid
        distances = np.linalg.norm(party_embeddings - centroid, axis=1)
        variance = float(np.var(distances))
        
        all_variances.append(variance)
        party_raw_data[party] = {
            'variance': variance,
            'n_members': df[party_mask]['deputy'].nunique(),
            'n_speeches': len(party_embeddings)
        }
    
    # Normalize variance to 0-100 cohesion score (inverse: low variance = high cohesion)
    if all_variances:
        max_var = max(all_variances) if max(all_variances) > 0 else 1
        
        for party, data in party_raw_data.items():
            # Invert and normalize: high variance -> low cohesion
            normalized_variance = data['variance'] / max_var
            cohesion_score = (1 - normalized_variance) * 100
            
            result[party] = {
                'cohesion_score': round(cohesion_score, 1),
                'variance': round(data['variance'], 6),
                'n_members': data['n_members'],
                'n_speeches': data['n_speeches'],
                'classification': 'compatto' if cohesion_score > 70 else ('frammentato' if cohesion_score < 30 else 'moderato')
            }
    
    logger.info("Computed cohesion scores for %d parties", len(result))
    
    return result


def categorize_party_coalition(party: str) -> str:
    """Categorize party as left, center, or right."""
    # Check against configured party lists
    for left in LEFT_PARTIES:
        if left.lower() in party.lower() or party.lower() in left.lower():
            return 'left'
    for right in RIGHT_PARTIES:
        if right.lower() in party.lower() or party.lower() in right.lower():
            return 'right'
    for center in CENTER_PARTIES:
        if center.lower() in party.lower() or party.lower() in center.lower():
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
    
    For each topic/cluster, computes what percentage comes from left vs right,
    identifying bipartisan topics (high overlap) vs polarized topics.
    
    Returns:
        {
            cluster_id: {
                'label': 'Topic Label',
                'left_pct': float,
                'right_pct': float,
                'center_pct': float,
                'overlap_score': 0-100 (higher = more bipartisan),
                'classification': 'bipartisan' | 'left-leaning' | 'right-leaning' | 'polarized'
            },
            ...
        }
    """
    result = {}
    
    # Categorize each party
    df = df.copy()
    df['coalition'] = df[party_col].apply(categorize_party_coalition)
    
    for cluster_id in df[cluster_col].unique():
        cluster_df = df[df[cluster_col] == cluster_id]
        total = len(cluster_df)
        
        if total == 0:
            continue
        
        # Count by coalition
        coalition_counts = cluster_df['coalition'].value_counts()
        left_count = coalition_counts.get('left', 0)
        right_count = coalition_counts.get('right', 0)
        center_count = coalition_counts.get('center', 0)
        
        left_pct = (left_count / total) * 100
        right_pct = (right_count / total) * 100
        center_pct = (center_count / total) * 100
        
        # Overlap score: how balanced is the cluster?
        # High score = balanced representation from multiple coalitions
        # Formula: 100 - |left_pct - right_pct|
        # If perfectly balanced (50-50), score = 100
        # If completely one-sided (100-0), score = 0
        imbalance = abs(left_pct - right_pct)
        overlap_score = 100 - imbalance
        
        # Classification
        if overlap_score > 60 and left_pct > 20 and right_pct > 20:
            classification = 'bipartisan'
        elif left_pct > right_pct + 30:
            classification = 'left-leaning'
        elif right_pct > left_pct + 30:
            classification = 'right-leaning'
        else:
            classification = 'mixed'
        
        label = cluster_labels.get(cluster_id, f"Cluster {cluster_id}") if cluster_labels else f"Cluster {cluster_id}"
        
        result[int(cluster_id)] = {
            'label': label,
            'left_pct': round(left_pct, 1),
            'right_pct': round(right_pct, 1),
            'center_pct': round(center_pct, 1),
            'overlap_score': round(overlap_score, 1),
            'classification': classification,
            'total_speeches': total
        }
    
    logger.info("Computed thematic overlap for %d clusters", len(result))
    
    return result


def find_closest_cross_party_pairs(
    df: pd.DataFrame,
    embeddings: np.ndarray,
    speaker_col: str = 'deputy',
    party_col: str = 'group',
    top_n: int = 20
) -> list[dict]:
    """
    Find pairs of speakers from different parties with most similar discourse.
    
    Returns list of unusual cross-party pairs sorted by similarity.
    """
    # Group by speaker and compute average embedding
    speakers = df[speaker_col].unique()
    speaker_data = {}
    
    for speaker in speakers:
        mask = df[speaker_col] == speaker
        party = df[mask][party_col].iloc[0]
        
        if party == 'Unknown Group':
            continue
            
        avg_embedding = np.mean(embeddings[mask], axis=0)
        speaker_data[speaker] = {
            'party': party,
            'embedding': avg_embedding,
            'coalition': categorize_party_coalition(party)
        }
    
    # Find cross-party similarities
    pairs = []
    speaker_list = list(speaker_data.keys())
    
    for i, s1 in enumerate(speaker_list):
        for s2 in speaker_list[i+1:]:
            p1 = speaker_data[s1]['party']
            p2 = speaker_data[s2]['party']
            c1 = speaker_data[s1]['coalition']
            c2 = speaker_data[s2]['coalition']
            
            # Skip same party
            if p1 == p2:
                continue
            
            # Compute similarity
            e1 = speaker_data[s1]['embedding']
            e2 = speaker_data[s2]['embedding']
            similarity = float(np.dot(e1, e2) / (np.linalg.norm(e1) * np.linalg.norm(e2) + 1e-10))
            
            pairs.append({
                'speaker1': s1,
                'party1': p1,
                'coalition1': c1,
                'speaker2': s2,
                'party2': p2,
                'coalition2': c2,
                'similarity': round(similarity, 4),
                'crosses_divide': c1 != c2 and c1 != 'other' and c2 != 'other'
            })
    
    # Sort by similarity
    pairs.sort(key=lambda x: -x['similarity'])
    
    logger.info("Found %d cross-party pairs, returning top %d", len(pairs), min(top_n, len(pairs)))
    
    return pairs[:top_n]
