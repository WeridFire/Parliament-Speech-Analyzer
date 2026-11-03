"""
Readability - Gulpease index for Italian text complexity.

Score interpretation:
- < 55: Difficult (university level)
- 55-80: Medium (high school level)
- > 80: Easy (elementary level)

Each speech is scored once in `core.features`; this aggregates. Group and
speaker scores are word-weighted (total letters, words and sentences pooled),
so a one-line interjection does not count as much as a twenty-minute speech.
"""

import logging

import pandas as pd

from backend.core.features import gulpease

logger = logging.getLogger(__name__)

MIN_SPEAKER_SPEECHES = 5


def _classify_readability(score: float) -> str:
    """Classify readability score into category."""
    if score < 55:
        return 'difficile'
    if score < 80:
        return 'medio'
    return 'facile'


def _pooled(group: pd.DataFrame) -> float:
    return gulpease(int(group['n_words'].sum()), int(group['n_sentences'].sum()), int(group['n_letters'].sum()))


def compute_readability_scores(
    df: pd.DataFrame,
    speaker_col: str = 'deputy',
    party_col: str = 'group',
) -> dict:
    """
    Returns:
        {
            'by_speaker': {speaker: {avg_score, classification, n_speeches, party}},
            'by_party': {party: {avg_score, classification, n_speeches}},
            'distribution': {'difficile': n, 'medio': n, 'facile': n}   per speech
        }
    """
    result = {
        'by_speaker': {},
        'by_party': {},
        'distribution': df['gulpease'].map(_classify_readability).value_counts().to_dict(),
    }

    for speaker, group in df.groupby(speaker_col):
        if len(group) < MIN_SPEAKER_SPEECHES:
            continue
        score = _pooled(group)
        result['by_speaker'][speaker] = {
            'avg_score': round(score, 1),
            'classification': _classify_readability(score),
            'n_speeches': int(len(group)),
            'party': group[party_col].iloc[0],
        }

    for party, group in df.groupby(party_col):
        score = _pooled(group)
        result['by_party'][party] = {
            'avg_score': round(score, 1),
            'classification': _classify_readability(score),
            'n_speeches': int(len(group)),
        }

    logger.info(
        "Computed readability scores for %d speakers and %d parties",
        len(result['by_speaker']), len(result['by_party'])
    )
    return result
