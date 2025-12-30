"""
Orchestrator - Unified interface for running all analyzers.

Replaces the old monolithic analytics.py with a clean registry-based approach.
"""

import logging
from pathlib import Path
from typing import Optional, Type

import numpy as np
import pandas as pd

from .base import BaseAnalyzer
from .registry import AnalyzerRegistry
from .cache import CacheManager
from .config_loader import load_config

logger = logging.getLogger(__name__)


class AnalyticsOrchestrator:
    """
    Unified interface for computing all political discourse analytics.
    
    Uses the registry pattern to discover and run all enabled analyzers.
    
    Usage:
        orchestrator = AnalyticsOrchestrator(
            df=speeches_df,
            embeddings=embeddings,
            cluster_labels=labels,
            cluster_centroids=centroids,
            source='camera'
        )
        
        # Run all enabled analyzers
        results = orchestrator.run_all()
        
        # Or run specific analyzer
        identity_results = orchestrator.run('identity')
    """
    
    def __init__(
        self,
        df: pd.DataFrame,
        embeddings: Optional[np.ndarray] = None,
        cluster_labels: Optional[dict] = None,
        cluster_centroids: Optional[np.ndarray] = None,
        source: str = 'default',
        config_path: Optional[Path] = None,
        cache_dir: Optional[Path] = None,
        enable_cache: bool = True,
        # Column names
        text_col: str = 'cleaned_text',
        speaker_col: str = 'deputy',
        party_col: str = 'group',
        cluster_col: str = 'cluster',
        date_col: str = 'date',
    ):
        """
        Initialize orchestrator.
        
        Args:
            df: DataFrame with speeches
            embeddings: Speech embeddings array
            cluster_labels: Dict mapping cluster_id -> label
            cluster_centroids: Array of cluster centroid vectors
            source: Data source name (e.g., 'camera', 'senato')
            config_path: Path to config.yaml
            cache_dir: Base directory for cache files
            enable_cache: Whether to use caching
            text_col, speaker_col, party_col, cluster_col, date_col: Column names
        """
        self.df = df
        self.embeddings = embeddings
        self.cluster_labels = cluster_labels or {}
        self.cluster_centroids = cluster_centroids
        self.source = source
        
        # Column names
        self.text_col = text_col
        self.speaker_col = speaker_col
        self.party_col = party_col
        self.cluster_col = cluster_col
        self.date_col = date_col
        
        # Load config
        self.config = load_config(config_path)
        
        # Setup cache
        if enable_cache and cache_dir:
            self.cache = CacheManager(cache_dir, source)
        else:
            self.cache = None
        
        logger.info(
            "Orchestrator initialized: %d speeches, source=%s, cache=%s",
            len(df), source, 'enabled' if self.cache else 'disabled'
        )
    
    def _create_analyzer(self, analyzer_class: Type[BaseAnalyzer]) -> BaseAnalyzer:
        """Create an analyzer instance with shared data."""
        return analyzer_class(
            df=self.df,
            embeddings=self.embeddings,
            cluster_labels=self.cluster_labels,
            cluster_centroids=self.cluster_centroids,
            cache_manager=self.cache,
            config=self.config,
            text_col=self.text_col,
            speaker_col=self.speaker_col,
            party_col=self.party_col,
            cluster_col=self.cluster_col,
            date_col=self.date_col,
        )
    
    def run(self, analyzer_name: str, use_cache: bool = True) -> dict:
        """
        Run a specific analyzer by name.
        
        Args:
            analyzer_name: Name of the analyzer (e.g., 'identity', 'sentiment')
            use_cache: Whether to use cached results
            
        Returns:
            Analyzer results dict
        """
        analyzer_class = AnalyzerRegistry.get(analyzer_name)
        
        if analyzer_class is None:
            raise ValueError(f"Unknown analyzer: {analyzer_name}. Available: {AnalyzerRegistry.names()}")
        
        analyzer = self._create_analyzer(analyzer_class)
        
        if use_cache:
            return analyzer.compute_cached()
        else:
            return analyzer.compute()
    
    def run_all(self, use_cache: bool = True) -> dict:
        """
        Run all enabled analyzers.
        
        Args:
            use_cache: Whether to use cached results
            
        Returns:
            Dict mapping analyzer_name -> results
        """
        results = {}
        enabled_analyzers = AnalyzerRegistry.get_enabled(self.config)
        
        logger.info("Running %d enabled analyzers...", len(enabled_analyzers))
        
        for analyzer_class in enabled_analyzers:
            name = analyzer_class.name
            
            try:
                # Check dependencies
                deps = analyzer_class.get_dependencies()
                missing = []
                
                if 'embeddings' in deps and self.embeddings is None:
                    missing.append('embeddings')
                if 'cluster_centroids' in deps and self.cluster_centroids is None:
                    missing.append('cluster_centroids')
                
                if missing:
                    logger.warning(
                        "Skipping %s: missing dependencies %s",
                        name, missing
                    )
                    continue
                
                logger.info("Running %s...", name)
                
                analyzer = self._create_analyzer(analyzer_class)
                
                if use_cache:
                    results[name] = analyzer.compute_cached()
                else:
                    results[name] = analyzer.compute()
                    
            except Exception as e:
                logger.error("Error running %s: %s", name, e, exc_info=True)
                results[name] = {'error': str(e)}
        
        logger.info("Completed %d analyzers", len(results))
        return results
    
    def get_available_analyzers(self) -> list[str]:
        """Get list of all registered analyzer names."""
        return AnalyzerRegistry.names()
    
    def get_enabled_analyzers(self) -> list[str]:
        """Get list of enabled analyzer names based on config."""
        return [a.name for a in AnalyzerRegistry.get_enabled(self.config)]
    
    def invalidate_cache(self, analyzer_name: str = None):
        """
        Invalidate cache for an analyzer or all analyzers.
        
        Args:
            analyzer_name: If None, invalidates all. Otherwise just the specified analyzer.
        """
        if self.cache:
            self.cache.invalidate(analyzer_name)


def run_analytics(
    df: pd.DataFrame,
    embeddings: np.ndarray,
    cluster_labels: dict,
    cluster_centroids: np.ndarray,
    source: str = 'default',
    config_path: Optional[Path] = None,
    cache_dir: Optional[Path] = None,
) -> dict:
    """
    Convenience function to run all enabled analytics.
    
    This is a drop-in replacement for the old analytics.py approach.
    """
    orchestrator = AnalyticsOrchestrator(
        df=df,
        embeddings=embeddings,
        cluster_labels=cluster_labels,
        cluster_centroids=cluster_centroids,
        source=source,
        config_path=config_path,
        cache_dir=cache_dir,
    )
    
    return orchestrator.run_all()
