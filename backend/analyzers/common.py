"""
Helpers shared by the analyzers: topic bookkeeping and distinctive vocabulary.

Distinctive vocabulary
----------------------
The previous keyword extraction ran TF-IDF with each party as one "document".
With a dozen documents the IDF term barely varies, so the ranking was decided by
raw frequency and every party's top words were the same parliamentary verbs
("chiedere", "ricordare", "riguardare"). It also lemmatised only the first
100.000 characters of each party's speeches - the oldest few dozen.

This uses the weighted log-odds ratio with an informative Dirichlet prior
(Monroe, Colaresi & Quinn, 2008, "Fightin' Words"), the standard method for
words that separate two groups of political speakers. Every word gets a
z-score: how much more a group uses it than everyone else, measured against how
much that difference could be noise given the counts. Common words shrink toward
zero, rare words do not win on a single use.
"""

import numpy as np
import pandas as pd

from backend.config import UNCLASSIFIED_CLUSTER, party_bloc

# A word must be used this often by the group before it can be "theirs" - and in
# this many different speeches, or one member repeating a name in a single
# intervention makes it the whole group's word.
MIN_TERM_COUNT = 5
MIN_TERM_SPEECHES = 5


def topic_ids(cluster_labels: dict) -> list[int]:
    """Configured topic ids, without the unclassified bucket."""
    return sorted(int(c) for c in cluster_labels if int(c) != UNCLASSIFIED_CLUSTER)


def topic_label(cluster_labels: dict, topic: int) -> str:
    return cluster_labels.get(topic, cluster_labels.get(str(topic), f"Tema {topic}"))


def classified(df: pd.DataFrame, cluster_col: str = 'cluster') -> pd.DataFrame:
    """Speeches that were assigned a topic."""
    return df[df[cluster_col] != UNCLASSIFIED_CLUSTER]


def blocs_of(df: pd.DataFrame, party_col: str = 'group') -> pd.Series:
    """Bloc per speech, from the column if the pipeline added it, else derived."""
    if 'bloc' in df.columns:
        return df['bloc']
    return df[party_col].map(party_bloc)


def topic_shares(series: pd.Series, topics: list[int]) -> dict[int, float]:
    """Percentage of the speeches in `series` (cluster ids) falling in each topic."""
    counts = series.value_counts()
    total = int(counts.reindex(topics, fill_value=0).sum())
    if total == 0:
        return {t: 0.0 for t in topics}
    return {t: round(float(counts.get(t, 0)) / total * 100, 2) for t in topics}


def log_odds_z(counts_a: np.ndarray, counts_b: np.ndarray, prior: np.ndarray) -> np.ndarray:
    """
    Weighted log-odds of each term in A vs B, with an informative Dirichlet prior.

    Returns one z-score per term: positive when A uses the term more than B.
    """
    counts_a = counts_a.astype(float)
    counts_b = counts_b.astype(float)
    prior = prior.astype(float)

    z = np.zeros_like(counts_a)
    n_a, n_b, a0 = counts_a.sum(), counts_b.sum(), prior.sum()
    if n_a == 0 or n_b == 0 or a0 == 0:
        return z

    # Terms nobody in the slice used have no odds to compare.
    used = prior > 0
    a, b, p = counts_a[used], counts_b[used], prior[used]

    # A term carrying a whole side's mass has no "other" outcome and no odds;
    # that only happens in degenerate vocabularies, and it scores zero.
    with np.errstate(divide='ignore', invalid='ignore'):
        odds_a = (a + p) / (n_a + a0 - a - p)
        odds_b = (b + p) / (n_b + a0 - b - p)
        delta = np.log(odds_a) - np.log(odds_b)
        variance = 1.0 / (a + p) + 1.0 / (b + p)
        scores = delta / np.sqrt(variance)
    z[used] = np.where(np.isfinite(scores), scores, 0.0)
    return z


def column_sums(terms, mask: np.ndarray, presence: bool = False) -> np.ndarray:
    """
    Total term counts over the rows selected by a boolean mask - or, with
    `presence`, the number of those rows that contain each term.
    """
    if not mask.any():
        return np.zeros(terms.shape[1])
    rows = terms[np.flatnonzero(mask)]
    if presence:
        rows = rows > 0
    return np.asarray(rows.sum(axis=0)).ravel()


def distinctive_terms(
    terms,
    vocabulary,
    mask_a: np.ndarray,
    mask_b: np.ndarray | None = None,
    top_n: int = 30,
    min_count: int = MIN_TERM_COUNT,
    min_speeches: int = MIN_TERM_SPEECHES,
) -> list[dict]:
    """
    Terms most characteristic of the rows in `mask_a` against `mask_b`
    (everyone else when omitted).

    Returns [{term, z, n}], strongest first; only terms the group uses at least
    `min_count` times, across at least `min_speeches` speeches, are eligible.
    """
    if terms is None or vocabulary is None or terms.shape[1] == 0:
        return []

    mask_a = np.asarray(mask_a, dtype=bool)
    mask_b = ~mask_a if mask_b is None else np.asarray(mask_b, dtype=bool)

    counts_a = column_sums(terms, mask_a)
    counts_b = column_sums(terms, mask_b)
    # The prior is the pooled usage of both sides, so it shrinks toward the
    # shared baseline rather than toward an outside corpus.
    z = log_odds_z(counts_a, counts_b, prior=counts_a + counts_b)

    speeches_a = column_sums(terms, mask_a, presence=True)
    eligible = np.flatnonzero((counts_a >= min_count) & (speeches_a >= min_speeches) & (z > 0))
    if eligible.size == 0:
        return []

    ranked = eligible[np.argsort(-z[eligible])][:top_n]
    return [
        {'term': str(vocabulary[j]), 'z': round(float(z[j]), 2), 'n': int(counts_a[j])}
        for j in ranked
    ]
