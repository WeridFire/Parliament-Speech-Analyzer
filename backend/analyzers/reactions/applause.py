"""
Applause and protests - how the other groups reacted to each speech.

The stenographic report records reactions from the floor as stage directions:
"(Applausi dei deputati dei gruppi MoVimento 5 Stelle e Partito
Democratico-Italia Democratica e Progressista)", "(Proteste dei deputati del
gruppo Lega-Salvini Premier)". Unlike every text-similarity measure, this is
behaviour: one group publicly endorsing or contesting another's speaker. A group
applauding an opponent is the clearest cross-party signal the reports contain.

Reactions are parsed once per speech in `core.features` (`note_events`). Each
speech counts at most once per reacting group and kind, however many times the
group interrupted it.
"""

import logging
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

from backend.analyzers.common import blocs_of
from backend.config import MAGGIORANZA, OPPOSIZIONE, party_bloc

logger = logging.getLogger(__name__)

APPLAUSE = 'applausi'
DISSENT = ('proteste', 'commenti')
MIN_PARTY_SPEECHES = 30
TOP_SPEAKERS = 10
# Below this many group-attributed applause events the matrices are not shown.
MIN_ATTRIBUTED = 20


def _reactions(events, kinds) -> set:
    """Groups that reacted to one speech with any of `kinds`."""
    groups = set()
    for kind, names in events or ():
        if kind in kinds:
            groups.update(names)
    return groups


def _matrix(df: pd.DataFrame, parties: list[str], kinds, party_col: str) -> list[list[int]]:
    """Rows: reacting group. Columns: speaker's group. Cells: speeches."""
    index = {p: i for i, p in enumerate(parties)}
    matrix = np.zeros((len(parties), len(parties)), dtype=int)

    for speaker_party, events in zip(df[party_col], df['note_events']):
        column = index.get(speaker_party)
        if column is None:
            continue
        for group in _reactions(events, kinds):
            row = index.get(group)
            if row is not None:
                matrix[row, column] += 1

    return matrix.tolist()


def compute_reactions(
    df: pd.DataFrame,
    speaker_col: str = 'deputy',
    party_col: str = 'group',
) -> dict:
    """
    Returns:
        {
            'parties': [...],                 groups with enough speeches, ordered
            'speeches': {party: n},           denominators for the rates below
            'applause': [[...]],              reacting group x speaker group, speeches
            'dissent':  [[...]],              same, for protests and comments
            'received': {party: {applause, dissent}},  % of the group's speeches drawing any
                                              applause / protest, attributed or not
            'cross_applause': [{from, to, n, rate}],   off-diagonal, rate per 100 speeches of `to`
            'bloc_applause': {maggioranza: {...}, opposizione: {...}},
            'top_cross_applauded': [{speaker, party, n, groups}],
            'top_contested': [{speaker, party, n, groups}],
            'coverage': {...}
        }

    The Senato's reports record a bare "(Applausi)" without naming the group,
    so for that chamber only `received` and `coverage` carry information;
    `coverage.attributed` says whether the matrices do.
    """
    counts = df[party_col].value_counts()
    parties = [p for p, n in counts.items() if n >= MIN_PARTY_SPEECHES]
    blocs = blocs_of(df, party_col)

    applause = _matrix(df, parties, {APPLAUSE}, party_col)
    dissent = _matrix(df, parties, set(DISSENT), party_col)

    kinds = df['note_events'].map(lambda events: {kind for kind, _ in events or ()})
    received = {}
    for party in parties:
        mask = (df[party_col] == party).to_numpy()
        party_kinds = kinds[mask]
        received[party] = {
            'applause': round(float(party_kinds.map(lambda k: APPLAUSE in k).mean()) * 100, 1),
            'dissent': round(float(party_kinds.map(lambda k: bool(k & set(DISSENT))).mean()) * 100, 1),
        }

    cross = []
    for i, source in enumerate(parties):
        for j, target in enumerate(parties):
            if i != j and applause[i][j]:
                cross.append({
                    'from': source,
                    'to': target,
                    'n': applause[i][j],
                    'rate': round(applause[i][j] / counts[target] * 100, 2),
                })
    cross.sort(key=lambda e: -e['rate'])

    # Per speaker: applause from groups other than their own, and dissent.
    cross_by_speaker, cross_groups = Counter(), defaultdict(Counter)
    contested, contested_groups = Counter(), defaultdict(Counter)
    party_of = {}
    bloc_applause = {
        bloc: {'speeches': 0, 'applauded_by_other_bloc': 0} for bloc in (MAGGIORANZA, OPPOSIZIONE)
    }

    for speaker, party, bloc, events in zip(df[speaker_col], df[party_col], blocs, df['note_events']):
        party_of[speaker] = party
        applauders = _reactions(events, {APPLAUSE}) - {party}
        if applauders:
            cross_by_speaker[speaker] += 1
            cross_groups[speaker].update(applauders)

        protesters = _reactions(events, set(DISSENT)) - {party}
        if protesters:
            contested[speaker] += 1
            contested_groups[speaker].update(protesters)

        if bloc in bloc_applause:
            bloc_applause[bloc]['speeches'] += 1
            other = OPPOSIZIONE if bloc == MAGGIORANZA else MAGGIORANZA
            if any(party_bloc(group) == other for group in applauders):
                bloc_applause[bloc]['applauded_by_other_bloc'] += 1

    for entry in bloc_applause.values():
        entry['rate'] = round(entry['applauded_by_other_bloc'] / entry['speeches'] * 100, 2) if entry['speeches'] else 0.0

    def ranked(counter, groups):
        return [
            {
                'speaker': speaker,
                'party': party_of[speaker],
                'n': int(n),
                'groups': [g for g, _ in groups[speaker].most_common()],
            }
            for speaker, n in counter.most_common(TOP_SPEAKERS)
        ]

    events = [e for speech in df['note_events'] for e in (speech or ())]
    attributed = sum(1 for kind, groups in events if kind == APPLAUSE and groups)
    coverage = {
        'speeches': int(len(df)),
        'with_reactions': int(sum(1 for speech in df['note_events'] if speech)),
        'applause_events': int(sum(1 for kind, _ in events if kind == APPLAUSE)),
        'applause_attributed': int(attributed),
        'dissent_events': int(sum(1 for kind, _ in events if kind in DISSENT)),
        # Whether the report names who applauded - true at the Camera only.
        'attributed': bool(attributed >= MIN_ATTRIBUTED),
    }

    logger.info(
        "Reactions: %d applause (%d attributed), %d protests/comments",
        coverage['applause_events'], coverage['applause_attributed'], coverage['dissent_events'],
    )

    return {
        'parties': parties,
        'speeches': {p: int(counts[p]) for p in parties},
        'applause': applause,
        'dissent': dissent,
        'received': received,
        'cross_applause': cross,
        'bloc_applause': bloc_applause,
        'top_cross_applauded': ranked(cross_by_speaker, cross_groups),
        'top_contested': ranked(contested, contested_groups),
        'coverage': coverage,
    }
