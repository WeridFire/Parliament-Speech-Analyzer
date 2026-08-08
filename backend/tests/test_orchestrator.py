"""
Tests for Orchestrator and Registry.

Tests:
- AnalyzerRegistry
- AnalyticsOrchestrator
"""

import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestAnalyzerRegistry:
    """Tests for AnalyzerRegistry."""
    
    def test_all_analyzers_registered(self):
        """Test that all expected analyzers are registered."""
        from backend.analyzers import AnalyzerRegistry
        
        expected = [
            'identity', 'sentiment', 'temporal', 'relations',
            'speaker', 'rhetoric', 'factions', 'alliances', 'topics'
        ]
        
        names = AnalyzerRegistry.names()
        
        for analyzer in expected:
            assert analyzer in names, f"Missing analyzer: {analyzer}"
    
    def test_get_analyzer(self):
        """Test getting analyzer by name."""
        from backend.analyzers import AnalyzerRegistry
        
        analyzer_class = AnalyzerRegistry.get('identity')
        
        assert analyzer_class is not None
        assert analyzer_class.name == 'identity'
    
    def test_get_nonexistent_returns_none(self):
        """Test that getting nonexistent analyzer returns None."""
        from backend.analyzers import AnalyzerRegistry
        
        result = AnalyzerRegistry.get('nonexistent_analyzer')
        
        assert result is None


class TestAnalyticsOrchestrator:
    """Tests for AnalyticsOrchestrator."""
    
    def test_orchestrator_creation(self, mock_data):
        """Test orchestrator creation."""
        from backend.analyzers import AnalyticsOrchestrator
        
        orchestrator = AnalyticsOrchestrator(
            df=mock_data.df,
            embeddings=mock_data.embeddings,
            cluster_labels=mock_data.cluster_labels,
            cluster_centroids=mock_data.cluster_centroids,
            source='test'
        )
        
        assert orchestrator is not None
    
    def test_run_single_analyzer(self, mock_data):
        """Test running a single analyzer."""
        from backend.analyzers import AnalyticsOrchestrator
        
        orchestrator = AnalyticsOrchestrator(
            df=mock_data.df,
            embeddings=mock_data.embeddings,
            cluster_labels=mock_data.cluster_labels,
            cluster_centroids=mock_data.cluster_centroids,
            source='test',
        )

        result = orchestrator.run('identity')

        assert isinstance(result, dict)
    
    def test_run_all_analyzers(self, mock_data):
        """Test running all enabled analyzers."""
        from backend.analyzers import AnalyticsOrchestrator
        
        orchestrator = AnalyticsOrchestrator(
            df=mock_data.df,
            embeddings=mock_data.embeddings,
            cluster_labels=mock_data.cluster_labels,
            cluster_centroids=mock_data.cluster_centroids,
            source='test',
        )

        results = orchestrator.run_all()

        assert isinstance(results, dict)
        assert len(results) > 0
        assert not orchestrator.failures, f"analyzers failed: {orchestrator.failures}"
    
    def test_get_available_analyzers(self, mock_data):
        """Test getting available analyzers."""
        from backend.analyzers import AnalyticsOrchestrator
        
        orchestrator = AnalyticsOrchestrator(
            df=mock_data.df,
            source='test',
        )

        available = orchestrator.get_available_analyzers()

        assert len(available) >= 9

    def test_invalid_analyzer_raises(self, mock_data):
        """Test that invalid analyzer name raises error."""
        from backend.analyzers import AnalyticsOrchestrator

        orchestrator = AnalyticsOrchestrator(
            df=mock_data.df,
            source='test',
        )

        with pytest.raises(ValueError):
            orchestrator.run('nonexistent')


class TestRunReporting:
    """
    A partial run must be visible.

    Analyzer failures are recorded rather than raised, so without an explicit
    record the payload ships with a silent hole where a metric should be.
    """

    def test_missing_dependencies_are_reported_as_skipped(self, mock_data):
        """Analyzers needing embeddings are skipped, not failed, when none exist."""
        from backend.analyzers import AnalyticsOrchestrator

        orchestrator = AnalyticsOrchestrator(df=mock_data.df, source='test')
        results = orchestrator.run_all()

        assert orchestrator.skipped, "expected embedding-dependent analyzers to be skipped"
        for name, missing in orchestrator.skipped.items():
            assert missing
            assert name not in results

    def test_failures_are_recorded(self, mock_data, monkeypatch):
        """A raising analyzer lands in `failures` and in the payload as an error."""
        from backend.analyzers import AnalyticsOrchestrator, AnalyzerRegistry

        identity = AnalyzerRegistry.get('identity')
        monkeypatch.setattr(
            identity, 'compute',
            lambda self: (_ for _ in ()).throw(RuntimeError('boom')),
        )

        orchestrator = AnalyticsOrchestrator(
            df=mock_data.df,
            embeddings=mock_data.embeddings,
            cluster_labels=mock_data.cluster_labels,
            cluster_centroids=mock_data.cluster_centroids,
            source='test',
        )
        results = orchestrator.run_all()

        assert orchestrator.failures.get('identity') == 'boom'
        assert results['identity'] == {'error': 'boom'}

    def test_clean_run_reports_nothing(self, mock_data):
        from backend.analyzers import AnalyticsOrchestrator

        orchestrator = AnalyticsOrchestrator(
            df=mock_data.df,
            embeddings=mock_data.embeddings,
            cluster_labels=mock_data.cluster_labels,
            cluster_centroids=mock_data.cluster_centroids,
            source='test',
        )
        orchestrator.run_all()

        assert orchestrator.failures == {}
