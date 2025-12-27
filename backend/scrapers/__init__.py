"""
Scrapers subpackage - data extraction from Italian Parliament

Provides unified interface to scrape speeches from:
- Senate (senato.it)
- Chamber of Deputies (camera.it)
"""

import logging
import pandas as pd

from .senate import fetch_speeches as fetch_senate_speeches
from .senate import get_session_list as get_senate_sessions
from .camera import fetch_speeches as fetch_camera_speeches
from .camera import get_session_list as get_camera_sessions

logger = logging.getLogger(__name__)

# Keep backward compatibility
fetch_speeches = fetch_senate_speeches
get_session_list = get_senate_sessions


def fetch_all_speeches(
    source: str = 'both',
    limit: int = 200,
    sessions_to_fetch: int = 10
) -> pd.DataFrame:
    """
    Unified function to fetch speeches from one or both chambers.
    
    Args:
        source: 'senate', 'camera', or 'both'
        limit: Maximum speeches per source
        sessions_to_fetch: Number of sessions per source
    
    Returns:
        DataFrame with columns: date, deputy, group, text, source
    """
    frames = []
    
    if source in ('senate', 'both'):
        logger.info("Fetching speeches from Senate...")
        senate_df = fetch_senate_speeches(limit=limit, sessions_to_fetch=sessions_to_fetch)
        if not senate_df.empty:
            senate_df['source'] = 'senate'
            frames.append(senate_df)
    
    if source in ('camera', 'both'):
        logger.info("Fetching speeches from Camera...")
        camera_df = fetch_camera_speeches(limit=limit, sessions_to_fetch=sessions_to_fetch)
        if not camera_df.empty:
            camera_df['source'] = 'camera'
            frames.append(camera_df)
    
    if not frames:
        logger.warning("No speeches fetched from any source")
        return pd.DataFrame()
    
    combined = pd.concat(frames, ignore_index=True)
    logger.info("Total speeches fetched: %d (senate=%d, camera=%d)",
                len(combined),
                len(combined[combined['source'] == 'senate']) if 'source' in combined.columns else 0,
                len(combined[combined['source'] == 'camera']) if 'source' in combined.columns else 0)
    
    return combined
