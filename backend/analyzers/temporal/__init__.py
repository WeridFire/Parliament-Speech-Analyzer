"""
Temporal Analyzer Package - Analyze how the agenda evolves over time.

Provides:
- Topic Trends (monthly topic shares, and volume per bloc)
"""

from .analyzer import TemporalAnalyzer
from .utils import parse_date, add_time_columns
from .trends import compute_topic_trends

__all__ = [
    'TemporalAnalyzer',
    'parse_date',
    'add_time_columns',
    'compute_topic_trends',
]
