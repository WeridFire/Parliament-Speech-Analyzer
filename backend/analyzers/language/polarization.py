"""
Polarization - "Us vs Them" language.

Counts oppositional markers (noi/loro pronouns, adversative terms, us-them
formulas) and reports their density. The score says how *oppositional the
phrasing* is, not how extreme the position: quoting an opponent in order to
disagree scores the same as meaning it.

Scores go out in the shared `{raw, pct, n}` shape - see backend/scoring - so
`raw` carries a real unit (markers per thousand words) and `pct` carries
standing within the corpus. Speaker and group rates are word-weighted, and a
speaker needs a minimum sample: the previous ranking was led by members with
three speeches.
"""

import logging

import pandas as pd

from backend.scoring import Score, percentile_ranks
from backend.scoring.normalize import classify_by_percentile

logger = logging.getLogger(__name__)

MIN_SPEECHES = 10


def _weighted_rate(group: pd.DataFrame) -> float:
    words = group['n_words'].sum()
    if not words:
        return 0.0
    return float((group['polarization'] * group['n_words']).sum() / words)


def compute_polarization_scores(
    df: pd.DataFrame,
    speaker_col: str = 'deputy',
    party_col: str = 'group'
) -> dict:
    """
    Aggregate polarization by speaker and party.

    Returns:
        {
            'by_speaker': {speaker: {raw, pct, n, classification, party}},
            'by_party': {party: {raw, pct, n, classification}},
            'top_polarizers': [{speaker, party, raw, pct, n}],
            'least_polarizers': [...],
            'unit': 'markers per 1000 words'
        }
    """
    speaker_rates, speaker_counts, speaker_party = {}, {}, {}
    for speaker, rows in df.groupby(speaker_col):
        if len(rows) < MIN_SPEECHES:
            continue
        speaker_rates[speaker] = _weighted_rate(rows)
        speaker_counts[speaker] = len(rows)
        speaker_party[speaker] = rows[party_col].iloc[0]

    party_rates, party_counts = {}, {}
    for party, rows in df.groupby(party_col):
        party_rates[party] = _weighted_rate(rows)
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
