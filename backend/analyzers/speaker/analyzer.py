"""
Speaker Analyzer - Main analyzer class for per-politician statistics.
"""
import logging

from backend.analyzers.base import BaseAnalyzer
from backend.analyzers.registry import analyzer

from .verbosity import aggregate_speaker_metrics
from .consistency import compute_consistency_index
from .leadership import compute_topic_leadership
from .intervention import compute_intervention_patterns
from .vocabulary import compute_vocabulary_richness
from .network import compute_interaction_network
from .entities import compute_entity_focus

logger = logging.getLogger(__name__)


@analyzer
class SpeakerAnalyzer(BaseAnalyzer):
    """
    Analyzer for detailed per-politician statistics.
    
    Computes 12 comprehensive metrics including verbosity, linguistic patterns,
    consistency, topic leadership, intervention patterns, vocabulary, network, and NER.
    """
    
    name = "speaker"
    description = "Detailed per-politician statistics"
    version = "1.0"
    
    default_features = {
        'verbosity': True,
        'linguistic': True,
        'consistency': True,
        'topic_leadership': True,
        'intervention_patterns': True,
        'vocabulary': True,
        'network': True,
        'entity_focus': False,  # Requires spaCy - slow
    }
    
    @classmethod
    def get_dependencies(cls) -> list[str]:
        return ['embeddings', 'cluster_labels', 'cluster_centroids']
    
    def compute(self) -> dict:
        """Compute all speaker statistics."""
        result = {
            'by_speaker': {},
            'rankings': {}
        }
        
        # Phase 1: Text-based metrics (verbosity + linguistic)
        if self.is_feature_enabled('verbosity') or self.is_feature_enabled('linguistic'):
            logger.info("Computing text-based speaker metrics...")
            text_metrics = aggregate_speaker_metrics(
                df=self.df,
                speaker_col=self.speaker_col,
                text_col=self.text_col
            )
            
            # Merge into result
            for speaker, data in text_metrics.items():
                result['by_speaker'].setdefault(speaker, {})
                if self.is_feature_enabled('verbosity'):
                    result['by_speaker'][speaker]['verbosity'] = data['verbosity']
                if self.is_feature_enabled('linguistic'):
                    result['by_speaker'][speaker]['linguistic'] = data['linguistic']
                result['by_speaker'][speaker]['n_speeches'] = data['n_speeches']
        
        # Phase 2: Consistency
        if self.is_feature_enabled('consistency'):
            logger.info("Computing consistency index...")
            consistency = compute_consistency_index(
                df=self.df,
                embeddings=self.embeddings,
                speaker_col=self.speaker_col
            )
            
            for speaker, data in consistency.items():
                result['by_speaker'].setdefault(speaker, {})
                result['by_speaker'][speaker]['consistency'] = data
        
        # Phase 3: Topic Leadership
        if self.is_feature_enabled('topic_leadership'):
            logger.info("Computing topic leadership...")
            leadership = compute_topic_leadership(
                df=self.df,
                embeddings=self.embeddings,
                cluster_centroids=self.cluster_centroids,
                cluster_labels=self.cluster_labels,
                speaker_col=self.speaker_col,
                cluster_col=self.cluster_col
            )
            
            for speaker, data in leadership['by_speaker'].items():
                result['by_speaker'].setdefault(speaker, {})
                result['by_speaker'][speaker]['topic_leadership'] = data
            
            result['topic_leaders'] = leadership['by_topic']
        
        # Phase 4: Intervention Patterns
        if self.is_feature_enabled('intervention_patterns'):
            logger.info("Computing intervention patterns...")
            patterns = compute_intervention_patterns(
                df=self.df,
                speaker_col=self.speaker_col,
                date_col=self.date_col
            )
            
            for speaker, data in patterns.items():
                result['by_speaker'].setdefault(speaker, {})
                result['by_speaker'][speaker]['intervention'] = data
        
        # Phase 5: Vocabulary Richness
        if self.is_feature_enabled('vocabulary'):
            logger.info("Computing vocabulary richness...")
            vocab = compute_vocabulary_richness(
                df=self.df,
                speaker_col=self.speaker_col,
                text_col=self.text_col
            )
            
            for speaker, data in vocab.items():
                result['by_speaker'].setdefault(speaker, {})
                result['by_speaker'][speaker]['vocabulary'] = data
        
        # Phase 6: Network
        if self.is_feature_enabled('network'):
            logger.info("Computing interaction network...")
            network = compute_interaction_network(
                df=self.df,
                speaker_col=self.speaker_col,
                text_col=self.text_col
            )
            
            for speaker, data in network.items():
                result['by_speaker'].setdefault(speaker, {})
                result['by_speaker'][speaker]['network'] = data
        
        # Phase 7: Entity Focus (optional)
        if self.is_feature_enabled('entity_focus'):
            logger.info("Computing entity focus (NER)...")
            entities = compute_entity_focus(
                df=self.df,
                speaker_col=self.speaker_col,
                text_col=self.text_col
            )
            
            if 'error' not in entities:
                for speaker, data in entities.items():
                    result['by_speaker'].setdefault(speaker, {})
                    result['by_speaker'][speaker]['entity_focus'] = data
        
        # Build rankings
        result['rankings'] = self._compute_rankings(result['by_speaker'])
        
        logger.info("Speaker analysis complete: %d speakers", len(result['by_speaker']))
        return result
    
    def _compute_rankings(self, by_speaker: dict) -> dict:
        """Compute top-N rankings for various metrics."""
        rankings = {}
        speakers = list(by_speaker.items())
        
        # Most verbose
        if any('verbosity' in d for s, d in speakers):
            speakers_with_verbosity = [(s, d) for s, d in speakers if 'verbosity' in d]
            rankings['most_verbose'] = sorted(
                [(s, d['verbosity']['avg_words_per_speech']) for s, d in speakers_with_verbosity],
                key=lambda x: -x[1]
            )[:10]
        
        # Most consistent
        if any('consistency' in d for s, d in speakers):
            speakers_with_consistency = [(s, d) for s, d in speakers if 'consistency' in d]
            rankings['most_consistent'] = sorted(
                [(s, d['consistency']['score']) for s, d in speakers_with_consistency],
                key=lambda x: -x[1]
            )[:10]
        
        # Most active
        if any('intervention' in d for s, d in speakers):
            speakers_with_int = [(s, d) for s, d in speakers if 'intervention' in d]
            rankings['most_active'] = sorted(
                [(s, d['intervention']['avg_speeches_per_month']) for s, d in speakers_with_int],
                key=lambda x: -x[1]
            )[:10]
        
        # Richest vocabulary
        if any('vocabulary' in d for s, d in speakers):
            speakers_with_vocab = [(s, d) for s, d in speakers if 'vocabulary' in d]
            rankings['richest_vocabulary'] = sorted(
                [(s, d['vocabulary']['type_token_ratio']) for s, d in speakers_with_vocab],
                key=lambda x: -x[1]
            )[:10]
        
        return rankings
