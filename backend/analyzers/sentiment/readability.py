"""
Readability - Gulpease index for Italian text complexity.
"""

import logging
import re

import pandas as pd

logger = logging.getLogger(__name__)


def compute_gulpease_score(text: str) -> dict:
    """
    Compute Gulpease readability index for Italian text.
    
    Formula: 89 + (300 * sentences - 10 * letters) / words
    
    Score interpretation:
    - < 55: Difficult (university level)
    - 55-80: Medium (high school level)
    - > 80: Easy (elementary level)
    
    Args:
        text: Input text
    
    Returns:
        {
            'score': float,
            'classification': 'difficile' | 'medio' | 'facile',
            'n_words': int,
            'n_sentences': int,
            'n_letters': int
        }
    """
    text = str(text).strip()
    
    if not text:
        return {
            'score': 0,
            'classification': 'n/a',
            'n_words': 0,
            'n_sentences': 0,
            'n_letters': 0
        }
    
    # Count words
    words = re.findall(r'\b\w+\b', text)
    n_words = len(words)
    
    if n_words == 0:
        return {
            'score': 0,
            'classification': 'n/a',
            'n_words': 0,
            'n_sentences': 0,
            'n_letters': 0
        }
    
    # Count sentences (approximate by punctuation)
    sentences = re.split(r'[.!?]+', text)
    n_sentences = len([s for s in sentences if s.strip()])
    n_sentences = max(n_sentences, 1)  # At least one sentence
    
    # Count letters (only alphabetic characters)
    n_letters = sum(1 for c in text if c.isalpha())
    
    # Gulpease formula
    score = 89 + (300 * n_sentences - 10 * n_letters) / n_words
    
    # Clamp to 0-100
    score = max(0, min(100, score))
    
    # Classification
    classification = _classify_readability(score)
    
    return {
        'score': round(score, 1),
        'classification': classification,
        'n_words': n_words,
        'n_sentences': n_sentences,
        'n_letters': n_letters
    }


def compute_readability_scores(
    df: pd.DataFrame,
    text_col: str = 'cleaned_text',
    speaker_col: str = 'deputy',
    party_col: str = 'group'
) -> dict:
    """
    Compute readability scores for all speeches and aggregate by speaker/party.
    
    Args:
        df: DataFrame with speeches
        text_col: Column with cleaned text
        speaker_col: Column with speaker names
        party_col: Column with party names
    
    Returns:
        {
            'by_speaker': {speaker: {avg_score, classification, n_speeches}, ...},
            'by_party': {party: {avg_score, classification, n_speeches}, ...},
            'distribution': {'difficile': count, 'medio': count, 'facile': count}
        }
    """
    # Compute per-speech scores
    scores = df[text_col].apply(compute_gulpease_score)
    df = df.copy()
    df['gulpease'] = scores.apply(lambda x: x['score'])
    df['readability_class'] = scores.apply(lambda x: x['classification'])
    
    result = {
        'by_speaker': {},
        'by_party': {},
        'distribution': df['readability_class'].value_counts().to_dict()
    }
    
    # Aggregate by speaker
    for speaker in df[speaker_col].unique():
        speaker_df = df[df[speaker_col] == speaker]
        avg_score = speaker_df['gulpease'].mean()
        
        result['by_speaker'][speaker] = {
            'avg_score': round(avg_score, 1),
            'classification': _classify_readability(avg_score),
            'n_speeches': len(speaker_df)
        }
    
    # Aggregate by party
    for party in df[party_col].unique():
        if party == 'Unknown Group':
            continue
            
        party_df = df[df[party_col] == party]
        avg_score = party_df['gulpease'].mean()
        
        result['by_party'][party] = {
            'avg_score': round(avg_score, 1),
            'classification': _classify_readability(avg_score),
            'n_speeches': len(party_df)
        }
    
    logger.info(
        "Computed readability scores for %d speakers and %d parties",
        len(result['by_speaker']), len(result['by_party'])
    )
    
    return result


def _classify_readability(score: float) -> str:
    """Classify readability score into category."""
    if score < 55:
        return 'difficile'
    elif score < 80:
        return 'medio'
    else:
        return 'facile'
