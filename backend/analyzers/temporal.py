"""
Temporal Analyzer - Analyze how political discourse evolves over time.

This module provides:
- Topic Trends (temporal distribution of themes)
- Semantic Drift (how party positions shift)
- Crisis Index (frequency of alarm terms over time)
"""

import logging
import re
from collections import defaultdict
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd

from backend.config import CRISIS_KEYWORDS

logger = logging.getLogger(__name__)


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse date string in various formats."""
    if pd.isna(date_str):
        return None
    
    formats = [
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%d-%m-%Y',
        '%Y/%m/%d',
        '%d %B %Y',  # Italian format
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(str(date_str).strip(), fmt)
        except ValueError:
            continue
    
    # Try extracting date from string
    match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', str(date_str))
    if match:
        try:
            day, month, year = match.groups()
            return datetime(int(year), int(month), int(day))
        except ValueError:
            pass
    
    return None


def add_time_columns(df: pd.DataFrame, date_col: str = 'date') -> pd.DataFrame:
    """Add parsed date and time period columns to DataFrame."""
    df = df.copy()
    
    # Parse dates
    df['parsed_date'] = df[date_col].apply(parse_date)
    
    # Add period columns
    df['year'] = df['parsed_date'].apply(lambda x: x.year if x else None)
    df['month'] = df['parsed_date'].apply(lambda x: f"{x.year}-{x.month:02d}" if x else None)
    df['week'] = df['parsed_date'].apply(lambda x: f"{x.year}-W{x.isocalendar()[1]:02d}" if x else None)
    
    return df


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
    period_col = 'month' if granularity == 'month' else 'week'
    
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
    
    # Convert defaultdicts to regular dicts for JSON serialization
    result['global'] = {k: dict(v) for k, v in result['global'].items()}
    result['by_party'] = {
        party: {period: dict(clusters) for period, clusters in periods.items()}
        for party, periods in result['by_party'].items()
    }
    
    logger.info("Computed topic trends for %d periods", len(result['periods']))
    
    return result


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
        periods: List of year values to compare, e.g. [2023, 2024]. If None, uses all available years.
    
    Returns:
        {
            party: {
                'drifts': [{from_period, to_period, distance, direction}, ...],
                'total_drift': float,
                'avg_drift_per_period': float
            },
            ...
        }
    """
    df = add_time_columns(df, date_col)
    
    # Filter valid data
    valid_df = df[df['year'].notna()].copy()
    
    if valid_df.empty:
        logger.warning("No valid dates for semantic drift analysis")
        return {}
    
    # Get available periods (years)
    if periods is None:
        periods = sorted(valid_df['year'].dropna().unique())
    
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
            period_mask = party_df['year'] == period
            if period_mask.sum() < 5:  # Need minimum speeches
                continue
            
            period_indices = party_df[period_mask].index
            # Map to original embedding indices
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
            
            # Direction: which cluster did they move towards?
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
    
    logger.info("Computed semantic drift for %d parties across %d periods", len(result), len(periods))
    
    return result


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
    
    Tracks daily/weekly/monthly frequency of crisis-related terms,
    broken down by topic cluster.
    
    Returns:
        {
            'global': {period: {crisis_count, total_words, crisis_rate}, ...},
            'by_cluster': {cluster_id: {period: {crisis_count, rate}, ...}, ...},
            'by_party': {party: {period: crisis_rate, ...}, ...},
            'crisis_keywords': list of keywords used,
            'periods': sorted period list
        }
    """
    df = add_time_columns(df, date_col)
    period_col = 'month' if granularity == 'month' else 'week'
    
    crisis_words = {w.lower() for w in CRISIS_KEYWORDS}
    
    result = {
        'global': defaultdict(lambda: {'crisis_count': 0, 'total_words': 0}),
        'by_cluster': defaultdict(lambda: defaultdict(lambda: {'crisis_count': 0, 'total_speeches': 0})),
        'by_party': defaultdict(lambda: defaultdict(lambda: {'crisis_count': 0, 'total_words': 0})),
        'crisis_keywords': list(CRISIS_KEYWORDS),
        'periods': []
    }
    
    valid_df = df[df[period_col].notna()]
    
    for _, row in valid_df.iterrows():
        period = row[period_col]
        text = str(row[text_col]).lower()
        cluster = int(row[cluster_col])
        party = row.get('group', 'Unknown')
        
        # Tokenize and count crisis words
        words = text.split()
        crisis_count = sum(1 for w in words if w in crisis_words)
        total_words = len(words)
        
        # Global
        result['global'][period]['crisis_count'] += crisis_count
        result['global'][period]['total_words'] += total_words
        
        # By cluster
        result['by_cluster'][cluster][period]['crisis_count'] += crisis_count
        result['by_cluster'][cluster][period]['total_speeches'] += 1
        
        # By party
        if party != 'Unknown Group':
            result['by_party'][party][period]['crisis_count'] += crisis_count
            result['by_party'][party][period]['total_words'] += total_words
    
    # Compute rates
    result['periods'] = sorted(result['global'].keys())
    
    # Add rates to global
    for period, data in result['global'].items():
        if data['total_words'] > 0:
            data['crisis_rate'] = round((data['crisis_count'] / data['total_words']) * 1000, 2)  # per 1000 words
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
    result['by_party'] = {
        party: {
            period: round((data['crisis_count'] / max(data['total_words'], 1)) * 1000, 2)
            for period, data in periods.items()
        }
        for party, periods in result['by_party'].items()
    }
    
    logger.info("Computed crisis index for %d periods", len(result['periods']))
    
    return result


def find_topic_surfing(
    df: pd.DataFrame,
    cluster_col: str = 'cluster',
    cluster_labels: dict = None,
    date_col: str = 'date',
    speaker_col: str = 'deputy',
    min_speeches: int = 5
) -> dict:
    """
    Identify politicians who "surf" topics - rapidly changing focus.
    
    Measures topic consistency over time for each speaker.
    
    Returns:
        {
            speaker: {
                'topic_changes': int,  # number of topic switches
                'consistency_score': 0-100,  # higher = more consistent
                'most_surfed_to': cluster_id,  # most frequently switched to
                'timeline': [{period, dominant_topic}, ...]
            },
            ...
        }
    """
    df = add_time_columns(df, date_col)
    
    result = {}
    labels = cluster_labels or {}
    
    for speaker in df[speaker_col].unique():
        speaker_df = df[df[speaker_col] == speaker].copy()
        
        if len(speaker_df) < min_speeches:
            continue
        
        # Filter valid dates and sort
        valid_speaker = speaker_df[speaker_df['month'].notna()].sort_values('parsed_date')
        
        if len(valid_speaker) < 3:
            continue
        
        # Group by month and find dominant topic
        monthly_topics = valid_speaker.groupby('month')[cluster_col].agg(
            lambda x: x.value_counts().idxmax()
        )
        
        # Count topic changes
        topics_list = monthly_topics.tolist()
        changes = sum(1 for i in range(1, len(topics_list)) if topics_list[i] != topics_list[i-1])
        
        # Consistency score: fewer changes = higher consistency
        max_possible_changes = len(topics_list) - 1
        consistency = ((max_possible_changes - changes) / max_possible_changes) * 100 if max_possible_changes > 0 else 100
        
        # Most common destination when switching
        switch_destinations = [topics_list[i] for i in range(1, len(topics_list)) if topics_list[i] != topics_list[i-1]]
        most_surfed_to = max(set(switch_destinations), key=switch_destinations.count) if switch_destinations else None
        
        result[speaker] = {
            'topic_changes': changes,
            'consistency_score': round(consistency, 1),
            'most_surfed_to': int(most_surfed_to) if most_surfed_to is not None else None,
            'most_surfed_to_label': labels.get(most_surfed_to, '') if most_surfed_to is not None else '',
            'n_periods': len(topics_list),
            'timeline': [
                {'period': period, 'topic': int(topic), 'label': labels.get(topic, '')}
                for period, topic in monthly_topics.items()
            ]
        }
    
    # Sort by surfing frequency
    result = dict(sorted(result.items(), key=lambda x: -x[1]['topic_changes']))
    
    logger.info("Analyzed topic surfing for %d speakers", len(result))
    
    return result
