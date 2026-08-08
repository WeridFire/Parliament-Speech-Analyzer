"""
Date parsing and period bucketing.

Lives in utils rather than in the temporal analyzer because three layers need it
(core aggregation, period orchestration, temporal metrics) and core must not
depend on analyzers. `backend.analyzers.temporal.utils` re-exports these names,
so existing imports keep working.
"""

import logging
import re
from datetime import datetime
from typing import Literal, Optional

import pandas as pd

logger = logging.getLogger(__name__)

Granularity = Literal['year', 'month', 'week']

ITALIAN_MONTHS = {
    'gennaio': 1, 'febbraio': 2, 'marzo': 3, 'aprile': 4,
    'maggio': 5, 'giugno': 6, 'luglio': 7, 'agosto': 8,
    'settembre': 9, 'ottobre': 10, 'novembre': 11, 'dicembre': 12,
}

DATE_FORMATS = (
    '%Y-%m-%d',      # 2024-01-15
    '%d/%m/%Y',      # 15/01/2024
    '%d-%m-%Y',      # 15-01-2024
    '%Y/%m/%d',      # 2024/01/15
    '%Y%m%d',        # 20240115 (open-data SPARQL form)
    '%d %B %Y',      # 15 January 2024
    '%d %b %Y',      # 15 Jan 2024
)


def parse_date(date_str: str) -> Optional[datetime]:
    """
    Parse a date string in any of the formats the sources emit.

    Returns None rather than raising: parliamentary sources contain malformed and
    placeholder dates, and one bad row must not abort a run.
    """
    if not date_str or not isinstance(date_str, str):
        return None

    date_str = date_str.strip()

    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    for month_name, month_num in ITALIAN_MONTHS.items():
        match = re.search(rf'(\d{{1,2}})\s+{month_name}\s+(\d{{4}})', date_str.lower())
        if match:
            try:
                return datetime(int(match.group(2)), month_num, int(match.group(1)))
            except ValueError:
                continue

    logger.debug("Could not parse date: %s", date_str)
    return None


def period_key(moment: Optional[datetime], granularity: Granularity = 'month') -> Optional[str]:
    """
    Bucket key for a moment: '2024', '2024-03' or '2024-W12'.

    Accepts None and pandas NaT: applying `parse_date` over a column makes pandas
    infer a datetime dtype, which turns the None results into NaT, and NaT's
    `.year` is a float rather than an error.
    """
    if moment is None or pd.isna(moment):
        return None
    if granularity == 'year':
        return str(moment.year)
    if granularity == 'month':
        return f"{moment.year}-{moment.month:02d}"
    if granularity == 'week':
        return f"{moment.year}-W{moment.isocalendar()[1]:02d}"
    raise ValueError(f"Unknown granularity: {granularity}")


def parse_date_series(dates: pd.Series) -> pd.Series:
    """Vectorised-ish parse of a date column, preserving position."""
    return dates.apply(parse_date)


def add_time_columns(df: pd.DataFrame, date_col: str = 'date') -> pd.DataFrame:
    """
    Add `_parsed_date`, `_year`, `_month` and `_week` to a copy of the frame.

    Kept for the temporal analyzers, which work on plain DataFrames.
    """
    df = df.copy()

    parsed = parse_date_series(df[date_col])
    df['_parsed_date'] = parsed
    df['_year'] = parsed.apply(lambda d: d.year if d else None)
    df['_month'] = parsed.apply(lambda d: period_key(d, 'month'))
    df['_week'] = parsed.apply(lambda d: period_key(d, 'week'))

    return df
