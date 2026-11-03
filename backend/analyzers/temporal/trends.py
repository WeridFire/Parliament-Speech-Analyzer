"""
Topic Trends - how the agenda moves month by month.

The previous version published raw counts only, and the number of sittings per
month swings widely (August has a fraction of July's): every topic "fell" in
August and "rose" in September. Shares of each month's speeches are what show
the agenda moving; counts are kept for the hover detail.
"""

import logging

import pandas as pd

from backend.analyzers.common import blocs_of, topic_ids
from backend.config import ALTRO, MAGGIORANZA, OPPOSIZIONE, UNCLASSIFIED_CLUSTER

from .utils import add_time_columns

logger = logging.getLogger(__name__)


def compute_topic_trends(
    df: pd.DataFrame,
    cluster_col: str = 'cluster',
    cluster_labels: dict = None,
    date_col: str = 'date',
    granularity: str = 'month',
    party_col: str = 'group',
) -> dict:
    """
    Returns:
        {
            'periods': [sorted periods],
            'totals': {period: classified speeches},
            'counts': {period: {topic: n}},
            'shares': {period: {topic: % of the period's classified speeches}},
            'blocs':  {period: {maggioranza, opposizione, altro}},   all speeches
        }
    """
    df = add_time_columns(df, date_col)
    period_col = '_month' if granularity == 'month' else '_week'
    rows = df[df[period_col].notna()]

    if rows.empty:
        logger.warning("No valid dates found for temporal analysis")
        return {'periods': [], 'totals': {}, 'counts': {}, 'shares': {}, 'blocs': {}}

    topics = topic_ids(cluster_labels or {})
    classified = rows[rows[cluster_col] != UNCLASSIFIED_CLUSTER]

    table = pd.crosstab(classified[period_col], classified[cluster_col])
    table = table.reindex(columns=topics, fill_value=0)
    totals = table.sum(axis=1)

    blocs = pd.crosstab(rows[period_col], blocs_of(rows, party_col))
    blocs = blocs.reindex(columns=[MAGGIORANZA, OPPOSIZIONE, ALTRO], fill_value=0)

    periods = sorted(rows[period_col].unique())

    result = {
        'periods': periods,
        'totals': {p: int(totals.get(p, 0)) for p in periods},
        'counts': {
            p: {t: int(table.at[p, t]) for t in topics} if p in table.index else {}
            for p in periods
        },
        'shares': {
            p: {
                t: round(table.at[p, t] / totals[p] * 100, 2) for t in topics
            } if p in table.index and totals[p] else {}
            for p in periods
        },
        'blocs': {
            p: {b: int(blocs.at[p, b]) for b in blocs.columns}
            for p in periods
        },
    }

    logger.info("Computed topic trends for %d periods", len(periods))
    return result
