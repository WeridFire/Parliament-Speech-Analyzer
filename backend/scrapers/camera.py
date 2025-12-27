"""
Camera dei Deputati Speech Scraper - Resoconto Stenografico

This module scrapes full parliamentary speeches from camera.it.
It fetches the "Resoconto Stenografico" (stenographic reports) which contain
the complete verbatim transcripts of Chamber of Deputies sessions.

URLs:
- Session list: https://documenti.camera.it/apps/commonServices/getDocumento.ashx?idLegislatura=19&sezione=assemblea&tipoDoc=elenco&annomese=YYYY,MM
- Stenographic: https://documenti.camera.it/apps/commonServices/getDocumento.ashx?idLegislatura=19&sezione=assemblea&tipoDoc=stenografico&idSeduta=XXXX
"""

import re
import logging
import time
from typing import Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
import pandas as pd

from backend.config import LEGISLATURE, MONTHS_BACK

logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://www.camera.it"
DOCS_URL = "https://documenti.camera.it"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# URL templates
SESSION_LIST_URL = f"{DOCS_URL}/apps/commonServices/getDocumento.ashx?idLegislatura={{leg}}&sezione=assemblea&tipoDoc=elenco&annomese={{year}},{{month}}"
STENOGRAPHIC_URL = f"{BASE_URL}/leg{{leg}}/410?idSeduta={{session_id}}&tipo=stenografico"


@dataclass
class Speech:
    """Represents a single speech from a Chamber session."""
    speaker: str
    party: str
    text: str
    date: str
    session_number: int
    url: str  # Direct link to the speech/session
    notes: list  # Parliamentary notes like (Applausi), (Interruzioni)


def get_session_list(legislature: int = LEGISLATURE, months_back: int = MONTHS_BACK, limit: int = 20) -> list[dict]:
    """
    Fetch the list of available Chamber sessions from recent months.
    
    Args:
        legislature: Legislature number (default 19 for current)
        months_back: How many months to look back
        limit: Maximum number of sessions to retrieve
    
    Returns:
        List of session dictionaries with 'id', 'date', 'url'
    """
    logger.info("Fetching session list from camera.it...")
    
    headers = {"User-Agent": USER_AGENT}
    sessions = []
    
    # Get current date and iterate backwards through months
    current_date = datetime.now()
    
    for i in range(months_back):
        target_date = current_date - timedelta(days=30 * i)
        year = target_date.year
        month = target_date.month
        
        url = SESSION_LIST_URL.format(leg=legislature, year=year, month=month)
        logger.debug("Fetching session list for %d/%d", month, year)
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for session links - pattern: idSeduta=XXXX
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                
                # Match links to stenographic reports
                if 'idSeduta=' in href and 'stenografico' in href.lower():
                    session_match = re.search(r'idSeduta=(\d+)', href)
                    if session_match:
                        session_id = session_match.group(1)
                        
                        # Check for duplicates
                        if any(s['id'] == session_id for s in sessions):
                            continue
                        
                        # Extract date from link text or context
                        date = _extract_date_from_context(link, year, month)
                        
                        sessions.append({
                            'id': session_id,
                            'url': STENOGRAPHIC_URL.format(leg=legislature, session_id=session_id),
                            'date': date
                        })
                
        except Exception as e:
            logger.warning("Error fetching session list for %d/%d: %s", month, year, e)
            continue
        
        time.sleep(0.5)  # Be respectful
    
    # Sort sessions by date (oldest first) to get a good temporal distribution
    sessions.sort(key=lambda x: x.get('date', ''))
    
    # Apply limit AFTER collecting from all months
    if limit and len(sessions) > limit:
        sessions = sessions[:limit]
    
    logger.info("Found %d sessions from camera.it", len(sessions))
    return sessions


def _extract_date_from_context(link_element, year: int, month: int) -> str:
    """Try to extract date from the link context or text."""
    text = link_element.get_text(strip=True)
    
    # Try pattern: "Seduta n. XXX Lunedì DD"
    day_match = re.search(r'(\d{1,2})\s*$', text)
    if day_match:
        day = int(day_match.group(1))
        return f"{year}-{month:02d}-{day:02d}"
    
    # Try parent elements
    parent = link_element.find_parent(['tr', 'li', 'div'])
    if parent:
        parent_text = parent.get_text()
        date_pattern = r'(Lunedì|Martedì|Mercoledì|Giovedì|Venerdì|Sabato|Domenica)\s+(\d{1,2})'
        match = re.search(date_pattern, parent_text, re.IGNORECASE)
        if match:
            day = int(match.group(2))
            return f"{year}-{month:02d}-{day:02d}"
    
    return f"{year}-{month:02d}-01"  # Default to first of month


def fetch_session_speeches(session_url: str, session_date: str = "") -> list[Speech]:
    """
    Fetch all speeches from a single Chamber session's stenographic report.
    
    Args:
        session_url: URL to the stenographic report
        session_date: Date of the session
    
    Returns:
        List of Speech objects
    """
    logger.info("Fetching speeches from: %s", session_url)
    
    headers = {"User-Agent": USER_AGENT}
    
    try:
        response = requests.get(session_url, headers=headers, timeout=60)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Parse speeches from content
        speeches = _parse_speeches_from_html(soup, session_date, session_url)
        
        logger.info("Extracted %d speeches from session", len(speeches))
        return speeches
        
    except Exception as e:
        logger.error("Error fetching session: %s", e)
        return []


