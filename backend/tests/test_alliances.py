"""
Tests for Alliances Analyzer.

Tests:
- Transversal Clusters
- Unusual Pairs
- Left-Right Alliances
"""

import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestAlliancesAnalyzer:
    """Tests for AlliancesAnalyzer class."""
    
    def test_analyzer_registration(self):
        """Test that AlliancesAnalyzer is registered."""
        from backend.analyzers import AnalyzerRegistry
        
        assert 'alliances' in AnalyzerRegistry.names()
    
    def test_analyzer_compute(self, mock_data, analyzer_kwargs):
        """Test full analyzer computation."""
        from backend.analyzers.alliances import AlliancesAnalyzer
        
        analyzer = AlliancesAnalyzer(**analyzer_kwargs)
        result = analyzer.compute()
        
        assert isinstance(result, dict)


class TestTransversalClusters:
    """Tests for transversal cluster detection."""
    
    def test_find_transversal_clusters(self, mock_df):
        """Test transversal cluster detection."""
        from backend.analyzers.alliances import find_transversal_clusters
        
        result = find_transversal_clusters(
            df=mock_df,
            min_parties=2,
            min_mixing=0.3
        )
        
        assert isinstance(result, list)
        
        for cluster in result:
            assert 'cluster' in cluster
            assert 'mixing_score' in cluster


class TestUnusualPairs:
    """Tests for unusual pair detection."""
    
    def test_find_unusual_pairs(self, mock_df, mock_embeddings):
        """Test unusual pair detection."""
        from backend.analyzers.alliances import find_unusual_pairs
        
        result = find_unusual_pairs(
            df=mock_df,
            embeddings=mock_embeddings,
            speaker_col='deputy',
            party_col='group',
            top_n=5
        )
        
        assert isinstance(result, list)
        
        for pair in result:
            assert 'speaker1' in pair
            assert 'speaker2' in pair
            assert 'party1' in pair
            assert 'party2' in pair
            assert 'similarity' in pair
            # Should be cross-party
            assert pair['party1'] != pair['party2']
