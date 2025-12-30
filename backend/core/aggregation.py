"""
Data aggregation and export logic.
"""

import logging
import numpy as np
import pandas as pd

from backend.config import MIN_SPEECHES_DISPLAY
from backend.analyzers import AnalyticsOrchestrator

logger = logging.getLogger(__name__)


def compute_deputies_data(
    df: pd.DataFrame, 
    topic_scores: np.ndarray,
    cluster_labels: dict,
    rebel_scores: dict
) -> list:
    """
    Compute aggregated deputy data from speeches DataFrame.
    
    Can be called with filtered DataFrames to get per-period deputy data.
    
    Args:
        df: DataFrame with speeches (must have x, y, cluster, deputy, group columns)
        topic_scores: Topic similarity scores array (same length as df)
        cluster_labels: Dict mapping cluster_id -> label
        rebel_scores: Dict with rebel info per deputy
        
    Returns:
        List of deputy dicts with x, y, cluster, party, n_speeches, etc.
    """
    deputies_data = []
    has_scores = topic_scores is not None and len(topic_scores) > 0
    
    for deputy in df['deputy'].unique():
        deputy_df = df[df['deputy'] == deputy]
        if len(deputy_df) == 0:
            continue
            
        avg_x = deputy_df['x'].mean()
        avg_y = deputy_df['y'].mean()
        party = deputy_df['group'].iloc[0]
        n_speeches = len(deputy_df)
        
        # Dominant cluster for this deputy
        dominant_cluster = deputy_df['cluster'].mode().iloc[0] if len(deputy_df) > 0 else 0
        cluster_label = cluster_labels.get(dominant_cluster, f"Cluster {dominant_cluster}")
        
        # Get clean name (without party brackets)
        clean_name = deputy.split('[')[0].strip()
        
        rebel_info = rebel_scores.get(deputy, {})
        
        # Determine primary role (use mode or first non-empty)
        role = ""
        if 'role' in deputy_df.columns:
            roles = deputy_df[deputy_df['role'] != '']['role']
            if not roles.empty:
                role = roles.mode()[0]
        
        deputy_obj = {
            'deputy': deputy,
            'name': clean_name,
            'party': party,
            'role': role,
            'x': float(avg_x),
            'y': float(avg_y),
            'n_speeches': n_speeches,
            'cluster': int(dominant_cluster),
            'cluster_label': cluster_label,
            'rebel_pct': rebel_info.get('rebel_pct', 0),
            'source': deputy_df['source'].iloc[0] if 'source' in deputy_df.columns else 'senate'
        }
        
        if has_scores:
            # Average topic scores for this deputy
            indices = deputy_df.index
            # Ensure indices are within bounds
            valid_indices = [i for i in indices if i < len(topic_scores)]
            if valid_indices:
                dep_scores = topic_scores[valid_indices]
                avg_scores = np.mean(dep_scores, axis=0)
                deputy_obj['topic_scores'] = [round(float(s), 3) for s in avg_scores]
            
        deputies_data.append(deputy_obj)
    
    # Filter deputies with insufficient speeches for display
    deputies_data = [d for d in deputies_data if d['n_speeches'] >= MIN_SPEECHES_DISPLAY]
    
    return deputies_data


def compute_deputies_by_period(
    df: pd.DataFrame,
    topic_scores: np.ndarray,
    cluster_labels: dict,
    rebel_scores: dict,
    date_col: str = 'date'
) -> dict:
    """
    Compute deputy aggregates for each year and month.
    
    Returns:
        {
            'global': [...],  # all deputies
            'by_year': {'2024': [...], '2023': [...], ...},
            'by_month': {'2024-12': [...], ...},
            'available_periods': {'years': [...], 'months': [...]}
        }
    """
    from backend.analyzers.temporal import parse_date
    
    logger.info("Computing deputies by period...")
    
    # Parse dates
    df = df.copy()
    df['_parsed_date'] = df[date_col].apply(parse_date)
    df['_year'] = df['_parsed_date'].apply(lambda x: x.year if x else None)
    df['_month'] = df['_parsed_date'].apply(
        lambda x: f"{x.year}-{x.month:02d}" if x else None
    )
    
    # Global deputies
    global_deputies = compute_deputies_data(df, topic_scores, cluster_labels, rebel_scores)
    
    # Extract available periods
    years = sorted([int(y) for y in df['_year'].dropna().unique()])
    months = sorted([m for m in df['_month'].dropna().unique()], reverse=True)
    
    # Per-year deputies
    by_year = {}
    for year in years:
        year_df = df[df['_year'] == year].reset_index(drop=True)
        if len(year_df) >= 10:  # Minimum speeches
            # Get topic_scores indices for this subset
            year_indices = df[df['_year'] == year].index.tolist()
            year_scores = topic_scores[year_indices] if topic_scores is not None else None
            year_deputies = compute_deputies_data(year_df, year_scores, cluster_labels, rebel_scores)
            if year_deputies:
                by_year[str(year)] = year_deputies
    
    logger.info("Computed deputies for %d years", len(by_year))
    
    # Per-month deputies
    by_month = {}
    for month in months:
        month_df = df[df['_month'] == month].reset_index(drop=True)
        if len(month_df) >= 5:  # Lower threshold for months
            month_indices = df[df['_month'] == month].index.tolist()
            month_scores = topic_scores[month_indices] if topic_scores is not None else None
            month_deputies = compute_deputies_data(month_df, month_scores, cluster_labels, rebel_scores)
            if month_deputies:
                by_month[month] = month_deputies
    
    logger.info("Computed deputies for %d months", len(by_month))
    
    # Update available periods to only include those with data
    available_periods = {
        'years': [int(y) for y in by_year.keys()],
        'months': list(by_month.keys())
    }
    
    return {
        'global': global_deputies,
        'by_year': by_year,
        'by_month': by_month,
        'available_periods': available_periods
    }


