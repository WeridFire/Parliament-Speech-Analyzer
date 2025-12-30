"""
Temporal Analyzer Package - Analyze discourse evolution over time.

Provides:
- Topic Trends (temporal distribution)
- Semantic Drift (party position shifts)
- Crisis Index (alarm term frequency)
- Topic Surfing (focus changes)
"""

from .analyzer import TemporalAnalyzer
from .utils import parse_date, add_time_columns
from .trends import compute_topic_trends
from .drift import compute_semantic_drift
from .crisis import compute_crisis_index
from .surfing import find_topic_surfing

__all__ = [
    'TemporalAnalyzer',
    'parse_date',
    'add_time_columns',
    'compute_topic_trends',
    'compute_semantic_drift',
    'compute_crisis_index',
    'find_topic_surfing',
]
