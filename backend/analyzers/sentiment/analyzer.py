"""
Sentiment Analyzer - Main analyzer class for sentiment metrics.

Orchestrates:
- Topic Sentiment
- Readability (Gulpease)
- Polarization
- Party-Topic Matrix
- Sentiment Rankings
"""

import logging
from typing import Optional

import pandas as pd

from backend.analyzers.base import BaseAnalyzer
from backend.analyzers.registry import analyzer

from .topic_sentiment import compute_topic_sentiment
from .readability import compute_readability_scores
from .polarization import compute_polarization_scores
from .rankings import compute_party_topic_sentiment, compute_sentiment_rankings
from .transformer import is_transformer_available, compute_transformer_sentiment

logger = logging.getLogger(__name__)


@analyzer
class SentimentAnalyzer(BaseAnalyzer):
    """
    Analyzer for qualitative analysis of political communication.
    
    Computes:
    - topic_sentiment: Aspect-based sentiment per topic
    - readability: Gulpease readability scores
    - polarization: "Us vs Them" language analysis
    - party_topic_sentiment: Party × Topic sentiment matrix
    - sentiment_rankings: Most positive/negative per topic
    """
    
    name = "sentiment"
    description = "Qualitative analysis of political communication"
    version = "1.0"
    
    default_features = {
        'topic_sentiment': True,
        'readability': True,
        'polarization': True,
        'party_topic_sentiment': True,
        'sentiment_rankings': True,
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Check config for transformer usage
        analyzer_config = self.config.get(self.name, {})
        self.use_transformer = analyzer_config.get('use_transformer', False)
    
    @classmethod
    def get_dependencies(cls) -> list[str]:
        """Sentiment analyzer optionally uses cluster_labels."""
        return ['cluster_labels']
    
    def compute(self) -> dict:
        """
        Compute all sentiment metrics.
        
        Returns:
            {
                'topic_sentiment': {...},
                'readability': {...},
                'polarization': {...},
                'party_topic_sentiment': {...},
                'sentiment_rankings': {...}
            }
        """
        result = {}
        
        # Topic Sentiment
        if self.is_feature_enabled('topic_sentiment'):
            logger.info("Computing topic sentiment...")
            
            # Use transformer if enabled and available
            if self.use_transformer and is_transformer_available():
                logger.info("Using transformer-based sentiment")
                # TODO: Integrate transformer sentiment
            
            result['topic_sentiment'] = compute_topic_sentiment(
                df=self.df,
                text_col=self.text_col,
                cluster_col=self.cluster_col,
                cluster_labels=self.cluster_labels,
                speaker_col=self.speaker_col,
                party_col=self.party_col
            )
        
        # Readability
        if self.is_feature_enabled('readability'):
            logger.info("Computing readability scores...")
            result['readability'] = compute_readability_scores(
                df=self.df,
                text_col=self.text_col,
                speaker_col=self.speaker_col,
                party_col=self.party_col
            )
        
        # Polarization
        if self.is_feature_enabled('polarization'):
            logger.info("Computing polarization scores...")
            result['polarization'] = compute_polarization_scores(
                df=self.df,
                text_col=self.text_col,
                speaker_col=self.speaker_col,
                party_col=self.party_col
            )
        
        # Party-Topic Sentiment Matrix
        if self.is_feature_enabled('party_topic_sentiment'):
            logger.info("Computing party-topic sentiment matrix...")
            result['party_topic_sentiment'] = compute_party_topic_sentiment(
                df=self.df,
                text_col=self.text_col,
                cluster_col=self.cluster_col,
                cluster_labels=self.cluster_labels,
                party_col=self.party_col
            )
        
        # Sentiment Rankings
        if self.is_feature_enabled('sentiment_rankings'):
            logger.info("Computing sentiment rankings...")
            result['sentiment_rankings'] = compute_sentiment_rankings(
                df=self.df,
                text_col=self.text_col,
                cluster_col=self.cluster_col,
                cluster_labels=self.cluster_labels,
                speaker_col=self.speaker_col,
                party_col=self.party_col
            )
        
        logger.info("Sentiment analysis complete")
        return result
