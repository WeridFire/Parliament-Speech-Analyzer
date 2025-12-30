"""
Temporal utilities - Date parsing and time column helpers.
"""

import logging
import re
from datetime import datetime
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


def parse_date(date_str: str) -> Optional[datetime]:
    """
    Parse date string in various formats.
    
    Supports:
    - ISO format: 2024-01-15
    - Italian format: 15/01/2024, 15-01-2024
    - Month-Year: gennaio 2024
    
    Returns:
        datetime object or None if parsing fails
    """
    if not date_str or not isinstance(date_str, str):
        return None
    
    date_str = date_str.strip()
    
    # Common date formats
    formats = [
        '%Y-%m-%d',      # 2024-01-15
        '%d/%m/%Y',      # 15/01/2024
        '%d-%m-%Y',      # 15-01-2024
        '%Y/%m/%d',      # 2024/01/15
        '%d %B %Y',      # 15 January 2024
        '%d %b %Y',      # 15 Jan 2024
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    # Try Italian month names
    italian_months = {
        'gennaio': 1, 'febbraio': 2, 'marzo': 3, 'aprile': 4,
        'maggio': 5, 'giugno': 6, 'luglio': 7, 'agosto': 8,
        'settembre': 9, 'ottobre': 10, 'novembre': 11, 'dicembre': 12
    }
    
    for month_name, month_num in italian_months.items():
        pattern = rf'(\d{{1,2}})\s+{month_name}\s+(\d{{4}})'
        match = re.search(pattern, date_str.lower())
        if match:
            try:
                return datetime(int(match.group(2)), month_num, int(match.group(1)))
            except ValueError:
                continue
    
    logger.debug("Could not parse date: %s", date_str)
    return None


def add_time_columns(df: pd.DataFrame, date_col: str = 'date') -> pd.DataFrame:
    """
    Add parsed date and time period columns to DataFrame.
    
    Adds columns: _parsed_date, _year, _month, _week
    
    Args:
        df: DataFrame with date column
        date_col: Name of date column
    
    Returns:
        DataFrame with added time columns
    """
    df = df.copy()
    
    df['_parsed_date'] = df[date_col].apply(parse_date)
    df['_year'] = df['_parsed_date'].apply(lambda x: x.year if x else None)
    df['_month'] = df['_parsed_date'].apply(
        lambda x: f"{x.year}-{x.month:02d}" if x else None
    )
    df['_week'] = df['_parsed_date'].apply(
        lambda x: f"{x.year}-W{x.isocalendar()[1]:02d}" if x else None
    )
    
    return df
