"""
Tests for Orchestrator and Registry.

Tests:
- AnalyzerRegistry
- AnalyticsOrchestrator
- CacheManager
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
            enable_cache=False
        )
        
        result = orchestrator.run('identity', use_cache=False)
        
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
            enable_cache=False
        )
        
        results = orchestrator.run_all(use_cache=False)
        
        assert isinstance(results, dict)
        assert len(results) > 0
    
    def test_get_available_analyzers(self, mock_data):
        """Test getting available analyzers."""
        from backend.analyzers import AnalyticsOrchestrator
        
        orchestrator = AnalyticsOrchestrator(
            df=mock_data.df,
            source='test',
            enable_cache=False
        )
        
        available = orchestrator.get_available_analyzers()
        
        assert len(available) >= 9
    
    def test_invalid_analyzer_raises(self, mock_data):
        """Test that invalid analyzer name raises error."""
        from backend.analyzers import AnalyticsOrchestrator
        
        orchestrator = AnalyticsOrchestrator(
            df=mock_data.df,
            source='test',
            enable_cache=False
        )
        
        with pytest.raises(ValueError):
            orchestrator.run('nonexistent')


class TestCacheManager:
    """Tests for CacheManager."""
    
    def test_cache_set_get(self, tmp_path):
        """Test cache set and get."""
        from backend.analyzers.cache import CacheManager
        
        cache = CacheManager(tmp_path, 'test')
        
        data = {'key': 'value', 'number': 42}
        cache.set('test_key', data)
        
        result = cache.get('test_key')
        
        assert result == data
    
    def test_cache_miss(self, tmp_path):
        """Test cache miss returns None."""
        from backend.analyzers.cache import CacheManager
        
        cache = CacheManager(tmp_path, 'test')
        
        result = cache.get('nonexistent_key')
        
        assert result is None
    
    def test_cache_invalidation(self, tmp_path):
        """Test cache invalidation."""
        from backend.analyzers.cache import CacheManager
        
        cache = CacheManager(tmp_path, 'test')
        
        cache.set('identity_v1', {'data': 'test'})
        cache.set('sentiment_v1', {'data': 'test2'})
        
        # Invalidate identity
        cache.invalidate('identity')
        
        assert cache.get('identity_v1') is None
        assert cache.get('sentiment_v1') is not None
