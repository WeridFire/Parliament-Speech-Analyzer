"""
Content-addressed cache for pipeline artifacts.

One store for everything the pipeline can avoid recomputing: scraped speeches,
embeddings, and (later) fetched session documents. Entries are keyed by
`kind / source / digest`, where the digest describes *what the artifact was
computed from*:

  * speeches   - the fetch parameters (legislature, months back), because the
                 content cannot be known before fetching it;
  * embeddings - a fingerprint of the exact texts plus the model name.

That distinction is the point of this module. The previous embeddings cache
compared row *counts*, so a re-scrape that returned the same number of different
speeches silently reused vectors belonging to other texts, and every metric
downstream was quietly wrong. A fingerprint mismatch simply misses the cache.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

from backend.utils.cache import (
    CACHE_DIR,
    get_cache_metadata,
    is_cache_valid,
    save_cache_metadata,
)

from .serialization import dump_json

logger = logging.getLogger(__name__)

CACHE_VERSION = "3.0"

# Legacy filenames, still read once so an existing scrape is not thrown away.
LEGACY_SPEECHES = "speeches_raw_{source}.json"

DIGEST_LENGTH = 12


@dataclass(frozen=True)
class CacheKey:
    """Identity of a cached artifact."""

    kind: str
    source: str
    digest: str = ""

    @property
    def stem(self) -> str:
        parts = [self.kind, self.source]
        if self.digest:
            parts.append(self.digest[:DIGEST_LENGTH])
        return "_".join(p for p in parts if p)

    def __str__(self) -> str:
        return self.stem


class ArtifactCache:
    """Filesystem store for keyed artifacts, with age checks and pruning."""

    def __init__(self, root: Optional[Path] = None):
        self.root = Path(root) if root else CACHE_DIR

    # -- paths ---------------------------------------------------------------

    def path(self, key: CacheKey, ext: str) -> Path:
        return self.root / f"{key.stem}{ext}"

    def _ensure_root(self):
        self.root.mkdir(parents=True, exist_ok=True)

    def _record(self, key: CacheKey, **extra):
        save_cache_metadata(key.stem, version=CACHE_VERSION, kind=key.kind,
                            source=key.source, digest=key.digest, **extra)

    def _fresh_enough(self, key: CacheKey, max_age_days: Optional[int]) -> bool:
        if max_age_days is None:
            return True
        if is_cache_valid(key.stem, max_age_days=max_age_days):
            return True
        logger.info("Cache entry %s is older than %d days, ignoring", key.stem, max_age_days)
        return False

    # -- json ----------------------------------------------------------------

    def load_json(self, key: CacheKey, max_age_days: Optional[int] = None) -> Optional[Any]:
        import json

        path = self.path(key, '.json')
        if not path.exists() or not self._fresh_enough(key, max_age_days):
            return None

        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Unreadable cache entry %s: %s", path.name, e)
            return None

    def save_json(self, key: CacheKey, value: Any, **meta):
        self._ensure_root()
        size = dump_json(value, self.path(key, '.json'))
        self._record(key, bytes=size, **meta)

    # -- dataframes ----------------------------------------------------------

    def load_dataframe(self, key: CacheKey, max_age_days: Optional[int] = None) -> Optional[pd.DataFrame]:
        records = self.load_json(key, max_age_days=max_age_days)
        return None if records is None else pd.DataFrame(records)

    def save_dataframe(self, key: CacheKey, df: pd.DataFrame, **meta):
        self.save_json(key, df.to_dict('records'), rows=len(df), **meta)

    # -- arrays --------------------------------------------------------------

    def load_array(self, key: CacheKey) -> Optional[np.ndarray]:
        path = self.path(key, '.npy')
        if not path.exists():
            return None
        try:
            return np.load(path)
        except (ValueError, OSError) as e:
            logger.warning("Unreadable array cache %s: %s", path.name, e)
            return None

    def save_array(self, key: CacheKey, array: np.ndarray, **meta):
        self._ensure_root()
        path = self.path(key, '.npy')
        np.save(path, array)
        self._record(key, bytes=path.stat().st_size, shape=list(array.shape), **meta)

    # -- housekeeping --------------------------------------------------------

    def prune(self, kind: str, source: str, keep: int = 2, protect: str = "") -> int:
        """
        Drop all but the `keep` newest entries for a kind/source.

        Content-addressed keys mean every content change writes a new file, so
        without this the cache grows without bound.

        `protect` is the stem of the entry that must survive regardless of its
        timestamp. Several writes can land inside one filesystem timestamp tick,
        and with equal mtimes the sort order is arbitrary - without this, a run
        could delete the embeddings it had just spent minutes computing.
        """
        prefix = f"{kind}_{source}_"
        entries = [
            p for p in self.root.glob(f"{prefix}*")
            if p.is_file() and not p.name.endswith('.meta.json') and p.stem != protect
        ]

        budget = keep - 1 if protect else keep
        if len(entries) <= budget:
            return 0

        # Newest first, with the name as a deterministic tie-break.
        entries.sort(key=lambda p: (p.stat().st_mtime, p.name), reverse=True)
        removed = 0
        for stale in entries[budget:]:
            meta = self.root / f"cache_meta_{stale.stem}.json"
            stale.unlink(missing_ok=True)
            meta.unlink(missing_ok=True)
            removed += 1
            logger.debug("Pruned stale cache entry %s", stale.name)

        logger.info("Pruned %d stale %s entries for %s", removed, kind, source)
        return removed

    def describe(self) -> list[dict]:
        """Inventory of cached artifacts, for `--cache-info`."""
        if not self.root.exists():
            return []

        items = []
        for path in sorted(self.root.iterdir()):
            if not path.is_file() or path.name.startswith('cache_meta_'):
                continue
            meta = get_cache_metadata(path.stem) or {}
            items.append({
                'name': path.name,
                'bytes': path.stat().st_size,
                'kind': meta.get('kind'),
                'source': meta.get('source'),
                'created_at': meta.get('created_at'),
            })
        return items


# =============================================================================
# ARTIFACT-SPECIFIC HELPERS
# =============================================================================

_default_cache = ArtifactCache()


def speeches_key(source: str, digest: str = "") -> CacheKey:
    return CacheKey(kind='speeches', source=source, digest=digest)


def embeddings_key(source: str, fingerprint: str) -> CacheKey:
    return CacheKey(kind='embeddings', source=source, digest=fingerprint)


def load_cached_speeches(
    source: str,
    max_age_days: Optional[int] = None,
    digest: str = "",
    cache: Optional[ArtifactCache] = None,
) -> Optional[pd.DataFrame]:
    """
    Load scraped speeches for a source, if a cache entry is present and fresh.

    `max_age_days=None` disables the age check; the pipeline passes the
    configured maximum so a stale scrape is refreshed instead of being reused
    forever.
    """
    cache = cache or _default_cache
    key = speeches_key(source, digest)

    df = cache.load_dataframe(key, max_age_days=max_age_days)
    if df is not None:
        logger.info("Loaded %d speeches from cache (%s)", len(df), key.stem)
        return df

    legacy = cache.root / LEGACY_SPEECHES.format(source=source)
    if legacy.exists():
        import json

        logger.info("Adopting legacy speeches cache %s", legacy.name)
        with open(legacy, 'r', encoding='utf-8') as f:
            return pd.DataFrame(json.load(f))

    return None


def save_speeches_cache(
    df: pd.DataFrame,
    source: str,
    digest: str = "",
    cache: Optional[ArtifactCache] = None,
):
    """Persist scraped speeches for a source."""
    cache = cache or _default_cache
    key = speeches_key(source, digest)
    cache.save_dataframe(key, df)
    cache.prune('speeches', source, keep=2, protect=key.stem)
    logger.info("Cached %d speeches (%s)", len(df), key.stem)


def load_cached_embeddings(
    source: str,
    fingerprint: str,
    cache: Optional[ArtifactCache] = None,
) -> Optional[np.ndarray]:
    """
    Load embeddings only if they were computed from exactly this content.

    There is deliberately no fallback to an unfingerprinted file: adopting one
    would reintroduce the length-only check this store exists to remove.
    """
    cache = cache or _default_cache
    embeddings = cache.load_array(embeddings_key(source, fingerprint))

    if embeddings is None:
        logger.info("No embeddings cached for this corpus (%s...)", fingerprint[:DIGEST_LENGTH])
    else:
        logger.info("Loaded embeddings from cache (%s...)", fingerprint[:DIGEST_LENGTH])

    return embeddings


def save_embeddings_cache(
    embeddings: np.ndarray,
    source: str,
    fingerprint: str,
    cache: Optional[ArtifactCache] = None,
):
    """Persist embeddings under the fingerprint of the texts they encode."""
    cache = cache or _default_cache
    key = embeddings_key(source, fingerprint)
    cache.save_array(key, embeddings)
    cache.prune('embeddings', source, keep=2, protect=key.stem)
