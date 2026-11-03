"""
Party Cohesion and Centroids - how homogeneous each group's discourse is.

Works on *centred* embeddings (the pipeline subtracts the corpus mean). Raw
sentence embeddings share a large common component, so every speech is already
similar to every other: party centroids came out 0.81-0.99 similar to each
other and the old cohesion score - 1 / (1 + mean distance to the centroid) -
was 0.29-0.31 for every party, all labelled "frammentato". With the common
component removed, similarity measures what distinguishes speeches.

Cohesion is the mean pairwise cosine similarity between a group's speeches,
computed exactly from the sum of the normalised vectors. Unlike distance to the
group's own centroid, it carries no self-similarity term, so a small group is
not flattered for being small.
"""
import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

MIN_PARTY_SPEECHES = 30


def unit_rows(embeddings: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return embeddings / norms


def mean_pairwise_similarity(unit_vectors: np.ndarray) -> float:
    """Average cosine over all distinct pairs: (|sum|^2 - n) / (n (n - 1))."""
    n = len(unit_vectors)
    if n < 2:
        return float('nan')
    total = unit_vectors.sum(axis=0)
    return float((total @ total - n) / (n * (n - 1)))


def compute_party_centroids(
    df: pd.DataFrame,
    embeddings: np.ndarray,
    party_col: str = 'group',
    min_speeches: int = 1,
) -> dict:
    """Mean of each party's normalised speech vectors."""
    vectors = unit_rows(embeddings)
    parties = df[party_col].to_numpy()
    centroids = {}

    for party in pd.unique(parties):
        mask = parties == party
        if mask.sum() >= min_speeches:
            centroids[party] = vectors[mask].mean(axis=0)

    return centroids


def compute_party_cohesion(
    df: pd.DataFrame,
    embeddings: np.ndarray,
    party_col: str = 'group',
    speaker_col: str = 'deputy',
) -> dict:
    """
    Returns:
        {party: {'cohesion': float, 'n_speeches': int, 'n_speakers': int}}

    `cohesion` is relative to the corpus, whose own mean pairwise similarity is
    about zero once centred: 0.10 means the group's speeches resemble each other
    noticeably more than two random speeches do.
    """
    vectors = unit_rows(embeddings)
    parties = df[party_col].to_numpy()
    result = {}

    for party in pd.unique(parties):
        mask = parties == party
        n = int(mask.sum())
        if n < MIN_PARTY_SPEECHES:
            continue
        result[party] = {
            'cohesion': round(mean_pairwise_similarity(vectors[mask]), 4),
            'n_speeches': n,
            'n_speakers': int(df.loc[mask, speaker_col].nunique()),
        }

    logger.info("Computed cohesion for %d parties", len(result))
    return result
