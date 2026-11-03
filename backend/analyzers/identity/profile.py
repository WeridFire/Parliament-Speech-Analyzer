"""
Topic Profile - how a group's speeches divide across the topics.

Replaces the "thematic fingerprint", which was the cosine similarity between a
party's mean embedding and each topic centroid. Those similarities sat in a
narrow band for every party and every topic, so the radar drew nearly the same
shape for everyone. A share of speeches is a quantity a reader can check, and
the lift - share in the group over share in the whole chamber - says what the
group talks about *more than the others*, which is what "identity" is meant to
show.
"""

import logging

import pandas as pd

from backend.analyzers.common import classified, topic_ids, topic_shares

logger = logging.getLogger(__name__)

# Below this a party's percentages are a handful of speeches each.
MIN_PARTY_SPEECHES = 30


def compute_topic_profile(
    df: pd.DataFrame,
    cluster_labels: dict,
    cluster_col: str = 'cluster',
    party_col: str = 'group',
) -> dict:
    """
    Returns:
        {
            'topics': [topic ids],
            'chamber': {topic: share %},
            'by_party': {party: {'n': int, 'shares': {topic: %}, 'lift': {topic: ratio}}}
        }
    """
    topics = topic_ids(cluster_labels)
    rows = classified(df, cluster_col)
    chamber = topic_shares(rows[cluster_col], topics)

    by_party = {}
    for party, group in rows.groupby(party_col):
        if len(group) < MIN_PARTY_SPEECHES:
            continue
        shares = topic_shares(group[cluster_col], topics)
        by_party[party] = {
            'n': int(len(group)),
            'shares': shares,
            'lift': {
                t: round(shares[t] / chamber[t], 2) if chamber[t] > 0 else None
                for t in topics
            },
        }

    logger.info("Computed topic profiles for %d parties", len(by_party))
    return {'topics': topics, 'chamber': chamber, 'by_party': by_party}
