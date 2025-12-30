"""
Transversal Themes - Cross-party alignment detection.
"""
import logging
import numpy as np
import pandas as pd

from backend.analyzers.relations.overlap import categorize_party_coalition

logger = logging.getLogger(__name__)


def compute_cluster_party_composition(
    df: pd.DataFrame,
    cluster_col: str = 'cluster',
    party_col: str = 'group'
) -> pd.DataFrame:
    """Compute party composition of each cluster."""
    results = []
    
    for cluster_id in df[cluster_col].unique():
        cluster_df = df[df[cluster_col] == cluster_id]
        
        party_counts = cluster_df[party_col].value_counts()
        total = len(cluster_df)
        
        known_parties = {p: c for p, c in party_counts.items() if p != 'Unknown Group'}
        n_parties = len(known_parties)
        
        # Entropy-based mixing score
        if n_parties > 1 and sum(known_parties.values()) > 0:
            proportions = np.array(list(known_parties.values())) / sum(known_parties.values())
            entropy = -np.sum(proportions * np.log(proportions + 1e-10))
            max_entropy = np.log(n_parties)
            mixing_score = entropy / max_entropy if max_entropy > 0 else 0
        else:
            mixing_score = 0
        
        results.append({
            'cluster': cluster_id,
            'n_speeches': total,
            'n_parties': n_parties,
            'parties': list(known_parties.keys()),
            'party_counts': dict(party_counts),
            'mixing_score': round(mixing_score, 4)
        })
    
    return pd.DataFrame(results).sort_values('mixing_score', ascending=False)


def find_transversal_clusters(
    df: pd.DataFrame,
    min_parties: int = 3,
    min_mixing: float = 0.5
) -> list:
    """Find clusters with high cross-party mixing."""
    composition = compute_cluster_party_composition(df)
    
    transversal = composition[
        (composition['n_parties'] >= min_parties) & 
        (composition['mixing_score'] >= min_mixing)
    ]
    
    return transversal.to_dict('records')


def find_unusual_pairs(
    df: pd.DataFrame,
    embeddings: np.ndarray,
    speaker_col: str = 'deputy',
    party_col: str = 'group',
    top_n: int = 10
) -> list:
    """Find speakers from different parties who speak similarly."""
    speakers = df[speaker_col].unique()
    speaker_data = {}
    
    for speaker in speakers:
        mask = df[speaker_col] == speaker
        party = df[mask][party_col].iloc[0]
        if party != 'Unknown Group' and mask.sum() >= 3:
            speaker_data[speaker] = {
                'party': party,
                'embedding': np.mean(embeddings[mask], axis=0)
            }
    
    pairs = []
    speaker_list = list(speaker_data.keys())
    
    for i, s1 in enumerate(speaker_list):
        for s2 in speaker_list[i+1:]:
            p1 = speaker_data[s1]['party']
            p2 = speaker_data[s2]['party']
            
            if p1 == p2:
                continue
            
            e1 = speaker_data[s1]['embedding']
            e2 = speaker_data[s2]['embedding']
            similarity = float(np.dot(e1, e2) / (np.linalg.norm(e1) * np.linalg.norm(e2) + 1e-10))
            
            pairs.append({
                'speaker1': s1, 'party1': p1,
                'speaker2': s2, 'party2': p2,
                'similarity': round(similarity, 4)
            })
    
    pairs.sort(key=lambda x: -x['similarity'])
    return pairs[:top_n]


def find_left_right_alliances(df: pd.DataFrame, embeddings: np.ndarray) -> list:
    """Find alliances crossing the left-right divide."""
    pairs = find_unusual_pairs(df, embeddings, top_n=50)
    
    cross_divide = []
    for pair in pairs:
        cat1 = categorize_party_coalition(pair['party1'])
        cat2 = categorize_party_coalition(pair['party2'])
        
        if (cat1 == 'left' and cat2 == 'right') or (cat1 == 'right' and cat2 == 'left'):
            pair['type'] = 'left-right'
            cross_divide.append(pair)
    
    return cross_divide[:10]
