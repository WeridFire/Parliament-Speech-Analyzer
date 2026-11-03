"""
Generalism Index - how widely a speaker or group spreads across the topics.

Shannon entropy of the topic distribution, normalised to 0-100:
- 100 = speaks equally about every topic
- 0   = speaks about a single topic

Two corrections over the previous version. The denominator is the number of
configured topics, not the number that happened to appear in the slice (a month
with five topics present used to rescale everyone). And entropy estimated from a
handful of speeches is biased low - two speeches can cover at most two topics -
so speakers need a real sample before they are scored at all.
"""

import logging

import numpy as np
import pandas as pd

from backend.analyzers.common import classified, topic_ids

logger = logging.getLogger(__name__)

MIN_SPEAKER_SPEECHES = 20
MIN_PARTY_SPEECHES = 30


def _entropy_score(clusters: pd.Series, n_topics: int) -> float:
    counts = clusters.value_counts().to_numpy(dtype=float)
    proportions = counts / counts.sum()
    entropy = -np.sum(proportions * np.log2(proportions))
    max_entropy = np.log2(n_topics) if n_topics > 1 else 1.0
    return float(entropy / max_entropy * 100)


def _classify_generalism(score: float) -> str:
    """Classify generalism score into category."""
    if score > 70:
        return 'generalista'
    if score < 40:
        return 'specialista'
    return 'bilanciato'


def compute_generalism_index(
    df: pd.DataFrame,
    cluster_labels: dict,
    cluster_col: str = 'cluster',
    speaker_col: str = 'deputy',
    party_col: str = 'group',
) -> dict:
    """
    Returns:
        {
            'by_deputy': {speaker: {score, dominant_topic, n_topics, n_speeches, classification, party}},
            'by_party': {party: {score, dominant_topic, n_topics, n_speeches, classification}}
        }
    """
    n_topics = len(topic_ids(cluster_labels))
    rows = classified(df, cluster_col)
    result = {'by_deputy': {}, 'by_party': {}}

    def describe(group: pd.DataFrame) -> dict:
        score = _entropy_score(group[cluster_col], n_topics)
        return {
            'score': round(score, 1),
            'dominant_topic': int(group[cluster_col].value_counts().idxmax()),
            'n_topics': int(group[cluster_col].nunique()),
            'n_speeches': int(len(group)),
            'classification': _classify_generalism(score),
        }

    for speaker, group in rows.groupby(speaker_col):
        if len(group) >= MIN_SPEAKER_SPEECHES:
            result['by_deputy'][speaker] = {**describe(group), 'party': group[party_col].iloc[0]}

    for party, group in rows.groupby(party_col):
        if len(group) >= MIN_PARTY_SPEECHES:
            result['by_party'][party] = describe(group)

    logger.info(
        "Computed generalism index for %d speakers and %d parties",
        len(result['by_deputy']), len(result['by_party']),
    )
    return result
