"""
Distinctive Keywords - the words that set each group apart from the rest.

Weighted log-odds with an informative prior over the shared term matrix; see
`backend.analyzers.common` for why this replaced per-party TF-IDF.
"""

import logging

import pandas as pd

from backend.analyzers.common import distinctive_terms

logger = logging.getLogger(__name__)

MIN_PARTY_SPEECHES = 30


def compute_distinctive_keywords(
    df: pd.DataFrame,
    terms,
    vocabulary,
    party_col: str = 'group',
    top_n: int = 30,
) -> dict:
    """
    Returns:
        {party: [{term, z, n}, ...]} - each party against every other speech.
    """
    parties = df[party_col].to_numpy()
    result = {}

    for party, n in df[party_col].value_counts().items():
        if n < MIN_PARTY_SPEECHES:
            continue
        words = distinctive_terms(terms, vocabulary, parties == party, top_n=top_n)
        if words:
            result[party] = words

    logger.info("Extracted distinctive keywords for %d parties", len(result))
    return result
