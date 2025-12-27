"""
Rhetoric Analyzer - Analyze speech style and rhetoric patterns

This module identifies rhetorical patterns like populist speech,
anti-establishment rhetoric, and emotional language.
"""

import logging
import re
from typing import Optional
from collections import Counter

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# Rhetorical pattern keywords (Italian)
POPULIST_MARKERS = {
    'élite', 'elite', 'casta', 'popolo', 'gente', 'cittadini', 'traditi',
    'sistema', 'establishment', 'palazzo', 'potere', 'potenti', 'oligarchia',
    'banche', 'banchieri', 'lobby', 'burocrati', 'tecnocrati', 'privilegiati'
}

ANTI_ESTABLISHMENT_MARKERS = {
    'vergogna', 'scandalo', 'corruzione', 'corrotti', 'ladri', 'rubato',
    'fallimento', 'fallito', 'disastro', 'disastroso', 'inaccettabile',
    'intollerabile', 'responsabili', 'colpevoli', 'immorale', 'indegno'
}

EMOTIONAL_INTENSIFIERS = {
    'assolutamente', 'completamente', 'totalmente', 'incredibile', 'incredibilmente',
    'gravissimo', 'gravissima', 'urgente', 'urgentissimo', 'drammatico',
    'drammaticamente', 'straordinario', 'eccezionale', 'storico', 'epocale',
    'fondamentale', 'cruciale', 'vitale', 'essenziale', 'indispensabile'
}

INSTITUTIONAL_MARKERS = {
    'proposta', 'emendamento', 'normativa', 'legislazione', 'procedura',
    'regolamento', 'commissione', 'relazione', 'parere', 'valutazione',
    'analisi', 'studio', 'dati', 'statistiche', 'documento', 'articolo',
    'comma', 'decreto', 'disposizione', 'provvedimento', 'iter'
}


def tokenize_simple(text: str) -> list[str]:
    """Simple tokenization for rhetoric analysis."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    return text.split()


def count_markers(tokens: list[str], markers: set[str]) -> int:
    """Count how many marker words appear in tokens."""
    return sum(1 for t in tokens if t in markers)


def compute_rhetoric_scores(text: str) -> dict[str, float]:
    """
    Compute rhetoric style scores for a single text.
    
    Returns dict with:
        - populist: 0-1 score for populist rhetoric
        - anti_establishment: 0-1 score for anti-establishment
        - emotional: 0-1 score for emotional intensity
        - institutional: 0-1 score for institutional/formal language
    """
    tokens = tokenize_simple(text)
    n_tokens = len(tokens) if tokens else 1
    
    # Normalize by text length
    return {
        'populist': count_markers(tokens, POPULIST_MARKERS) / n_tokens * 100,
        'anti_establishment': count_markers(tokens, ANTI_ESTABLISHMENT_MARKERS) / n_tokens * 100,
        'emotional': count_markers(tokens, EMOTIONAL_INTENSIFIERS) / n_tokens * 100,
        'institutional': count_markers(tokens, INSTITUTIONAL_MARKERS) / n_tokens * 100,
    }


def add_rhetoric_scores(df: pd.DataFrame, text_col: str = 'cleaned_text') -> pd.DataFrame:
    """
    Add rhetoric score columns to DataFrame.
    
    Returns DataFrame with added columns: populist, anti_establishment, emotional, institutional
    """
    scores = df[text_col].apply(compute_rhetoric_scores)
    
    df = df.copy()
    df['populist'] = scores.apply(lambda x: x['populist'])
    df['anti_establishment'] = scores.apply(lambda x: x['anti_establishment'])
    df['emotional'] = scores.apply(lambda x: x['emotional'])
    df['institutional'] = scores.apply(lambda x: x['institutional'])
    
    return df


def compute_rhetoric_profile(
    df: pd.DataFrame,
    group_col: str = 'deputy'
) -> pd.DataFrame:
    """
    Compute average rhetoric profile per speaker or party.
    
    Returns DataFrame with rhetoric averages per group.
    """
    required_cols = ['populist', 'anti_establishment', 'emotional', 'institutional']
    
    # Check if scores exist
    if not all(col in df.columns for col in required_cols):
        df = add_rhetoric_scores(df)
    
    return df.groupby(group_col)[required_cols].mean().reset_index()


def find_rhetorical_twins(
    df: pd.DataFrame,
    speaker_col: str = 'deputy',
    party_col: str = 'group',
    top_n: int = 10
) -> list[dict]:
    """
    Find pairs from different parties with similar rhetorical style.
    """
    profiles = compute_rhetoric_profile(df, speaker_col)
    
    # Get speaker -> party mapping
    speaker_party = df.groupby(speaker_col)[party_col].first().to_dict()
    
    # Compute pairwise similarity
    style_cols = ['populist', 'anti_establishment', 'emotional', 'institutional']
    
    pairs = []
    speakers = profiles[speaker_col].tolist()
    
    for i, s1 in enumerate(speakers):
        for s2 in speakers[i+1:]:
            p1 = speaker_party.get(s1, 'Unknown')
            p2 = speaker_party.get(s2, 'Unknown')
            
            # Skip same party or Unknown
            if p1 == p2 or p1 == 'Unknown Group' or p2 == 'Unknown Group':
                continue
            
            # Compute style distance
            v1 = profiles[profiles[speaker_col] == s1][style_cols].values[0]
            v2 = profiles[profiles[speaker_col] == s2][style_cols].values[0]
            
            distance = np.linalg.norm(v1 - v2)
            similarity = 1 / (1 + distance)
            
            # Dominant style
            dominant1 = style_cols[np.argmax(v1)]
            dominant2 = style_cols[np.argmax(v2)]
            
            pairs.append({
                'speaker1': s1,
                'party1': p1,
                'speaker2': s2,
                'party2': p2,
                'style_similarity': similarity,
                'shared_style': dominant1 if dominant1 == dominant2 else 'mixed'
            })
    
    pairs.sort(key=lambda x: -x['style_similarity'])
    return pairs[:top_n]


def classify_rhetorical_style(row: pd.Series) -> str:
    """Classify a speech into a rhetorical category."""
    scores = {
        'populist': row.get('populist', 0),
        'anti_establishment': row.get('anti_establishment', 0),
        'emotional': row.get('emotional', 0),
        'institutional': row.get('institutional', 0)
    }
    
    max_score = max(scores.values())
    if max_score < 0.2:
        return 'neutrale'
    
    dominant = max(scores, key=scores.get)
    return dominant
