"""
Tests for Topics Analyzer.

Tests:
- Topic Extraction
- Cluster Labeling
"""

import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestTopicsAnalyzer:
    """Tests for TopicsAnalyzer class."""
    
    def test_analyzer_registration(self):
        """Test that TopicsAnalyzer is registered."""
        from backend.analyzers import AnalyzerRegistry
        
        assert 'topics' in AnalyzerRegistry.names()
    
    def test_analyzer_compute(self, mock_data, analyzer_kwargs):
        """Test full analyzer computation."""
        from backend.analyzers.topics import TopicsAnalyzer
        
        analyzer = TopicsAnalyzer(**analyzer_kwargs)
        result = analyzer.compute()
        
        assert isinstance(result, dict)
        assert 'cluster_topics' in result
        assert 'cluster_labels' in result


class TestTopicExtraction:
    """Tests for topic extraction."""
    
    def test_extract_cluster_topics(self, mock_df):
        """Test topic extraction."""
        from backend.analyzers.topics import extract_cluster_topics
        
        result = extract_cluster_topics(
            df=mock_df,
            text_col='cleaned_text',
            cluster_col='cluster',
            top_n=5
        )
        
        assert isinstance(result, dict)
        
        for cluster_id, keywords in result.items():
            assert isinstance(keywords, list)
            assert len(keywords) <= 5
            for kw in keywords:
                assert isinstance(kw, str)


class TestClusterLabeling:
    """Tests for cluster labeling."""
    
    def test_get_cluster_labels(self, mock_df):
        """Test cluster label generation."""
        from backend.analyzers.topics import get_cluster_labels
        
        result = get_cluster_labels(mock_df)
        
        assert isinstance(result, dict)
        
        for cluster_id, label in result.items():
            assert isinstance(label, str)
            assert len(label) > 0
