"""
Language Analyzer - readability and polarization of the phrasing.

Replaces the sentiment analyzer. Its tone measure counted 25 "positive" and 25
"negative" words - "problema", "rischio", "obiettivo" among them - so a speech
on a crisis was "negative" whatever it said about it, the topic-level averages
were indistinguishable from zero, and the per-topic rankings were led by members
with a single speech scored +1.
"""

import logging

from backend.analyzers.base import BaseAnalyzer
from backend.analyzers.registry import analyzer
from backend.core.features import ensure_features

from .polarization import compute_polarization_scores
from .readability import compute_readability_scores

logger = logging.getLogger(__name__)


@analyzer
class LanguageAnalyzer(BaseAnalyzer):
    """Readability (Gulpease) and "us vs them" polarization."""

    name = "language"
    description = "Readability and polarization of the phrasing"
    version = "1.0"

    min_speeches = 50

    default_features = {
        'readability': True,
        'polarization': True,
    }

    def compute(self) -> dict:
        df = ensure_features(self.df)
        result = {}

        if self.is_feature_enabled('readability'):
            logger.info("Computing readability scores...")
            result['readability'] = compute_readability_scores(
                df, speaker_col=self.speaker_col, party_col=self.party_col,
            )

        if self.is_feature_enabled('polarization'):
            logger.info("Computing polarization scores...")
            result['polarization'] = compute_polarization_scores(
                df, speaker_col=self.speaker_col, party_col=self.party_col,
            )

        return result
