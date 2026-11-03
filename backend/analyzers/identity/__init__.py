"""
Identity Analyzer Package - What each group talks about, and how.

Provides:
- Topic Profile (share of speeches per topic, and its lift over the chamber)
- Generalism Index (entropy-based specialization score)
- Distinctive Keywords (weighted log-odds per party)
"""

from .analyzer import IdentityAnalyzer
from .profile import compute_topic_profile
from .generalism import compute_generalism_index
from .keywords import compute_distinctive_keywords

__all__ = [
    'IdentityAnalyzer',
    'compute_topic_profile',
    'compute_generalism_index',
    'compute_distinctive_keywords',
]
