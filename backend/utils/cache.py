"""
Cache utilities for managing speech and embedding caches.

Provides functions for cache validation, metadata management, and cleanup.
"""
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Cache directory (relative to this file's parent, i.e., backend/)
CACHE_DIR = Path(__file__).parent.parent / '.cache'


def get_cache_metadata(name: str) -> Optional[dict]:
    """
    Load cache metadata (timestamp, version) for an artifact.

    Args:
        name: Artifact identifier - a source ('camera') or a full cache key
              stem ('embeddings_camera_9f2c1a4b')

    Returns:
        Metadata dict with 'created_at' and 'version', or None if not found
    """
    meta_file = CACHE_DIR / f'cache_meta_{name}.json'
    if meta_file.exists():
        try:
            with open(meta_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning("Failed to read cache metadata: %s", e)
    return None


def save_cache_metadata(name: str, version: str = "2.0", **extra):
    """
    Save cache creation timestamp, version and any artifact-specific fields.

    Args:
        name: Artifact identifier (source name or full cache key stem)
        version: Cache format version for future compatibility
        **extra: Additional fields to record (kind, digest, rows, bytes, ...)
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    meta_file = CACHE_DIR / f'cache_meta_{name}.json'
    metadata = {
        'created_at': datetime.now().isoformat(),
        'version': version,
        'source': extra.pop('source', name),
        **extra,
    }
    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    logger.debug("Saved cache metadata for %s", name)


def is_cache_valid(name: str, max_age_days: int = 7) -> bool:
    """
    Check if a cache entry is still within its age budget.

    Args:
        name: Artifact identifier (source name or full cache key stem)
        max_age_days: Maximum age in days before the entry is considered stale

    Returns:
        True if the entry exists and is younger than max_age_days
    """
    source = name
    meta = get_cache_metadata(name)
    if not meta or 'created_at' not in meta:
        return False
    
    try:
        created = datetime.fromisoformat(meta['created_at'])
        age_days = (datetime.now() - created).days
        is_valid = age_days < max_age_days
        
        if not is_valid:
            logger.info("Cache for %s is stale (%d days old, max=%d)", source, age_days, max_age_days)
        
        return is_valid
    except ValueError as e:
        logger.warning("Invalid cache timestamp: %s", e)
        return False


def get_cache_age_days(source: str) -> Optional[int]:
    """
    Get the age of cache in days.
    
    Args:
        source: Data source identifier
    
    Returns:
        Age in days, or None if cache doesn't exist
    """
    meta = get_cache_metadata(source)
    if not meta or 'created_at' not in meta:
        return None
    
    try:
        created = datetime.fromisoformat(meta['created_at'])
        return (datetime.now() - created).days
    except ValueError:
        return None


def clear_cache(source: Optional[str] = None):
    """
    Delete cached files.
    
    Args:
        source: If specified, only clear cache for this source.
                If None, clear all caches.
    """
    if not CACHE_DIR.exists():
        logger.info("No cache directory to clear")
        return
    
    if source:
        # Clear specific source cache
        patterns = [
            f'speeches_raw_{source}.json',
            f'embeddings_{source}.npy',
            f'cache_meta_{source}.json'
        ]
        for pattern in patterns:
            cache_file = CACHE_DIR / pattern
            if cache_file.exists():
                cache_file.unlink()
                logger.info("Deleted %s", cache_file.name)
    else:
        # Clear all caches
        for f in CACHE_DIR.iterdir():
            if f.is_file():
                f.unlink()
                logger.info("Deleted %s", f.name)
    
    logger.info("Cache cleared%s", f" for {source}" if source else "")


def show_cache_info():
    """Display cache status and file information."""
    if not CACHE_DIR.exists():
        print("📁 No cache directory exists")
        return
    
    files = list(CACHE_DIR.iterdir())
    if not files:
        print("📁 Cache directory is empty")
        return
    
    print(f"\n📁 Cache directory: {CACHE_DIR}")
    print("-" * 60)
    
    total_size = 0
    for f in sorted(files):
        if f.is_file():
            size_kb = f.stat().st_size / 1024
            total_size += size_kb
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            age = (datetime.now() - mtime).days
            
            # Determine file type icon
            if f.suffix == '.json':
                icon = "📄"
            elif f.suffix == '.npy':
                icon = "🔢"
            else:
                icon = "📎"
            
            print(f"  {icon} {f.name:40} {size_kb:>8.1f} KB  ({age} days old)")
    
    print("-" * 60)
    print(f"  Total: {total_size:.1f} KB in {len(files)} files")

    # Show recorded metadata per artifact (entries are keyed by cache stem)
    entries = sorted(CACHE_DIR.glob('cache_meta_*.json'))
    if not entries:
        return

    print("\n📊 Cache entries:")
    for meta_file in entries:
        name = meta_file.name[len('cache_meta_'):-len('.json')]
        meta = get_cache_metadata(name)
        if not meta:
            continue
        age = get_cache_age_days(name)
        kind = meta.get('kind', meta.get('source', '?'))
        rows = meta.get('rows')
        detail = f", {rows} rows" if rows else ""
        print(f"  {name:45} {kind:12} ({age} days old{detail})")
