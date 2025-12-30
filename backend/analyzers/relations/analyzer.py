"""
Relations Analyzer - Main analyzer class.
"""
import logging

from backend.analyzers.base import BaseAnalyzer
from backend.analyzers.registry import analyzer

from .affinity import compute_party_affinity_matrix
from .cohesion import compute_party_cohesion
from .overlap import compute_thematic_overlap
from .pairs import find_closest_cross_party_pairs

logger = logging.getLogger(__name__)


@analyzer
class RelationsAnalyzer(BaseAnalyzer):
    """Analyzer for party relationships and affinities."""
    
    name = "relations"
    description = "Party relationships and affinities"
    version = "1.0"
    
    default_features = {
        'affinity_matrix': True,
        'party_cohesion': True,
        'thematic_overlap': True,
        'cross_party_pairs': True,
    }
    
    @classmethod
    def get_dependencies(cls) -> list[str]:
        return ['embeddings', 'cluster_labels']
    
    def compute(self) -> dict:
        """Compute all relationship metrics."""
        result = {}
        
        if self.is_feature_enabled('affinity_matrix'):
            logger.info("Computing affinity matrix...")
            result['affinity_matrix'] = compute_party_affinity_matrix(
                df=self.df, embeddings=self.embeddings, party_col=self.party_col
            )
        
        if self.is_feature_enabled('party_cohesion'):
            logger.info("Computing party cohesion...")
            result['party_cohesion'] = compute_party_cohesion(
                df=self.df, embeddings=self.embeddings, party_col=self.party_col
            )
        
        if self.is_feature_enabled('thematic_overlap'):
            logger.info("Computing thematic overlap...")
            result['thematic_overlap'] = compute_thematic_overlap(
                df=self.df, cluster_col=self.cluster_col,
                cluster_labels=self.cluster_labels, party_col=self.party_col
            )
        
        if self.is_feature_enabled('cross_party_pairs'):
            logger.info("Finding cross-party pairs...")
            result['cross_party_pairs'] = find_closest_cross_party_pairs(
                df=self.df, embeddings=self.embeddings,
                speaker_col=self.speaker_col, party_col=self.party_col
            )
        
        logger.info("Relations analysis complete")
        return result