def _parse_speeches_from_html(soup: BeautifulSoup, session_date: str, session_url: str) -> list[Speech]:
    """
    Parse speech content from the stenographic report HTML.
    
    Camera.it format has speakers as links followed by party:
    - <a href="...">NOME COGNOME</a> (PARTITO). speech text...
    - <a href="...">PRESIDENTE</a>. speech text...
    """
    speeches = []
    
    # Get all text content
    # Camera.it uses specific div/section for stenographic content
    main_content = soup.find('div', class_='sezione') or soup.find('main') or soup
    
    # Get raw HTML and parse speech blocks
    html_text = str(main_content)
    
    # Pattern to match speaker blocks in the HTML
    # Matches: <a...>SPEAKER NAME</a> (PARTY). text  OR  <a...>PRESIDENTE</a>. text
    speech_pattern = re.compile(
        r'<a[^>]*>([A-Z][A-Z\s\'\-]+(?:\s+[A-Za-z]+)*)</a>\s*(?:\(([^)]+)\))?\s*[\.,:]\s*([^<]+)',
        re.IGNORECASE
    )
    
    # Also try to get from plain text paragraphs
    paragraphs = main_content.find_all(['p', 'div'])
    
    for p in paragraphs:
        # Get text with preserved structure
        text = p.get_text(separator=' ', strip=True)
        
        if not text or len(text) < 30:
            continue
        
        # Check for links with speaker names in this paragraph
        links = p.find_all('a')
        for link in links:
            link_text = link.get_text(strip=True)
            
            # Skip non-speaker links (too short or not uppercase start)
            if not link_text or len(link_text) < 3:
                continue
            if not link_text[0].isupper():
                continue
                
            # Check if this looks like a speaker name
            # Speaker names are typically ALL CAPS or First Last format
            name = link_text.strip()
            
            # Get text after this link
            try:
                # Get the full paragraph text
                full_text = p.get_text()
                
                # Find where the name appears
                name_pos = full_text.find(name)
                if name_pos == -1:
                    continue
                
                remaining = full_text[name_pos + len(name):].strip()
                
                # Check for party in parentheses
                party = ""
                party_match = re.match(r'\s*\(([^)]+)\)', remaining)
                if party_match:
                    party = party_match.group(1).strip()
                    remaining = remaining[party_match.end():].strip()
                
                # Remove leading punctuation
                remaining = re.sub(r'^[\.,:]\s*', '', remaining)
                
                # This is a valid speech if we have substantial text
                if len(remaining) > 50:
                    # Clean notes like (Applausi)
                    notes = re.findall(r'\(([^)]+)\)', remaining)
                    clean_text = re.sub(r'\([^)]*\)', '', remaining).strip()
                    
                    if len(clean_text) > 30 and name not in ['PRESIDENTE', 'Presidente']:
                        speeches.append(Speech(
                            speaker=name,
                            party=party,
                            text=clean_text,
                            date=session_date,
                            session_number=0,
                            url=session_url,
                            notes=notes
                        ))
                        break  # Only one speech per paragraph
                    elif name in ['PRESIDENTE', 'Presidente'] and len(clean_text) > 30:
                        speeches.append(Speech(
                            speaker='PRESIDENTE',
                            party='',
                            text=clean_text,
                            date=session_date,
                            session_number=0,
                            url=session_url,
                            notes=notes
                        ))
                        break
            except Exception as e:
                logger.debug("Failed to parse speech from link: %s", e)
                continue
    
    return speeches


def fetch_speeches(limit: int = 200, sessions_to_fetch: int = 10) -> pd.DataFrame:
    """
    Main function to fetch speeches from multiple sessions.
    
    Args:
        limit: Maximum total speeches to return
        sessions_to_fetch: Number of sessions to scrape
    
    Returns:
        DataFrame with columns: date, deputy, group, text
        (Same format as senate.py for compatibility)
    """
    logger.info("Starting Camera speech scraping (limit=%d, sessions=%d)...", limit, sessions_to_fetch)
    
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
            # Create unique speaker ID: include party if known
            speaker_name = speech.speaker
            party = speech.party or ''
            
            # If party is known and speaker is not PRESIDENTE, create unique ID
            if party and speaker_name not in ['PRESIDENTE']:
                unique_speaker = f"{speaker_name} [{party}]"
            else:
                unique_speaker = speaker_name
            
            all_speeches.append({
                'date': speech.date,
                'deputy': unique_speaker,
                'speaker_base': speaker_name,
                'group': party or 'Unknown Group',
                'text': speech.text,
                'source': 'camera',  # Mark source for identification
                'url': speech.url  # Link to original speech
            })
        
        if len(all_speeches) >= limit:
            break
        
        # Be respectful to the server
        time.sleep(1)
    
    df = pd.DataFrame(all_speeches[:limit])
    logger.info("Scraped %d speeches from Camera", len(df))
    
    return df


# For testing
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("Testing Camera Scraper...")
    print("=" * 60)
    
    # Test session list
    sessions = get_session_list(limit=3)
    print(f"\nFound {len(sessions)} sessions:")
    for s in sessions:
        print(f"  - ID: {s.get('id', 'N/A')}")
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
            print(f"  Party: {speech.party}")
            print(f"  Date: {speech.date}")
            print(f"  Text ({len(speech.text)} chars): {speech.text[:150]}...")
