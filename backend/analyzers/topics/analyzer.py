"""
Topics Analyzer - Main analyzer class.
"""
import logging

from backend.analyzers.base import BaseAnalyzer
from backend.analyzers.registry import analyzer

from .owners import compute_topic_owners

logger = logging.getLogger(__name__)


@analyzer
class TopicsAnalyzer(BaseAnalyzer):
    """Who carries each topic: spokespeople, group involvement, vocabulary."""

    name = "topics"
    description = "Who carries each topic"
    version = "2.0"

    min_speeches = 100

    default_features = {}  # No sub-features

    @classmethod
    def get_dependencies(cls) -> list[str]:
        return ['cluster_labels']

    def compute(self) -> dict:
        """Compute topic ownership."""
        logger.info("Computing topic owners...")
        return {
            'by_topic': compute_topic_owners(
                df=self.df,
                cluster_labels=self.cluster_labels,
                terms=self.terms,
                vocabulary=self.vocabulary,
                cluster_col=self.cluster_col,
                speaker_col=self.speaker_col,
                party_col=self.party_col,
            )
        }
