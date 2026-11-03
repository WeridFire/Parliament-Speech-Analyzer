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
    party_bloc,
)
from backend.core.dataset import SpeechDataset

logger = logging.getLogger(__name__)

# Minimum speeches for a period bucket to be worth aggregating
MIN_SPEECHES_YEAR = 10
MIN_SPEECHES_MONTH = 5


def _cluster_label(cluster_labels: dict, cluster: int) -> str:
    if cluster == UNCLASSIFIED_CLUSTER:
        return cluster_labels.get(cluster, UNCLASSIFIED_LABEL)
    return cluster_labels.get(cluster, f"Cluster {cluster}")


def compute_deputies_data(df: pd.DataFrame, cluster_labels: dict) -> list:
    """
    One record per speaker: mean map position, speech count, dominant topic.

    A single groupby. The previous version sliced the frame once per deputy -
    and once per deputy per period - which made it the slowest step outside
    the analyzers.
    """
    if df.empty:
        return []

    grouped = df.groupby('deputy', sort=False)
    stats = grouped.agg(
        x=('x', 'mean'),
        y=('y', 'mean'),
        n_speeches=('deputy', 'size'),
        party=('group', 'first'),
    )
    stats = stats[stats['n_speeches'] >= MIN_SPEECHES_DISPLAY]
    if stats.empty:
        return []

    # Dominant topic: the most frequent cluster, ties to the lowest id.
    counts = df.groupby(['deputy', 'cluster']).size().rename('n').reset_index()
    dominant = (
        counts.sort_values(['deputy', 'n', 'cluster'], ascending=[True, False, True])
        .drop_duplicates('deputy')
        .set_index('deputy')['cluster']
    )

    roles = {}
    if 'role' in df.columns:
        with_role = df[df['role'].fillna('') != '']
        roles = with_role.groupby('deputy')['role'].agg(lambda r: r.mode().iloc[0]).to_dict()

    sources = grouped['source'].first() if 'source' in df.columns else None

    records = []
    for deputy, row in stats.iterrows():
        cluster = int(dominant[deputy])
        records.append({
            'deputy': deputy,
            'name': deputy.split('[')[0].strip(),
            'party': row['party'],
            'bloc': party_bloc(row['party']),
            'role': roles.get(deputy, ''),
            'x': float(row['x']),
            'y': float(row['y']),
            'n_speeches': int(row['n_speeches']),
            'cluster': cluster,
            'cluster_label': _cluster_label(cluster_labels, cluster),
            'source': sources[deputy] if sources is not None else 'senate',
        })

    return records


def compute_deputies_by_period(
    df: pd.DataFrame,
    cluster_labels: dict,
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

    dataset = SpeechDataset(df=df)
    global_deputies = compute_deputies_data(dataset.df, cluster_labels)

    by_year = _aggregate_by_period(dataset, cluster_labels, 'year', MIN_SPEECHES_YEAR, date_col, False)
    by_month = _aggregate_by_period(dataset, cluster_labels, 'month', MIN_SPEECHES_MONTH, date_col, True)
    logger.info("Computed deputies for %d years and %d months", len(by_year), len(by_month))

    return {
        'global': global_deputies,
        'by_year': by_year,
        'by_month': by_month,
        # Only advertise periods that actually produced deputies
        'available_periods': {
            'years': [int(y) for y in by_year],
            'months': list(by_month),
        },
    }


def _aggregate_by_period(
    dataset: SpeechDataset,
    cluster_labels: dict,
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
        deputies = compute_deputies_data(bucket.df, cluster_labels)
        if deputies:
            buckets[key] = deputies

    return buckets


def build_speech_records(dataset: SpeechDataset, chamber: str) -> list:
    """
    One export record per speech: what the map and the speech panel display.

    `text` is the original-case speech, truncated; the full text is one click
    away behind `url`. Per-speech fields nobody displayed - fourteen topic
    similarities, a rhetoric label and a divergence score - are no longer
    shipped.
    """
    df = dataset.df
    text = df['raw_text'] if 'raw_text' in df.columns else df['text']

    frame = pd.DataFrame({
        'deputy': df['deputy'],
        'party': df['group'],
        'date': df['date'],
        'text': text.astype(str).str.slice(0, DISPLAY_TEXT_CHARS),
        'x': df['x'].astype(float),
        'y': df['y'].astype(float),
        'cluster': df['cluster'].astype(int),
        'cluster_label': df['cluster_label'],
        'source': df['source'] if 'source' in df.columns else chamber,
        'url': df['url'] if 'url' in df.columns else '',
    })
    if 'cluster_conf' in df.columns:
        frame['cluster_conf'] = df['cluster_conf'].astype(float).round(3)

    return frame.to_dict('records')


def build_cluster_meta(df: pd.DataFrame, cluster_labels: dict, cluster_topics: dict) -> dict:
    """Label, keywords and speech count for each cluster present in `df`."""
    counts = df['cluster'].value_counts()
    return {
        int(cid): {
            'label': _cluster_label(cluster_labels, int(cid)),
            'keywords': cluster_topics.get(int(cid), []),
            'count': int(n),
        }
        for cid, n in counts.items()
    }


def build_party_meta(df: pd.DataFrame) -> list:
    """Groups present in the chamber, with their bloc and size, largest first."""
    counts = df['group'].value_counts()
    return [
        {'name': party, 'bloc': party_bloc(party), 'n_speeches': int(n)}
        for party, n in counts.items()
    ]


def compute_source_output(args):
    """
    Compute the complete payload for a single chamber.

    Returns:
        tuple: (source_name, output_dict, filename)
    """
    (src, dataset, cluster_labels, cluster_topics, vocabulary) = args

    source_df = dataset.df
    logger.info("Computing analytics for source: %s (%d speeches)", src, len(source_df))

    from backend.analyzers.period_orchestrator import compute_analytics_by_period
    from backend.config import COMPUTE_ANALYTICS_BY_PERIOD

    source_analytics, analytics_report = compute_analytics_by_period(
        df=source_df,
        embeddings=dataset.embeddings,
        cluster_labels=cluster_labels,
        cluster_centroids=None,
        source=src,
        date_col='date',
        compute_by_period=COMPUTE_ANALYTICS_BY_PERIOD,
        terms=dataset.terms,
        vocabulary=vocabulary,
    )
    logger.info("%s: %s", src, analytics_report.summary())

    deputies_by_period = compute_deputies_by_period(source_df, cluster_labels, date_col='date')
    speeches = build_speech_records(dataset, src)

    dates = source_df['date'].dropna().astype(str)
    source_output = {
        'speeches': speeches,
        'deputies': deputies_by_period['global'],
        'deputies_by_period': deputies_by_period,
        'clusters': build_cluster_meta(source_df, cluster_labels, cluster_topics),
        'parties': build_party_meta(source_df),
        'stats': {
            'total_speeches': len(speeches),
            'total_deputies': len(deputies_by_period['global']),
            'total_speakers': int(source_df['deputy'].nunique()),
            'total_parties': int(source_df['group'].nunique()),
            'n_clusters': int(source_df['cluster'].nunique()),
            'unclassified_speeches': int((source_df['cluster'] == UNCLASSIFIED_CLUSTER).sum()),
            'first_date': dates.min() if len(dates) else None,
            'last_date': dates.max() if len(dates) else None,
            'source': src,
            'analytics_run': analytics_report.as_dict(),
        },
        'analytics': source_analytics,
    }

    # Map source to Italian filename
    filename = {'senate': 'senato', 'camera': 'camera'}.get(src, src)

    logger.info("Completed analytics for source: %s", src)
    return (src, source_output, filename)
