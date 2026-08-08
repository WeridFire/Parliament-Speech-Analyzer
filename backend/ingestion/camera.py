"""
Camera dei Deputati source.

Sittings come from the open data (`ocd:seduta`), which removes the old
month-by-month crawl that stepped back in 30-day hops - over a 15-month window
that drift re-requested some months and skipped others entirely.

The sitting number in the `seduta.rdf/s19_<n>` URI is the `idSeduta` the public
site uses, so the stenographic URL is built directly and no listing page has to
be scraped to find it. Verified against the live site.

The HTML parsing is carried over from the previous scraper: that part worked.
"""

import logging
import re
from typing import Optional

from bs4 import BeautifulSoup

from backend.config import LEGISLATURE
from backend.config.roles import build_role_pattern, get_role_category, normalize_role
from backend.utils.dates import parse_date

from .base import SessionRef, Speech
from .rosters import get_roster_index
from .sparql import CAMERA_SESSIONS, camera_client, legislature_uri
from .transport import ResilientTransport

logger = logging.getLogger(__name__)

BASE_URL = "https://www.camera.it"
STENOGRAPHIC_URL = BASE_URL + "/leg{leg}/410?idSeduta={number:04d}&tipo=stenografico"

SESSION_URI_RE = re.compile(r"seduta\.rdf/s(\d+)_(\d+)")

MIN_SPEECH_CHARS = 30


class CameraSource:
    """Speeches from camera.it stenographic reports."""

    chamber = 'camera'

    # camera.it serves plain HTTP without a challenge, so a small pool is safe.
    max_workers = 3

    def __init__(
        self,
        legislature: int = LEGISLATURE,
        transport: Optional[ResilientTransport] = None,
        use_cloudscraper: bool = False,
    ):
        self.legislature = legislature
        self.transport = transport or ResilientTransport(use_cloudscraper=use_cloudscraper)

    # -- discovery -----------------------------------------------------------

    def list_sessions(self, months_back: int) -> list[SessionRef]:
        """Assembly sittings within the window, from the open data."""
        since = _since_yyyymmdd(months_back)

        rows = camera_client().select(CAMERA_SESSIONS.format(
            legislature_uri=legislature_uri(self.legislature),
            leg=self.legislature,
            since=since,
        ))

        sessions = {}
        for row in rows:
            match = SESSION_URI_RE.search(row['seduta'])
            parsed = parse_date(row['date'])
            if not match or parsed is None:
                continue

            number = int(match.group(2))
            sessions[number] = SessionRef(
                chamber=self.chamber,
                session_id=str(number),
                session_date=parsed.date(),
                number=number,
                url=STENOGRAPHIC_URL.format(leg=self.legislature, number=number),
                label=row.get('label', ''),
            )

        ordered = sorted(sessions.values(), key=lambda s: s.session_date, reverse=True)
        logger.info("Camera: %d assembly sittings since %s", len(ordered), since)
        return ordered

    # -- fetching ------------------------------------------------------------

    def fetch_session(self, ref: SessionRef) -> list[Speech]:
        html = self.transport.get(ref.url)
        speeches = parse_camera_html(html, ref)
        logger.debug("Camera sitting %s: %d speeches", ref.session_id, len(speeches))
        return speeches


def _since_yyyymmdd(months_back: int) -> str:
    """Window start as the plain YYYYMMDD string Camera stores dates in."""
    from datetime import date

    from dateutil.relativedelta import relativedelta

    start = date.today() - relativedelta(months=months_back)
    return start.strftime('%Y%m%d')


def parse_camera_html(html: str, ref: SessionRef) -> list[Speech]:
    """
    Extract speeches from a Camera stenographic report.

    Three shapes appear in these documents, tried in order:
      1. speaker as an <a> link (the standard modern format);
      2. "SURNAME, ministro ... . text" (government roles);
      3. "SURNAME (GROUP). text".
    """
    soup = BeautifulSoup(html, 'html.parser')
    content = soup.find('div', class_='sezione') or soup.find('main') or soup

    role_pattern = build_role_pattern()
    role_fallback = re.compile(
        rf"^([A-Z][A-Z\-']+(?:\s+[A-Z][A-Z\-']+)?),\s*({role_pattern})[^.]*\.\s*(.+)",
        re.IGNORECASE | re.DOTALL,
    )
    party_fallback = re.compile(
        r"^([A-Z][A-Z\-']+(?:\s+[A-Z][A-Z\-']+)?)\s*\(([^)]+)\)\.\s+(.+)",
        re.DOTALL,
    )

    roster = get_roster_index()
    speeches: list[Speech] = []

    for block in content.find_all(['p', 'div']):
        text = block.get_text(separator=' ', strip=True)
        if not text or len(text) < MIN_SPEECH_CHARS:
            continue

        speech = (
            _parse_linked_speaker(block, ref, role_pattern, roster)
            or _parse_with_pattern(text, ref, role_fallback, roster, kind='role')
            or _parse_with_pattern(text, ref, party_fallback, roster, kind='party')
        )
        if speech:
            speeches.append(speech)

    return speeches