def compute_source_output(args):
    """
    Compute complete analytics output for a single data source.
    
    This function is designed to be called in parallel via multiprocessing.
    Args are packed into a tuple to support ProcessPoolExecutor.map().
    
    Returns:
        tuple: (source_name, output_dict, filename)
    """
    (src, source_df, source_embeddings, cluster_labels, cluster_topics, 
     topic_scores, rebel_scores, deputy_sources, speeches_data, deputies_data, 
     cluster_centroids) = args
    
    logger.info("Computing analytics for source: %s (%d speeches)", src, len(source_df))
    
    # Filter speeches and deputies for this source
    source_speeches = [s for s in speeches_data if s.get('source', 'senate') == src]
    source_deputies = [d for d in deputies_data if d.get('source', 'senate') == src]
    
    # Calculate rebels for this specific source
    source_candidates = []
    source_rebel_scores_map = {}
    
    for dep, info in rebel_scores.items():
        # Check source of deputy
        dep_source = deputy_sources.get(dep, 'senate')
        if dep_source == src:
            # Add to detailed scores map
            source_rebel_scores_map[dep] = info
            # Check if candidate for top list
            if info['rebel_pct'] > 30:
                source_candidates.append({'deputy': dep, **info})
    
    # Sort and take top 15
    source_rebels = sorted(source_candidates, key=lambda x: -x['rebel_pct'])[:15]
    
    # Compute analytics SEPARATELY for this source using AnalyticsOrchestrator
    source_orchestrator = AnalyticsOrchestrator(
        df=source_df,
        embeddings=source_embeddings,
        cluster_labels=cluster_labels,
        cluster_centroids=cluster_centroids,
        source=src,
        enable_cache=False,
        text_col='cleaned_text',
        speaker_col='deputy',
        party_col='group',
        cluster_col='cluster',
        date_col='date',
    )
    source_analytics = source_orchestrator.run_all(use_cache=False)
    
    # Build cluster metadata for this source
    source_cluster_meta = {}
    for cid in source_df['cluster'].unique():
        keywords = cluster_topics.get(cid, [])
        label = cluster_labels.get(cid, f"Cluster {cid}")
        count = len(source_df[source_df['cluster'] == cid])
        source_cluster_meta[int(cid)] = {
            'label': label,
            'keywords': keywords,
            'count': count
        }
    
    # Compute per-period deputies for this source
    source_deputies_by_period = compute_deputies_by_period(
        source_df, topic_scores, cluster_labels, source_rebel_scores_map, date_col='date'
    )
    
    source_output = {
        'speeches': source_speeches,
        'deputies': source_deputies,
        'deputies_by_period': source_deputies_by_period,
        'clusters': source_cluster_meta,
        'rebels': source_rebels,
        'all_rebel_scores': source_rebel_scores_map,
        'stats': {
            'total_speeches': len(source_speeches),
            'total_deputies': len(source_deputies),
            'total_parties': len(set(d['party'] for d in source_speeches if d['party'] != 'Unknown Group')),
            'n_clusters': len(source_cluster_meta),
            'source': src
        },
        # Advanced analytics computed for THIS source only
        'analytics': source_analytics
    }
    
    # Map source to Italian filename
    filename_map = {'senate': 'senato', 'camera': 'camera'}
    filename = filename_map.get(src, src)
    
    logger.info("Completed analytics for source: %s", src)
    
    return (src, source_output, filename)
