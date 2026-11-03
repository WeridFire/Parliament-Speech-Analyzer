"""
Topics Analyzer Package - Who carries each topic.

Provides:
- per topic: its de-facto spokespeople, the groups that over- and under-invest
  in it, and the words that characterise it
"""
from .analyzer import TopicsAnalyzer
from .owners import compute_topic_owners, cluster_keywords

__all__ = [
    'TopicsAnalyzer',
    'compute_topic_owners',
    'cluster_keywords',
]
