"""
Tests for Factions Analyzer.

Tests:
- Senator Conformity
- Faction Detection
"""

import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestFactionsAnalyzer:
    """Tests for FactionsAnalyzer class."""
    
    def test_analyzer_registration(self):
        """Test that FactionsAnalyzer is registered."""
        from backend.analyzers import AnalyzerRegistry
        
        assert 'factions' in AnalyzerRegistry.names()
    
    def test_analyzer_compute(self, mock_data, analyzer_kwargs):
        """Test full analyzer computation."""
        from backend.analyzers.factions import FactionsAnalyzer
        
        analyzer = FactionsAnalyzer(**analyzer_kwargs)
        result = analyzer.compute()
        
        assert isinstance(result, dict)


class TestSenatorConformity:
    """Tests for senator conformity computation."""
    
    def test_compute_senator_conformity(self, mock_df, mock_embeddings):
        """Test senator conformity computation."""
        from backend.analyzers.factions import compute_senator_conformity
        
        result = compute_senator_conformity(
            df=mock_df,
            embeddings=mock_embeddings,
            speaker_col='deputy',
            party_col='group'
        )
        
        assert len(result) > 0
        
        # Check DataFrame structure
        assert 'speaker' in result.columns
        assert 'party' in result.columns
        assert 'conformity' in result.columns
        assert 'faction_label' in result.columns
    
    def test_faction_labels_valid(self, mock_df, mock_embeddings):
        """Test that faction labels are valid."""
        from backend.analyzers.factions import compute_senator_conformity
        
        result = compute_senator_conformity(
            df=mock_df,
            embeddings=mock_embeddings,
            speaker_col='deputy',
            party_col='group'
        )
        
        valid_labels = {'mainstream', 'maverick', 'bridge'}
        
        for label in result['faction_label']:
            assert label in valid_labels


class TestGetAllFactions:
    """Tests for get_all_factions function."""
    
    def test_get_all_factions(self, mock_df, mock_embeddings):
        """Test get_all_factions function."""
        from backend.analyzers.factions import get_all_factions
        
        result = get_all_factions(mock_df, mock_embeddings)
        
        assert isinstance(result, dict)
        
        for party, data in result.items():
            if data:  # Non-empty
                assert 'n_senators' in data
                assert 'avg_conformity' in data
