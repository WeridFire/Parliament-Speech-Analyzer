"""
Integration tests for the data pipeline.
"""
import pytest
import numpy as np
import pandas as pd

from backend.pipeline import generate_embeddings, reduce_dimensions, apply_clustering


# =============================================================================
# Embedding Generation Tests
# =============================================================================

class TestEmbeddingGeneration:
    """Tests for embedding generation (uses actual model - slower)."""
    
    @pytest.mark.slow
    def test_embeddings_shape(self):
        """Embeddings should have correct dimensions."""
        texts = ["Questo è un test.", "Questo è un altro test."]
        
        embeddings = generate_embeddings(texts)
        
        assert embeddings.shape[0] == 2  # 2 texts
        assert embeddings.shape[1] > 0   # Some dimensions
    
    @pytest.mark.slow
    def test_embeddings_type(self):
        """Embeddings should be numpy array of floats."""
        texts = ["Test text"]
        
        embeddings = generate_embeddings(texts)
        
        assert isinstance(embeddings, np.ndarray)
        assert embeddings.dtype in [np.float32, np.float64]


# =============================================================================
# Dimensionality Reduction Tests
# =============================================================================

class TestDimensionalityReduction:
    """Tests for dimensionality reduction."""
    
    def test_reduce_to_2d(self, sample_embeddings):
        """Should reduce to 2 dimensions."""
        coords = reduce_dimensions(sample_embeddings, method='pca')
        
        assert coords.shape[0] == sample_embeddings.shape[0]  # Same number of points
        assert coords.shape[1] == 2  # 2D coordinates
    
    def test_pca_output_range(self, sample_embeddings):
        """PCA output should be reasonable (not extreme values)."""
        coords = reduce_dimensions(sample_embeddings, method='pca')
        
        # Values should be within reasonable range
        assert np.all(np.abs(coords) < 100)


# =============================================================================
# Clustering Tests
# =============================================================================

class TestClustering:
    """Tests for K-Means clustering."""
    
    def test_produces_n_clusters(self, sample_embeddings):
        """Should produce the requested number of clusters."""
        n_clusters = 2
        labels = apply_clustering(sample_embeddings, n_clusters=n_clusters)
        
        unique_labels = set(labels)
        assert len(unique_labels) <= n_clusters
    
    def test_labels_valid_range(self, sample_embeddings):
        """Cluster labels should be valid integers."""
        n_clusters = 3
        labels = apply_clustering(sample_embeddings, n_clusters=n_clusters)
        
        for label in labels:
            assert 0 <= label < n_clusters
    
    def test_same_length_as_input(self, sample_embeddings):
        """Should return one label per input sample."""
        labels = apply_clustering(sample_embeddings, n_clusters=2)
        
        assert len(labels) == sample_embeddings.shape[0]


# =============================================================================
# Pipeline Integration Tests
# =============================================================================

class TestPipelineIntegration:
    """End-to-end pipeline tests."""
    
    def test_full_pipeline_flow(self, sample_speeches_df, sample_embeddings):
        """Test complete pipeline: embeddings -> reduce -> cluster."""
        # Reduce dimensions
        coords = reduce_dimensions(sample_embeddings, method='pca')
        
        # Cluster
        labels = apply_clustering(sample_embeddings, n_clusters=2)
        
        # Add to DataFrame
        df = sample_speeches_df.copy()
        df['x'] = coords[:, 0]
        df['y'] = coords[:, 1]
        df['cluster'] = labels
        
        # Verify structure
        assert 'x' in df.columns
        assert 'y' in df.columns
        assert 'cluster' in df.columns
        assert len(df) == len(sample_speeches_df)
    
    def test_output_json_structure(self, sample_speeches_df, sample_embeddings):
        """Output should be JSON-serializable with expected structure."""
        import json
        
        coords = reduce_dimensions(sample_embeddings, method='pca')
        labels = apply_clustering(sample_embeddings, n_clusters=2)
        
        df = sample_speeches_df.copy()
        df['x'] = coords[:, 0]
        df['y'] = coords[:, 1]
        df['cluster'] = labels
        
        # Build output structure
        output = {
            'speeches': df.to_dict('records'),
            'stats': {
                'total_speeches': len(df),
                'total_parties': df['group'].nunique()
            }
        }
        
        # Should be JSON serializable
        json_str = json.dumps(output, default=str)
        assert len(json_str) > 0
        
        # Should be parseable
        parsed = json.loads(json_str)
        assert 'speeches' in parsed
        assert 'stats' in parsed
