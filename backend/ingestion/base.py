"""
Ingestion contracts: what a chamber source must provide.

Both chambers differ only in *how* they answer two questions - which sittings
exist, and what was said in one. Everything else (concurrency, caching, retries,
rate limiting, coverage accounting) is shared by the crawler, so it is written
once and both sources inherit it.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional, Protocol, runtime_checkable


class IngestionError(Exception):
    """Base class for ingestion failures."""


class ChallengeBlocked(IngestionError):
    """
    The host served an anti-bot challenge instead of the document.

    Raised rather than swallowed on purpose: a blocked fetch that silently
    returns nothing is how the Senate dataset quietly shrank to five weeks of
    coverage. Callers record it and report it.
    """

    def __init__(self, url: str, status: int, hint: str = ""):
        self.url = url
        self.status = status
        self.hint = hint
        super().__init__(f"anti-bot challenge at {url} (HTTP {status}){f': {hint}' if hint else ''}")


@dataclass(frozen=True)
class SessionRef:
    """
    A sitting that is known to exist, before any document is fetched.

    Sourced from the official open data, so the count of these is the
    denominator for coverage: known vs fetched vs parsed.
    """

    chamber: str            # 'camera' | 'senate'
    session_id: str         # chamber-native id ('677', '24350')
    session_date: date
    number: Optional[int] = None
    url: str = ""
    label: str = ""

    @property
    def key(self) -> str:
        """Stable cache key for this sitting's document."""
        return f"{self.chamber}_{self.session_id}"

    @property
    def iso_date(self) -> str:
        return self.session_date.isoformat()


@dataclass
class Speech:
    """A single speech extracted from a stenographic report."""

    speaker: str
    party: str
    text: str
    date: str
    url: str = ""
    session_id: str = ""
    notes: list = field(default_factory=list)
    role: str = ""
    role_category: str = ""
    profile_url: str = ""
    # How the speaker was resolved against the official roster; lets the run
    # report distinguish confident attributions from guesses.
    match_strategy: str = ""
    match_ambiguous: bool = False

    def as_record(self, chamber: str) -> dict:
        """Flatten to the row shape the pipeline consumes."""
        group = self.party or ("Governo" if self.role_category == "governo" else "Unknown Group")
        unique_speaker = f"{self.speaker} [{self.party}]" if self.party else self.speaker

        return {
            'date': self.date,
            'deputy': unique_speaker,
            'speaker_base': self.speaker,
            'group': group,
            'text': self.text,
            'source': chamber,
            'url': self.url,
            'session_id': self.session_id,
            'role': self.role,
            'role_category': self.role_category,
            'profile_url': self.profile_url,
            'match_strategy': self.match_strategy,
            'match_ambiguous': self.match_ambiguous,
        }


@runtime_checkable
class SpeechSource(Protocol):
    """What each chamber implements. Two methods, nothing else."""

    chamber: str

    # How many sittings this chamber may be fetched in parallel. A source that
    # needs the browser transport must declare 1: Playwright's synchronous API
    # is bound to the thread that started it, so a shared browser cannot be
    # driven from a pool. Declaring it here keeps the constraint next to the
    # source that has it, rather than in the crawl loop.
    max_workers: int

    def list_sessions(self, months_back: int) -> list[SessionRef]:
        """Sittings held within the window, newest first."""
        ...

    def fetch_session(self, ref: SessionRef) -> list[Speech]:
        """Speeches from one sitting's stenographic report."""
        ...
