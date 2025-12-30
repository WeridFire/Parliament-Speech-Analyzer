"""
Temporal Analyzer - Main analyzer class for temporal metrics.
"""

import logging

from backend.analyzers.base import BaseAnalyzer
from backend.analyzers.registry import analyzer

from .trends import compute_topic_trends
from .drift import compute_semantic_drift
from .crisis import compute_crisis_index
from .surfing import find_topic_surfing

logger = logging.getLogger(__name__)


@analyzer
class TemporalAnalyzer(BaseAnalyzer):
    """
    Analyzer for temporal evolution of political discourse.
    
    Computes:
    - topic_trends: Topic distribution over time
    - semantic_drift: How party positions shift
    - crisis_index: Alarm term frequency
    - topic_surfing: Politicians who rapidly change focus
    """
    
    name = "temporal"
    description = "Temporal evolution of political discourse"
    version = "1.0"
    
    default_features = {
        'topic_trends': True,
        'semantic_drift': True,
        'crisis_index': True,
        'topic_surfing': True,
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        analyzer_config = self.config.get(self.name, {})
        self.granularity = analyzer_config.get('granularity', 'month')
    
    @classmethod
    def get_dependencies(cls) -> list[str]:
        return ['embeddings', 'cluster_labels']
    
    def compute(self) -> dict:
        """Compute all temporal metrics."""
        result = {}
        
        if self.is_feature_enabled('topic_trends'):
            logger.info("Computing topic trends...")
            result['topic_trends'] = compute_topic_trends(
                df=self.df,
                cluster_col=self.cluster_col,
                cluster_labels=self.cluster_labels,
                date_col=self.date_col,
                granularity=self.granularity,
                party_col=self.party_col,
                speaker_col=self.speaker_col
            )
        
        if self.is_feature_enabled('semantic_drift'):
            logger.info("Computing semantic drift...")
            result['semantic_drift'] = compute_semantic_drift(
                df=self.df,
                embeddings=self.embeddings,
                party_col=self.party_col,
                date_col=self.date_col
            )
        
        if self.is_feature_enabled('crisis_index'):
            logger.info("Computing crisis index...")
            result['crisis_index'] = compute_crisis_index(
                df=self.df,
                text_col=self.text_col,
                cluster_col=self.cluster_col,
                cluster_labels=self.cluster_labels,
                date_col=self.date_col,
                granularity=self.granularity
            )
        
        if self.is_feature_enabled('topic_surfing'):
            logger.info("Finding topic surfing...")
            result['topic_surfing'] = find_topic_surfing(
                df=self.df,
                cluster_col=self.cluster_col,
                cluster_labels=self.cluster_labels,
                date_col=self.date_col,
                speaker_col=self.speaker_col
            )
        
        logger.info("Temporal analysis complete")
        return result
