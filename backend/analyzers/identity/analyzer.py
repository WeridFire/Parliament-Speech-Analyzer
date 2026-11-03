"""
Identity Analyzer - Main analyzer class for identity metrics.

Orchestrates:
- Topic Profile
- Generalism Index
- Distinctive Keywords
"""

import logging

from backend.analyzers.base import BaseAnalyzer
from backend.analyzers.registry import analyzer

from .profile import compute_topic_profile
from .generalism import compute_generalism_index
from .keywords import compute_distinctive_keywords

logger = logging.getLogger(__name__)


@analyzer
class IdentityAnalyzer(BaseAnalyzer):
    """
    Analyzer for political identity.

    Computes:
    - topic_profile: share of each group's speeches per topic, and lift over the chamber
    - generalism_index: entropy-based specialization score
    - distinctive_keywords: log-odds distinctive terms per party
    """

    name = "identity"
    description = "What each group talks about, and with which words"
    version = "2.0"

    # Entropy and distinctive vocabulary both need a corpus to be distinctive
    # *against*; on a thin slice they mostly measure sampling.
    min_speeches = 150

    default_features = {
        'topic_profile': True,
        'generalism_index': True,
        'distinctive_keywords': True,
    }

    @classmethod
    def get_dependencies(cls) -> list[str]:
        return ['cluster_labels']

    def compute(self) -> dict:
        """
        Returns:
            {'topic_profile': {...}, 'generalism_index': {...}, 'distinctive_keywords': {...}}
        """
        self.validate_dependencies()
        result = {}

        if self.is_feature_enabled('topic_profile'):
            logger.info("Computing topic profiles...")
            result['topic_profile'] = compute_topic_profile(
                df=self.df,
                cluster_labels=self.cluster_labels,
                cluster_col=self.cluster_col,
                party_col=self.party_col,
            )

        if self.is_feature_enabled('generalism_index'):
            logger.info("Computing generalism index...")
            result['generalism_index'] = compute_generalism_index(
                df=self.df,
                cluster_labels=self.cluster_labels,
                cluster_col=self.cluster_col,
                speaker_col=self.speaker_col,
                party_col=self.party_col,
            )

        # The term matrix is optional: without it the keywords are skipped
        # rather than recomputed from raw text.
        if self.is_feature_enabled('distinctive_keywords') and self.terms is not None:
            logger.info("Computing distinctive keywords...")
            result['distinctive_keywords'] = compute_distinctive_keywords(
                df=self.df,
                terms=self.terms,
                vocabulary=self.vocabulary,
                party_col=self.party_col,
            )

        logger.info("Identity analysis complete")
        return result
