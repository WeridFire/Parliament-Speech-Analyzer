"""
Faction Detector - Analyze internal party divisions

This module identifies potential factions within political parties
by measuring how much each senator's speech patterns deviate from
their party's mainstream.
"""

import logging
import numpy as np
import pandas as pd

from .relations import compute_party_centroids

logger = logging.getLogger(__name__)



def compute_senator_conformity(
    df: pd.DataFrame,
    embeddings: np.ndarray,
    speaker_col: str = 'deputy',
    party_col: str = 'group'
) -> pd.DataFrame:
    """
    Compute conformity scores for each senator.
    
    Returns DataFrame with senator profiles and scores.
    """
    # Compute party centroids
    centroids = compute_party_centroids(df, embeddings, party_col)
    
    if not centroids:
        return pd.DataFrame()
    
    # Get unique speakers
    speakers = df[speaker_col].unique()
    
    profiles = []
    
    for speaker in speakers:
        speaker_mask = df[speaker_col] == speaker
        speaker_df = df[speaker_mask]
        speaker_embeddings = embeddings[speaker_mask]
        
        if len(speaker_embeddings) < 1:
            continue
        
        party = speaker_df[party_col].iloc[0]
        n_speeches = len(speaker_df)
        
        # Average embedding for this speaker
        speaker_centroid = np.mean(speaker_embeddings, axis=0)
        
        # Distance to own party centroid
        if party in centroids:
            own_distance = np.linalg.norm(speaker_centroid - centroids[party])
        else:
            own_distance = float('inf')
        
        # Distance to other party centroids
        other_distances = {}
        for other_party, centroid in centroids.items():
            if other_party != party:
                other_distances[other_party] = np.linalg.norm(speaker_centroid - centroid)
        
        # Nearest other party
        if other_distances:
            nearest_other = min(other_distances, key=other_distances.get)
            nearest_distance = other_distances[nearest_other]
        else:
            nearest_other = "N/A"
            nearest_distance = float('inf')
        
        # Conformity score: inverse of distance to own party, normalized
        # Higher = more conforming
        max_distance = max(own_distance, 1.0)  # Avoid division by zero
        conformity = 1.0 / (1.0 + own_distance)
        
        # Cross-party affinity: how close to nearest other party
        cross_affinity = 1.0 / (1.0 + nearest_distance)
        
        # Label
        if conformity > 0.7:
            label = "mainstream"
        elif cross_affinity > conformity:
            label = "bridge"  # Closer to other party than own
        else:
            label = "maverick"  # Far from both
        
        profiles.append({
            'speaker': speaker,
            'party': party,
            'n_speeches': n_speeches,
            'conformity': conformity,
            'nearest_other_party': nearest_other,
            'cross_affinity': cross_affinity,
            'faction_label': label
        })
    
    return pd.DataFrame(profiles)


def find_party_factions(
    df: pd.DataFrame,
    embeddings: np.ndarray,
    party: str,
    party_col: str = 'group'
) -> dict:
    """
    Analyze factions within a specific party.
    
    Returns dict with faction analysis.
    """
    profiles = compute_senator_conformity(df, embeddings, party_col=party_col)
    
    if profiles.empty:
        return {}
    
    party_profiles = profiles[profiles['party'] == party]
    
    if party_profiles.empty:
        return {}
    
    return {
        'party': party,
        'n_senators': len(party_profiles),
        'avg_conformity': party_profiles['conformity'].mean(),
        'mavericks': party_profiles[party_profiles['faction_label'] == 'maverick']['speaker'].tolist(),
        'bridges': party_profiles[party_profiles['faction_label'] == 'bridge']['speaker'].tolist(),
        'mainstream': party_profiles[party_profiles['faction_label'] == 'mainstream']['speaker'].tolist(),
    }


def get_all_factions(df: pd.DataFrame, embeddings: np.ndarray) -> dict[str, dict]:
    """Get faction analysis for all parties."""
    parties = [p for p in df['group'].unique() if p != 'Unknown Group']
    return {party: find_party_factions(df, embeddings, party) for party in parties}
