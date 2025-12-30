"""
Polarization - "Us vs Them" language analysis.
"""

import logging

import pandas as pd

from backend.config import POLARIZATION_PRONOUNS, ADVERSATIVE_TERMS, US_THEM_PATTERNS
from .utils import tokenize_simple, count_keywords

logger = logging.getLogger(__name__)


def compute_polarization_score(text: str) -> dict:
    """
    Compute polarization score based on "Us vs Them" language.
    
    Analyzes:
    - Pronoun usage (noi/loro/voi)
    - Adversative terms (contro, nemici, etc.)
    - Us-them patterns
    
    Args:
        text: Input text
    
    Returns:
        {
            'score': 0-100 (higher = more polarizing),
            'pronoun_count': int,
            'adversative_count': int,
            'pattern_count': int,
            'classification': 'bassa' | 'media' | 'alta'
        }
    """
    text_lower = str(text).lower()
    tokens = tokenize_simple(text_lower)
    n_words = len(tokens) if tokens else 1
    
    # Count pronouns
    pronouns_lower = {p.lower() for p in POLARIZATION_PRONOUNS}
    pronoun_count = count_keywords(tokens, pronouns_lower)
    
    # Count adversative terms
    adversative_lower = {a.lower() for a in ADVERSATIVE_TERMS}
    adversative_count = count_keywords(tokens, adversative_lower)
    
    # Count patterns
    pattern_count = sum(1 for pattern in US_THEM_PATTERNS if pattern.lower() in text_lower)
    
    # Compute score
    # Weight: pronouns * 1, adversative * 2, patterns * 3
    raw_score = (pronoun_count * 1 + adversative_count * 2 + pattern_count * 3)
    
    # Normalize by text length and scale to 0-100
    normalized_score = (raw_score / n_words) * 500  # Empirical scaling
    score = min(100, max(0, normalized_score))
    
    # Classification
    classification = _classify_polarization(score)
    
    return {
        'score': round(score, 1),
        'pronoun_count': pronoun_count,
        'adversative_count': adversative_count,
        'pattern_count': pattern_count,
        'classification': classification
    }


def compute_polarization_scores(
    df: pd.DataFrame,
    text_col: str = 'cleaned_text',
    speaker_col: str = 'deputy',
    party_col: str = 'group'
) -> dict:
    """
    Compute polarization scores for all speeches and aggregate.
    
    Args:
        df: DataFrame with speeches
        text_col: Column with cleaned text
        speaker_col: Column with speaker names
        party_col: Column with party names
    
    Returns:
        {
            'by_speaker': {speaker: {avg_score, classification, ...}, ...},
            'by_party': {party: {avg_score, classification, ...}, ...},
            'top_polarizers': [{speaker, party, score}, ...],
            'least_polarizers': [{speaker, party, score}, ...]
        }
    """
    # Compute per-speech scores
    scores = df[text_col].apply(compute_polarization_score)
    df = df.copy()
    df['polarization'] = scores.apply(lambda x: x['score'])
    df['polarization_class'] = scores.apply(lambda x: x['classification'])
    
    result = {
        'by_speaker': {},
        'by_party': {},
        'top_polarizers': [],
        'least_polarizers': []
    }
    
    # Aggregate by speaker
    speaker_scores = []
    for speaker in df[speaker_col].unique():
        speaker_df = df[df[speaker_col] == speaker]
        
        if len(speaker_df) < 3:  # Minimum speeches
            continue
            
        avg_score = speaker_df['polarization'].mean()
        party = speaker_df[party_col].iloc[0]
        
        result['by_speaker'][speaker] = {
            'avg_score': round(avg_score, 1),
            'classification': _classify_polarization(avg_score),
            'n_speeches': len(speaker_df),
            'party': party
        }
        
        speaker_scores.append({
            'speaker': speaker,
            'party': party,
            'score': round(avg_score, 1)
        })
    
    # Aggregate by party
    for party in df[party_col].unique():
        if party == 'Unknown Group':
            continue
            
        party_df = df[df[party_col] == party]
        avg_score = party_df['polarization'].mean()
        
        result['by_party'][party] = {
            'avg_score': round(avg_score, 1),
            'classification': _classify_polarization(avg_score),
            'n_speeches': len(party_df)
        }
    
    # Top and least polarizers
    speaker_scores.sort(key=lambda x: -x['score'])
    result['top_polarizers'] = speaker_scores[:10]
    result['least_polarizers'] = speaker_scores[-10:][::-1]
    
    logger.info(
        "Computed polarization scores for %d speakers and %d parties",
        len(result['by_speaker']), len(result['by_party'])
    )
    
    return result


def _classify_polarization(score: float) -> str:
    """Classify polarization score into category."""
    if score < 20:
        return 'bassa'
    elif score < 50:
        return 'media'
    else:
        return 'alta'
