"""
Mentions - which groups talk about which public figures.

Each speech is scanned once (`core.features.find_mentions`) for a curated list
of leaders, ministers and foreign heads of government; see
`backend.config.figures` for why the list is curated rather than every member.
A speech counts once per figure it names. Rates are per 100 speeches of the
mentioning group, so a large group does not dominate simply by speaking more.
"""

import logging
from collections import Counter, defaultdict

import pandas as pd

from backend.analyzers.common import blocs_of
from backend.config import FIGURE_GROUP_LABELS, FIGURES, MAGGIORANZA, OPPOSIZIONE

logger = logging.getLogger(__name__)

MIN_PARTY_SPEECHES = 30
MIN_FIGURE_MENTIONS = 5
MATRIX_FIGURES = 15
TOP_SPEAKERS = 5

_BY_ID = {figure['id']: figure for figure in FIGURES}


def compute_mentions(
    df: pd.DataFrame,
    speaker_col: str = 'deputy',
    party_col: str = 'group',
) -> dict:
    """
    Returns:
        {
            'figures': [{id, name, short, group, group_label, party, n, rate,
                         by_bloc: {maggioranza, opposizione}, top_speakers: [{speaker, party, n}]}],
            'matrix': {'parties': [...], 'figures': [ids], 'rates': [[...]]},
            'speeches': {party: n}
        }
    """
    total = len(df)
    if total == 0:
        return {}

    party_counts = df[party_col].value_counts()
    blocs = blocs_of(df, party_col)
    bloc_counts = blocs.value_counts()

    by_figure = Counter()
    by_party = defaultdict(Counter)
    by_bloc = defaultdict(Counter)
    by_speaker = defaultdict(Counter)
    party_of = {}

    for speaker, party, bloc, mentions in zip(df[speaker_col], df[party_col], blocs, df['mentions']):
        party_of[speaker] = party
        for figure_id in mentions or ():
            by_figure[figure_id] += 1
            by_party[figure_id][party] += 1
            by_bloc[figure_id][bloc] += 1
            by_speaker[figure_id][speaker] += 1

    figures = []
    for figure_id, n in by_figure.most_common():
        if n < MIN_FIGURE_MENTIONS:
            continue
        figure = _BY_ID[figure_id]
        figures.append({
            'id': figure_id,
            'name': figure['name'],
            'short': figure.get('short', figure['name'].split()[-1]),
            'group': figure['group'],
            'group_label': FIGURE_GROUP_LABELS.get(figure['group'], figure['group']),
            'party': figure['party'],
            'n': int(n),
            'rate': round(n / total * 100, 2),
            'by_bloc': {
                bloc: round(by_bloc[figure_id][bloc] / bloc_counts[bloc] * 100, 2)
                if bloc_counts.get(bloc) else 0.0
                for bloc in (MAGGIORANZA, OPPOSIZIONE)
            },
            'top_speakers': [
                {'speaker': s, 'party': party_of[s], 'n': int(c)}
                for s, c in by_speaker[figure_id].most_common(TOP_SPEAKERS)
            ],
        })

    parties = [p for p, n in party_counts.items() if n >= MIN_PARTY_SPEECHES]
    matrix_ids = [f['id'] for f in figures[:MATRIX_FIGURES]]
    rates = [
        [round(by_party[fid][party] / party_counts[party] * 100, 2) for fid in matrix_ids]
        for party in parties
    ]

    logger.info("Mentions: %d figures named in %d speeches", len(figures), int(df['mentions'].map(bool).sum()))

    return {
        'figures': figures,
        'matrix': {'parties': parties, 'figures': matrix_ids, 'rates': rates},
        'speeches': {p: int(party_counts[p]) for p in parties},
    }
