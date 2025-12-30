"""
Tests for Speaker Analyzer.

Tests:
- Verbosity/Linguistic Metrics
- Consistency Index
- Topic Leadership
- Intervention Patterns
- Vocabulary Richness
- Interaction Network
"""

import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestSpeakerAnalyzer:
    """Tests for SpeakerAnalyzer class."""
    
    def test_analyzer_registration(self):
        """Test that SpeakerAnalyzer is registered."""
        from backend.analyzers import AnalyzerRegistry
        
        assert 'speaker' in AnalyzerRegistry.names()
    
    def test_analyzer_compute(self, mock_data, analyzer_kwargs):
        """Test full analyzer computation."""
        from backend.analyzers.speaker import SpeakerAnalyzer
        
        analyzer = SpeakerAnalyzer(**analyzer_kwargs)
        result = analyzer.compute()
        
        assert isinstance(result, dict)
        assert 'by_speaker' in result


class TestVerbosityMetrics:
    """Tests for verbosity and linguistic metrics."""
    
    def test_aggregate_speaker_metrics(self, mock_df):
        """Test aggregated speaker metrics computation."""
        from backend.analyzers.speaker import aggregate_speaker_metrics
        
        result = aggregate_speaker_metrics(
            df=mock_df,
            speaker_col='deputy',
            text_col='cleaned_text'
        )
        
        assert len(result) > 0
        
        for speaker, data in result.items():
            assert 'verbosity' in data
            assert 'linguistic' in data
            assert 'n_speeches' in data
    
    def test_verbosity_values(self, mock_df):
        """Test that verbosity values are reasonable."""
        from backend.analyzers.speaker import aggregate_speaker_metrics
        
        result = aggregate_speaker_metrics(
            df=mock_df,
            speaker_col='deputy',
            text_col='cleaned_text'
        )
        
        for speaker, data in result.items():
            verbosity = data['verbosity']
            assert verbosity['avg_words_per_speech'] > 0
            assert verbosity['total_words'] > 0


class TestConsistencyIndex:
    """Tests for consistency index computation."""
    
    def test_compute_consistency_index(self, mock_df, mock_embeddings):
        """Test consistency index computation."""
        from backend.analyzers.speaker import compute_consistency_index
        
        result = compute_consistency_index(
            df=mock_df,
            embeddings=mock_embeddings,
            speaker_col='deputy'
        )
        
        assert len(result) > 0
        
        for speaker, data in result.items():
            assert 'score' in data
            assert 'classification' in data
            assert 0 <= data['score'] <= 100


class TestTopicLeadership:
    """Tests for topic leadership computation."""
    
    def test_compute_topic_leadership(self, mock_df, mock_embeddings, mock_cluster_centroids, mock_cluster_labels):
        """Test topic leadership computation."""
        from backend.analyzers.speaker import compute_topic_leadership
        
        result = compute_topic_leadership(
            df=mock_df,
            embeddings=mock_embeddings,
            cluster_centroids=mock_cluster_centroids,
            cluster_labels=mock_cluster_labels,
            speaker_col='deputy',
            cluster_col='cluster'
        )
        
        assert 'by_speaker' in result
        assert 'by_topic' in result


class TestInterventionPatterns:
    """Tests for intervention patterns computation."""
    
    def test_compute_intervention_patterns(self, mock_df):
        """Test intervention patterns computation."""
        from backend.analyzers.speaker import compute_intervention_patterns
        
        result = compute_intervention_patterns(
            df=mock_df,
            speaker_col='deputy',
            date_col='date'
        )
        
        assert len(result) > 0
        
        for speaker, data in result.items():
            assert 'avg_speeches_per_month' in data
            assert 'regularity_score' in data


class TestVocabularyRichness:
    """Tests for vocabulary richness computation."""
    
    def test_compute_vocabulary_richness(self, mock_df):
        """Test vocabulary richness computation."""
        from backend.analyzers.speaker import compute_vocabulary_richness
        
        result = compute_vocabulary_richness(
            df=mock_df,
            speaker_col='deputy',
            text_col='cleaned_text'
        )
        
        assert len(result) > 0
        
        for speaker, data in result.items():
            assert 'type_token_ratio' in data
            assert 0 <= data['type_token_ratio'] <= 1


class TestInteractionNetwork:
    """Tests for interaction network computation."""
    
    def test_compute_interaction_network(self, mock_df):
        """Test interaction network computation."""
        from backend.analyzers.speaker import compute_interaction_network
        
        result = compute_interaction_network(
            df=mock_df,
            speaker_col='deputy',
            text_col='cleaned_text'
        )
        
        assert len(result) > 0
        
        for speaker, data in result.items():
            assert 'mentions_given' in data
            assert 'mentions_received' in data
            assert 'out_degree' in data
            assert 'in_degree' in data
