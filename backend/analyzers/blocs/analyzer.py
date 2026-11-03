"""
Blocs Analyzer - Main analyzer class.
"""
import logging

from backend.analyzers.base import BaseAnalyzer
from backend.analyzers.registry import analyzer

from .ownership import compute_bloc_keywords, compute_bloc_summary, compute_issue_ownership

logger = logging.getLogger(__name__)


@analyzer
class BlocsAnalyzer(BaseAnalyzer):
    """Majority (with the government) against the opposition."""

    name = "blocs"
    description = "Majority vs opposition: agenda and vocabulary"
    version = "1.0"

    # Two blocs, each needing enough speeches per topic for a share to mean anything.
    min_speeches = 150

    default_features = {
        'summary': True,
        'ownership': True,
        'keywords': True,
    }

    @classmethod
    def get_dependencies(cls) -> list[str]:
        return ['cluster_labels']

    def compute(self) -> dict:
        """Compute the bloc comparison."""
        result = {}

        if self.is_feature_enabled('summary'):
            result['summary'] = compute_bloc_summary(self.df, speaker_col=self.speaker_col)

        if self.is_feature_enabled('ownership'):
            logger.info("Computing issue ownership...")
            result['ownership'] = compute_issue_ownership(
                self.df, self.cluster_labels, cluster_col=self.cluster_col,
            )

        if self.is_feature_enabled('keywords') and self.terms is not None:
            logger.info("Computing bloc keywords...")
            result['keywords'] = compute_bloc_keywords(self.df, self.terms, self.vocabulary)

        return result
