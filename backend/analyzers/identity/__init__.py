"""
Identity Analyzer Package - Analyze political identity and DNA.

Provides:
- Thematic Fingerprint (radar chart data)
- Generalism Index (entropy-based specialization score)
- Distinctive Keywords (TF-IDF per party)
"""

from .analyzer import IdentityAnalyzer
from .fingerprint import compute_thematic_fingerprint
from .generalism import compute_generalism_index
from .keywords import compute_distinctive_keywords, tokenize, tokenize_advanced, tokenize_basic

__all__ = [
    'IdentityAnalyzer',
    'compute_thematic_fingerprint',
    'compute_generalism_index',
    'compute_distinctive_keywords',
    'tokenize',
    'tokenize_advanced',
    'tokenize_basic',
]
