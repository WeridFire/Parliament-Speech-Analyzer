"""
Senate Speech Scraper - Resoconto Stenografico

This module scrapes full parliamentary speeches from senato.it.
"""

import re
import logging
import time
import pandas as pd
from bs4 import BeautifulSoup

from backend.config import LEGISLATURE, MONTHS_BACK
from backend.utils import retry
from backend.config.roles import build_role_pattern, normalize_role, get_role_category
from backend.scrapers.utils import (
    Speech, get_http_client, validate_participant, normalize_name, USER_AGENT
)

logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://www.senato.it"
SESSIONS_LIST_URL = f"{BASE_URL}/lavori/assemblea/resoconti-elenco-cronologico"
SESSION_URL_TEMPLATE = f"{BASE_URL}/show-doc?leg={{leg}}&tipodoc=Resaula&id={{id}}&idoggetto=0&part=doc_dc-ressten_rs"


def get_session_list(legislature: int = LEGISLATURE, use_cloudscraper: bool = False) -> list[dict]:
    """Fetch the list of available Senate sessions from the chronological list."""
    logger.info(f"Fetching session list from {SESSIONS_LIST_URL}...")
    
    http_client = get_http_client(use_cloudscraper)
    
    try:
        response = http_client.get(SESSIONS_LIST_URL, headers={"User-Agent": USER_AGENT}, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        sessions = []
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if 'show-doc' in href and 'Resaula' in href:
                id_match = re.search(r'id=(\d+)', href)
                if id_match:
                    session_id = id_match.group(1)
                    title = link.get_text(strip=True)
                    date = _extract_date_from_context(link, title)
                    
                    sessions.append({
                        'id': session_id,
                        'url': SESSION_URL_TEMPLATE.format(leg=legislature, id=session_id),
                        'title': title,
                        'date': date
                    })
        
        logger.info(f"Found {len(sessions)} sessions")
        return sessions
    except Exception as e:
        logger.error(f"Error fetching session list: {e}")
        return []


def _extract_date_from_context(link_element, title: str) -> str:
    """Try to extract date from the link context or title."""
    date_pattern = r'(\d{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+(\d{4})'
    
    # Try title, then parent text
    text_to_search = [title]
    parent = link_element.find_parent(['tr', 'li', 'div'])
    if parent:
        text_to_search.append(parent.get_text())
        
    months = {
        'gennaio': '01', 'febbraio': '02', 'marzo': '03', 'aprile': '04',
        'maggio': '05', 'giugno': '06', 'luglio': '07', 'agosto': '08',
        'settembre': '09', 'ottobre': '10', 'novembre': '11', 'dicembre': '12'
    }

    for text in text_to_search:
        match = re.search(date_pattern, text, re.IGNORECASE)
        if match:
            day, month, year = match.groups()
            return f"{year}-{months[month.lower()]}-{int(day):02d}"
            
    return "Unknown"


@retry(max_attempts=3, delay=1.0)
def fetch_session_speeches(session_url: str, session_date: str = "", use_cloudscraper: bool = False) -> list[Speech]:
    """Fetch all speeches from a single Senate session's stenographic report."""
    logger.info(f"Fetching speeches from: {session_url}")
    
    http_client = get_http_client(use_cloudscraper)
    response = http_client.get(session_url, headers={"User-Agent": USER_AGENT}, timeout=60)
    response.raise_for_status()
    
    speeches = _parse_speeches_from_html(BeautifulSoup(response.text, 'html.parser'), session_date, session_url, use_cloudscraper=use_cloudscraper)
    logger.info(f"Extracted {len(speeches)} speeches from session")
    return speeches


def _parse_speeches_from_html(soup: BeautifulSoup, session_date: str, session_url: str, use_cloudscraper: bool = False) -> list[Speech]:
    """Parse speech content from the stenographic report HTML."""
    speeches = []
    
    # Pre-compile regex patterns
    patterns = {
        'party': re.compile(r'^([A-Z][A-Z\-\']+(?:\s+[A-Z][A-Z\-\']+)?)\s*\(([^)]+)\)\.\s+(.+)', re.DOTALL),
        'pres': re.compile(r'^(PRESIDENTE|PRESIDENTESSA)\.\s+(.+)', re.DOTALL),
        'simple': re.compile(r'^([A-Z][A-Z\-\']+(?:\s+[A-Z][A-Z\-\']+){0,2})\.\s+(.+)', re.DOTALL),
        'role': re.compile(rf'^([A-Z][A-Z\-\']+(?:\s+[A-Z][A-Z\-\']+)?),\s*({build_role_pattern()})[^.]*\.\s*(.+)', re.IGNORECASE | re.DOTALL),
        'note': re.compile(r'\(([^)]+)\)')
    }

    for p in soup.find_all('p'):
        text = p.get_text(strip=True)
        if not text or len(text) < 10:
            continue

        speaker, party, role, role_cat, speech_text = None, "", "", "", None

        # 1. Match SURNAME (PARTY). text
        m = patterns['party'].match(text)
        if m:
            speaker, party, speech_text = m.groups()
            speaker, party, speech_text = speaker.strip(), party.strip(), speech_text.strip()
            
        # 2. Match PRESIDENTE. text
        elif patterns['pres'].match(text):
            m = patterns['pres'].match(text)
            speaker, speech_text = m.groups()
            speaker, speech_text = speaker.strip(), speech_text.strip()
            role, role_cat = "presidente", "presidenza"
            
        # 3. Match SURNAME, role. text
        elif patterns['role'].match(text):
            m = patterns['role'].match(text)
            speaker, raw_role, speech_text = m.groups()
            speaker, speech_text = speaker.strip(), speech_text.strip()
            role = normalize_role(raw_role)
            role_cat = get_role_category(role)
            
        # 4. Match SURNAME. text
        elif patterns['simple'].match(text):
            m = patterns['simple'].match(text)
            pot_speaker, pot_text = m.groups()
            if len(pot_speaker) <= 30 and pot_speaker.isupper():
                speaker, speech_text = pot_speaker.strip(), pot_text.strip()

        if speaker and speech_text:
            notes = patterns['note'].findall(speech_text)
            clean_text = patterns['note'].sub('', speech_text).strip()
            
            if len(clean_text) > 30:
                profile_url = ""
                # Validate/Enrich
                if role_cat != "presidenza":
                    info = validate_participant(speaker, party, use_cloudscraper=use_cloudscraper)
                    if info:
                        speaker, party, profile_url = info['name'], info['party'], info['profile_url']
                    elif role_cat != "governo": # Require validation unless Govt/Pres
                         continue

                speeches.append(Speech(
                    speaker=speaker, party=party, text=clean_text, date=session_date,
                    session_number=0, url=session_url, notes=notes,
                    role=role, role_category=role_cat, profile_url=profile_url
                ))

    return speeches


def fetch_speeches(use_cloudscraper: bool = False) -> pd.DataFrame:
    """Main function to fetch speeches from all sessions within MONTHS_BACK."""
    from datetime import datetime, timedelta
    
    logger.info(f"Starting Senate speech scraping for last {MONTHS_BACK} months...")
    
    sessions = get_session_list(LEGISLATURE, use_cloudscraper=use_cloudscraper)
    if not sessions:
        return pd.DataFrame()
    
    # Filter sessions by date (within MONTHS_BACK)
    cutoff_date = datetime.now() - timedelta(days=MONTHS_BACK * 30)
    filtered_sessions = []
    for session in sessions:
        try:
            session_date = datetime.strptime(session['date'], '%Y-%m-%d')
            if session_date >= cutoff_date:
                filtered_sessions.append(session)
        except (ValueError, TypeError):
            # If date parsing fails, include the session
            filtered_sessions.append(session)
    
    logger.info(f"Filtered to {len(filtered_sessions)} sessions within {MONTHS_BACK} months")
    
    all_res = []
    for session in filtered_sessions:
        speeches = fetch_session_speeches(session['url'], session.get('date', 'Unknown'), use_cloudscraper)
        
        for s in speeches:
            group = s.party if s.party and s.speaker not in ['PRESIDENTE', 'PRESIDENTESSA'] else (
                 f"Governo" if s.role_category == "governo" else ("Presidenza" if s.role else 'Unknown Group')
            )
            
            # Skip procedural speeches
            if group == "Presidenza" or s.speaker in ['PRESIDENTE', 'PRESIDENTESSA']:
                continue
                
            unique_speaker = f"{s.speaker} [{s.party}]" if (s.party and group != "Presidenza" and group != "Governo") else s.speaker
            
            all_res.append({
                'date': s.date, 'deputy': unique_speaker, 'speaker_base': s.speaker,
                'group': group, 'text': s.text, 'source': 'senate', 'url': s.url,
                'role': s.role, 'role_category': s.role_category, 'profile_url': s.profile_url
            })
        
        time.sleep(1)
            
    df = pd.DataFrame(all_res)
    logger.info(f"Scraped {len(df)} speeches total from {len(filtered_sessions)} sessions")
    return df

if __name__ == "__main__":
    # Test block
    logging.basicConfig(level=logging.INFO)
    print(fetch_speeches())
