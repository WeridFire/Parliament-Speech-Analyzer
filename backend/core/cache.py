"""
Cache management functions for backend core.
"""

import json
import logging
from pathlib import Path
import numpy as np
import pandas as pd

from backend.utils import CACHE_DIR, save_cache_metadata

logger = logging.getLogger(__name__)


def load_cached_speeches(source: str) -> pd.DataFrame | None:
    """Load speeches from cache if available for the specific source."""
    cache_file = CACHE_DIR / f'speeches_raw_{source}.json'
    if cache_file.exists():
        logger.info("Loading speeches from cache: %s", cache_file.name)
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return pd.DataFrame(data)
    return None


def save_speeches_cache(df: pd.DataFrame, source: str):
    """Save speeches to cache for the specific source."""
    CACHE_DIR.mkdir(exist_ok=True)
    cache_file = CACHE_DIR / f'speeches_raw_{source}.json'
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(df.to_dict('records'), f, ensure_ascii=False, indent=2)
    # Save cache metadata for validation
    save_cache_metadata(source)
    logger.info("Cached %d speeches to %s", len(df), cache_file.name)


def load_cached_embeddings(source: str) -> np.ndarray | None:
    """Load embeddings from cache if available for the specific source."""
    cache_file = CACHE_DIR / f'embeddings_{source}.npy'
    if cache_file.exists():
        logger.info("Loading embeddings from cache: %s", cache_file.name)
        return np.load(cache_file)
    return None


def save_embeddings_cache(embeddings: np.ndarray, source: str):
    """Save embeddings to cache for the specific source."""
    CACHE_DIR.mkdir(exist_ok=True)
    cache_file = CACHE_DIR / f'embeddings_{source}.npy'
    np.save(cache_file, embeddings)
    logger.info("Cached embeddings to %s", cache_file.name)
