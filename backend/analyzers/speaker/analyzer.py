"""
Speaker Analyzer - Main analyzer class for per-politician statistics.
"""
import logging

from backend.analyzers.base import BaseAnalyzer
from backend.analyzers.registry import analyzer
from backend.core.features import ensure_features

from .profile import compute_speaker_profiles
from .vocabulary import compute_vocabulary_richness

logger = logging.getLogger(__name__)

# Rankings over averages need a sample; activity rankings do not.
MIN_RANKED_SPEECHES = 10
TOP_N = 10


@analyzer
class SpeakerAnalyzer(BaseAnalyzer):
    """
    Analyzer for per-politician statistics.

    Computes activity, verbosity, linguistic rates, vocabulary richness (MATTR),
    each member's main topics and the reactions their speeches drew.
    """

    name = "speaker"
    description = "Detailed per-politician statistics"
    version = "2.0"

    min_speeches = 50

    default_features = {
        'profile': True,
        'vocabulary': True,
    }

    def compute(self) -> dict:
        """Compute all speaker statistics."""
        df = ensure_features(self.df)
        by_speaker = {}

        if self.is_feature_enabled('profile'):
            logger.info("Computing speaker profiles...")
            by_speaker = compute_speaker_profiles(
                df,
                cluster_labels=self.cluster_labels,
                speaker_col=self.speaker_col,
                party_col=self.party_col,
                cluster_col=self.cluster_col,
                date_col=self.date_col,
            )

        if self.is_feature_enabled('vocabulary'):
            logger.info("Computing vocabulary richness...")
            text_col = 'raw_text' if 'raw_text' in df.columns else self.text_col
            for speaker, data in compute_vocabulary_richness(df, self.speaker_col, text_col).items():
                if speaker in by_speaker:
                    by_speaker[speaker]['vocabulary'] = data

        logger.info("Speaker analysis complete: %d speakers", len(by_speaker))
        return {'by_speaker': by_speaker, 'rankings': self._compute_rankings(by_speaker)}

    @staticmethod
    def _compute_rankings(by_speaker: dict) -> dict:
        """Top-N rankings, as [[speaker, value], ...]."""

        def top(value_of, min_speeches=1):
            scored = [
                (speaker, value_of(data))
                for speaker, data in by_speaker.items()
                if data['n_speeches'] >= min_speeches and value_of(data) is not None
            ]
            return [[s, v] for s, v in sorted(scored, key=lambda x: -x[1])[:TOP_N]]

        return {
            'most_active': top(lambda d: d['n_speeches']),
            'most_verbose': top(lambda d: d['verbosity']['avg_words'], MIN_RANKED_SPEECHES),
            'richest_vocabulary': top(lambda d: d.get('vocabulary', {}).get('mattr')),
            'most_data': top(lambda d: d['linguistic']['data_citation_rate'], MIN_RANKED_SPEECHES),
            'most_questions': top(lambda d: d['linguistic']['question_rate'], MIN_RANKED_SPEECHES),
            'most_cross_applauded': top(lambda d: d['reactions']['applauded_by_others'] or None),
        }
