"""
Majority vs opposition.

Replaces the "thematic overlap", which never worked: it looked groups up in
left/right/centre tables keyed on short codes ("PD", "Lega"), the Camera emits
long labels, and so every group fell into "other" and every topic came out as
"mixed". It also compared raw counts, and the opposition simply speaks more -
in this legislature it takes most of the floor time - so by counts nearly every
topic would have been "opposition-dominated".

Ownership is measured on *attention*: the share of each bloc's own speeches that
goes to a topic. A topic is owned by a bloc when that bloc spends markedly more
of its floor time on it than the other does, regardless of how much either
speaks overall.
"""

import logging

import numpy as np
import pandas as pd

from backend.analyzers.common import blocs_of, classified, distinctive_terms, topic_ids, topic_label
from backend.config import MAGGIORANZA, OPPOSIZIONE

logger = logging.getLogger(__name__)

# |log2(attention ratio)| above this - about 1.4x - and the topic belongs to a bloc.
OWNERSHIP_THRESHOLD = 0.5
# Topics with fewer speeches than this across both blocs are not classified.
MIN_TOPIC_SPEECHES = 20


def compute_bloc_summary(df: pd.DataFrame, speaker_col: str = 'deputy') -> dict:
    """Speeches, speakers and length of intervention per bloc."""
    blocs = blocs_of(df)
    words = df['n_words'] if 'n_words' in df.columns else df['cleaned_text'].str.split().str.len()
    total = len(df)

    summary = {}
    for bloc in (MAGGIORANZA, OPPOSIZIONE):
        mask = (blocs == bloc).to_numpy()
        n = int(mask.sum())
        summary[bloc] = {
            'n_speeches': n,
            'n_speakers': int(df.loc[mask, speaker_col].nunique()),
            'share': round(n / total * 100, 1) if total else 0.0,
            'avg_words': round(float(words[mask].mean()), 1) if n else 0.0,
        }
    return summary


def compute_issue_ownership(
    df: pd.DataFrame,
    cluster_labels: dict,
    cluster_col: str = 'cluster',
) -> list[dict]:
    """
    One entry per topic, sorted from most majority-owned to most opposition-owned.

    Returns:
        [{topic, label, maggioranza, opposizione,       attention, % of the bloc's speeches
          n_maggioranza, n_opposizione, ratio, owner}]  ratio = log2(maj / opp)
    """
    rows = classified(df, cluster_col)
    blocs = blocs_of(rows)
    majority = rows[blocs == MAGGIORANZA][cluster_col]
    opposition = rows[blocs == OPPOSIZIONE][cluster_col]
    if majority.empty or opposition.empty:
        return []

    maj_counts = majority.value_counts()
    opp_counts = opposition.value_counts()

    entries = []
    for topic in topic_ids(cluster_labels):
        n_maj, n_opp = int(maj_counts.get(topic, 0)), int(opp_counts.get(topic, 0))
        maj_share = n_maj / len(majority) * 100
        opp_share = n_opp / len(opposition) * 100

        if n_maj + n_opp < MIN_TOPIC_SPEECHES or n_maj == 0 or n_opp == 0:
            ratio, owner = None, None
        else:
            ratio = float(np.log2(maj_share / opp_share))
            if ratio >= OWNERSHIP_THRESHOLD:
                owner = MAGGIORANZA
            elif ratio <= -OWNERSHIP_THRESHOLD:
                owner = OPPOSIZIONE
            else:
                owner = 'condiviso'

        entries.append({
            'topic': topic,
            'label': topic_label(cluster_labels, topic),
            MAGGIORANZA: round(maj_share, 2),
            OPPOSIZIONE: round(opp_share, 2),
            'n_maggioranza': n_maj,
            'n_opposizione': n_opp,
            'ratio': None if ratio is None else round(ratio, 2),
            'owner': owner,
        })

    entries.sort(key=lambda e: -(e['ratio'] if e['ratio'] is not None else -99))
    return entries


def compute_bloc_keywords(df: pd.DataFrame, terms, vocabulary, top_n: int = 25) -> dict:
    """Words that most separate majority speeches from opposition speeches, both ways."""
    blocs = blocs_of(df).to_numpy()
    majority, opposition = blocs == MAGGIORANZA, blocs == OPPOSIZIONE
    return {
        MAGGIORANZA: distinctive_terms(terms, vocabulary, majority, opposition, top_n=top_n),
        OPPOSIZIONE: distinctive_terms(terms, vocabulary, opposition, majority, top_n=top_n),
    }
