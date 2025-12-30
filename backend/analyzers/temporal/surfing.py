"""
Topic Surfing - Identify politicians who rapidly change focus.
"""

import logging

import pandas as pd

from .utils import add_time_columns

logger = logging.getLogger(__name__)


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
    
    Args:
        df: DataFrame with speeches
        cluster_col: Column with cluster assignments
        cluster_labels: Dict mapping cluster_id -> label
        date_col: Column with dates
        speaker_col: Column with speaker names
        min_speeches: Minimum speeches to include speaker
    
    Returns:
        {
            speaker: {
                'topic_changes': int,
                'consistency_score': 0-100,
                'most_surfed_to': cluster_id,
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
        valid_speaker = speaker_df[speaker_df['_month'].notna()].sort_values('_parsed_date')
        
        if len(valid_speaker) < 3:
            continue
        
        # Group by month and find dominant topic
        monthly_topics = valid_speaker.groupby('_month')[cluster_col].agg(
            lambda x: x.value_counts().idxmax()
        )
        
        # Count topic changes
        topics_list = monthly_topics.tolist()
        changes = sum(1 for i in range(1, len(topics_list)) if topics_list[i] != topics_list[i-1])
        
        # Consistency score
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
