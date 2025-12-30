"""
Cross-Party Pairs - Similar speakers from different parties.
"""
import logging
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


def find_closest_cross_party_pairs(
    df: pd.DataFrame,
    embeddings: np.ndarray,
    speaker_col: str = 'deputy',
    party_col: str = 'group',
    top_n: int = 20
) -> list:
    """
    Find pairs of speakers from different parties with most similar discourse.
    """
    speakers = df[speaker_col].unique()
    
    # Compute average embedding per speaker
    speaker_data = {}
    for speaker in speakers:
        mask = df[speaker_col] == speaker
        if mask.sum() < 3:  # Minimum speeches
            continue
        
        party = df[mask][party_col].iloc[0]
        if party == 'Unknown Group':
            continue
            
        avg_embedding = np.mean(embeddings[mask], axis=0)
        speaker_data[speaker] = {'party': party, 'embedding': avg_embedding}
    
    if len(speaker_data) < 2:
        return []
    
    # Find cross-party pairs
    pairs = []
    speaker_list = list(speaker_data.keys())
    
    for i, s1 in enumerate(speaker_list):
        for s2 in speaker_list[i + 1:]:
            p1 = speaker_data[s1]['party']
            p2 = speaker_data[s2]['party']
            
            if p1 == p2:
                continue
            
            e1 = speaker_data[s1]['embedding']
            e2 = speaker_data[s2]['embedding']
            
            similarity = float(np.dot(e1, e2) / (np.linalg.norm(e1) * np.linalg.norm(e2) + 1e-10))
            
            pairs.append({
                'speaker1': s1,
                'party1': p1,
                'speaker2': s2,
                'party2': p2,
                'similarity': round(similarity, 4)
            })
    
    pairs.sort(key=lambda x: -x['similarity'])
    
    logger.info("Found %d cross-party pairs, returning top %d", len(pairs), top_n)
    return pairs[:top_n]
