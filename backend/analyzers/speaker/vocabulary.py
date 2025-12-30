"""
Vocabulary Richness - Lexical diversity metrics.
"""
import logging
from collections import Counter

import pandas as pd

from .utils import tokenize_simple

logger = logging.getLogger(__name__)


def compute_vocabulary_richness(
    df: pd.DataFrame,
    speaker_col: str = 'deputy',
    text_col: str = 'cleaned_text'
) -> dict:
    """
    Compute vocabulary richness metrics for each speaker.
    
    Returns:
    - type_token_ratio (TTR): unique words / total words
    - hapax_ratio: words used only once / total unique words
    - vocabulary_size: number of unique words
    """
    result = {}
    
    for speaker in df[speaker_col].unique():
        speaker_df = df[df[speaker_col] == speaker]
        n_speeches = len(speaker_df)
        
        if n_speeches < 2:
            continue
        
        # Collect all tokens
        all_tokens = []
        for text in speaker_df[text_col]:
            all_tokens.extend(tokenize_simple(str(text)))
        
        if len(all_tokens) < 50:
            continue
        
        total_tokens = len(all_tokens)
        word_counts = Counter(all_tokens)
        unique_words = len(word_counts)
        
        # Type-Token Ratio
        ttr = unique_words / total_tokens if total_tokens > 0 else 0
        
        # Hapax legomena (words appearing exactly once)
        hapax = sum(1 for w, c in word_counts.items() if c == 1)
        hapax_ratio = hapax / unique_words if unique_words > 0 else 0
        
        # Classification based on TTR
        # Higher TTR = richer vocabulary
        if ttr > 0.3:
            classification = 'ricco'
        elif ttr > 0.2:
            classification = 'medio'
        else:
            classification = 'ripetitivo'
        
        result[speaker] = {
            'type_token_ratio': round(ttr, 4),
            'hapax_ratio': round(hapax_ratio, 4),
            'vocabulary_size': unique_words,
            'total_words': total_tokens,
            'classification': classification,
            'n_speeches': n_speeches
        }
    
    logger.info("Computed vocabulary richness for %d speakers", len(result))
    return result
