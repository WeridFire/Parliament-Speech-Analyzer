"""
Sentiment Analyzer Package - Qualitative analysis of political communication.

Provides:
- Topic Sentiment (aspect-based sentiment per cluster)
- Readability Scores (Gulpease index)
- Polarization Scores ("Us vs Them" analysis)
- Party-Topic Sentiment Matrix
- Sentiment Rankings
"""

from .analyzer import SentimentAnalyzer
from .topic_sentiment import compute_topic_sentiment
from .readability import compute_gulpease_score, compute_readability_scores
from .polarization import compute_polarization_score, compute_polarization_scores
from .rankings import compute_party_topic_sentiment, compute_sentiment_rankings

__all__ = [
    'SentimentAnalyzer',
    'compute_topic_sentiment',
    'compute_gulpease_score',
    'compute_readability_scores',
    'compute_polarization_score',
    'compute_polarization_scores',
    'compute_party_topic_sentiment',
    'compute_sentiment_rankings',
]
