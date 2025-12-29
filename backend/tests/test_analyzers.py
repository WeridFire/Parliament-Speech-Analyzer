"""
Tests for backend analyzers (rhetoric, relations, topics).
"""
import pytest
import numpy as np
import pandas as pd

from backend.analyzers.rhetoric import (
    tokenize_simple,
    compute_rhetoric_scores,
    add_rhetoric_scores,
    classify_rhetorical_style
)
from backend.analyzers.relations import (
    compute_party_centroids,
    categorize_party_coalition
)


# =============================================================================
# Tokenization Tests
# =============================================================================

class TestTokenization:
    """Tests for tokenization functions."""
    
    def test_tokenize_simple_basic(self):
        """Should split text into lowercase tokens."""
        result = tokenize_simple("Ciao, mondo!")
        assert "ciao" in result
        assert "mondo" in result
        assert "," not in result  # Punctuation removed
    
    def test_tokenize_simple_punctuation(self):
        """Should remove all punctuation."""
        result = tokenize_simple("L'Italia è bella, no?")
        # Check tokens are clean
        for token in result:
            assert not any(c in token for c in ".,;:!?'\"")
    
    def test_tokenize_simple_empty(self):
        """Should handle empty string."""
        result = tokenize_simple("")
        assert result == []


# =============================================================================
# Rhetoric Analysis Tests
# =============================================================================

class TestRhetoricAnalysis:
    """Tests for rhetoric scoring functions."""
    
    def test_rhetoric_scores_keys(self):
        """Should return all expected score types."""
        scores = compute_rhetoric_scores("Test text for analysis")
        
        expected_keys = ['populist', 'anti_establishment', 'emotional', 'institutional']
        for key in expected_keys:
            assert key in scores
    
    def test_rhetoric_scores_non_negative(self):
        """All scores should be non-negative."""
        scores = compute_rhetoric_scores("La casta politica ha tradito il popolo!")
        
        for key, value in scores.items():
            assert value >= 0, f"{key} score should be >= 0, got {value}"
    
    def test_populist_markers_detected(self):
        """Should detect populist keywords."""
        populist_text = "La casta e l'élite hanno tradito il popolo italiano"
        neutral_text = "La proposta di legge è stata approvata"
        
        populist_scores = compute_rhetoric_scores(populist_text)
        neutral_scores = compute_rhetoric_scores(neutral_text)
        
        assert populist_scores['populist'] > neutral_scores['populist']
    
    def test_add_rhetoric_scores_columns(self, sample_speeches_df):
        """Should add rhetoric columns to DataFrame."""
        df = sample_speeches_df.copy()
        result = add_rhetoric_scores(df, text_col='cleaned_text')
        
        expected_cols = ['populist', 'anti_establishment', 'emotional', 'institutional']
        for col in expected_cols:
            assert col in result.columns
    
    def test_classify_rhetorical_style_neutral(self):
        """Should classify low-scoring speech as neutral."""
        row = pd.Series({
            'populist': 0.1,
            'anti_establishment': 0.05,
            'emotional': 0.1,
            'institutional': 0.1
        })
        result = classify_rhetorical_style(row)
        assert result == 'neutrale'


# =============================================================================
# Party Categorization Tests
# =============================================================================

class TestPartyCategorization:
    """Tests for party coalition categorization."""
    
    def test_categorize_left_party(self):
        """Should categorize PD as left."""
        assert categorize_party_coalition("PD-IDP") == "left"
        assert categorize_party_coalition("M5S") == "left"
    
    def test_categorize_right_party(self):
        """Should categorize FdI as right."""
        result = categorize_party_coalition("FdI")
        assert result == "right"
    
    def test_categorize_center_party(self):
        """Should categorize IV as center."""
        result = categorize_party_coalition("IV-C-RE")
        assert result == "center"
    
    def test_categorize_unknown_party(self):
        """Should return 'other' for unknown parties."""
        result = categorize_party_coalition("Partito Inventato XYZ")
        assert result == "other"


# =============================================================================
# Party Centroids Tests
# =============================================================================

class TestPartyCentroids:
    """Tests for party centroid computation."""
    
    def test_compute_centroids_returns_dict(self, sample_speeches_df, sample_embeddings):
        """Should return a dictionary of centroids."""
        centroids = compute_party_centroids(
            sample_speeches_df,
            sample_embeddings,
            party_col='group'
        )
        
        assert isinstance(centroids, dict)
        assert len(centroids) > 0
    
    def test_centroids_correct_dimension(self, sample_speeches_df, sample_embeddings):
        """Centroids should have same dimension as embeddings."""
        centroids = compute_party_centroids(
            sample_speeches_df,
            sample_embeddings,
            party_col='group'
        )
        
        embedding_dim = sample_embeddings.shape[1]
        for party, centroid in centroids.items():
            assert centroid.shape[0] == embedding_dim
    
    def test_excludes_unknown_group(self, sample_embeddings):
        """Should exclude 'Unknown Group' from centroids."""
        df = pd.DataFrame({
            'group': ['PD-IDP', 'Unknown Group', 'FdI', 'Unknown Group']
        })
        
        centroids = compute_party_centroids(df, sample_embeddings, party_col='group')
        
        assert 'Unknown Group' not in centroids
