"""
Official member registers, and the matcher that resolves scraped names to them.

Two problems this solves.

*Source*: rosters used to be scraped by walking A-Z index pages on both sites,
which is slow, brittle, and (for senato.it) now behind a bot challenge. The open
data publishes the same register.

*Matching*: stenographic reports name speakers inconsistently - "MALAN",
"Giuseppe Conte", "CONTE Giuseppe" - against a register that stores "Cognome
Nome". The old matcher scanned every roster name up to three times per speech
and, when several people shared a surname, silently returned the first one. This
one indexes once, and reports how a match was reached so ambiguous attributions
are visible in the run report instead of invisible in the data.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

from backend.config import LEGISLATURE
from backend.core.cache import ArtifactCache, CacheKey

from .sparql import (
    CAMERA_ROSTER,
    SENATO_ROSTER,
    camera_client,
    legislature_uri,
    senato_client,
)

logger = logging.getLogger(__name__)

ROSTER_CACHE_DAYS = 30


def normalize_name(name: str) -> str:
    """Collapse whitespace; title-case shouted names ('MARIO ROSSI' -> 'Mario Rossi')."""
    name = ' '.join(str(name).split())
    return name.title() if name.isupper() else name


@dataclass(frozen=True)
class RosterEntry:
    """One member of parliament as the official register describes them."""

    full_name: str          # "Cognome Nome"
    surname: str
    first_name: str
    party: str
    chamber: str
    profile_url: str = ""


@dataclass(frozen=True)
class RosterMatch:
    """Result of resolving a scraped name, with provenance."""

    name: str
    party: str
    profile_url: str
    strategy: str           # exact | caseless | surname | reversed | party-disambiguated
    ambiguous: bool = False

    def as_dict(self) -> dict:
        return {
            'name': self.name,
            'party': self.party,
            'profile_url': self.profile_url,
            'strategy': self.strategy,
            'ambiguous': self.ambiguous,
        }


class RosterIndex:
    """
    Indexed lookup over the combined register.

    Built once per run; every lookup is a dict hit rather than a scan over ~950
    names.
    """

    def __init__(self, entries: list[RosterEntry]):
        self.entries = entries
        self._by_exact: dict[str, RosterEntry] = {}
        self._by_caseless: dict[str, RosterEntry] = {}
        self._by_surname: dict[str, list[RosterEntry]] = defaultdict(list)

        for entry in entries:
            self._by_exact.setdefault(entry.full_name, entry)
            self._by_caseless.setdefault(entry.full_name.lower(), entry)
            self._by_surname[entry.surname.lower()].append(entry)

    def __len__(self) -> int:
        return len(self.entries)

    @property
    def all_names(self) -> set[str]:
        return set(self._by_exact)

    def match(self, name: str, party: str = "") -> Optional[RosterMatch]:
        """
        Resolve a scraped speaker name, or return None if it is not a member.

        Returning None is meaningful: it rejects parser false positives (a stray
        capitalised word read as a speaker).
        """
        if not name:
            return None

        if name.upper() in ('PRESIDENTE', 'PRESIDENTESSA'):
            return None

        normalized = normalize_name(name)

        entry = self._by_exact.get(normalized)
        if entry:
            return self._as_match(entry, party, 'exact')

        entry = self._by_caseless.get(normalized.lower())
        if entry:
            return self._as_match(entry, party, 'caseless')

        return self._match_by_parts(normalized, party)

    def _match_by_parts(self, normalized: str, party: str) -> Optional[RosterMatch]:
        """Surname-only and reversed-order forms."""
        parts = normalized.split()

        if len(parts) == 1:
            candidates = self._by_surname.get(parts[0].lower(), [])
            return self._resolve(candidates, party, 'surname')

        # "Giuseppe Conte" (Camera style) or "Conte Giuseppe" (register style)
        first, last = parts[0].lower(), parts[-1].lower()

        for surname, given in ((last, first), (first, last)):
            candidates = [
                e for e in self._by_surname.get(surname, [])
                if e.first_name.lower().startswith(given)
            ]
            if candidates:
                return self._resolve(candidates, party, 'reversed')

        # Surname matched but the given name did not - still better than nothing
        for surname in (last, first):
            candidates = self._by_surname.get(surname, [])
            if candidates:
                return self._resolve(candidates, party, 'surname')

        return None

    def _resolve(self, candidates: list[RosterEntry], party: str, strategy: str) -> Optional[RosterMatch]:
        """Pick among candidates, preferring a party match and flagging ties."""
        if not candidates:
            return None

        if len(candidates) == 1:
            return self._as_match(candidates[0], party, strategy)

        if party:
            for candidate in candidates:
                if party.lower() in (candidate.party or '').lower():
                    return self._as_match(candidate, party, 'party-disambiguated')

        logger.debug(
            "Ambiguous roster match: %s -> %s",
            candidates[0].surname, [c.full_name for c in candidates],
        )
        return self._as_match(candidates[0], party, strategy, ambiguous=True)

    @staticmethod
    def _as_match(entry: RosterEntry, party: str, strategy: str, ambiguous: bool = False) -> RosterMatch:
        return RosterMatch(
            name=entry.full_name,
            party=entry.party or party,   # the register wins over the scraped label
            profile_url=entry.profile_url,
            strategy=strategy,
            ambiguous=ambiguous,
        )


# =============================================================================
# FETCHING
# =============================================================================

def _clean_group_label(label: str) -> str:
    """'PARTITO DEMOCRATICO - ... (07.01.2025)' -> without the trailing date."""
    if not label:
        return ""
    return label.split(' (')[0].strip()


def fetch_camera_roster(legislature: int = LEGISLATURE) -> list[RosterEntry]:
    """Deputies of a legislature, with their current parliamentary group."""
    logger.info("Fetching Camera roster from open data (leg %d)...", legislature)

    rows = camera_client().select(
        CAMERA_ROSTER.format(legislature_uri=legislature_uri(legislature))
    )

    # A deputy has one adesione per group they ever joined; the one still open
    # (no motivoTermine) is their current group.
    best: dict[str, dict] = {}
    for row in rows:
        uri = row['deputato']
        current = not row.get('fine')
        existing = best.get(uri)
        if existing is None or (current and not existing['current']):
            best[uri] = {
                'surname': row['cognome'],
                'first_name': row['nome'],
                'group': _clean_group_label(row.get('gruppo', '')),
                'current': current,
                'uri': uri,
            }

    entries = [
        RosterEntry(
            full_name=normalize_name(f"{d['surname']} {d['first_name']}"),
            surname=normalize_name(d['surname']),
            first_name=normalize_name(d['first_name']),
            party=d['group'],
            chamber='camera',
            profile_url=d['uri'],
        )
        for d in best.values()
    ]

    logger.info("Camera roster: %d deputies", len(entries))
    return entries


def fetch_senato_roster(legislature: int = LEGISLATURE) -> list[RosterEntry]:
    """
    Senators of a legislature.

    Group affiliation is not exposed on the same path as Camera's, so party is
    left empty here and filled from the `(GROUP)` marker the stenographic report
    itself carries next to each speaker.
    """
    logger.info("Fetching Senato roster from open data (leg %d)...", legislature)

    rows = senato_client().select(SENATO_ROSTER.format(leg=legislature))

    entries = [
        RosterEntry(
            full_name=normalize_name(f"{row['cognome']} {row['nome']}"),
            surname=normalize_name(row['cognome']),
            first_name=normalize_name(row['nome']),
            party="",
            chamber='senate',
            profile_url=row['senatore'],
        )
        for row in rows
    ]

    logger.info("Senato roster: %d senators", len(entries))
    return entries


def build_roster_index(
    legislature: int = LEGISLATURE,
    cache: Optional[ArtifactCache] = None,
    force_refresh: bool = False,
) -> RosterIndex:
    """Fetch (or reuse) both registers and index them."""
    cache = cache or ArtifactCache()
    key = CacheKey(kind='rosters', source=f'leg{legislature}')

    if not force_refresh:
        cached = cache.load_json(key, max_age_days=ROSTER_CACHE_DAYS)
        if cached:
            logger.info("Loaded roster from cache (%d members)", len(cached))
            return RosterIndex([RosterEntry(**row) for row in cached])

    entries: list[RosterEntry] = []
    for fetch in (fetch_camera_roster, fetch_senato_roster):
        try:
            entries.extend(fetch(legislature))
        except Exception as e:
            logger.error("Roster fetch failed (%s): %s", fetch.__name__, e)

    if entries:
        cache.save_json(key, [vars(e) for e in entries], rows=len(entries))

    return RosterIndex(entries)


# =============================================================================
# MODULE-LEVEL CONVENIENCE
# =============================================================================

_index: Optional[RosterIndex] = None


def get_roster_index(force_refresh: bool = False) -> RosterIndex:
    """Process-wide roster index, built on first use."""
    global _index
    if _index is None or force_refresh:
        _index = build_roster_index(force_refresh=force_refresh)
    return _index


def set_roster_index(index: Optional[RosterIndex]):
    """Inject an index (tests, or a pre-built one from the caller)."""
    global _index
    _index = index


def rosters_available() -> bool:
    """Whether a non-empty register is loaded."""
    return _index is not None and len(_index) > 0


def validate_participant(name: str, party: str = "", **_ignored) -> Optional[dict]:
    """
    Resolve a scraped speaker against the register.

    Kept as a function for the parsers, which call it per candidate speaker.
    """
    match = get_roster_index().match(name, party)
    return match.as_dict() if match else None
