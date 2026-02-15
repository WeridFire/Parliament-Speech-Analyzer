"""
Period Orchestrator - Compute analytics for each time period.

Wraps AnalyticsOrchestrator to generate per-year and per-month analytics.
This enables the frontend period selector to show period-specific data.
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd

from .orchestrator import AnalyticsOrchestrator
from .temporal import parse_date

logger = logging.getLogger(__name__)

# Minimum speeches required per period
MIN_SPEECHES_YEAR = 10
MIN_SPEECHES_MONTH = 5


def compute_analytics_by_period(
    df: pd.DataFrame,
    embeddings: np.ndarray,
    cluster_labels: dict,
    cluster_centroids: np.ndarray,
    source: str = 'default',
    date_col: str = 'date',
    enable_cache: bool = False,
    compute_by_period: bool = True,
) -> dict:
    """
    Compute analytics for global, by_year, and by_month periods.
    
    Args:
        df: DataFrame with speeches
        embeddings: Embeddings array aligned with df
        cluster_labels: Dict mapping cluster_id -> label
        cluster_centroids: Cluster centroid vectors
        source: Data source name
        date_col: Column containing dates
        enable_cache: Whether to use caching
        compute_by_period: If False, only compute global analytics (faster)
        
    Returns:
        {
            'global': {...all analytics...},
            'by_year': {'2024': {...}, '2023': {...}},
            'by_month': {'2024-12': {...}, '2024-11': {...}}
        }
    """
    logger.info("Computing analytics by period...")
    
    # Parse dates
    df = df.copy()
    df['_parsed_date'] = df[date_col].apply(parse_date)
    df['_year'] = df['_parsed_date'].apply(lambda x: x.year if x else None)
    df['_month'] = df['_parsed_date'].apply(
        lambda x: f"{x.year}-{x.month:02d}" if x else None
    )
    
    # Helper to run orchestrator on a subset
    def run_for_subset(subset_df: pd.DataFrame, subset_embeddings: np.ndarray) -> dict:
        orchestrator = AnalyticsOrchestrator(
            df=subset_df,
            embeddings=subset_embeddings,
            cluster_labels=cluster_labels,
            cluster_centroids=cluster_centroids,
            source=source,
            enable_cache=enable_cache,
        )
        return orchestrator.run_all(use_cache=enable_cache)
    
    # Global analytics
    logger.info("Computing global analytics...")
    global_analytics = run_for_subset(df, embeddings)
    
    # Early return if period computation is disabled
    if not compute_by_period:
        logger.info("Period computation disabled, returning global-only analytics")
        return {
            'global': global_analytics,
            'by_year': {},
            'by_month': {},
        }
    
    # Per-year analytics
    by_year = {}
    years = sorted([int(y) for y in df['_year'].dropna().unique()])
    
    for year in years:
        mask = df['_year'] == year
        year_df = df[mask].reset_index(drop=True)
        
        if len(year_df) >= MIN_SPEECHES_YEAR:
            logger.info(f"Computing analytics for year {year} ({len(year_df)} speeches)...")
            year_indices = df[mask].index.tolist()
            year_embeddings = embeddings[year_indices] if embeddings is not None else None
            
            try:
                by_year[str(year)] = run_for_subset(year_df, year_embeddings)
            except Exception as e:
                logger.warning(f"Failed to compute analytics for year {year}: {e}")
    
    logger.info(f"Computed analytics for {len(by_year)} years")
    
    # Per-month analytics
    by_month = {}
    months = sorted([m for m in df['_month'].dropna().unique()], reverse=True)
    
    for month in months:
        mask = df['_month'] == month
        month_df = df[mask].reset_index(drop=True)
        
        if len(month_df) >= MIN_SPEECHES_MONTH:
            logger.info(f"Computing analytics for month {month} ({len(month_df)} speeches)...")
            month_indices = df[mask].index.tolist()
            month_embeddings = embeddings[month_indices] if embeddings is not None else None
            
            try:
                by_month[month] = run_for_subset(month_df, month_embeddings)
            except Exception as e:
                logger.warning(f"Failed to compute analytics for month {month}: {e}")
    
    logger.info(f"Computed analytics for {len(by_month)} months")
    
    return {
        'global': global_analytics,
        'by_year': by_year,
        'by_month': by_month,
    }
