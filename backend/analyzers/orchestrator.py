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
        granularity: str = 'global',
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
            text_col, speaker_col, party_col, cluster_col, date_col: Column names
        """
        self.df = df
        self.embeddings = embeddings
        self.cluster_labels = cluster_labels or {}
        self.cluster_centroids = cluster_centroids
        self.source = source
        # 'global' | 'year' | 'month' - analyzers decide for themselves whether
        # they are meaningful at this granularity and sample size.
        self.granularity = granularity
        
        # Column names
        self.text_col = text_col
        self.speaker_col = speaker_col
        self.party_col = party_col
        self.cluster_col = cluster_col
        self.date_col = date_col
        
        # Load config
        self.config = load_config(config_path)

        # Populated by run_all() so callers can report on a partial run
        self.failures: dict[str, str] = {}
        self.skipped: dict[str, list[str]] = {}

        logger.info("Orchestrator initialized: %d speeches, source=%s", len(df), source)
    
    def _create_analyzer(self, analyzer_class: Type[BaseAnalyzer]) -> BaseAnalyzer:
        """Create an analyzer instance with shared data."""
        return analyzer_class(
            df=self.df,
            embeddings=self.embeddings,
            cluster_labels=self.cluster_labels,
            cluster_centroids=self.cluster_centroids,
            config=self.config,
            text_col=self.text_col,
            speaker_col=self.speaker_col,
            party_col=self.party_col,
            cluster_col=self.cluster_col,
            date_col=self.date_col,
        )
    
    def run(self, analyzer_name: str) -> dict:
        """
        Run a specific analyzer by name.

        Args:
            analyzer_name: Name of the analyzer (e.g., 'identity', 'sentiment')

        Returns:
            Analyzer results dict
        """
        analyzer_class = AnalyzerRegistry.get(analyzer_name)

        if analyzer_class is None:
            raise ValueError(f"Unknown analyzer: {analyzer_name}. Available: {AnalyzerRegistry.names()}")

        return self._create_analyzer(analyzer_class).compute()

    def run_all(self) -> dict:
        """
        Run all enabled analyzers.

        A failing analyzer is recorded rather than aborting the run - one broken
        metric should not cost the whole export - but the failure is also kept in
        `self.failures` so the caller can report it instead of shipping a payload
        with a silent hole in it.

        Returns:
            Dict mapping analyzer_name -> results
        """
        results = {}
        self.failures = {}
        enabled_analyzers = AnalyzerRegistry.get_enabled(self.config)

        logger.info("Running %d enabled analyzers...", len(enabled_analyzers))

        for analyzer_class in enabled_analyzers:
            name = analyzer_class.name

            missing = self._missing_dependencies(analyzer_class)
            if missing:
                logger.warning("Skipping %s: missing dependencies %s", name, missing)
                self.skipped[name] = missing
                continue

            allowed, reason = analyzer_class.supports(self.granularity, len(self.df))
            if not allowed:
                logger.debug("Skipping %s at %s: %s", name, self.granularity, reason)
                self.skipped[name] = [reason]
                continue

            logger.info("Running %s...", name)

            try:
                results[name] = self._create_analyzer(analyzer_class).compute()
            except Exception as e:
                logger.error("Error running %s: %s", name, e, exc_info=True)
                results[name] = {'error': str(e)}
                self.failures[name] = str(e)

        logger.info("Completed %d analyzers (%d failed)", len(results), len(self.failures))
        return results

    def _missing_dependencies(self, analyzer_class: Type[BaseAnalyzer]) -> list[str]:
        """Which declared dependencies this orchestrator cannot supply."""
        deps = analyzer_class.get_dependencies()
        available = {
            'embeddings': self.embeddings is not None,
            'cluster_centroids': self.cluster_centroids is not None,
            'cluster_labels': bool(self.cluster_labels),
        }
        return [dep for dep in deps if dep in available and not available[dep]]

    def get_available_analyzers(self) -> list[str]:
        """Get list of all registered analyzer names."""
        return AnalyzerRegistry.names()

    def get_enabled_analyzers(self) -> list[str]:
        """Get list of enabled analyzer names based on config."""
        return [a.name for a in AnalyzerRegistry.get_enabled(self.config)]


def run_analytics(
    df: pd.DataFrame,
    embeddings: np.ndarray,
    cluster_labels: dict,
    cluster_centroids: np.ndarray,
    source: str = 'default',
    config_path: Optional[Path] = None,
) -> dict:
    """Convenience function to run all enabled analytics."""
    orchestrator = AnalyticsOrchestrator(
        df=df,
        embeddings=embeddings,
        cluster_labels=cluster_labels,
        cluster_centroids=cluster_centroids,
        source=source,
        config_path=config_path,
    )
    
    return orchestrator.run_all()
