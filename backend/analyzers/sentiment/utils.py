"""
Common utilities for sentiment analysis.
"""

import re
from typing import Set


def tokenize_simple(text: str) -> list[str]:
    """Simple tokenization for sentiment analysis."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    return text.split()


def count_keywords(tokens: list[str], keywords: Set[str]) -> int:
    """Count how many keyword occurrences appear in tokens."""
    keywords_lower = {k.lower() for k in keywords}
    return sum(1 for t in tokens if t in keywords_lower)
