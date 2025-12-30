"""
Tests for Relations Analyzer.

Tests:
- Party Affinity Matrix
- Party Cohesion
- Thematic Overlap
- Cross-Party Pairs
"""

import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestRelationsAnalyzer:
    """Tests for RelationsAnalyzer class."""
    
    def test_analyzer_registration(self):
        """Test that RelationsAnalyzer is registered."""
        from backend.analyzers import AnalyzerRegistry
        
        assert 'relations' in AnalyzerRegistry.names()
    
    def test_analyzer_compute(self, mock_data, analyzer_kwargs):
        """Test full analyzer computation."""
        from backend.analyzers.relations import RelationsAnalyzer
        
        analyzer = RelationsAnalyzer(**analyzer_kwargs)
        result = analyzer.compute()
        
        assert isinstance(result, dict)


class TestAffinityMatrix:
    """Tests for party affinity matrix."""
    
    def test_compute_affinity_matrix(self, mock_df, mock_embeddings):
        """Test affinity matrix computation."""
        from backend.analyzers.relations import compute_party_affinity_matrix
        
        result = compute_party_affinity_matrix(
            df=mock_df,
            embeddings=mock_embeddings,
            party_col='group'
        )
        
        assert 'parties' in result
        assert 'matrix' in result
        assert 'pairs' in result
    
    def test_matrix_symmetry(self, mock_df, mock_embeddings):
        """Test that affinity matrix is symmetric."""
        from backend.analyzers.relations import compute_party_affinity_matrix
        
        result = compute_party_affinity_matrix(
            df=mock_df,
            embeddings=mock_embeddings,
            party_col='group'
        )
        
        matrix = result['matrix']
        n = len(matrix)
        
        for i in range(n):
            for j in range(n):
                assert abs(matrix[i][j] - matrix[j][i]) < 0.001
    
    def test_diagonal_is_one(self, mock_df, mock_embeddings):
        """Test that diagonal elements are 1 (self-similarity)."""
        from backend.analyzers.relations import compute_party_affinity_matrix
        
        result = compute_party_affinity_matrix(
            df=mock_df,
            embeddings=mock_embeddings,
            party_col='group'
        )
        
        matrix = result['matrix']
        
        for i in range(len(matrix)):
            assert abs(matrix[i][i] - 1.0) < 0.001


class TestPartyCohesion:
    """Tests for party cohesion computation."""
    
    def test_compute_party_cohesion(self, mock_df, mock_embeddings):
        """Test party cohesion computation."""
        from backend.analyzers.relations import compute_party_cohesion
        
        result = compute_party_cohesion(
            df=mock_df,
            embeddings=mock_embeddings,
            party_col='group'
        )
        
        assert len(result) > 0
        
        for party, data in result.items():
            assert 'cohesion_score' in data
            assert 'interpretation' in data
            assert 0 <= data['cohesion_score'] <= 1


class TestThematicOverlap:
    """Tests for thematic overlap computation."""
    
    def test_compute_thematic_overlap(self, mock_df, mock_cluster_labels):
        """Test thematic overlap computation."""
        from backend.analyzers.relations import compute_thematic_overlap
        
        result = compute_thematic_overlap(
            df=mock_df,
            cluster_col='cluster',
            cluster_labels=mock_cluster_labels,
            party_col='group'
        )
        
        assert len(result) > 0
        
        for cluster_id, data in result.items():
            assert 'left_pct' in data
            assert 'right_pct' in data
            assert 'type' in data
