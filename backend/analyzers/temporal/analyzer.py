"""
Temporal Analyzer - Main analyzer class for temporal metrics.
"""

import logging

from backend.analyzers.base import BaseAnalyzer
from backend.analyzers.registry import analyzer

from .trends import compute_topic_trends

logger = logging.getLogger(__name__)


@analyzer
class TemporalAnalyzer(BaseAnalyzer):
    """
    Analyzer for the evolution of the agenda over time.

    Computes:
    - topic_trends: monthly topic shares and counts, and monthly volume per bloc
    """

    name = "temporal"
    description = "Temporal evolution of the agenda"
    version = "2.0"

    # Trends describe movement *between* periods. Recomputing them inside a
    # single month asks how discourse evolved during a slice chosen to remove
    # that evolution.
    period_safe = False

    default_features = {
        'topic_trends': True,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        analyzer_config = self.config.get(self.name, {})
        self.granularity = analyzer_config.get('granularity', 'month')

    @classmethod
    def get_dependencies(cls) -> list[str]:
        return ['cluster_labels']

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
            )

        logger.info("Temporal analysis complete")
        return result
