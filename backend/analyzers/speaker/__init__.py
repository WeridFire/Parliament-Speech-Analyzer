"""
Speaker Analyzer Package - Detailed per-politician statistics.

Provides 12 comprehensive metrics:
1. Verbosity Index
2. Question Rate
3. Self-Reference Rate
4. Data Citation Rate
5. Negation Rate
6. Temporal Orientation
7. Consistency Index
8. Topic Leadership
9. Intervention Patterns
10. Vocabulary Richness
11. Interaction Network
12. Named Entity Focus (optional)
"""

from .analyzer import SpeakerAnalyzer
from .verbosity import aggregate_speaker_metrics, compute_text_metrics_batch
from .consistency import compute_consistency_index
from .leadership import compute_topic_leadership
from .intervention import compute_intervention_patterns
from .vocabulary import compute_vocabulary_richness
from .network import compute_interaction_network
from .entities import compute_entity_focus

__all__ = [
    'SpeakerAnalyzer',
    'aggregate_speaker_metrics',
    'compute_text_metrics_batch',
    'compute_consistency_index',
    'compute_topic_leadership',
    'compute_intervention_patterns',
    'compute_vocabulary_richness',
    'compute_interaction_network',
    'compute_entity_focus',
]
