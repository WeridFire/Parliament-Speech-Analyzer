"""
Data aggregation and export logic.
"""

import logging
import numpy as np
import pandas as pd

from backend.config import (
    DISPLAY_TEXT_CHARS,
    MIN_SPEECHES_DISPLAY,
    UNCLASSIFIED_CLUSTER,
    UNCLASSIFIED_LABEL,
)
from backend.core.dataset import SpeechDataset
from backend.analyzers import AnalyticsOrchestrator

logger = logging.getLogger(__name__)

# Minimum speeches for a period bucket to be worth aggregating
MIN_SPEECHES_YEAR = 10
MIN_SPEECHES_MONTH = 5


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
    dataset = SpeechDataset(df=df, topic_scores=topic_scores)
    return _aggregate_deputies(dataset, cluster_labels, rebel_scores)


def _aggregate_deputies(
    dataset: SpeechDataset,
    cluster_labels: dict,
    rebel_scores: dict,
) -> list:
    """
    Aggregate one deputy record per speaker in `dataset`.

    Speaker slices go through SpeechDataset.subset, so a speaker's topic scores
    are always averaged over that speaker's own rows.
    """
    deputies_data = []
    df = dataset.df

    for deputy in df['deputy'].unique():
        speaker = dataset.subset(df['deputy'] == deputy)
        if speaker.is_empty:
            continue

        speaker_df = speaker.df
        dominant_cluster = speaker_df['cluster'].mode().iloc[0]

        role = ""
        if 'role' in speaker_df.columns:
            roles = speaker_df[speaker_df['role'] != '']['role']
            if not roles.empty:
                role = roles.mode()[0]

        divergence_info = rebel_scores.get(deputy, {})
        default_label = (
            UNCLASSIFIED_LABEL if dominant_cluster == UNCLASSIFIED_CLUSTER
            else f"Cluster {dominant_cluster}"
        )

        deputy_obj = {
            'deputy': deputy,
            'name': deputy.split('[')[0].strip(),
            'party': speaker_df['group'].iloc[0],
            'role': role,
            'x': float(speaker_df['x'].mean()),
            'y': float(speaker_df['y'].mean()),
            'n_speeches': len(speaker),
            'cluster': int(dominant_cluster),
            'cluster_label': cluster_labels.get(dominant_cluster, default_label),
            'divergence_pct': divergence_info.get('divergence_pct', 0),
            'source': speaker_df['source'].iloc[0] if 'source' in speaker_df.columns else 'senate',
        }

        if speaker.topic_scores is not None and len(speaker.topic_scores):
            avg_scores = np.mean(speaker.topic_scores, axis=0)
            deputy_obj['topic_scores'] = [round(float(s), 3) for s in avg_scores]

        deputies_data.append(deputy_obj)

    # Filter deputies with insufficient speeches for display
    return [d for d in deputies_data if d['n_speeches'] >= MIN_SPEECHES_DISPLAY]


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
    logger.info("Computing deputies by period...")

    dataset = SpeechDataset(df=df, topic_scores=topic_scores)

    global_deputies = _aggregate_deputies(dataset, cluster_labels, rebel_scores)

    by_year = _aggregate_by_period(
        dataset, cluster_labels, rebel_scores, 'year', MIN_SPEECHES_YEAR, date_col,
        newest_first=False,
    )
    logger.info("Computed deputies for %d years", len(by_year))

    by_month = _aggregate_by_period(
        dataset, cluster_labels, rebel_scores, 'month', MIN_SPEECHES_MONTH, date_col,
        newest_first=True,
    )
    logger.info("Computed deputies for %d months", len(by_month))

    # Only advertise periods that actually produced deputies
    available_periods = {
        'years': [int(y) for y in by_year],
        'months': list(by_month),
    }

    return {
        'global': global_deputies,
        'by_year': by_year,
        'by_month': by_month,
        'available_periods': available_periods
    }


def _aggregate_by_period(
    dataset: SpeechDataset,
    cluster_labels: dict,
    rebel_scores: dict,
    granularity: str,
    min_speeches: int,
    date_col: str,
    newest_first: bool,
) -> dict:
    """Aggregate deputies within each period bucket that clears the threshold."""
    buckets = {}

    for key, bucket in dataset.by_period(
        granularity, date_col=date_col, min_speeches=min_speeches, newest_first=newest_first
    ):
        deputies = _aggregate_deputies(bucket, cluster_labels, rebel_scores)
        if deputies:
            buckets[key] = deputies

    return buckets


