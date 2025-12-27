"""
Senate Speech Scraper - Resoconto Stenografico

This module scrapes full parliamentary speeches from senato.it.
It fetches the "Resoconto Stenografico" (stenographic reports) which contain
the complete verbatim transcripts of Senate sessions.

URLs:
- List: https://www.senato.it/lavori/assemblea/resoconti-elenco-cronologico
- Session: https://www.senato.it/show-doc?leg=19&tipodoc=Resaula&id={ID}&idoggetto=0
- Stenographic: https://www.senato.it/show-doc?leg=19&tipodoc=Resaula&id={ID}&idoggetto=0&part=doc_dc-ressten_rs
"""

import re
import logging
import time
from typing import Optional
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup
import pandas as pd

from backend.config import LEGISLATURE

# Configure logging
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://www.senato.it"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# URLs
SESSIONS_LIST_URL = f"{BASE_URL}/lavori/assemblea/resoconti-elenco-cronologico"
SESSION_URL_TEMPLATE = f"{BASE_URL}/show-doc?leg={{leg}}&tipodoc=Resaula&id={{id}}&idoggetto=0&part=doc_dc-ressten_rs"


@dataclass
class Speech:
    """Represents a single speech from a Senate session."""
    speaker: str
    party: str
    text: str
    date: str
    session_number: int
    url: str  # Direct link to the speech/session
    notes: list  # Parliamentary notes like (Applausi), (Interruzioni)


