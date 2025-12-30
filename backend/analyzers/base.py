"""
Base Analyzer - Abstract base class for all analyzers.

All analyzers in this package inherit from BaseAnalyzer which provides:
- Standard interface (compute, get_dependencies)
- Configuration management (enable/disable features)
- Caching integration
- Shared data injection (df, embeddings, etc.)
"""

from abc import ABC, abstractmethod
from typing import Optional, Any, TYPE_CHECKING
import logging

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from .cache import CacheManager

logger = logging.getLogger(__name__)


class BaseAnalyzer(ABC):
    """
    Abstract base class for all analyzers.
    
    Each analyzer must implement:
    - name: unique identifier (class attribute)
    - compute(): main computation logic
    
    Optional overrides:
    - get_dependencies(): list of required data
    - features: dict of sub-feature flags
    """
    
    # Class attributes - override in subclasses
    name: str = "base"
    description: str = "Base analyzer"
    version: str = "1.0"
    
    # Feature flags for sub-metrics (override in subclasses)
    # Format: {'feature_name': default_enabled}
    default_features: dict[str, bool] = {}
    
    def __init__(
        self,
        df: pd.DataFrame,
        embeddings: Optional[np.ndarray] = None,
        cluster_labels: Optional[dict] = None,
        cluster_centroids: Optional[np.ndarray] = None,
        cache_manager: Optional["CacheManager"] = None,
        config: Optional[dict] = None,
        # Common column names
        text_col: str = 'cleaned_text',
        speaker_col: str = 'deputy',
        party_col: str = 'group',
        cluster_col: str = 'cluster',
        date_col: str = 'date',
    ):
        """
        Initialize analyzer with data and configuration.
        
        Args:
            df: DataFrame with speeches
            embeddings: Speech embeddings array (N x D)
            cluster_labels: Dict mapping cluster_id -> label string
            cluster_centroids: Array of cluster centroid vectors
            cache_manager: Optional cache manager for persistence
            config: Optional configuration dict (from YAML)
            text_col: Column name for cleaned text
            speaker_col: Column name for speaker names
            party_col: Column name for party names
            cluster_col: Column name for cluster assignments
            date_col: Column name for dates
        """
        self.df = df
        self.embeddings = embeddings
        self.cluster_labels = cluster_labels or {}
        self.cluster_centroids = cluster_centroids
        self.cache = cache_manager
        self.config = config or {}
        
        # Column names
        self.text_col = text_col
        self.speaker_col = speaker_col
        self.party_col = party_col
        self.cluster_col = cluster_col
        self.date_col = date_col
        
        # Initialize features from defaults
        self.features = self.default_features.copy()
        
        # Apply config overrides
        self._apply_config()
        
        logger.debug(
            "%s initialized: %d speeches, features=%s",
            self.name, len(df), self.features
        )
    
    def _apply_config(self):
        """Apply configuration to enable/disable features."""
        analyzer_config = self.config.get(self.name, {})
        
        # Override features from config
        feature_config = analyzer_config.get('features', {})
        for feature, enabled in feature_config.items():
            if feature in self.features:
                self.features[feature] = enabled
                logger.debug(
                    "%s: feature '%s' set to %s from config",
                    self.name, feature, enabled
                )
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a specific feature is enabled."""
        return self.features.get(feature, False)
    
    @abstractmethod
    def compute(self) -> dict:
        """
        Main computation method. Must be implemented by subclasses.
        
        Returns:
            Dict with analyzer results, structure depends on analyzer type.
        """
        pass
    
    def compute_cached(self, cache_key: str = None) -> dict:
        """
        Compute with caching support.
        
        Args:
            cache_key: Optional custom cache key. If None, uses name_version.
            
        Returns:
            Cached or freshly computed results.
        """
        key = cache_key or f"{self.name}_v{self.version}"
        
        # Check cache
        if self.cache and self.cache.has(key):
            logger.info("%s: loading from cache (key=%s)", self.name, key)
            return self.cache.get(key)
        
        # Compute
        logger.info("%s: computing...", self.name)
        result = self.compute()
        
        # Store in cache
        if self.cache:
            self.cache.set(key, result)
            logger.debug("%s: cached result (key=%s)", self.name, key)
        
        return result
    
    @classmethod
    def get_dependencies(cls) -> list[str]:
        """
        Return list of required data for this analyzer.
        
        Possible values: 'embeddings', 'cluster_labels', 'cluster_centroids'
        
        Returns:
            List of dependency names.
        """
        return []
    
    @classmethod
    def is_enabled(cls, config: dict) -> bool:
        """
        Check if this analyzer is enabled in config.
        
        Args:
            config: Configuration dict.
            
        Returns:
            True if enabled (default), False if explicitly disabled.
        """
        analyzer_config = config.get(cls.name, {})
        return analyzer_config.get('enabled', True)
    
    def validate_dependencies(self) -> bool:
        """
        Check if all required dependencies are available.
        
        Returns:
            True if all dependencies are met.
            
        Raises:
            ValueError if a required dependency is missing.
        """
        deps = self.get_dependencies()
        
        for dep in deps:
            if dep == 'embeddings' and self.embeddings is None:
                raise ValueError(f"{self.name} requires embeddings but none provided")
            elif dep == 'cluster_labels' and not self.cluster_labels:
                raise ValueError(f"{self.name} requires cluster_labels but none provided")
            elif dep == 'cluster_centroids' and self.cluster_centroids is None:
                raise ValueError(f"{self.name} requires cluster_centroids but none provided")
        
        return True
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.name}' v{self.version}>"
