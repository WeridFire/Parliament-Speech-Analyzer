"""
The shared crawl loop.

Everything that is not chamber-specific parsing lives here: concurrency, polite
rate limiting, per-sitting caching, and coverage accounting. Both sources get it
for free, and improvements land in one place.

Two properties worth calling out:

*Resumable.* Each sitting's parsed speeches are cached individually, so a run
that dies at sitting 400 of 443 costs 43 fetches to finish, not 443. Previously
only the final combined frame was cached, so any interruption threw the lot away.

*Accountable.* The open data tells us how many sittings exist, so a run can
report `known / fetched / parsed / blocked` instead of just handing back however
many speeches it happened to get. A silently empty result is the failure mode
that hid the Senate coverage collapse.
"""

import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Optional

from backend.core.cache import ArtifactCache, CacheKey

from .base import ChallengeBlocked, SessionRef, Speech, SpeechSource

logger = logging.getLogger(__name__)

DEFAULT_WORKERS = 3


@dataclass
class CrawlReport:
    """What a run actually managed to collect, against what exists."""

    chamber: str
    known: int = 0
    fetched: int = 0
    from_cache: int = 0
    parsed: int = 0
    speeches: int = 0
    blocked: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def coverage(self) -> float:
        return (self.parsed / self.known * 100) if self.known else 0.0

    @property
    def ok(self) -> bool:
        return self.known > 0 and self.blocked == 0 and self.parsed > 0

    def summary(self) -> str:
        return (
            f"{self.chamber}: {self.known} sittings known, {self.fetched} fetched "
            f"({self.from_cache} cached), {self.parsed} parsed, {self.speeches} speeches, "
            f"{self.blocked} blocked, {self.failed} failed - {self.coverage:.0f}% coverage"
        )

    def as_dict(self) -> dict:
        return {
            'chamber': self.chamber,
            'known': self.known,
            'fetched': self.fetched,
            'from_cache': self.from_cache,
            'parsed': self.parsed,
            'speeches': self.speeches,
            'blocked': self.blocked,
            'failed': self.failed,
            'coverage_pct': round(self.coverage, 1),
            'errors': self.errors[:20],
        }


class RateLimiter:
    """Global minimum spacing between requests, shared across worker threads."""

    def __init__(self, min_interval: float):
        self.min_interval = min_interval
        self._lock = threading.Lock()
        self._next_allowed = 0.0

    def wait(self):
        import time

        with self._lock:
            now = time.monotonic()
            wait_for = max(0.0, self._next_allowed - now)
            self._next_allowed = max(now, self._next_allowed) + self.min_interval

        if wait_for:
            time.sleep(wait_for)


def _session_key(ref: SessionRef) -> CacheKey:
    return CacheKey(kind='session', source=ref.chamber, digest=ref.session_id)


def crawl(
    source: SpeechSource,
    months_back: int,
    cache: Optional[ArtifactCache] = None,
    max_workers: Optional[int] = None,
    limit: Optional[int] = None,
    use_cache: bool = True,
) -> tuple[list[Speech], CrawlReport]:
    """
    Fetch every sitting the source knows about within the window.

    Args:
        source: chamber implementation
        months_back: how far back to look
        cache: artifact cache for per-sitting results
        max_workers: concurrent fetches (kept small - these are public
            services). Defaults to whatever the source declares it can take.
        limit: stop after N sittings (for smoke runs)
        use_cache: read cached sittings; set False to force refetch

    Returns:
        (speeches, report)
    """
    cache = cache or ArtifactCache()
    report = CrawlReport(chamber=source.chamber)

    if max_workers is None:
        max_workers = getattr(source, 'max_workers', DEFAULT_WORKERS)

    try:
        sessions = source.list_sessions(months_back)
    except Exception as e:
        logger.error("%s: could not list sittings: %s", source.chamber, e)
        report.errors.append(f"list_sessions: {e}")
        return [], report

    if limit:
        sessions = sessions[:limit]

    report.known = len(sessions)
    logger.info("%s: %d sittings to collect", source.chamber, report.known)

    speeches: list[Speech] = []
    pending: list[SessionRef] = []

    # Cache pass first: a resumed run should not touch the network for sittings
    # it already has.
    for ref in sessions:
        cached = cache.load_json(_session_key(ref)) if use_cache else None
        if cached is not None:
            report.from_cache += 1
            report.fetched += 1
            if cached:
                report.parsed += 1
                speeches.extend(Speech(**row) for row in cached)
        else:
            pending.append(ref)

    report.speeches = len(speeches)
    logger.info(
        "%s: %d sittings from cache, %d to fetch",
        source.chamber, report.from_cache, len(pending),
    )

    if not pending:
        return speeches, report

    def fetch_one(ref: SessionRef):
        return ref, source.fetch_session(ref)

    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(fetch_one, ref): ref for ref in pending}

            for future in as_completed(futures):
                ref = futures[future]
                try:
                    _, session_speeches = future.result()
                except ChallengeBlocked as e:
                    report.blocked += 1
                    if report.blocked <= 3:
                        logger.error("%s blocked: %s", ref.key, e)
                    continue
                except Exception as e:
                    report.failed += 1
                    report.errors.append(f"{ref.key}: {e}")
                    logger.warning("%s failed: %s", ref.key, e)
                    continue

                report.fetched += 1
                if session_speeches:
                    report.parsed += 1
                    speeches.extend(session_speeches)

                cache.save_json(
                    _session_key(ref),
                    [vars(s) for s in session_speeches],
                    rows=len(session_speeches),
                )
    finally:
        # A browser transport holds a Chromium subprocess; nothing else here
        # owns a resource worth releasing, so this is a no-op for plain HTTP.
        transport = getattr(source, 'transport', None)
        if transport is not None and hasattr(transport, 'close'):
            transport.close()

    report.speeches = len(speeches)

    if report.blocked:
        logger.error(
            "%s: %d of %d sittings blocked by an anti-bot challenge",
            source.chamber, report.blocked, report.known,
        )

    logger.info(report.summary())
    return speeches, report
