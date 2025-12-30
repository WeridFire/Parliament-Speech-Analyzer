"""
Tests for Sentiment Analyzer.

Tests:
- Topic Sentiment
- Readability (Gulpease)
- Polarization
- Rankings
"""

import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestSentimentAnalyzer:
    """Tests for SentimentAnalyzer class."""
    
    def test_analyzer_registration(self):
        """Test that SentimentAnalyzer is registered."""
        from backend.analyzers import AnalyzerRegistry
        
        assert 'sentiment' in AnalyzerRegistry.names()
    
    def test_analyzer_compute(self, mock_data, analyzer_kwargs):
        """Test full analyzer computation."""
        from backend.analyzers.sentiment import SentimentAnalyzer
        
        analyzer = SentimentAnalyzer(**analyzer_kwargs)
        result = analyzer.compute()
        
        assert isinstance(result, dict)
        assert len(result) > 0


class TestTopicSentiment:
    """Tests for topic sentiment computation."""
    
    def test_compute_topic_sentiment(self, mock_df, mock_cluster_labels):
        """Test topic sentiment computation."""
        from backend.analyzers.sentiment import compute_topic_sentiment
        
        result = compute_topic_sentiment(
            df=mock_df,
            text_col='cleaned_text',
            cluster_col='cluster',
            cluster_labels=mock_cluster_labels,
            speaker_col='deputy',
            party_col='group'
        )
        
        assert 'by_speaker' in result
        assert 'by_party' in result
        assert 'by_cluster' in result
    
    def test_sentiment_scores_valid(self, mock_df, mock_cluster_labels):
        """Test that sentiment scores are in valid range."""
        from backend.analyzers.sentiment import compute_topic_sentiment
        
        result = compute_topic_sentiment(
            df=mock_df,
            text_col='cleaned_text',
            cluster_col='cluster',
            cluster_labels=mock_cluster_labels,
            speaker_col='deputy',
            party_col='group'
        )
        
        for cluster_id, data in result['by_cluster'].items():
            assert -1 <= data['avg_sentiment'] <= 1


class TestReadability:
    """Tests for readability (Gulpease) computation."""
    
    def test_compute_gulpease_single(self):
        """Test Gulpease on single text."""
        from backend.analyzers.sentiment import compute_gulpease_score
        
        text = "Questa è una frase semplice. Ed ecco un'altra frase."
        result = compute_gulpease_score(text)
        
        assert 'score' in result
        assert 'classification' in result
        assert 'n_words' in result
        assert 0 <= result['score'] <= 100
    
    def test_readability_classification(self):
        """Test readability classifications."""
        from backend.analyzers.sentiment import compute_gulpease_score
        
        # Very simple text
        simple = "Io amo te. Tu ami me. Noi siamo felici."
        result = compute_gulpease_score(simple)
        
        assert result['classification'] in ('facile', 'medio', 'difficile')
    
    def test_compute_readability_scores(self, mock_df):
        """Test batch readability computation."""
        from backend.analyzers.sentiment import compute_readability_scores
        
        result = compute_readability_scores(
            df=mock_df,
            text_col='cleaned_text',
            speaker_col='deputy',
            party_col='group'
        )
        
        assert 'by_speaker' in result
        assert 'by_party' in result


class TestPolarization:
    """Tests for polarization computation."""
    
    def test_compute_polarization_scores(self, mock_df):
        """Test polarization computation."""
        from backend.analyzers.sentiment import compute_polarization_scores
        
        result = compute_polarization_scores(
            df=mock_df,
            text_col='cleaned_text',
            speaker_col='deputy',
            party_col='group'
        )
        
        assert 'by_speaker' in result
        assert 'by_party' in result
        assert 'top_polarizers' in result
    
    def test_polarization_scores_valid(self, mock_df):
        """Test that polarization scores are in valid range."""
        from backend.analyzers.sentiment import compute_polarization_scores
        
        result = compute_polarization_scores(
            df=mock_df,
            text_col='cleaned_text',
            speaker_col='deputy',
            party_col='group'
        )
        
        for party, data in result['by_party'].items():
            assert 0 <= data['avg_score'] <= 100
