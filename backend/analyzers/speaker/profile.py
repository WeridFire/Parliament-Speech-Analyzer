"""
Speaker profile - per-member statistics aggregated from the per-speech features.

What is gone, and why:
  * consistency index - variance of the member's embeddings, with no
    small-sample correction: three speeches scored 100/100 "molto coerente";
  * topic leadership - the speaker closest to a topic centroid, i.e. whoever
    said least about anything else (replaced by `top_topics` and the topics
    analyzer's spokespeople);
  * intervention patterns - "speeches per active month", which made a member
    with ten speeches in a single month the most active of the legislature;
  * temporal orientation - its "future" markers were words like "sviluppo" and
    "obiettivo";
  * mention network - matched nothing at the Camera (see the mentions analyzer).
"""
import logging

import pandas as pd

from backend.analyzers.common import blocs_of, topic_label
from backend.config import UNCLASSIFIED_CLUSTER
from backend.utils.dates import parse_date_series, period_key

logger = logging.getLogger(__name__)

MIN_SPEECHES = 5
TOP_TOPICS = 3


def _per_thousand(count: float, words: float) -> float:
    return round(count / words * 1000, 2) if words else 0.0


def compute_speaker_profiles(
    df: pd.DataFrame,
    cluster_labels: dict,
    speaker_col: str = 'deputy',
    party_col: str = 'group',
    cluster_col: str = 'cluster',
    date_col: str = 'date',
) -> dict:
    """
    Returns:
        {speaker: {
            party, bloc, n_speeches, speaking_days, active_months, total_months,
            verbosity: {avg_words, avg_sentence_words, total_words},
            linguistic: {question_rate, self_reference_rate, negation_rate, data_citation_rate},
            top_topics: [{topic, label, n, share}],
            reactions: {applauded_by_others, contested},
        }}
    """
    df = df.copy()
    df['_month'] = parse_date_series(df[date_col]).apply(lambda d: period_key(d, 'month'))
    df['_bloc'] = blocs_of(df, party_col)
    total_months = int(df['_month'].nunique())

    sums = df.groupby(speaker_col).agg(
        n_speeches=(speaker_col, 'size'),
        party=(party_col, 'first'),
        bloc=('_bloc', 'first'),
        speaking_days=(date_col, 'nunique'),
        active_months=('_month', 'nunique'),
        words=('n_words', 'sum'),
        sentences=('n_sentences', 'sum'),
        questions=('questions', 'sum'),
        self_refs=('self_refs', 'sum'),
        negations=('negations', 'sum'),
        numerics=('numerics', 'sum'),
    )
    sums = sums[sums['n_speeches'] >= MIN_SPEECHES]

    topics = (
        df[df[cluster_col] != UNCLASSIFIED_CLUSTER]
        .groupby([speaker_col, cluster_col]).size()
        .rename('n').reset_index()
        .sort_values([speaker_col, 'n'], ascending=[True, False])
    )
    top_topics = {
        speaker: rows.head(TOP_TOPICS)
        for speaker, rows in topics.groupby(speaker_col)
    }
    classified_totals = topics.groupby(speaker_col)['n'].sum()

    reactions = {}
    for speaker, party, events in zip(df[speaker_col], df[party_col], df['note_events']):
        entry = reactions.setdefault(speaker, [0, 0])
        applauders = {g for kind, groups in (events or ()) if kind == 'applausi' for g in groups}
        protesters = {g for kind, groups in (events or ()) if kind != 'applausi' for g in groups}
        entry[0] += bool(applauders - {party})
        entry[1] += bool(protesters - {party})

    result = {}
    for speaker, row in sums.iterrows():
        words = float(row['words'])
        topic_rows = top_topics.get(speaker)
        classified_n = int(classified_totals.get(speaker, 0))

        result[speaker] = {
            'party': row['party'],
            'bloc': row['bloc'],
            'n_speeches': int(row['n_speeches']),
            'speaking_days': int(row['speaking_days']),
            'active_months': int(row['active_months']),
            'total_months': total_months,
            'verbosity': {
                'avg_words': round(words / row['n_speeches'], 1),
                'avg_sentence_words': round(words / row['sentences'], 1) if row['sentences'] else 0.0,
                'total_words': int(words),
            },
            'linguistic': {
                'question_rate': _per_thousand(row['questions'], words),
                'self_reference_rate': _per_thousand(row['self_refs'], words),
                'negation_rate': _per_thousand(row['negations'], words),
                'data_citation_rate': _per_thousand(row['numerics'], words),
            },
            'top_topics': [
                {
                    'topic': int(t),
                    'label': topic_label(cluster_labels, int(t)),
                    'n': int(n),
                    'share': round(n / classified_n * 100, 1) if classified_n else 0.0,
                }
                for t, n in zip(topic_rows[cluster_col], topic_rows['n'])
            ] if topic_rows is not None else [],
            'reactions': {
                'applauded_by_others': reactions.get(speaker, [0, 0])[0],
                'contested': reactions.get(speaker, [0, 0])[1],
            },
        }

    logger.info("Computed profiles for %d speakers", len(result))
    return result
