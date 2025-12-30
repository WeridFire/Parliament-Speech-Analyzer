"""
Crisis Index - Track alarm term frequency over time.
"""

import logging
from collections import defaultdict

import pandas as pd

from backend.config import CRISIS_KEYWORDS
from .utils import add_time_columns

logger = logging.getLogger(__name__)


def compute_crisis_index(
    df: pd.DataFrame,
    text_col: str = 'cleaned_text',
    cluster_col: str = 'cluster',
    cluster_labels: dict = None,
    date_col: str = 'date',
    granularity: str = 'month'
) -> dict:
    """
    Compute crisis/alarm term frequency over time.
    
    Args:
        df: DataFrame with speeches
        text_col: Column with text
        cluster_col: Column with cluster assignments
        cluster_labels: Dict mapping cluster_id -> label
        date_col: Column with dates
        granularity: 'month' or 'week'
    
    Returns:
        {
            'global': {period: {crisis_count, total_words, crisis_rate}, ...},
            'by_cluster': {cluster_id: {period: {crisis_count, rate}, ...}, ...},
            'crisis_keywords': list,
            'periods': sorted period list
        }
    """
    df = add_time_columns(df, date_col)
    period_col = '_month' if granularity == 'month' else '_week'
    
    crisis_words = {w.lower() for w in CRISIS_KEYWORDS}
    
    result = {
        'global': defaultdict(lambda: {'crisis_count': 0, 'total_words': 0}),
        'by_cluster': defaultdict(lambda: defaultdict(lambda: {'crisis_count': 0, 'total_speeches': 0})),
        'crisis_keywords': list(CRISIS_KEYWORDS),
        'periods': []
    }
    
    valid_df = df[df[period_col].notna()]
    
    for _, row in valid_df.iterrows():
        period = row[period_col]
        text = str(row[text_col]).lower()
        cluster = int(row[cluster_col])
        
        words = text.split()
        crisis_count = sum(1 for w in words if w in crisis_words)
        total_words = len(words)
        
        result['global'][period]['crisis_count'] += crisis_count
        result['global'][period]['total_words'] += total_words
        
        result['by_cluster'][cluster][period]['crisis_count'] += crisis_count
        result['by_cluster'][cluster][period]['total_speeches'] += 1
    
    # Compute rates
    result['periods'] = sorted(result['global'].keys())
    
    for period, data in result['global'].items():
        if data['total_words'] > 0:
            data['crisis_rate'] = round((data['crisis_count'] / data['total_words']) * 1000, 2)
        else:
            data['crisis_rate'] = 0
    
    # Convert to regular dicts
    result['global'] = dict(result['global'])
    result['by_cluster'] = {
        int(k): {
            period: {
                'crisis_count': v['crisis_count'],
                'crisis_rate': round(v['crisis_count'] / max(v['total_speeches'], 1), 2)
            }
            for period, v in periods.items()
        }
        for k, periods in result['by_cluster'].items()
    }
    
    logger.info("Computed crisis index for %d periods", len(result['periods']))
    
    return result
