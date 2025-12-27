"""
Political Analytics - Unified interface for all analysis modules.

This module provides a single entry point for computing all analytics:
- Identity metrics (fingerprint, generalism, keywords)
- Relationship metrics (affinity, cohesion, overlap)
- Temporal metrics (trends, drift, crisis)
- Qualitative metrics (sentiment, readability, polarization)
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd

from .identity import (
    compute_thematic_fingerprint,
    compute_generalism_index,
    compute_distinctive_keywords
)
from .relations import (
    compute_party_affinity_matrix,
    compute_party_cohesion,
    compute_thematic_overlap,
    find_closest_cross_party_pairs,
    compute_party_centroids
)
from .temporal import (
    compute_topic_trends,
    compute_semantic_drift,
    compute_crisis_index,
    find_topic_surfing,
    parse_date
)
from .sentiment import (
    compute_topic_sentiment,
    compute_readability_scores,
    compute_polarization_scores
)
from .transformer_sentiment import (
    compute_topic_sentiment_transformer,
    is_transformer_available
)

logger = logging.getLogger(__name__)


def filter_data_by_period(
    df: pd.DataFrame,
    embeddings: np.ndarray,
    year: int = None,
    month: str = None,
    date_col: str = 'date'
) -> tuple[pd.DataFrame, np.ndarray]:
    """
    Filter DataFrame and embeddings by time period.
    
    Args:
        df: DataFrame with speeches
        embeddings: Embeddings array (same length as df)
        year: Filter by year (e.g., 2024)
        month: Filter by month (e.g., "2024-12") - takes precedence over year
        date_col: Name of date column
    
    Returns:
        (filtered_df, filtered_embeddings)
    """
    if year is None and month is None:
        return df, embeddings
    
    # Parse dates and extract year/month
    df = df.copy()
    df['_parsed_date'] = df[date_col].apply(parse_date)
    df['_year'] = df['_parsed_date'].apply(lambda x: x.year if x else None)
    df['_month'] = df['_parsed_date'].apply(
        lambda x: f"{x.year}-{x.month:02d}" if x else None
    )
    
    # Build filter mask
    if month:  # Month filter includes year
        mask = df['_month'] == month
    elif year:
        mask = df['_year'] == year
    else:
        mask = pd.Series([True] * len(df), index=df.index)
    
    # Apply filter
    filtered_df = df[mask].reset_index(drop=True)
    filtered_embeddings = embeddings[mask.values]
    
    # Clean up temporary columns
    filtered_df = filtered_df.drop(columns=['_parsed_date', '_year', '_month'])
    
    logger.debug("Filtered to %d speeches for period year=%s month=%s", 
                 len(filtered_df), year, month)
    
    return filtered_df, filtered_embeddings


def convert_to_native_types(obj):
    """
    Recursively convert numpy types to native Python types for JSON serialization.
    
    Handles: numpy integers, floats, arrays, and dictionary keys.
    """
    if isinstance(obj, dict):
        # Convert both keys and values
        return {
            convert_to_native_types(k): convert_to_native_types(v) 
            for k, v in obj.items()
        }
    elif isinstance(obj, list):
        return [convert_to_native_types(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    else:
        return obj


class PoliticalAnalytics:
    """
    Unified interface for computing all political discourse analytics.
    
    Orchestrates all analyzer modules and provides caching of intermediate results.
    """
    
    def __init__(
        self,
        df: pd.DataFrame,
        embeddings: np.ndarray,
        cluster_labels: dict,
        text_col: str = 'cleaned_text',
        cluster_col: str = 'cluster',
        speaker_col: str = 'deputy',
        party_col: str = 'group',
        date_col: str = 'date',
        use_transformer_sentiment: bool = False
    ):
        """
        Initialize the analytics engine.
        
        Args:
            df: DataFrame with speeches (must include cluster assignments)
            embeddings: Speech embeddings array (N x D)
            cluster_labels: Dict mapping cluster_id -> label string
            text_col: Column name for cleaned text
            cluster_col: Column name for cluster assignments
            speaker_col: Column name for speaker names
            party_col: Column name for party names
            date_col: Column name for dates
        """
        self.df = df
        self.embeddings = embeddings
        self.cluster_labels = cluster_labels
        self.text_col = text_col
        self.cluster_col = cluster_col
        self.speaker_col = speaker_col
        self.party_col = party_col
        self.date_col = date_col
        self.use_transformer_sentiment = use_transformer_sentiment
        
        # Cache for computed results
        self._cache = {}
        
        # Pre-compute cluster centroids
        self._cluster_centroids = None
        
        logger.info("PoliticalAnalytics initialized with %d speeches, %d clusters",
                    len(df), len(cluster_labels))
    
    @property
    def cluster_centroids(self) -> np.ndarray:
        """Get or compute cluster centroids."""
        if self._cluster_centroids is None:
            n_clusters = len(self.cluster_labels)
            centroids = []
            
            for cluster_id in sorted(self.cluster_labels.keys()):
                mask = self.df[self.cluster_col] == cluster_id
                if mask.sum() > 0:
                    centroid = np.mean(self.embeddings[mask], axis=0)
                else:
                    centroid = np.zeros(self.embeddings.shape[1])
                centroids.append(centroid)
            
            self._cluster_centroids = np.array(centroids)
        
        return self._cluster_centroids
    
    def compute_identity_metrics(self) -> dict:
        """
        Compute identity analysis metrics.
        
        Returns:
            {
                'thematic_fingerprints': {...},
                'generalism_index': {...},
                'distinctive_keywords': {...}
            }
        """
        if 'identity' in self._cache:
            return self._cache['identity']
        
        logger.info("Computing identity metrics...")
        
        result = {
            'thematic_fingerprints': compute_thematic_fingerprint(
                self.df, 
                self.embeddings, 
                self.cluster_centroids,
                self.cluster_labels,
                self.speaker_col,
                self.party_col
            ),
            'generalism_index': compute_generalism_index(
                self.df,
                self.cluster_col,
                self.speaker_col,
                self.party_col
            ),
            'distinctive_keywords': compute_distinctive_keywords(
                self.df,
                self.party_col,
                self.text_col
            )
        }
        
        self._cache['identity'] = result
        logger.info("Identity metrics computed")
        
        return result
    
    def compute_relationship_metrics(self) -> dict:
        """
        Compute relationship analysis metrics.
        
        Returns:
            {
                'affinity_matrix': {...},
                'party_cohesion': {...},
                'thematic_overlap': {...},
                'cross_party_pairs': [...]
            }
        """
        if 'relations' in self._cache:
            return self._cache['relations']
        
        logger.info("Computing relationship metrics...")
        
        result = {
            'affinity_matrix': compute_party_affinity_matrix(
                self.df,
                self.embeddings,
                self.party_col
            ),
            'party_cohesion': compute_party_cohesion(
                self.df,
                self.embeddings,
                self.party_col
            ),
            'thematic_overlap': compute_thematic_overlap(
                self.df,
                self.cluster_col,
                self.cluster_labels,
                self.party_col
            ),
            'cross_party_pairs': find_closest_cross_party_pairs(
                self.df,
                self.embeddings,
                self.speaker_col,
                self.party_col
            )
        }
        
        self._cache['relations'] = result
        logger.info("Relationship metrics computed")
        
        return result
    
    def compute_temporal_metrics(self, granularity: str = 'month') -> dict:
        """
        Compute temporal analysis metrics.
        
        Args:
            granularity: 'month' or 'week'
        
        Returns:
            {
                'topic_trends': {...},
                'semantic_drift': {...},
                'crisis_index': {...},
                'topic_surfing': {...}
            }
        """
        cache_key = f'temporal_{granularity}'
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        logger.info("Computing temporal metrics (granularity=%s)...", granularity)
        
        result = {
            'topic_trends': compute_topic_trends(
                self.df,
                self.cluster_col,
                self.cluster_labels,
                self.date_col,
                granularity,
                self.party_col,
                self.speaker_col
            ),
            'semantic_drift': compute_semantic_drift(
                self.df,
                self.embeddings,
                self.party_col,
                self.date_col
            ),
            'crisis_index': compute_crisis_index(
                self.df,
                self.text_col,
                self.cluster_col,
                self.cluster_labels,
                self.date_col,
                granularity
            ),
            'topic_surfing': find_topic_surfing(
                self.df,
                self.cluster_col,
                self.cluster_labels,
                self.date_col,
                self.speaker_col
            )
        }
        
        self._cache[cache_key] = result
        logger.info("Temporal metrics computed")
        
        return result
    
    def compute_qualitative_metrics(self) -> dict:
        """
        Compute qualitative analysis metrics.
        
        Returns:
            {
                'topic_sentiment': {...},
                'readability': {...},
                'polarization': {...}
            }
        """
        if 'qualitative' in self._cache:
            return self._cache['qualitative']
        
        logger.info("Computing qualitative metrics...")
        
        # Use transformer sentiment if enabled and available
        if self.use_transformer_sentiment:
            if is_transformer_available():
                topic_sentiment = compute_topic_sentiment_transformer(
                    self.df,
                    self.text_col,
                    self.cluster_col,
                    self.cluster_labels,
                    self.speaker_col,
                    self.party_col
                )
            else:
                logger.warning("Transformer not available, falling back to keyword-based")
                topic_sentiment = compute_topic_sentiment(
                    self.df,
                    self.text_col,
                    self.cluster_col,
                    self.cluster_labels,
                    self.speaker_col,
                    self.party_col
                )
        else:
            topic_sentiment = compute_topic_sentiment(
                self.df,
                self.text_col,
                self.cluster_col,
                self.cluster_labels,
                self.speaker_col,
                self.party_col
            )
        
        result = {
            'topic_sentiment': topic_sentiment,
            'readability': compute_readability_scores(
                self.df,
                self.text_col,
                self.speaker_col,
                self.party_col
            ),
            'polarization': compute_polarization_scores(
                self.df,
                self.text_col,
                self.speaker_col,
                self.party_col
            )
        }
        
        self._cache['qualitative'] = result
        logger.info("Qualitative metrics computed")
        
        return result
    
    def get_all_metrics(self, granularity: str = 'month') -> dict:
        """
        Compute and return all analytics metrics.
        
        Returns:
            {
                'identity': {...},
                'relations': {...},
                'temporal': {...},
                'qualitative': {...}
            }
        """
        logger.info("Computing all analytics metrics...")
        
        result = {
            'identity': self.compute_identity_metrics(),
            'relations': self.compute_relationship_metrics(),
            'temporal': self.compute_temporal_metrics(granularity),
            'qualitative': self.compute_qualitative_metrics()
        }
        
        # Convert all numpy types to native Python types for JSON serialization
        return convert_to_native_types(result)
    
    def _extract_available_periods(self) -> dict:
        """Extract unique years and months from data."""
        df = self.df.copy()
        df['_parsed_date'] = df[self.date_col].apply(parse_date)
        df['_year'] = df['_parsed_date'].apply(lambda x: x.year if x else None)
        df['_month'] = df['_parsed_date'].apply(
            lambda x: f"{x.year}-{x.month:02d}" if x else None
        )
        
        years = sorted([int(y) for y in df['_year'].dropna().unique()])
        months = sorted([m for m in df['_month'].dropna().unique()], reverse=True)
        
        return {'years': years, 'months': months}
    
    def compute_metrics_for_period(
        self,
        year: int = None,
        month: str = None,
        min_speeches: int = 10
    ) -> dict | None:
        """
        Compute identity + relations + qualitative metrics for a specific period.
        
        Args:
            year: Filter by year (e.g., 2024)
            month: Filter by month (e.g., "2024-12") - takes precedence over year
            min_speeches: Minimum speeches required for valid analysis
        
        Returns:
            Dict with identity/relations/qualitative, or None if insufficient data
        """
        # Filter data
        filtered_df, filtered_embeddings = filter_data_by_period(
            self.df, self.embeddings, year=year, month=month, date_col=self.date_col
        )
        
        if len(filtered_df) < min_speeches:
            logger.debug("Skipping period year=%s month=%s: only %d speeches", 
                         year, month, len(filtered_df))
            return None
        
        # Check we have enough parties for meaningful analysis
        n_parties = filtered_df[self.party_col].nunique()
        if n_parties < 2:
            logger.debug("Skipping period year=%s month=%s: only %d parties", 
                         year, month, n_parties)
            return None
        
        # Create temporary analytics instance for filtered data
        period_analytics = PoliticalAnalytics(
            df=filtered_df,
            embeddings=filtered_embeddings,
            cluster_labels=self.cluster_labels,
            text_col=self.text_col,
            cluster_col=self.cluster_col,
            speaker_col=self.speaker_col,
            party_col=self.party_col,
            date_col=self.date_col
        )
        
        # Compute metrics (skip temporal - it already has time granularity)
        result = {
            'identity': period_analytics.compute_identity_metrics(),
            'relations': period_analytics.compute_relationship_metrics(),
            'qualitative': period_analytics.compute_qualitative_metrics()
        }
        
        # Add period metadata
        result['_meta'] = {
            'n_speeches': len(filtered_df),
            'n_deputies': filtered_df[self.speaker_col].nunique(),
            'n_parties': n_parties
        }
        
        return result
    
    def get_all_metrics_by_period(self, granularity: str = 'month') -> dict:
        """
        Compute all analytics with yearly and monthly breakdowns.
        
        Returns:
            {
                'global': {identity, relations, temporal, qualitative},
                'by_year': {2024: {...}, 2023: {...}, ...},
                'by_month': {'2024-12': {...}, ...},
                'available_periods': {years: [...], months: [...]}
            }
        """
        logger.info("Computing all analytics with period breakdowns...")
        
        # 1. Global metrics (current behavior)
        global_metrics = {
            'identity': self.compute_identity_metrics(),
            'relations': self.compute_relationship_metrics(),
            'temporal': self.compute_temporal_metrics(granularity),
            'qualitative': self.compute_qualitative_metrics()
        }
        
        # 2. Extract available periods
        available_periods = self._extract_available_periods()
        
        # 3. Compute per-year metrics
        by_year = {}
        for year in available_periods['years']:
            year_metrics = self.compute_metrics_for_period(year=year)
            if year_metrics:
                by_year[str(year)] = year_metrics
        
        logger.info("Computed metrics for %d years", len(by_year))
        
        # 4. Compute per-month metrics
        by_month = {}
        for month in available_periods['months']:
            month_metrics = self.compute_metrics_for_period(month=month)
            if month_metrics:
                by_month[month] = month_metrics
        
        logger.info("Computed metrics for %d months", len(by_month))
        
        # 5. Update available_periods to only include periods with data
        available_periods['years'] = [int(y) for y in by_year.keys()]
        available_periods['months'] = list(by_month.keys())
        
        result = {
            'global': global_metrics,
            'by_year': by_year,
            'by_month': by_month,
            'available_periods': available_periods
        }
        
        return convert_to_native_types(result)
    
    def clear_cache(self):
        """Clear cached results."""
        self._cache = {}
        self._cluster_centroids = None
        logger.info("Analytics cache cleared")
