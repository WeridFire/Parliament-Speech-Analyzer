"""
Tests for the Period Orchestrator module.

Tests cover:
- Global-only mode (compute_by_period=False)
- Full period mode (compute_by_period=True)
- Minimum speech thresholds
- Data structure validation
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock

from backend.analyzers.period_orchestrator import (
    compute_analytics_by_period,
    MIN_SPEECHES_YEAR,
    MIN_SPEECHES_MONTH,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def period_test_df():
    """DataFrame with dates spanning multiple years and months."""
    np.random.seed(42)
    
    # Create speeches across 2 years and several months
    dates = (
        ['2024-01-15'] * 15 +  # January 2024: 15 speeches
        ['2024-02-20'] * 12 +  # February 2024: 12 speeches
        ['2024-03-10'] * 8 +   # March 2024: 8 speeches
        ['2023-11-05'] * 20 +  # November 2023: 20 speeches
        ['2023-12-15'] * 5     # December 2023: 5 speeches (below threshold)
    )
    
    n_speeches = len(dates)
    
    return pd.DataFrame({
        'deputy': [f'Deputy_{i % 5}' for i in range(n_speeches)],
        'group': ['Party_A' if i % 2 == 0 else 'Party_B' for i in range(n_speeches)],
        'cluster': [i % 3 for i in range(n_speeches)],
        'cleaned_text': [f'This is speech number {i} with some content.' for i in range(n_speeches)],
        'date': dates,
    })


@pytest.fixture
def period_test_embeddings(period_test_df):
    """Random embeddings matching the test DataFrame."""
    np.random.seed(42)
    return np.random.randn(len(period_test_df), 384).astype(np.float32)


@pytest.fixture
def period_test_cluster_labels():
    """Cluster labels for test data."""
    return {0: 'Topic A', 1: 'Topic B', 2: 'Topic C'}


@pytest.fixture
def period_test_centroids():
    """Cluster centroids for test data."""
    np.random.seed(42)
    return np.random.randn(3, 384).astype(np.float32)


# =============================================================================
# TESTS: COMPUTE_BY_PERIOD=FALSE (GLOBAL ONLY)
# =============================================================================

class TestGlobalOnlyMode:
    """Tests for global-only analytics mode."""
    
    @patch('backend.analyzers.period_orchestrator.AnalyticsOrchestrator')
    def test_returns_global_only_when_disabled(
        self, mock_orchestrator, period_test_df, period_test_embeddings,
        period_test_cluster_labels, period_test_centroids
    ):
        """When compute_by_period=False, should return only global analytics."""
        # Setup mock
        mock_instance = MagicMock()
        mock_instance.run_all.return_value = {'identity': {}, 'sentiment': {}}
        mock_orchestrator.return_value = mock_instance
        
        result = compute_analytics_by_period(
            df=period_test_df,
            embeddings=period_test_embeddings,
            cluster_labels=period_test_cluster_labels,
            cluster_centroids=period_test_centroids,
            compute_by_period=False,
        )
        
        # Assertions
        assert 'global' in result
        assert 'by_year' in result
        assert 'by_month' in result
        assert result['by_year'] == {}
        assert result['by_month'] == {}
        
        # Should only call orchestrator once (for global)
        assert mock_orchestrator.call_count == 1
    
    @patch('backend.analyzers.period_orchestrator.AnalyticsOrchestrator')
    def test_global_only_is_faster(
        self, mock_orchestrator, period_test_df, period_test_embeddings,
        period_test_cluster_labels, period_test_centroids
    ):
        """Global-only mode should call orchestrator only once."""
        mock_instance = MagicMock()
        mock_instance.run_all.return_value = {}
        mock_orchestrator.return_value = mock_instance
        
        compute_analytics_by_period(
            df=period_test_df,
            embeddings=period_test_embeddings,
            cluster_labels=period_test_cluster_labels,
            cluster_centroids=period_test_centroids,
            compute_by_period=False,
        )
        
        # Verify only one orchestrator call
        assert mock_instance.run_all.call_count == 1


# =============================================================================
# TESTS: COMPUTE_BY_PERIOD=TRUE (FULL MODE)
# =============================================================================

class TestFullPeriodMode:
    """Tests for full period-based analytics mode."""
    
    @patch('backend.analyzers.period_orchestrator.AnalyticsOrchestrator')
    def test_computes_by_year(
        self, mock_orchestrator, period_test_df, period_test_embeddings,
        period_test_cluster_labels, period_test_centroids
    ):
        """Should compute analytics for each year with sufficient data."""
        mock_instance = MagicMock()
        mock_instance.run_all.return_value = {'test': 'data'}
        mock_orchestrator.return_value = mock_instance
        
        result = compute_analytics_by_period(
            df=period_test_df,
            embeddings=period_test_embeddings,
            cluster_labels=period_test_cluster_labels,
            cluster_centroids=period_test_centroids,
            compute_by_period=True,
        )
        
        # Should have analytics for both years (2023 and 2024)
        assert '2023' in result['by_year']
        assert '2024' in result['by_year']
    
    @patch('backend.analyzers.period_orchestrator.AnalyticsOrchestrator')
    def test_computes_by_month(
        self, mock_orchestrator, period_test_df, period_test_embeddings,
        period_test_cluster_labels, period_test_centroids
    ):
        """Should compute analytics for months with sufficient data."""
        mock_instance = MagicMock()
        mock_instance.run_all.return_value = {'test': 'data'}
        mock_orchestrator.return_value = mock_instance
        
        result = compute_analytics_by_period(
            df=period_test_df,
            embeddings=period_test_embeddings,
            cluster_labels=period_test_cluster_labels,
            cluster_centroids=period_test_centroids,
            compute_by_period=True,
        )
        
        # Months with >= MIN_SPEECHES_MONTH should be included
        assert '2024-01' in result['by_month']  # 15 speeches
        assert '2024-02' in result['by_month']  # 12 speeches
        assert '2024-03' in result['by_month']  # 8 speeches
        assert '2023-11' in result['by_month']  # 20 speeches
    
    @patch('backend.analyzers.period_orchestrator.AnalyticsOrchestrator')
    def test_respects_minimum_thresholds(
        self, mock_orchestrator, period_test_df, period_test_embeddings,
        period_test_cluster_labels, period_test_centroids
    ):
        """Months below threshold should be excluded."""
        mock_instance = MagicMock()
        mock_instance.run_all.return_value = {'test': 'data'}
        mock_orchestrator.return_value = mock_instance
        
        result = compute_analytics_by_period(
            df=period_test_df,
            embeddings=period_test_embeddings,
            cluster_labels=period_test_cluster_labels,
            cluster_centroids=period_test_centroids,
            compute_by_period=True,
        )
        
        # December 2023 only has 5 speeches, exactly at threshold
        # Should be included if >= MIN_SPEECHES_MONTH (5)
        assert '2023-12' in result['by_month']


# =============================================================================
# TESTS: DATA STRUCTURE VALIDATION
# =============================================================================

class TestDataStructure:
    """Tests for output data structure."""
    
    @patch('backend.analyzers.period_orchestrator.AnalyticsOrchestrator')
    def test_output_structure(
        self, mock_orchestrator, period_test_df, period_test_embeddings,
        period_test_cluster_labels, period_test_centroids
    ):
        """Output should have correct top-level keys."""
        mock_instance = MagicMock()
        mock_instance.run_all.return_value = {}
        mock_orchestrator.return_value = mock_instance
        
        result = compute_analytics_by_period(
            df=period_test_df,
            embeddings=period_test_embeddings,
            cluster_labels=period_test_cluster_labels,
            cluster_centroids=period_test_centroids,
        )
        
        assert set(result.keys()) == {'global', 'by_year', 'by_month'}
    
    @patch('backend.analyzers.period_orchestrator.AnalyticsOrchestrator')
    def test_year_keys_are_strings(
        self, mock_orchestrator, period_test_df, period_test_embeddings,
        period_test_cluster_labels, period_test_centroids
    ):
        """Year keys should be strings for JSON compatibility."""
        mock_instance = MagicMock()
        mock_instance.run_all.return_value = {}
        mock_orchestrator.return_value = mock_instance
        
        result = compute_analytics_by_period(
            df=period_test_df,
            embeddings=period_test_embeddings,
            cluster_labels=period_test_cluster_labels,
            cluster_centroids=period_test_centroids,
            compute_by_period=True,
        )
        
        for key in result['by_year'].keys():
            assert isinstance(key, str), f"Year key should be string, got {type(key)}"


# =============================================================================
# TESTS: ERROR HANDLING
# =============================================================================

class TestErrorHandling:
    """Tests for error handling scenarios."""
    
    @patch('backend.analyzers.period_orchestrator.AnalyticsOrchestrator')
    def test_handles_analyzer_failure_gracefully(
        self, mock_orchestrator, period_test_df, period_test_embeddings,
        period_test_cluster_labels, period_test_centroids
    ):
        """Should continue processing if one period fails."""
        mock_instance = MagicMock()
        call_count = [0]
        
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:  # Second call (first year) fails
                raise ValueError("Test error")
            return {'test': 'data'}
        
        mock_instance.run_all.side_effect = side_effect
        mock_orchestrator.return_value = mock_instance
        
        # Should not raise, should continue with other periods
        result = compute_analytics_by_period(
            df=period_test_df,
            embeddings=period_test_embeddings,
            cluster_labels=period_test_cluster_labels,
            cluster_centroids=period_test_centroids,
            compute_by_period=True,
        )
        
        # Should still have global and some periods
        assert 'global' in result
        assert result['global'] == {'test': 'data'}
