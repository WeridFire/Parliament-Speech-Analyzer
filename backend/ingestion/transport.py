"""
HTTP transport with explicit anti-bot challenge detection.

senato.it sits behind a CloudFront JavaScript challenge: it answers automated
requests with HTTP 202 and a ~2 KB interstitial saying "we need to verify that
you're not a robot", for plain requests and for cloudscraper alike. The old
scraper treated that as "no sessions found" and returned an empty frame, which
is why the Senate half of the dataset silently shrank to five weeks.

So challenges are detected and raised, never swallowed. An optional browser
transport (Playwright, if installed) can satisfy the challenge; without it the
run reports precisely how many sittings were blocked.
"""

import logging
import random
import time
from typing import Optional

import requests

from .base import ChallengeBlocked

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

DEFAULT_HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'it-IT,it;q=0.9,en;q=0.8',
}

# Markers of a challenge page rather than the document we asked for.
CHALLENGE_MARKERS = (
    'challenge-container',
    "verify that you're not a robot",
    'JavaScript is disabled',
    'Checking your browser',
)

# A challenge body is tiny; a real stenographic report is tens of KB.
CHALLENGE_MAX_BYTES = 8_000


def looks_like_challenge(status: int, body: str) -> bool:
    """True when a response is an anti-bot interstitial rather than content."""
    if len(body) > CHALLENGE_MAX_BYTES:
        return False
    if status == 202 and 'challenge' in body.lower():
        return True
    lowered = body.lower()
    return any(marker.lower() in lowered for marker in CHALLENGE_MARKERS)


class HttpTransport:
    """
    Polite HTTP fetcher: one session, jittered delay, challenge detection.

    Uses a real `requests.Session` so connections are reused across the hundreds
    of sittings a full run touches.
    """

    name = 'http'

    def __init__(
        self,
        use_cloudscraper: bool = False,
        min_delay: float = 0.5,
        timeout: int = 60,
    ):
        self.timeout = timeout
        self.min_delay = min_delay
        self._last_request = 0.0
        self.session = self._build_session(use_cloudscraper)

    @staticmethod
    def _build_session(use_cloudscraper: bool):
        if use_cloudscraper:
            try:
                import cloudscraper
                logger.info("Using cloudscraper transport")
                return cloudscraper.create_scraper()
            except ImportError:
                logger.warning("cloudscraper not installed; falling back to requests")

        session = requests.Session()
        session.headers.update(DEFAULT_HEADERS)
        return session

    def _throttle(self):
        """Space out requests, with jitter so we do not hammer in lockstep."""
        elapsed = time.monotonic() - self._last_request
        wait = self.min_delay - elapsed
        if wait > 0:
            time.sleep(wait + random.uniform(0, 0.3))
        self._last_request = time.monotonic()

    def get(self, url: str) -> str:
        """
        Fetch a URL and return its body.

        Raises:
            ChallengeBlocked: the host served an anti-bot challenge.
            requests.HTTPError: ordinary HTTP failure.
        """
        self._throttle()

        response = self.session.get(url, headers=DEFAULT_HEADERS, timeout=self.timeout)

        # Respect explicit backpressure before treating anything as an error.
        retry_after = response.headers.get('Retry-After')
        if retry_after and response.status_code in (429, 503):
            delay = min(float(retry_after), 30) if retry_after.isdigit() else 5.0
            logger.warning("Rate limited on %s, waiting %.1fs", url, delay)
            time.sleep(delay)
            response = self.session.get(url, headers=DEFAULT_HEADERS, timeout=self.timeout)

        body = response.text

        if looks_like_challenge(response.status_code, body):
            raise ChallengeBlocked(url, response.status_code, "CloudFront JS challenge")

        response.raise_for_status()
        return body


class BrowserTransport:
    """
    Playwright-backed transport for hosts behind a JavaScript challenge.

    Optional: Playwright is not a project dependency. `is_available()` reports
    whether it can be used, so the crawler can fall back to reporting blocked
    sittings instead of failing to import.
    """

    name = 'browser'

    def __init__(self, timeout: int = 60, wait_ms: int = 5000):
        self.timeout = timeout
        self.wait_ms = wait_ms
        self._playwright = None
        self._browser = None

    @staticmethod
    def is_available() -> bool:
        try:
            import playwright.sync_api  # noqa: F401
            return True
        except ImportError:
            return False

    def _ensure_browser(self):
        if self._browser is not None:
            return

        from playwright.sync_api import sync_playwright

        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=True)
        logger.info("Started headless browser for challenged hosts")

    def get(self, url: str) -> str:
        self._ensure_browser()

        page = self._browser.new_page(user_agent=USER_AGENT)
        try:
            page.goto(url, timeout=self.timeout * 1000, wait_until='domcontentloaded')
            # The challenge resolves itself and reloads; give it a moment.
            page.wait_for_timeout(self.wait_ms)
            body = page.content()
        finally:
            page.close()

        if looks_like_challenge(200, body):
            raise ChallengeBlocked(url, 200, "challenge survived browser transport")

        return body

    def close(self):
        if self._browser is not None:
            self._browser.close()
            self._browser = None
        if self._playwright is not None:
            self._playwright.stop()
            self._playwright = None


class ResilientTransport:
    """
    HTTP first, browser only when a challenge demands it.

    This is the transport the sources use: the common case stays cheap, and the
    expensive path engages exactly when the cheap one is refused.
    """

    name = 'resilient'

    def __init__(self, use_cloudscraper: bool = False, allow_browser: bool = True, **kwargs):
        self.http = HttpTransport(use_cloudscraper=use_cloudscraper, **kwargs)
        self.allow_browser = allow_browser
        self._browser: Optional[BrowserTransport] = None
        self.challenges_seen = 0
        self.browser_rescues = 0

    def get(self, url: str) -> str:
        try:
            return self.http.get(url)
        except ChallengeBlocked:
            self.challenges_seen += 1

            if not self.allow_browser or not BrowserTransport.is_available():
                raise

            if self._browser is None:
                self._browser = BrowserTransport()

            logger.info("Challenge on %s, retrying through the browser transport", url)
            body = self._browser.get(url)
            self.browser_rescues += 1
            return body

    def close(self):
        if self._browser is not None:
            self._browser.close()
            self._browser = None