def build_speech_records(dataset: SpeechDataset, chamber: str, divergence: dict) -> list:
    """
    One export record per speech.

    Note what is *not* here: the payload used to carry both `text` (the cleaned,
    lowercased text truncated to 500 chars) and `snippet` (the full raw text).
    The names were backwards, the truncation saved nothing because the untruncated
    copy shipped alongside it, and the frontend displayed the lowercased one. Now
    a single `text` field carries the original-case speech, truncated.
    """
    records = []
    df = dataset.df
    scores = dataset.topic_scores

    for position, (_, row) in enumerate(df.iterrows()):
        record = {
            'deputy': row['deputy'],
            'party': row['group'],
            'date': row['date'],
            'text': str(row.get('raw_text', row['text']))[:DISPLAY_TEXT_CHARS],
            'x': float(row['x']),
            'y': float(row['y']),
            'cluster': int(row['cluster']),
            'cluster_label': row['cluster_label'],
            'rhetoric_style': row['rhetoric_style'],
            'divergence_pct': divergence.get(row['deputy'], {}).get('divergence_pct', 0),
            'source': row.get('source', chamber),
            'url': row.get('url', ''),
        }

        if 'cluster_conf' in df.columns:
            record['cluster_conf'] = round(float(row['cluster_conf']), 3)

        if scores is not None:
            record['topic_scores'] = [round(float(s), 3) for s in scores[position]]

        records.append(record)

    return records


def compute_source_output(args):
    """
    Compute the complete payload for a single chamber.

    Runs in a worker process, so it receives only that chamber's data: the
    previous version shipped every chamber's speeches and deputies to every
    worker, which then filtered them back down.

    Returns:
        tuple: (source_name, output_dict, filename)
    """
    (src, dataset, cluster_labels, cluster_topics, divergence_scores, cluster_centroids) = args

    source_df = dataset.df
    logger.info("Computing analytics for source: %s (%d speeches)", src, len(source_df))

    # Restrict divergence scores to speakers actually present in this chamber
    speakers = set(source_df['deputy'].unique())
    source_divergence = {d: info for d, info in divergence_scores.items() if d in speakers}

    source_rebels = sorted(
        ({'deputy': d, **info} for d, info in source_divergence.items()
         if info.get('divergence_pct', 0) > 30),
        key=lambda x: -x['divergence_pct'],
    )[:15]

    source_speeches = build_speech_records(dataset, src, source_divergence)

    # Compute analytics SEPARATELY for this source, with period-based breakdown
    from backend.analyzers.period_orchestrator import compute_analytics_by_period
    from backend.config import COMPUTE_ANALYTICS_BY_PERIOD
    
    source_analytics, analytics_report = compute_analytics_by_period(
        df=source_df,
        embeddings=dataset.embeddings,
        cluster_labels=cluster_labels,
        cluster_centroids=cluster_centroids,
        source=src,
        date_col='date',
        compute_by_period=COMPUTE_ANALYTICS_BY_PERIOD,
    )
    logger.info("%s: %s", src, analytics_report.summary())

    # Build cluster metadata for this source
    source_cluster_meta = {}
    for cid in source_df['cluster'].unique():
        keywords = cluster_topics.get(cid, [])
        label = cluster_labels.get(cid, UNCLASSIFIED_LABEL if cid == UNCLASSIFIED_CLUSTER else f"Cluster {cid}")
        source_cluster_meta[int(cid)] = {
            'label': label,
            'keywords': keywords,
            'count': int((source_df['cluster'] == cid).sum()),
        }

    source_deputies_by_period = compute_deputies_by_period(
        source_df, dataset.topic_scores, cluster_labels, source_divergence, date_col='date'
    )
    source_deputies = source_deputies_by_period['global']

    source_output = {
        'speeches': source_speeches,
        'deputies': source_deputies,
        'deputies_by_period': source_deputies_by_period,
        'clusters': source_cluster_meta,
        'rebels': source_rebels,
        'all_divergence_scores': source_divergence,
        'stats': {
            'total_speeches': len(source_speeches),
            'total_deputies': len(source_deputies),
            'total_parties': len({d['party'] for d in source_speeches if d['party'] != 'Unknown Group'}),
            'n_clusters': len(source_cluster_meta),
            'unclassified_speeches': int((source_df['cluster'] == UNCLASSIFIED_CLUSTER).sum()),
            'source': src,
            'analytics_run': analytics_report.as_dict(),
        },
        # Advanced analytics computed for THIS source only
        'analytics': source_analytics
    }

    # Map source to Italian filename
    filename_map = {'senate': 'senato', 'camera': 'camera'}
    filename = filename_map.get(src, src)

    logger.info("Completed analytics for source: %s", src)

    return (src, source_output, filename)
