"""
Mentions Analyzer - Main analyzer class.
"""
import logging

from backend.analyzers.base import BaseAnalyzer
from backend.analyzers.registry import analyzer
from backend.core.features import ensure_features

from .figures import compute_mentions

logger = logging.getLogger(__name__)


@analyzer
class MentionsAnalyzer(BaseAnalyzer):
    """Which groups name which leaders, ministers and foreign heads of government."""

    name = "mentions"
    description = "Who mentions whom"
    version = "1.0"

    min_speeches = 100

    default_features = {}

    def compute(self) -> dict:
        """Compute mention rates."""
        df = ensure_features(self.df)
        return compute_mentions(df, speaker_col=self.speaker_col, party_col=self.party_col)
