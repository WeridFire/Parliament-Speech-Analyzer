"""
Intervention Patterns - Activity level and regularity over time.
"""
import logging
from collections import Counter

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def _parse_month(date_str) -> str:
    """Parse date string to YYYY-MM format."""
    if pd.isna(date_str):
        return None
    
    try:
        from datetime import datetime
        
        # Try common formats
        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']:
            try:
                dt = datetime.strptime(str(date_str).strip(), fmt)
                return f"{dt.year}-{dt.month:02d}"
            except ValueError:
                continue
    except Exception:
        pass
    
    return None


def compute_intervention_patterns(
    df: pd.DataFrame,
    speaker_col: str = 'deputy',
    date_col: str = 'date'
) -> dict:
    """
    Analyze intervention patterns over time for each speaker.
    
    Returns:
    - avg_speeches_per_month: activity level
    - regularity_score: 0-100 (100 = very regular)
    - active_months: number of months with at least one speech
    - burst_score: tendency to cluster speeches (0-100)
    """
    # Parse dates and group by month
    df = df.copy()
    df['_month'] = df[date_col].apply(_parse_month)
    
    valid_df = df[df['_month'].notna()]
    
    if valid_df.empty:
        logger.warning("No valid dates for intervention pattern analysis")
        return {}
    
    all_months = sorted(valid_df['_month'].unique())
    n_total_months = len(all_months)
    
    result = {}
    
    for speaker in valid_df[speaker_col].unique():
        speaker_df = valid_df[valid_df[speaker_col] == speaker]
        n_speeches = len(speaker_df)
        
        if n_speeches < 3:
            continue
        
        # Monthly counts
        monthly_counts = Counter(speaker_df['_month'].tolist())
        active_months = len(monthly_counts)
        
        # Activity level
        avg_per_month = n_speeches / active_months if active_months > 0 else 0
        
        # Regularity: how evenly spread across months
        counts = list(monthly_counts.values())
        if len(counts) > 1 and np.mean(counts) > 0:
            cv = np.std(counts) / np.mean(counts)  # Coefficient of variation
            regularity = max(0, min(100, (1 - cv) * 100))
        else:
            regularity = 50
        
        # Burst score: concentration in few months
        total = sum(counts)
        if total > 0 and len(counts) > 1:
            max_month = max(counts)
            burst = (max_month / total) * 100
        else:
            burst = 100
        
        result[speaker] = {
            'avg_speeches_per_month': round(avg_per_month, 2),
            'regularity_score': round(regularity, 1),
            'active_months': active_months,
            'total_months': n_total_months,
            'activity_ratio': round(active_months / n_total_months * 100, 1) if n_total_months > 0 else 0,
            'burst_score': round(burst, 1),
            'n_speeches': n_speeches
        }
    
    logger.info("Computed intervention patterns for %d speakers", len(result))
    return result
