"""
Topic Owners - who speaks for each topic.

Replaces "topic leadership", which named as leader of a topic the speaker whose
*average embedding* sat closest to the topic centroid - in practice whoever had
said least about anything else, often on two speeches. Here the people who
carry a topic are simply the ones who intervene on it most, and each group's
involvement is read as lift: its share of the topic's speeches over its share
of all speeches. A lift of 2 means the group talks about this topic twice as
much as its size in the debate would predict.
"""

import logging

import numpy as np
import pandas as pd

from backend.analyzers.common import classified, distinctive_terms, topic_ids, topic_label
from backend.config import UNCLASSIFIED_CLUSTER

logger = logging.getLogger(__name__)

# A spokesperson needs more than an occasional intervention on the topic.
MIN_SPEAKER_TOPIC_SPEECHES = 3
TOP_SPEAKERS = 8
# Below this a group's lift on a topic is noise.
MIN_PARTY_TOPIC_SPEECHES = 5


def compute_topic_owners(
    df: pd.DataFrame,
    cluster_labels: dict,
    terms=None,
    vocabulary=None,
    cluster_col: str = 'cluster',
    speaker_col: str = 'deputy',
    party_col: str = 'group',
) -> dict:
    """
    Returns:
        {topic: {
            'label', 'n', 'share',
            'top_speakers': [{speaker, party, n, focus}],   focus = % of the speaker's own speeches
            'parties': [{party, n, share, lift}],           share = % of the topic's speeches
            'keywords': [{term, z, n}],
        }}
    """
    rows = classified(df, cluster_col)
    total = len(rows)
    if total == 0:
        return {}

    speaker_totals = rows[speaker_col].value_counts()
    party_totals = rows[party_col].value_counts()
    speaker_party = rows.groupby(speaker_col)[party_col].first()

    # Row mask over the *unfiltered* frame, because the term matrix is aligned
    # with it, not with `rows`.
    clusters = df[cluster_col].to_numpy()
    in_scope = clusters != UNCLASSIFIED_CLUSTER

    result = {}
    for topic in topic_ids(cluster_labels):
        topic_rows = rows[rows[cluster_col] == topic]
        n = len(topic_rows)
        if n == 0:
            continue

        speaker_counts = topic_rows[speaker_col].value_counts()
        speakers = [
            {
                'speaker': speaker,
                'party': speaker_party.get(speaker, ''),
                'n': int(count),
                'focus': round(count / speaker_totals[speaker] * 100, 1),
            }
            for speaker, count in speaker_counts.items()
            if count >= MIN_SPEAKER_TOPIC_SPEECHES
        ][:TOP_SPEAKERS]

        parties = []
        for party, count in topic_rows[party_col].value_counts().items():
            share = count / n * 100
            expected = party_totals[party] / total * 100
            parties.append({
                'party': party,
                'n': int(count),
                'share': round(share, 1),
                'lift': round(share / expected, 2) if count >= MIN_PARTY_TOPIC_SPEECHES else None,
            })

        keywords = []
        if terms is not None:
            keywords = distinctive_terms(
                terms, vocabulary, clusters == topic, in_scope & (clusters != topic), top_n=15,
            )

        result[topic] = {
            'label': topic_label(cluster_labels, topic),
            'n': int(n),
            'share': round(n / total * 100, 1),
            'top_speakers': speakers,
            'parties': parties,
            'keywords': keywords,
        }

    logger.info("Computed owners for %d topics", len(result))
    return result


def cluster_keywords(df: pd.DataFrame, terms, vocabulary, cluster_col: str = 'cluster', top_n: int = 5) -> dict:
    """
    Distinctive terms per cluster, for labelling K-Means clusters when no topic
    list is configured.
    """
    clusters = df[cluster_col].to_numpy()
    return {
        int(c): [w['term'] for w in distinctive_terms(terms, vocabulary, clusters == c, top_n=top_n)]
        for c in np.unique(clusters)
    }
