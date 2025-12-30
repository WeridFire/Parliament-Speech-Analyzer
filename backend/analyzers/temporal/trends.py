"""
Topic Trends - Compute topic distribution over time.
"""

import logging
from collections import defaultdict

import pandas as pd

from .utils import add_time_columns

logger = logging.getLogger(__name__)


def compute_topic_trends(
    df: pd.DataFrame,
    cluster_col: str = 'cluster',
    cluster_labels: dict = None,
    date_col: str = 'date',
    granularity: str = 'month',
    party_col: str = 'group',
    speaker_col: str = 'deputy'
) -> dict:
    """
    Compute topic distribution over time.
    
    Args:
        df: DataFrame with speeches
        cluster_col: Column with cluster assignments
        cluster_labels: Dict mapping cluster_id -> label
        date_col: Column with dates
        granularity: 'month' or 'week'
        party_col: Column with party info
        speaker_col: Column with speaker info
    
    Returns:
        {
            'global': {period: {cluster_id: count, ...}, ...},
            'by_party': {party: {period: {cluster_id: count, ...}, ...}, ...},
            'periods': [sorted list of periods],
            'cluster_labels': {cluster_id: label, ...}
        }
    """
    df = add_time_columns(df, date_col)
    period_col = '_month' if granularity == 'month' else '_week'
    
    result = {
        'global': defaultdict(lambda: defaultdict(int)),
        'by_party': defaultdict(lambda: defaultdict(lambda: defaultdict(int))),
        'periods': [],
        'cluster_labels': cluster_labels or {}
    }
    
    # Filter rows with valid dates
    valid_df = df[df[period_col].notna()]
    
    if valid_df.empty:
        logger.warning("No valid dates found for temporal analysis")
        return result
    
    # Global trends
    for _, row in valid_df.iterrows():
        period = row[period_col]
        cluster = int(row[cluster_col])
        party = row[party_col]
        
        result['global'][period][cluster] += 1
        
        if party != 'Unknown Group':
            result['by_party'][party][period][cluster] += 1
    
    # Get sorted periods
    result['periods'] = sorted(result['global'].keys())
    
    # Convert defaultdicts to regular dicts
    result['global'] = {k: dict(v) for k, v in result['global'].items()}
    result['by_party'] = {
        party: {period: dict(clusters) for period, clusters in periods.items()}
        for party, periods in result['by_party'].items()
    }
    
    logger.info("Computed topic trends for %d periods", len(result['periods']))
    
    return result