def _split_notes(text: str) -> tuple[str, list]:
    """Separate parenthetical stage directions - (Applausi) - from the speech."""
    notes = re.findall(r'\(([^)]+)\)', text)
    clean = re.sub(r'\([^)]*\)', '', text).strip()
    return clean, notes


def _parse_linked_speaker(block, ref: SessionRef, role_pattern: str, roster) -> Optional[Speech]:
    """Standard format: the speaker's name is a link into their profile."""
    for link in block.find_all('a'):
        name = link.get_text(strip=True)
        if not name or len(name) < 3 or not name[0].isupper():
            continue

        full_text = block.get_text()
        position = full_text.find(name)
        if position == -1:
            continue

        remainder = full_text[position + len(name):].strip()

        party = ""
        if match := re.match(r'\s*\(([^)]+)\)', remainder):
            party = match.group(1).strip()
            remainder = remainder[match.end():].strip()

        role, role_category = "", ""
        if match := re.match(rf'^\s*,\s*({role_pattern})[^.]*', remainder, re.IGNORECASE):
            role = normalize_role(match.group(1))
            role_category = get_role_category(role)
            remainder = remainder[match.end():].strip()

        remainder = re.sub(r'^[\.,:]\s*', '', remainder)
        if len(remainder) <= MIN_SPEECH_CHARS:
            continue

        clean, notes = _split_notes(remainder)
        if len(clean) <= 20:
            continue

        if name.upper() in ('PRESIDENTE', 'PRESIDENTESSA'):
            return None  # procedural, dropped downstream anyway

        match_result = roster.match(name, party)
        if not match_result:
            return None

        return Speech(
            speaker=match_result.name,
            party=match_result.party or party,
            text=clean,
            date=ref.iso_date,
            url=ref.url,
            session_id=ref.session_id,
            notes=notes,
            role=role,
            role_category=role_category,
            profile_url=match_result.profile_url,
            match_strategy=match_result.strategy,
            match_ambiguous=match_result.ambiguous,
        )

    return None


def _parse_with_pattern(text: str, ref: SessionRef, pattern, roster, kind: str) -> Optional[Speech]:
    """Fallback shapes where the speaker is plain uppercase text."""
    match = pattern.match(text)
    if not match:
        return None

    speaker, middle, body = match.groups()

    # Uppercase-only guard: without it, prose like "Concludo, ministro..." parses
    # as a speaker.
    if not speaker.isupper():
        return None

    role, role_category, party = "", "", ""
    if kind == 'role':
        role = normalize_role(middle)
        role_category = get_role_category(role)
    else:
        party = middle.strip()

    clean, notes = _split_notes(body)
    if len(clean) <= 20:
        return None

    match_result = roster.match(speaker, party)

    if not match_result:
        # Ministers speak without being in the chamber's register; keep them only
        # when the report itself identified a government role.
        if role_category != 'governo':
            return None
        return Speech(
            speaker=speaker, party='Governo', text=clean, date=ref.iso_date,
            url=ref.url, session_id=ref.session_id, notes=notes,
            role=role, role_category=role_category, match_strategy='government',
        )

    return Speech(
        speaker=match_result.name,
        party=match_result.party or party or ('Governo' if role_category == 'governo' else ''),
        text=clean,
        date=ref.iso_date,
        url=ref.url,
        session_id=ref.session_id,
        notes=notes,
        role=role,
        role_category=role_category,
        profile_url=match_result.profile_url,
        match_strategy=match_result.strategy,
        match_ambiguous=match_result.ambiguous,
    )
