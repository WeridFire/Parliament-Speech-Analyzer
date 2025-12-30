"""
Cache Manager - Unified caching system for all analyzers.

Provides:
- In-memory caching for current run
- Persistent JSON caching to disk
- Cache invalidation by pattern
- Separate caches per data source (camera/senato)
"""

import json
import hashlib
import logging
from pathlib import Path
from typing import Any, Optional
from datetime import datetime

import numpy as np

logger = logging.getLogger(__name__)


class NumpyEncoder(json.JSONEncoder):
    """JSON encoder that handles numpy types."""
    
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        return super().default(obj)


class CacheManager:
    """
    Unified cache manager for all analyzers.
    
    Features:
    - Two-level caching: memory (fast) + disk (persistent)
    - Automatic serialization of numpy types
    - Cache invalidation by analyzer name or pattern
    - Metadata tracking (timestamps, versions)
    
    Usage:
        cache = CacheManager(cache_dir, source='camera')
        
        # Check and get
        if cache.has('identity_v1.0'):
            result = cache.get('identity_v1.0')
        
        # Compute and store
        result = compute_something()
        cache.set('identity_v1.0', result)
        
        # Invalidate
        cache.invalidate('identity')  # Invalidates all identity_* keys
    """
    
    def __init__(
        self,
        cache_dir: Path,
        source: str = 'default',
        persist: bool = True
    ):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Base directory for cache files.
            source: Data source name (e.g., 'camera', 'senato').
            persist: Whether to persist to disk.
        """
        self.cache_dir = Path(cache_dir) / 'analyzers' / source
        self.source = source
        self.persist = persist
        
        if persist:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache
        self._memory: dict[str, Any] = {}
        
        # Metadata for each cached item
        self._metadata: dict[str, dict] = {}
        
        logger.debug("CacheManager initialized: source=%s, dir=%s", source, self.cache_dir)
    
    def _get_path(self, key: str) -> Path:
        """Get file path for a cache key."""
        # Sanitize key for filename
        safe_key = key.replace('/', '_').replace('\\', '_')
        return self.cache_dir / f"{safe_key}.json"
    
    def _get_meta_path(self) -> Path:
        """Get path for metadata file."""
        return self.cache_dir / "_metadata.json"
    
    def has(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key.
            
        Returns:
            True if key exists in memory or on disk.
        """
        if key in self._memory:
            return True
        
        if self.persist:
            return self._get_path(key).exists()
        
        return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key.
            
        Returns:
            Cached value or None if not found.
        """
        # Try memory first
        if key in self._memory:
            logger.debug("Cache hit (memory): %s", key)
            return self._memory[key]
        
        # Try disk
        if self.persist:
            path = self._get_path(key)
            if path.exists():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    # Store in memory for faster subsequent access
                    self._memory[key] = data
                    logger.debug("Cache hit (disk): %s", key)
                    return data
                except (json.JSONDecodeError, IOError) as e:
                    logger.warning("Failed to load cache %s: %s", key, e)
        
        logger.debug("Cache miss: %s", key)
        return None
    
    def set(
        self,
        key: str,
        value: Any,
        version: str = None,
        persist: bool = None
    ):
        """
        Set value in cache.
        
        Args:
            key: Cache key.
            value: Value to cache.
            version: Optional version string for metadata.
            persist: Override instance persist setting.
        """
        # Store in memory
        self._memory[key] = value
        
        # Update metadata
        self._metadata[key] = {
            'timestamp': datetime.now().isoformat(),
            'version': version,
        }
        
        # Persist to disk if enabled
        should_persist = persist if persist is not None else self.persist
        if should_persist:
            try:
                path = self._get_path(key)
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(value, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
                logger.debug("Cached to disk: %s", key)
            except (TypeError, IOError) as e:
                logger.warning("Failed to persist cache %s: %s", key, e)
    
    def invalidate(self, pattern: str = None):
        """
        Invalidate cache entries.
        
        Args:
            pattern: If None, invalidates all. Otherwise invalidates keys containing pattern.
        """
        if pattern is None:
            # Clear all
            count = len(self._memory)
            self._memory.clear()
            self._metadata.clear()
            
            if self.persist:
                for f in self.cache_dir.glob("*.json"):
                    if f.name != "_metadata.json":
                        f.unlink()
            
            logger.info("Invalidated all cache entries (%d items)", count)
        else:
            # Clear matching keys
            keys_to_remove = [k for k in self._memory if pattern in k]
            for k in keys_to_remove:
                del self._memory[k]
                self._metadata.pop(k, None)
            
            if self.persist:
                for f in self.cache_dir.glob(f"*{pattern}*.json"):
                    if f.name != "_metadata.json":
                        f.unlink()
            
            logger.info("Invalidated %d cache entries matching '%s'", len(keys_to_remove), pattern)
    
    def get_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dict with cache stats (size, keys, etc.).
        """
        disk_files = list(self.cache_dir.glob("*.json")) if self.persist else []
        
        return {
            'source': self.source,
            'memory_keys': len(self._memory),
            'disk_files': len(disk_files),
            'cache_dir': str(self.cache_dir),
            'keys': list(self._memory.keys()),
        }
    
    def clear_memory(self):
        """Clear only in-memory cache (keeps disk cache)."""
        self._memory.clear()
        logger.debug("Cleared memory cache")


def create_cache_key(analyzer_name: str, version: str, **kwargs) -> str:
    """
    Create a deterministic cache key from analyzer name and parameters.
    
    Args:
        analyzer_name: Name of the analyzer.
        version: Version string.
        **kwargs: Additional parameters to include in key.
        
    Returns:
        Cache key string.
    """
    parts = [analyzer_name, f"v{version}"]
    
    for k, v in sorted(kwargs.items()):
        if v is not None:
            parts.append(f"{k}={v}")
    
    return "_".join(parts)
