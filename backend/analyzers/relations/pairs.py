"""
Cross-Party Pairs - Similar speakers from different parties.

One matrix product instead of the previous pure-Python double loop over every
pair of speakers (which the alliances analyzer then ran a second time, under
another name, with the same result).
"""
import logging

import numpy as np
import pandas as pd

from backend.analyzers.common import blocs_of

from .cohesion import unit_rows

logger = logging.getLogger(__name__)

# A speaker's average position is only stable over a real sample of speeches.
MIN_SPEAKER_SPEECHES = 10


def find_closest_cross_party_pairs(
    df: pd.DataFrame,
    embeddings: np.ndarray,
    speaker_col: str = 'deputy',
    party_col: str = 'group',
    top_n: int = 20
) -> list:
    """
    Returns:
        [{speaker1, party1, speaker2, party2, similarity, crosses_blocs}], most similar first.
        `crosses_blocs` is True when one speaker sits with the majority and the
        other with the opposition.
    """
    vectors = unit_rows(embeddings)
    counts = df[speaker_col].value_counts()
    speakers = [s for s, n in counts.items() if n >= MIN_SPEAKER_SPEECHES]
    if len(speakers) < 2:
        return []

    names = df[speaker_col].to_numpy()
    first_rows = df.drop_duplicates(speaker_col).set_index(speaker_col)
    blocs = blocs_of(first_rows, party_col)

    means = unit_rows(np.stack([vectors[names == s].mean(axis=0) for s in speakers]))
    similarity = means @ means.T
    parties = np.array([first_rows.at[s, party_col] for s in speakers])

    # Upper triangle, different parties only.
    valid = np.triu(parties[:, None] != parties[None, :], k=1)
    i_idx, j_idx = np.nonzero(valid)
    order = np.argsort(-similarity[i_idx, j_idx])[:top_n]

    pairs = []
    for k in order:
        i, j = i_idx[k], j_idx[k]
        s1, s2 = speakers[i], speakers[j]
        pairs.append({
            'speaker1': s1,
            'party1': parties[i],
            'speaker2': s2,
            'party2': parties[j],
            'similarity': round(float(similarity[i, j]), 4),
            'crosses_blocs': {blocs[s1], blocs[s2]} == {'maggioranza', 'opposizione'},
        })

    logger.info("Found %d cross-party pairs among %d speakers", len(pairs), len(speakers))
    return pairs