def get_session_list(legislature: int = LEGISLATURE, limit: int = 20) -> list[dict]:
    """
    Fetch the list of available Senate sessions from the chronological list.
    
    Args:
        legislature: Legislature number (default 19 for current)
        limit: Maximum number of sessions to retrieve
    
    Returns:
        List of session dictionaries with 'id', 'date', 'url', 'title'
    """
    logger.info(f"Fetching session list from {SESSIONS_LIST_URL}...")
    
    headers = {"User-Agent": USER_AGENT}
    
    try:
        response = requests.get(SESSIONS_LIST_URL, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        sessions = []
        
        # Look for links containing show-doc with Resaula
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            
            # Match links to stenographic reports
            if 'show-doc' in href and 'Resaula' in href:
                # Extract session ID from URL
                id_match = re.search(r'id=(\d+)', href)
                if id_match:
                    session_id = id_match.group(1)
                    
                    # Build the stenographic report URL
                    steno_url = SESSION_URL_TEMPLATE.format(leg=legislature, id=session_id)
                    
                    # Get title/text
                    title = link.get_text(strip=True)
                    
                    # Try to extract date from title or parent
                    date = _extract_date_from_context(link, title)
                    
                    sessions.append({
                        'id': session_id,
                        'url': steno_url,
                        'title': title,
                        'date': date
                    })
                    
                    if len(sessions) >= limit:
                        break
        
        logger.info(f"Found {len(sessions)} sessions")
        return sessions
        
    except Exception as e:
        logger.error(f"Error fetching session list: {e}")
        return []


def _extract_date_from_context(link_element, title: str) -> str:
    """Try to extract date from the link context or title."""
    # Try to find date pattern in title (e.g., "18 dicembre 2024")
    date_pattern = r'(\d{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+(\d{4})'
    match = re.search(date_pattern, title, re.IGNORECASE)
    if match:
        day, month, year = match.groups()
        months = {
            'gennaio': '01', 'febbraio': '02', 'marzo': '03', 'aprile': '04',
            'maggio': '05', 'giugno': '06', 'luglio': '07', 'agosto': '08',
            'settembre': '09', 'ottobre': '10', 'novembre': '11', 'dicembre': '12'
        }
        return f"{year}-{months[month.lower()]}-{int(day):02d}"
    
    # Try parent elements
    parent = link_element.find_parent(['tr', 'li', 'div'])
    if parent:
        text = parent.get_text()
        match = re.search(date_pattern, text, re.IGNORECASE)
        if match:
            day, month, year = match.groups()
            months = {
                'gennaio': '01', 'febbraio': '02', 'marzo': '03', 'aprile': '04',
                'maggio': '05', 'giugno': '06', 'luglio': '07', 'agosto': '08',
                'settembre': '09', 'ottobre': '10', 'novembre': '11', 'dicembre': '12'
            }
            return f"{year}-{months[month.lower()]}-{int(day):02d}"
    
    return "Unknown"


def fetch_session_speeches(session_url: str, session_date: str = "") -> list[Speech]:
    """
    Fetch all speeches from a single Senate session's stenographic report.
    
    Args:
        session_url: URL to the stenographic report
        session_date: Date of the session
    
    Returns:
        List of Speech objects
    """
    logger.info(f"Fetching speeches from: {session_url}")
    
    headers = {"User-Agent": USER_AGENT}
    
    try:
        response = requests.get(session_url, headers=headers, timeout=60)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Parse speeches from content
        speeches = _parse_speeches_from_html(soup, session_date, session_url)
        
        logger.info(f"Extracted {len(speeches)} speeches from session")
        return speeches
        
    except Exception as e:
        logger.error(f"Error fetching session: {e}")
        return []


def _parse_speeches_from_html(soup: BeautifulSoup, session_date: str, session_url: str) -> list[Speech]:
    """
    Parse speech content from the stenographic report HTML.
    
    The stenographic report has paragraphs where the speaker name appears
    at the start followed by a period, then their speech text.
    Example: "PRESIDENTE. La seduta è aperta..."
    
    Valid speakers are:
    - PRESIDENTE / PRESIDENTESSA
    - SURNAME (PARTY). text  (e.g., BOCCIA (PD-IDP). Signora Presidente...)
    - ALL CAPS SURNAME. text
    - SURNAME, role. text (e.g., LOMBARDO, segretario, dà lettura...)
    """
    speeches = []
    
    # Pattern 1: SURNAME (PARTY). text
    # e.g., "BOCCIA (PD-IDP). Signora Presidente..."
    speaker_with_party_pattern = re.compile(
        r'^([A-Z][A-Z\-\']+(?:\s+[A-Z][A-Z\-\']+)?)\s*\(([^)]+)\)\.\s+(.+)',
        re.DOTALL
    )
    
    # Pattern 2: PRESIDENTE/PRESIDENTESSA. text (no party)
    presidente_pattern = re.compile(
        r'^(PRESIDENTE|PRESIDENTESSA)\.\s+(.+)',
        re.DOTALL
    )
    
    # Pattern 3: SURNAME. text (no party)
    speaker_no_party_pattern = re.compile(
        r'^([A-Z][A-Z\-\']+(?:\s+[A-Z][A-Z\-\']+){0,2})\.\s+(.+)',
        re.DOTALL
    )
    
    # Pattern 4: SURNAME, role. text (e.g., "LOMBARDO, segretario, dà lettura...")
    role_pattern = re.compile(
        r'^([A-Z][A-Z\-\']+(?:\s+[A-Z][A-Z\-\']+)?),\s*(segretario|relatore|sottosegretario)\b[,\.]?\s*(.+)',
        re.IGNORECASE | re.DOTALL
    )
    
    # Note pattern
    note_pattern = re.compile(r'\(([^)]+)\)')
    
    # Get all paragraphs
    for p in soup.find_all('p'):
        text = p.get_text(strip=True)
        
        if not text or len(text) < 10:
            continue
        
        speaker = None
        party = ""
        speech_text = None
        
        # Try pattern 1: SURNAME (PARTY). text
        match = speaker_with_party_pattern.match(text)
        if match:
            speaker = match.group(1).strip()
            party = match.group(2).strip()
            speech_text = match.group(3).strip()
        
        # Try pattern 2: PRESIDENTE. text
        if not speaker:
            match = presidente_pattern.match(text)
            if match:
                speaker = match.group(1).strip()
                speech_text = match.group(2).strip()
        
        # Try pattern 4: role pattern (before generic speaker)
        if not speaker:
            match = role_pattern.match(text)
            if match:
                speaker = f"{match.group(1)} ({match.group(2).lower()})"
                speech_text = match.group(3).strip()
        
        # Try pattern 3: SURNAME. text (last resort)
        if not speaker:
            match = speaker_no_party_pattern.match(text)
            if match:
                potential_speaker = match.group(1).strip()
                # Validate: must be ALL CAPS, max 30 chars
                if len(potential_speaker) <= 30 and potential_speaker == potential_speaker.upper():
                    speaker = potential_speaker
                    speech_text = match.group(2).strip()
        
        # If we found a speaker, create the speech
        if speaker and speech_text:
            # Extract notes from speech text
            notes = note_pattern.findall(speech_text)
            clean_text = note_pattern.sub('', speech_text).strip()
            if len(clean_text) > 30:
                speeches.append(Speech(
                    speaker=speaker,
                    party=party,
                    text=clean_text,
                    date=session_date,
                    session_number=0,
                    url=session_url,
                    notes=notes
                ))
    
    return speeches


def fetch_speeches(limit: int = 200, sessions_to_fetch: int = 5) -> pd.DataFrame:
    """
    Main function to fetch speeches from multiple sessions.
    
    Args:
        limit: Maximum total speeches to return
        sessions_to_fetch: Number of sessions to scrape
    
    Returns:
        DataFrame with columns: date, deputy, group, text
    """
    logger.info(f"Starting Senate speech scraping (limit={limit}, sessions={sessions_to_fetch})...")
    
    # Get session list
    sessions = get_session_list(legislature=LEGISLATURE, limit=sessions_to_fetch)
    
    if not sessions:
        logger.warning("No sessions found. Returning empty DataFrame.")
        return pd.DataFrame()
    
    all_speeches = []
    
    for session in sessions:
        speeches = fetch_session_speeches(
            session['url'], 
            session_date=session.get('date', 'Unknown')
        )
        
        for speech in speeches:
            # Create unique speaker ID: include party if known to disambiguate homonyms
            speaker_name = speech.speaker
            party = speech.party or ''
            
            # If party is known and speaker is not PRESIDENTE, create unique ID
            if party and speaker_name not in ['PRESIDENTE', 'PRESIDENTESSA']:
                unique_speaker = f"{speaker_name} [{party}]"
            else:
                unique_speaker = speaker_name
            
            all_speeches.append({
                'date': speech.date,
                'deputy': unique_speaker,  # Now includes party for disambiguation
                'speaker_base': speaker_name,  # Original surname only
                'group': party or 'Unknown Group',
                'text': speech.text,
                'source': 'senate',
                'url': speech.url  # Link to original speech
            })
        
        if len(all_speeches) >= limit:
            break
        
        # Be respectful to the server
        time.sleep(1)
    
    df = pd.DataFrame(all_speeches[:limit])
    logger.info(f"Scraped {len(df)} speeches total")
    
    return df


# For testing
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("Testing Senate Scraper...")
    print("=" * 60)
    
    # Test session list
    sessions = get_session_list(limit=5)
    print(f"\nFound {len(sessions)} sessions:")
    for s in sessions:
        print(f"  - ID: {s.get('id', 'N/A')}")
        print(f"    Title: {s.get('title', 'N/A')[:60]}...")
        print(f"    Date: {s.get('date', 'N/A')}")
        print(f"    URL: {s.get('url', 'N/A')[:80]}...")
        print()
    
    # Test fetching speeches from first session
    if sessions:
        print(f"\n{'=' * 60}")
        print("Fetching speeches from first session...")
        speeches = fetch_session_speeches(sessions[0]['url'], sessions[0].get('date', ''))
        print(f"Found {len(speeches)} speeches")
        
        for speech in speeches[:3]:
            print(f"\n  Speaker: {speech.speaker}")
            print(f"  Date: {speech.date}")
            print(f"  Text ({len(speech.text)} chars): {speech.text[:150]}...")
            if speech.notes:
                print(f"  Notes: {speech.notes[:3]}")
