"""
Speaker Analyzer Package - Per-politician statistics.

Provides:
1. Activity (speeches, speaking days, active months)
2. Verbosity (words per speech, words per sentence)
3. Linguistic rates (questions, self-reference, negation, cited data)
4. Vocabulary richness (MATTR)
5. Main topics
6. Reactions drawn (applause from other groups, protests)
"""

from .analyzer import SpeakerAnalyzer
from .profile import compute_speaker_profiles
from .vocabulary import compute_vocabulary_richness, mattr

__all__ = [
    'SpeakerAnalyzer',
    'compute_speaker_profiles',
    'compute_vocabulary_richness',
    'mattr',
]
