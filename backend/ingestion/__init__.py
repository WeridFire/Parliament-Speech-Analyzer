"""
Ingestion - collecting parliamentary speeches.

Replaces `backend.scrapers`. The public entry point is unchanged
(`fetch_all_speeches`), but underneath:

  * sittings are discovered from the official open data instead of by crawling
    listing pages, which fixes Camera's drifting month loop and Senato's
    single-page cap;
  * a shared crawler handles concurrency, per-sitting caching and retries;
  * anti-bot challenges are raised and counted, never mistaken for "no data";
  * every run returns a coverage report alongside the speeches.
"""

import logging
from typing import Optional

import pandas as pd

from backend.config import LEGISLATURE, MONTHS_BACK
from backend.core.cache import ArtifactCache

from .base import ChallengeBlocked, IngestionError, SessionRef, Speech, SpeechSource
from .camera import CameraSource
from .crawler import CrawlReport, crawl
from .rosters import (
    RosterEntry,
    RosterIndex,
    RosterMatch,
    build_roster_index,
    get_roster_index,
    set_roster_index,
    validate_participant,
)
from .senato import SenatoSource
from .transport import HttpTransport, ResilientTransport

logger = logging.getLogger(__name__)

SOURCES = {
    'camera': CameraSource,
    'senate': SenatoSource,
}

__all__ = [
    'fetch_all_speeches',
    'fetch_source_speeches',
    'CameraSource',
    'SenatoSource',
    'SpeechSource',
    'SessionRef',
    'Speech',
    'CrawlReport',
    'crawl',
    'ChallengeBlocked',
    'IngestionError',
    'RosterIndex',
    'RosterEntry',
    'RosterMatch',
    'build_roster_index',
    'get_roster_index',
    'set_roster_index',
    'validate_participant',
    'HttpTransport',
    'ResilientTransport',
]


def fetch_source_speeches(
    chamber: str,
    months_back: int = MONTHS_BACK,
    use_cloudscraper: bool = False,
    limit: Optional[int] = None,
    cache: Optional[ArtifactCache] = None,
    max_workers: Optional[int] = None,
) -> tuple[pd.DataFrame, CrawlReport]:
    """Collect one chamber, returning its speeches and a coverage report."""
    if chamber not in SOURCES:
        raise ValueError(f"Unknown chamber '{chamber}'. Known: {sorted(SOURCES)}")

    source = SOURCES[chamber](use_cloudscraper=use_cloudscraper)
    speeches, report = crawl(
        source, months_back=months_back, cache=cache, limit=limit, max_workers=max_workers
    )

    records = [s.as_record(chamber) for s in speeches]
    return pd.DataFrame(records), report


def fetch_all_speeches(
    source: str = 'both',
    use_cloudscraper: bool = False,
    months_back: int = MONTHS_BACK,
    limit: Optional[int] = None,
    reports: Optional[list] = None,
) -> pd.DataFrame:
    """
    Fetch speeches from one or both chambers.

    Args:
        source: 'senate', 'camera' or 'both'
        use_cloudscraper: route requests through cloudscraper
        months_back: window size
        limit: cap sittings per chamber (smoke runs)
        reports: optional list that receives each chamber's CrawlReport

    Returns:
        DataFrame of speech records (empty if everything was blocked).
    """
    chambers = ['senate', 'camera'] if source == 'both' else [source]
    frames = []

    for chamber in chambers:
        logger.info("Collecting %s...", chamber)
        df, report = fetch_source_speeches(
            chamber, months_back=months_back, use_cloudscraper=use_cloudscraper, limit=limit
        )

        if reports is not None:
            reports.append(report)

        logger.info(report.summary())

        if report.blocked:
            logger.error(
                "%s: %d sittings unreachable behind an anti-bot challenge. "
                "Install Playwright for the browser transport, or run from a "
                "network that is not challenged.",
                chamber, report.blocked,
            )

        if not df.empty:
            frames.append(df)

    if not frames:
        logger.warning("No speeches collected from any chamber")
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    logger.info("Collected %d speeches across %d chamber(s)", len(combined), len(frames))
    return combined
