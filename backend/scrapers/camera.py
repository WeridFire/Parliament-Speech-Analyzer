"""
Camera dei Deputati Speech Scraper - Resoconto Stenografico

This module scrapes full parliamentary speeches from camera.it.
"""

import re
import logging
import time
from datetime import datetime, timedelta
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
BASE_URL = "https://www.camera.it"
DOCS_URL = "https://documenti.camera.it"

# URL templates
SESSION_LIST_URL = f"{DOCS_URL}/apps/commonServices/getDocumento.ashx?idLegislatura={{leg}}&sezione=assemblea&tipoDoc=elenco&annomese={{year}},{{month}}"
STENOGRAPHIC_URL = f"{BASE_URL}/leg{{leg}}/410?idSeduta={{session_id}}&tipo=stenografico"


def get_session_list(legislature: int = LEGISLATURE, months_back: int = MONTHS_BACK, use_cloudscraper: bool = False) -> list[dict]:
    """Fetch the list of available Chamber sessions from recent months."""
    logger.info(f"Fetching session list from camera.it for last {months_back} months...")
    
    http_client = get_http_client(use_cloudscraper)
    sessions = []
    current_date = datetime.now()
    
    for i in range(months_back):
        target_date = current_date - timedelta(days=30 * i)
        year, month = target_date.year, target_date.month
        
        try:
            url = SESSION_LIST_URL.format(leg=legislature, year=year, month=month)
            response = http_client.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if 'idSeduta=' in href and 'stenografico' in href.lower():
                    m = re.search(r'idSeduta=(\d+)', href)
                    if m:
                        session_id = m.group(1)
                        if any(s['id'] == session_id for s in sessions): continue
                        
                        sessions.append({
                            'id': session_id,
                            'url': STENOGRAPHIC_URL.format(leg=legislature, session_id=session_id),
                            'date': _extract_date_from_context(link, year, month)
                        })
        except Exception as e:
            logger.warning(f"Error fetching sessions for {month}/{year}: {e}")
            continue
        
        time.sleep(0.5)

    sessions.sort(key=lambda x: x.get('date', ''))
    logger.info(f"Found {len(sessions)} sessions from camera.it")
    return sessions


def _extract_date_from_context(link_element, year: int, month: int) -> str:
    """Try to extract date from the link context or text."""
    text = link_element.get_text(strip=True)
    
    # Try pattern: "Seduta n. XXX Lunedì DD"
    if m := re.search(r'(\d{1,2})\s*$', text):
        return f"{year}-{month:02d}-{int(m.group(1)):02d}"
    
    # Try parent elements
    parent = link_element.find_parent(['tr', 'li', 'div'])
    if parent:
        parent_text = parent.get_text()
        m = re.search(r'(Lunedì|Martedì|Mercoledì|Giovedì|Venerdì|Sabato|Domenica)\s+(\d{1,2})', parent_text, re.IGNORECASE)
        if m:
            return f"{year}-{month:02d}-{int(m.group(2)):02d}"
    
    return f"{year}-{month:02d}-01"


