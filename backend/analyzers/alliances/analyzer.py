"""
Alliances Analyzer - Main analyzer class.
"""
import logging

from backend.analyzers.base import BaseAnalyzer
from backend.analyzers.registry import analyzer

from .transversal import find_transversal_clusters, find_unusual_pairs, find_left_right_alliances

logger = logging.getLogger(__name__)


@analyzer
class AlliancesAnalyzer(BaseAnalyzer):
    """Analyzer for cross-party themes and alliances."""
    
    name = "alliances"
    description = "Cross-party themes and unusual alliances"
    version = "1.0"
    
    default_features = {
        'transversal_clusters': True,
        'unusual_pairs': True,
        'left_right_alliances': True,
    }
    
    @classmethod
    def get_dependencies(cls) -> list[str]:
        return ['embeddings']
    
    def compute(self) -> dict:
        """Compute alliance analysis."""
        logger.info("Computing alliance analysis...")
        
        result = {}
        
        if self.is_feature_enabled('transversal_clusters'):
            result['transversal_clusters'] = find_transversal_clusters(self.df)
        
        if self.is_feature_enabled('unusual_pairs'):
            result['unusual_pairs'] = find_unusual_pairs(
                df=self.df,
                embeddings=self.embeddings,
                speaker_col=self.speaker_col,
                party_col=self.party_col
            )
        
        if self.is_feature_enabled('left_right_alliances'):
            result['left_right_alliances'] = find_left_right_alliances(
                df=self.df,
                embeddings=self.embeddings
            )
        
        logger.info("Alliance analysis complete")
        return result
