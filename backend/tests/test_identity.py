"""
Tests for Identity Analyzer.

Tests:
- Thematic Fingerprint
- Generalism Index
- Distinctive Keywords
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestIdentityAnalyzer:
    """Tests for IdentityAnalyzer class."""
    
    def test_analyzer_registration(self):
        """Test that IdentityAnalyzer is registered."""
        from backend.analyzers import AnalyzerRegistry
        
        assert 'identity' in AnalyzerRegistry.names()
    
    def test_analyzer_compute(self, mock_data, analyzer_kwargs):
        """Test full analyzer computation."""
        from backend.analyzers.identity import IdentityAnalyzer
        
        analyzer = IdentityAnalyzer(**analyzer_kwargs)
        result = analyzer.compute()
        
        assert isinstance(result, dict)
        # Check for expected keys based on enabled features
        assert any(key in result for key in ['thematic_fingerprint', 'generalism_index', 'distinctive_keywords'])


class TestThematicFingerprint:
    """Tests for thematic fingerprint computation."""
    
    def test_compute_fingerprint(self, mock_df, mock_embeddings, mock_cluster_centroids, mock_cluster_labels):
        """Test fingerprint computation."""
        from backend.analyzers.identity import compute_thematic_fingerprint
        
        result = compute_thematic_fingerprint(
            df=mock_df,
            embeddings=mock_embeddings,
            cluster_centroids=mock_cluster_centroids,
            cluster_labels=mock_cluster_labels,
            speaker_col='deputy',
            party_col='group'
        )
        
        assert isinstance(result, dict)
        assert 'by_deputy' in result
        assert 'by_party' in result
        assert 'cluster_labels' in result
        assert len(result['by_deputy']) > 0
    
    def test_fingerprint_values_valid(self, mock_df, mock_embeddings, mock_cluster_centroids, mock_cluster_labels):
        """Test that fingerprint similarity values are in valid range [-1, 1]."""
        from backend.analyzers.identity import compute_thematic_fingerprint
        
        result = compute_thematic_fingerprint(
            df=mock_df,
            embeddings=mock_embeddings,
            cluster_centroids=mock_cluster_centroids,
            cluster_labels=mock_cluster_labels
        )
        
        for deputy, clusters in result['by_deputy'].items():
            for cluster_id, similarity in clusters.items():
                assert -1 <= similarity <= 1, f"Similarity {similarity} out of range for {deputy}"


class TestGeneralismIndex:
    """Tests for generalism index computation."""
    
    def test_compute_generalism(self, mock_df, mock_cluster_labels):
        """Test generalism index computation."""
        from backend.analyzers.identity import compute_generalism_index
        
        result = compute_generalism_index(
            df=mock_df,
            cluster_col='cluster',
            speaker_col='deputy',
            party_col='group'
        )
        
        assert isinstance(result, dict)
        assert 'by_deputy' in result
        assert 'by_party' in result
        assert len(result['by_deputy']) > 0
    
    def test_generalism_score_range(self, mock_df):
        """Test that generalism scores are in 0-100 range."""
        from backend.analyzers.identity import compute_generalism_index
        
        result = compute_generalism_index(
            df=mock_df,
            cluster_col='cluster',
            speaker_col='deputy',
            party_col='group'
        )
        
        for deputy, data in result['by_deputy'].items():
            assert 0 <= data['score'] <= 100
    
    def test_classification_values(self, mock_df):
        """Test that classifications are valid."""
        from backend.analyzers.identity import compute_generalism_index
        
        result = compute_generalism_index(
            df=mock_df,
            cluster_col='cluster',
            speaker_col='deputy',
            party_col='group'
        )
        
        valid_classifications = {'monotematico', 'specialista', 'equilibrato', 'generalista'}
        
        for deputy, data in result['by_deputy'].items():
            assert data['classification'] in valid_classifications


class TestDistinctiveKeywords:
    """Tests for distinctive keywords computation."""
    
    def test_compute_keywords(self, mock_df):
        """Test keywords extraction (per party)."""
        from backend.analyzers.identity import compute_distinctive_keywords
        
        result = compute_distinctive_keywords(
            df=mock_df,
            party_col='group',
            text_col='cleaned_text',
            top_n=5
        )
        
        assert isinstance(result, dict)
        assert len(result) > 0
        
        # Check structure - result is keyed by party
        first_party = list(result.keys())[0]
        keywords = result[first_party]
        
        assert isinstance(keywords, list)
        assert len(keywords) <= 5
    
    def test_keywords_are_strings(self, mock_df):
        """Test that keywords are strings."""
        from backend.analyzers.identity import compute_distinctive_keywords
        
        result = compute_distinctive_keywords(
            df=mock_df,
            party_col='group',
            text_col='cleaned_text',
            top_n=5
        )
        
        for party, keywords in result.items():
            for kw in keywords:
                assert isinstance(kw, str)
                assert len(kw) > 0
