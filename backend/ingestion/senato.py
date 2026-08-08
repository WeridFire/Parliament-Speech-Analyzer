"""
Senato della Repubblica source.

Sittings come from `osr:SedutaAssemblea`, which is the fix for the coverage
collapse: the previous scraper read a single un-paginated listing page, so a
15-month window returned about five weeks of speeches. The open data lists all
443 assembly sittings of legislature 19.

Speech text still has to come from senato.it, which currently answers automated
requests with a CloudFront JavaScript challenge. The transport detects that and
raises, so blocked sittings appear in the run report instead of quietly becoming
an empty dataset - and if Playwright is installed, the browser transport can
satisfy the challenge.
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
from .sparql import SENATO_SESSIONS, senato_client
from .transport import ResilientTransport

logger = logging.getLogger(__name__)

BASE_URL = "https://www.senato.it"
DOCUMENT_URL = (
    BASE_URL + "/show-doc?leg={leg}&tipodoc=Resaula&id={session_id}"
    "&idoggetto=0&part=doc_dc-ressten_rs"
)

SESSION_URI_RE = re.compile(r"sedutaassemblea/(\d+)")

MIN_SPEECH_CHARS = 30


class SenatoSource:
    """Speeches from senato.it stenographic reports."""

    chamber = 'senate'

    # Serial by necessity, not by politeness. senato.it answers with a JS
    # challenge, so fetches may go through Playwright, whose synchronous API
    # can only be driven from the thread that started the browser. One worker
    # means one thread for the whole run, which is the condition that holds.
    max_workers = 1

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
        since = _since_iso(months_back)

        rows = senato_client().select(SENATO_SESSIONS.format(
            leg=self.legislature,
            since=since,
        ))

        sessions = []
        for row in rows:
            match = SESSION_URI_RE.search(row['seduta'])
            parsed = parse_date(row['data'])
            if not match or parsed is None:
                continue

            session_id = match.group(1)
            sessions.append(SessionRef(
                chamber=self.chamber,
                session_id=session_id,
                session_date=parsed.date(),
                number=int(row['numero']) if row.get('numero', '').isdigit() else None,
                url=DOCUMENT_URL.format(leg=self.legislature, session_id=session_id),
                label=f"Seduta n. {row.get('numero', '?')}",
            ))

        sessions.sort(key=lambda s: s.session_date, reverse=True)
        logger.info("Senato: %d assembly sittings since %s", len(sessions), since)
        return sessions

    # -- fetching ------------------------------------------------------------

    def fetch_session(self, ref: SessionRef) -> list[Speech]:
        html = self.transport.get(ref.url)
        speeches = parse_senato_html(html, ref)
        logger.debug("Senato sitting %s: %d speeches", ref.session_id, len(speeches))
        return speeches


def _since_iso(months_back: int) -> str:
    from datetime import date

    from dateutil.relativedelta import relativedelta

    return (date.today() - relativedelta(months=months_back)).isoformat()


def parse_senato_html(html: str, ref: SessionRef) -> list[Speech]:
    """
    Extract speeches from a Senato stenographic report.

    Senato reports are flatter than Camera's: each speech is a <p> beginning with
    the speaker in caps, optionally followed by their group in parentheses.
    """
    soup = BeautifulSoup(html, 'html.parser')
    roster = get_roster_index()

    role_pattern = build_role_pattern()
    patterns = {
        'party': re.compile(r"^([A-Z][A-Z\-']+(?:\s+[A-Z][A-Z\-']+)?)\s*\(([^)]+)\)\.\s+(.+)", re.DOTALL),
        'president': re.compile(r"^(PRESIDENTE|PRESIDENTESSA)\.\s+(.+)", re.DOTALL),
        'role': re.compile(
            rf"^([A-Z][A-Z\-']+(?:\s+[A-Z][A-Z\-']+)?),\s*({role_pattern})[^.]*\.\s*(.+)",
            re.IGNORECASE | re.DOTALL,
        ),
        'simple': re.compile(r"^([A-Z][A-Z\-']+(?:\s+[A-Z][A-Z\-']+){0,2})\.\s+(.+)", re.DOTALL),
    }
    note_re = re.compile(r'\(([^)]+)\)')

    speeches = []

    for paragraph in soup.find_all('p'):
        text = paragraph.get_text(strip=True)
        if not text or len(text) < 10:
            continue

        speaker, party, role, role_category, body = _match_speaker(text, patterns)
        if not speaker or not body:
            continue

        if role_category == 'presidenza':
            continue  # procedural

        notes = note_re.findall(body)
        clean = note_re.sub('', body).strip()
        if len(clean) <= MIN_SPEECH_CHARS:
            continue

        match_result = roster.match(speaker, party)

        if not match_result:
            if role_category != 'governo':
                continue
            speeches.append(Speech(
                speaker=speaker, party='Governo', text=clean, date=ref.iso_date,
                url=ref.url, session_id=ref.session_id, notes=notes,
                role=role, role_category=role_category, match_strategy='government',
            ))
            continue

        speeches.append(Speech(
            speaker=match_result.name,
            # The register does not expose senators' groups, so the group marker
            # printed next to the speaker in the report is the better source.
            party=party or match_result.party,
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
        ))

    return speeches


def _match_speaker(text: str, patterns) -> tuple:
    """Return (speaker, party, role, role_category, body) for the first shape that fits."""
    if match := patterns['party'].match(text):
        speaker, party, body = match.groups()
        return speaker.strip(), party.strip(), "", "", body.strip()

    if match := patterns['president'].match(text):
        speaker, body = match.groups()
        return speaker.strip(), "", "presidente", "presidenza", body.strip()

    if match := patterns['role'].match(text):
        speaker, raw_role, body = match.groups()
        role = normalize_role(raw_role)
        return speaker.strip(), "", role, get_role_category(role), body.strip()

    if match := patterns['simple'].match(text):
        speaker, body = match.groups()
        if len(speaker) <= 30 and speaker.isupper():
            return speaker.strip(), "", "", "", body.strip()

    return None, "", "", "", None
