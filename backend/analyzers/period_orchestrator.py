"""
Period Orchestrator - Compute analytics for each time period.

Wraps AnalyticsOrchestrator to generate per-year and per-month analytics, which
is what backs the frontend's period selector.

Period slicing goes through SpeechDataset, so each bucket's speeches and
embeddings are narrowed together and cannot drift apart.
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd

from backend.core.dataset import SpeechDataset

from .orchestrator import AnalyticsOrchestrator

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
    compute_by_period: bool = True,
) -> tuple[dict, 'AnalyticsRunReport']:
    """
    Compute analytics for global, by_year, and by_month periods.

    Args:
        df: DataFrame with speeches
        embeddings: Embeddings array aligned with df
        cluster_labels: Dict mapping cluster_id -> label
        cluster_centroids: Cluster centroid vectors
        source: Data source name
        date_col: Column containing dates
        compute_by_period: If False, only compute global analytics (faster)

    Returns:
        A pair of (analytics, report):

            {
                'global': {...all analytics...},
                'by_year': {'2024': {...}, '2023': {...}},
                'by_month': {'2024-12': {...}, '2024-11': {...}}
            }

        The report travels separately rather than as a key inside the analytics,
        so run metadata cannot accidentally be serialised into the payload.
    """
    logger.info("Computing analytics by period...")

    dataset = SpeechDataset(df=df, embeddings=embeddings)
    report = AnalyticsRunReport()

    def run_for(subset: SpeechDataset, granularity: str, period: str) -> dict:
        orchestrator = AnalyticsOrchestrator(
            df=subset.df,
            embeddings=subset.embeddings,
            cluster_labels=cluster_labels,
            cluster_centroids=cluster_centroids,
            source=source,
            granularity=granularity,
        )
        results = orchestrator.run_all()
        report.record(period, orchestrator)
        return results

    logger.info("Computing global analytics...")
    global_analytics = run_for(dataset, 'global', 'global')

    if not compute_by_period:
        logger.info("Period computation disabled, returning global-only analytics")
        return {'global': global_analytics, 'by_year': {}, 'by_month': {}}, report

    by_year = _run_buckets(dataset, run_for, 'year', MIN_SPEECHES_YEAR, date_col,
                           newest_first=False, report=report)
    logger.info("Computed analytics for %d years", len(by_year))

    by_month = _run_buckets(dataset, run_for, 'month', MIN_SPEECHES_MONTH, date_col,
                            newest_first=True, report=report)
    logger.info("Computed analytics for %d months", len(by_month))

    return {
        'global': global_analytics,
        'by_year': by_year,
        'by_month': by_month,
    }, report


class AnalyticsRunReport:
    """
    What ran, what was skipped and what broke, across every period.

    Analyzer failures are recorded rather than raised so one broken metric does
    not cost the whole export - but they have to surface somewhere, or the
    payload ships with a silent hole.
    """

    def __init__(self):
        self.failures: dict[str, dict[str, str]] = {}
        self.skipped: dict[str, dict[str, list[str]]] = {}

    def record(self, period: str, orchestrator: AnalyticsOrchestrator):
        if orchestrator.failures:
            self.failures[period] = dict(orchestrator.failures)
        if orchestrator.skipped:
            self.skipped[period] = dict(orchestrator.skipped)

    @property
    def failed_analyzers(self) -> set[str]:
        return {name for period in self.failures.values() for name in period}

    def as_dict(self) -> dict:
        return {
            'failed_analyzers': sorted(self.failed_analyzers),
            'failures': self.failures,
            # Skips are expected (an analyzer declining a thin month), so they
            # are summarised rather than listed period by period.
            'skipped_global': self.skipped.get('global', {}),
        }

    def summary(self) -> str:
        if not self.failures:
            return "all analyzers completed"
        return (
            f"{len(self.failed_analyzers)} analyzer(s) failed in "
            f"{len(self.failures)} period(s): {sorted(self.failed_analyzers)}"
        )


def _run_buckets(
    dataset: SpeechDataset,
    run_for,
    granularity: str,
    min_speeches: int,
    date_col: str,
    newest_first: bool,
    report: 'AnalyticsRunReport',
) -> dict:
    """Run the analytics callable over each period bucket, skipping failures."""
    results = {}

    for key, bucket in dataset.by_period(
        granularity, date_col=date_col, min_speeches=min_speeches, newest_first=newest_first
    ):
        logger.info("Computing analytics for %s (%d speeches)...", key, len(bucket))
        try:
            bucket_results = run_for(bucket, granularity, key)
        except Exception as e:
            logger.warning("Failed to compute analytics for %s: %s", key, e)
            continue

        # An entirely skipped bucket (every analyzer declined the sample size)
        # would otherwise ship as an empty object the frontend has to handle.
        if bucket_results:
            results[key] = bucket_results

    return results
