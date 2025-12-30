"""
Tests for Temporal Analyzer.

Tests:
- Topic Trends
- Semantic Drift
- Crisis Index
- Topic Surfing
"""

import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestTemporalAnalyzer:
    """Tests for TemporalAnalyzer class."""
    
    def test_analyzer_registration(self):
        """Test that TemporalAnalyzer is registered."""
        from backend.analyzers import AnalyzerRegistry
        
        assert 'temporal' in AnalyzerRegistry.names()
    
    def test_analyzer_compute(self, mock_data, analyzer_kwargs):
        """Test full analyzer computation."""
        from backend.analyzers.temporal import TemporalAnalyzer
        
        analyzer = TemporalAnalyzer(**analyzer_kwargs)
        result = analyzer.compute()
        
        assert isinstance(result, dict)


class TestTopicTrends:
    """Tests for topic trends computation."""
    
    def test_compute_topic_trends(self, mock_df, mock_cluster_labels):
        """Test topic trends computation."""
        from backend.analyzers.temporal import compute_topic_trends
        
        result = compute_topic_trends(
            df=mock_df,
            cluster_col='cluster',
            cluster_labels=mock_cluster_labels,
            date_col='date',
            granularity='month',
            party_col='group'
        )
        
        assert 'global' in result
        assert 'by_party' in result
        assert 'periods' in result
        assert isinstance(result['periods'], list)


class TestSemanticDrift:
    """Tests for semantic drift computation."""
    
    def test_compute_semantic_drift(self, mock_df, mock_embeddings):
        """Test semantic drift computation."""
        from backend.analyzers.temporal import compute_semantic_drift
        
        result = compute_semantic_drift(
            df=mock_df,
            embeddings=mock_embeddings,
            party_col='group',
            date_col='date'
        )
        
        # May be empty if not enough time periods
        assert isinstance(result, dict)


class TestCrisisIndex:
    """Tests for crisis index computation."""
    
    def test_compute_crisis_index(self, mock_df, mock_cluster_labels):
        """Test crisis index computation."""
        from backend.analyzers.temporal import compute_crisis_index
        
        result = compute_crisis_index(
            df=mock_df,
            text_col='cleaned_text',
            cluster_col='cluster',
            cluster_labels=mock_cluster_labels,
            date_col='date',
            granularity='month'
        )
        
        assert 'global' in result
        assert 'crisis_keywords' in result
        assert 'periods' in result
