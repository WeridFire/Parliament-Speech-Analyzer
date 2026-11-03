"""
Reactions Analyzer - Main analyzer class.
"""
import logging

from backend.analyzers.base import BaseAnalyzer
from backend.analyzers.registry import analyzer
from backend.core.features import ensure_features

from .applause import compute_reactions

logger = logging.getLogger(__name__)


@analyzer
class ReactionsAnalyzer(BaseAnalyzer):
    """Applause and protests between groups, from the stage directions."""

    name = "reactions"
    description = "Applause and protests between groups"
    version = "1.0"

    min_speeches = 100

    default_features = {}

    def compute(self) -> dict:
        """Compute the reaction matrices."""
        df = ensure_features(self.df)
        if not df['note_events'].map(bool).any():
            logger.info("No stage directions in this slice; reactions skipped")
            return {}
        return compute_reactions(df, speaker_col=self.speaker_col, party_col=self.party_col)
