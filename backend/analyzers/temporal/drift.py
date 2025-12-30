"""
Semantic Drift - Measure how party positions shift over time.
"""

import logging

import numpy as np
import pandas as pd

from .utils import add_time_columns

logger = logging.getLogger(__name__)


def compute_semantic_drift(
    df: pd.DataFrame,
    embeddings: np.ndarray,
    party_col: str = 'group',
    date_col: str = 'date',
    periods: list = None
) -> dict:
    """
    Compute semantic drift - how party positions shift over time.
    
    Measures the Euclidean distance between party centroids at different time periods.
    
    Args:
        df: DataFrame with speeches
        embeddings: Speech embeddings
        party_col: Party column
        date_col: Date column
        periods: List of year values to compare. If None, uses all available years.
    
    Returns:
        {
            party: {
                'drifts': [{from_period, to_period, distance}, ...],
                'total_drift': float,
                'avg_drift_per_period': float
            },
            ...
        }
    """
    df = add_time_columns(df, date_col)
    
    # Filter valid data
    valid_df = df[df['_year'].notna()].copy()
    
    if valid_df.empty:
        logger.warning("No valid dates for semantic drift analysis")
        return {}
    
    # Get available periods (years)
    if periods is None:
        periods = sorted(valid_df['_year'].dropna().unique())
    
    if len(periods) < 2:
        logger.warning("Need at least 2 time periods for drift analysis")
        return {}
    
    result = {}
    
    for party in valid_df[party_col].unique():
        if party == 'Unknown Group':
            continue
        
        party_mask = valid_df[party_col] == party
        party_df = valid_df[party_mask]
        
        # Compute centroid per period
        period_centroids = {}
        for period in periods:
            period_mask = party_df['_year'] == period
            if period_mask.sum() < 5:  # Need minimum speeches
                continue
            
            period_indices = party_df[period_mask].index
            original_indices = [df.index.get_loc(idx) for idx in period_indices if idx in df.index]
            
            if original_indices:
                period_centroids[period] = np.mean(embeddings[original_indices], axis=0)
        
        if len(period_centroids) < 2:
            continue
        
        # Compute drifts between consecutive periods
        drifts = []
        sorted_periods = sorted(period_centroids.keys())
        
        for i in range(len(sorted_periods) - 1):
            p1, p2 = sorted_periods[i], sorted_periods[i + 1]
            c1, c2 = period_centroids[p1], period_centroids[p2]
            
            distance = float(np.linalg.norm(c2 - c1))
            
            drifts.append({
                'from_period': int(p1),
                'to_period': int(p2),
                'distance': round(distance, 4)
            })
        
        total_drift = sum(d['distance'] for d in drifts)
        
        result[party] = {
            'drifts': drifts,
            'total_drift': round(total_drift, 4),
            'avg_drift_per_period': round(total_drift / len(drifts), 4) if drifts else 0,
            'periods_analyzed': sorted_periods
        }
    
    logger.info("Computed semantic drift for %d parties", len(result))
    
    return result
