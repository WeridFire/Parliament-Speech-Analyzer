"""
Vocabulary Richness - lexical diversity that does not reward saying less.

The previous measure was the type-token ratio (distinct words / total words),
which falls mechanically as a text gets longer: the "richest vocabulary" ranking
was a list of the members who had spoken least. MATTR - the moving-average
type-token ratio over a fixed window - compares everyone on windows of the same
length, so volume no longer decides the result.
"""
import logging
from collections import Counter

import pandas as pd

from backend.core.features import WORD_RE

logger = logging.getLogger(__name__)

MATTR_WINDOW = 500
# Below this a speaker has too few full windows for a stable average.
MIN_TOKENS = 1000


def mattr(tokens: list[str], window: int = MATTR_WINDOW) -> float:
    """Mean distinct-word ratio over every window of `window` consecutive tokens."""
    n = len(tokens)
    if n < window:
        return len(set(tokens)) / n if n else 0.0

    counts = Counter(tokens[:window])
    total = len(counts)
    for i in range(window, n):
        incoming, outgoing = tokens[i], tokens[i - window]
        counts[incoming] += 1
        counts[outgoing] -= 1
        if counts[outgoing] == 0:
            del counts[outgoing]
        total += len(counts)

    return total / ((n - window + 1) * window)


def compute_vocabulary_richness(
    df: pd.DataFrame,
    speaker_col: str = 'deputy',
    text_col: str = 'raw_text',
) -> dict:
    """
    Returns:
        {speaker: {'mattr': float, 'n_tokens': int}} for speakers with enough text.
    """
    result = {}
    for speaker, texts in df.groupby(speaker_col)[text_col]:
        tokens = [t for text in texts for t in WORD_RE.findall(str(text).lower())]
        if len(tokens) < MIN_TOKENS:
            continue
        result[speaker] = {'mattr': round(mattr(tokens), 4), 'n_tokens': len(tokens)}

    logger.info("Computed vocabulary richness for %d speakers", len(result))
    return result
