"""
Polarization - "Us vs Them" language.

Counts oppositional markers (noi/loro pronouns, adversative terms, us-them
formulas) and reports their density. The score says how *oppositional the
phrasing* is, not how extreme the position: quoting an opponent in order to
disagree scores the same as meaning it.

Scores go out in the shared `{raw, pct, n}` shape - see backend/scoring - so
`raw` carries a real unit (markers per thousand words) and `pct` carries
standing within the corpus. The previous version multiplied the density by 500
and clamped it to 100, which flattened everyone above a modest threshold into a
single indistinguishable top score.
"""

import logging

import pandas as pd

from backend.config import POLARIZATION_PRONOUNS, ADVERSATIVE_TERMS, US_THEM_PATTERNS
from backend.scoring import Score, percentile_ranks, rate_per_thousand
from backend.scoring.normalize import classify_by_percentile

from .utils import tokenize_simple, count_keywords

logger = logging.getLogger(__name__)

# Relative weight of each marker family. A fixed formula, stated here rather
# than buried in the arithmetic.
PRONOUN_WEIGHT = 1
ADVERSATIVE_WEIGHT = 2
PATTERN_WEIGHT = 3

MIN_SPEECHES = 3


def compute_polarization_score(text: str) -> dict:
    """
    Oppositional marker density for one speech.

    Returns:
        {
            'rate': markers per thousand words (unbounded),
            'pronoun_count', 'adversative_count', 'pattern_count': int,
            'n_words': int
        }
    """
    text_lower = str(text).lower()
    tokens = tokenize_simple(text_lower)
    n_words = len(tokens)

    pronoun_count = count_keywords(tokens, {p.lower() for p in POLARIZATION_PRONOUNS})
    adversative_count = count_keywords(tokens, {a.lower() for a in ADVERSATIVE_TERMS})
    pattern_count = sum(1 for pattern in US_THEM_PATTERNS if pattern.lower() in text_lower)

    weighted = (
        pronoun_count * PRONOUN_WEIGHT
        + adversative_count * ADVERSATIVE_WEIGHT
        + pattern_count * PATTERN_WEIGHT
    )

    return {
        'rate': rate_per_thousand(weighted, n_words),
        'pronoun_count': pronoun_count,
        'adversative_count': adversative_count,
        'pattern_count': pattern_count,
        'n_words': n_words,
    }


def compute_polarization_scores(
    df: pd.DataFrame,
    text_col: str = 'cleaned_text',
    speaker_col: str = 'deputy',
    party_col: str = 'group'
) -> dict:
    """
    Aggregate polarization by speaker and party.

    Returns:
        {
            'by_speaker': {speaker: {raw, pct, n, classification, party}},
            'by_party': {party: {raw, pct, n, classification}},
            'top_polarizers': [{speaker, party, raw, pct}],
            'least_polarizers': [...],
            'unit': 'markers per 1000 words'
        }
    """
    df = df.copy()
    df['_polarization_rate'] = df[text_col].apply(lambda t: compute_polarization_score(t)['rate'])

    speaker_rates, speaker_counts, speaker_party = {}, {}, {}
    for speaker, rows in df.groupby(speaker_col):
        if len(rows) < MIN_SPEECHES:
            continue
        speaker_rates[speaker] = float(rows['_polarization_rate'].mean())
        speaker_counts[speaker] = len(rows)
        speaker_party[speaker] = rows[party_col].iloc[0]

    party_rates, party_counts = {}, {}
    for party, rows in df.groupby(party_col):
        if party == 'Unknown Group':
            continue
        party_rates[party] = float(rows['_polarization_rate'].mean())
        party_counts[party] = len(rows)

    speaker_pct = percentile_ranks(speaker_rates)
    party_pct = percentile_ranks(party_rates)

    by_speaker = {
        speaker: {
            **Score(raw=rate, pct=speaker_pct[speaker], n=speaker_counts[speaker]).as_dict(),
            'classification': classify_by_percentile(speaker_pct[speaker]),
            'party': speaker_party[speaker],
        }
        for speaker, rate in speaker_rates.items()
    }

    by_party = {
        party: {
            **Score(raw=rate, pct=party_pct[party], n=party_counts[party]).as_dict(),
            'classification': classify_by_percentile(party_pct[party]),
        }
        for party, rate in party_rates.items()
    }

    ranked = sorted(
        (
            {
                'speaker': speaker,
                'party': speaker_party[speaker],
                'raw': round(rate, 2),
                'pct': round(speaker_pct[speaker], 1),
                'n': speaker_counts[speaker],
            }
            for speaker, rate in speaker_rates.items()
        ),
        key=lambda entry: -entry['raw'],
    )

    logger.info(
        "Computed polarization for %d speakers and %d parties",
        len(by_speaker), len(by_party),
    )

    return {
        'by_speaker': by_speaker,
        'by_party': by_party,
        'top_polarizers': ranked[:10],
        'least_polarizers': ranked[-10:][::-1],
        'unit': 'markers per 1000 words',
    }