@retry(max_attempts=3, delay=1.0)
def fetch_session_speeches(session_url: str, session_date: str = "", use_cloudscraper: bool = False) -> list[Speech]:
    """Fetch all speeches from a single Chamber session's stenographic report."""
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
    main_content = soup.find('div', class_='sezione') or soup.find('main') or soup
    
    # Patterns
    role_pattern_str = build_role_pattern()
    role_fallback_pattern = re.compile(rf'^([A-Z][A-Z\-\']+(?:\s+[A-Z][A-Z\-\']+)?),\s*({role_pattern_str})[^.]*\.\s*(.+)', re.IGNORECASE | re.DOTALL)
    party_fallback_pattern = re.compile(r'^([A-Z][A-Z\-\']+(?:\s+[A-Z][A-Z\-\']+)?)\s*\(([^)]+)\)\.\s+(.+)', re.DOTALL)

    for p in main_content.find_all(['p', 'div']):
        text = p.get_text(separator=' ', strip=True)
        if not text or len(text) < 30: continue
        
        speaker_found = False
        
        # 1. Try generic <a href> link detection (Standard Camera format)
        for link in p.find_all('a'):
            link_text = link.get_text(strip=True)
            if not link_text or len(link_text) < 3 or (not link_text[0].isupper() and link_text not in ['Presidente']):
                continue
                
            name = link_text.strip()
            full_text = p.get_text()
            name_pos = full_text.find(name)
            if name_pos == -1: continue
            
            remaining = full_text[name_pos + len(name):].strip()
            
            # Check for party in parentheses
            party = ""
            if m := re.match(r'\s*\(([^)]+)\)', remaining):
                party = m.group(1).strip()
                remaining = remaining[m.end():].strip()
            
            # Check for role
            role, role_cat = "", ""
            if m := re.match(rf'^\s*,\s*({role_pattern_str})[^.]*', remaining, re.IGNORECASE):
                role = normalize_role(m.group(1))
                role_cat = get_role_category(role)
                remaining = remaining[m.end():].strip()

            remaining = re.sub(r'^[\.,:]\s*', '', remaining)
            
            if len(remaining) > 30:
                notes = re.findall(r'\(([^)]+)\)', remaining)
                clean_text = re.sub(r'\([^)]*\)', '', remaining).strip()
                
                if len(clean_text) > 20:
                    profile_url = ""
                    # Validate
                    if name in ['PRESIDENTE', 'Presidente']:
                        speaker, role, role_cat = "PRESIDENTE", "presidente", "presidenza"
                    else:
                        info = validate_participant(name, party, source_type='camera', use_cloudscraper=use_cloudscraper)
                        if info:
                            name, party, profile_url = info['name'], info['party'], info['profile_url']
                        else:
                            # Allow through if rosters unavailable, skip if rosters exist but no match
                            from backend.scrapers.utils import check_rosters_available
                            if check_rosters_available():
                                continue
                            # Rosters unavailable - keep original speaker/party

                    speeches.append(Speech(
                        speaker=name, party=party, text=clean_text, date=session_date,
                        session_number=0, url=session_url, notes=notes,
                        role=role, role_category=role_cat, profile_url=profile_url
                    ))
                    speaker_found = True
                    break
        
        if speaker_found: continue

        # 2. Fallback: Role Pattern
        if m := role_fallback_pattern.match(text):
            speaker, role, speech_text = m.groups()
            
            # Speaker name must be ALL CAPS (e.g., "SISTO") to be valid
            # This prevents matching text like "Concludo dicendo, ministro..."
            if not speaker.isupper():
                continue
                
            role = normalize_role(role)
            role_cat = get_role_category(role)
            
            notes = re.findall(r'\([^)]+\)', speech_text)
            clean_text = re.sub(r'\([^)]*\)', '', speech_text).strip()
            
            if len(clean_text) > 20:
                info = validate_participant(speaker, "", use_cloudscraper=use_cloudscraper)
                # Allow through if: validated OR (governo role AND roster available to validate)
                from backend.scrapers.utils import check_rosters_available
                # For governo, only accept if we can validate the name OR rosters are unavailable
                if info:
                    speeches.append(Speech(
                        speaker=info['name'],
                        party=info['party'] or ("Governo" if role_cat == "governo" else ""),
                        text=clean_text, date=session_date, session_number=0, url=session_url,
                        notes=notes, role=role, role_category=role_cat,
                        profile_url=info.get('profile_url', '')
                    ))
                elif role_cat == "governo" and not check_rosters_available():
                    # Only accept governo without validation if rosters unavailable
                    speeches.append(Speech(
                        speaker=speaker,
                        party="Governo",
                        text=clean_text, date=session_date, session_number=0, url=session_url,
                        notes=notes, role=role, role_category=role_cat,
                        profile_url=''
                    ))
            continue

        # 3. Fallback: Party Pattern
        if m := party_fallback_pattern.match(text):
            speaker, party, speech_text = m.groups()
            notes = re.findall(r'\(([^)]+)\)', speech_text)
            clean_text = re.sub(r'\([^)]*\)', '', speech_text).strip()
            
            if len(clean_text) > 20 and speaker.isupper():
                info = validate_participant(speaker, party, use_cloudscraper=use_cloudscraper)
                # Allow through if validated or rosters unavailable
                from backend.scrapers.utils import check_rosters_available
                if info or not check_rosters_available():
                     speeches.append(Speech(
                        speaker=info['name'] if info else speaker,
                        party=info['party'] if info else party,
                        text=clean_text, date=session_date, session_number=0, url=session_url,
                        notes=notes, role="", role_category="",
                        profile_url=info['profile_url'] if info else ''
                    ))

    return speeches


def fetch_speeches(use_cloudscraper: bool = False) -> pd.DataFrame:
    """Main function to fetch speeches from all sessions within MONTHS_BACK."""
    logger.info(f"Starting Camera speech scraping for last {MONTHS_BACK} months...")
    
    sessions = get_session_list(LEGISLATURE, months_back=MONTHS_BACK, use_cloudscraper=use_cloudscraper)
    if not sessions:
        return pd.DataFrame()
    
    all_res = []
    
    for session in sessions:
        speeches = fetch_session_speeches(session['url'], session.get('date', 'Unknown'), use_cloudscraper)
        
        for s in speeches:
            group = s.party if s.party and s.speaker not in ['PRESIDENTE'] else (
                 f"Governo" if s.role_category == "governo" else ("Presidenza" if s.role else 'Unknown Group')
            )
            
            # Skip procedural speeches
            if group == "Presidenza" or s.speaker == 'PRESIDENTE':
                continue
                
            unique_speaker = f"{s.speaker} [{s.party}]" if (s.party and group != "Presidenza" and group != "Governo") else s.speaker
            
            all_res.append({
                'date': s.date, 'deputy': unique_speaker, 'speaker_base': s.speaker,
                'group': group, 'text': s.text, 'source': 'camera', 'url': s.url,
                'role': s.role, 'role_category': s.role_category, 'profile_url': s.profile_url
            })
        
        time.sleep(1)
    
    df = pd.DataFrame(all_res)
    logger.info(f"Scraped {len(df)} speeches from Camera ({len(sessions)} sessions)")
    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(fetch_speeches())
