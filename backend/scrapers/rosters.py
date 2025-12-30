"""
Fetch and cache official deputy/senator rosters from Camera and Senato.

This module provides authoritative whitelists of deputies and senators to validate
scraped names and eliminate false positives.
"""

import json
import logging
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

import requests
from bs4 import BeautifulSoup

from backend.utils import CACHE_DIR, get_http_client

logger = logging.getLogger(__name__)

# Cache settings
ROSTER_CACHE_FILE = CACHE_DIR / 'rosters_leg19.json'
ROSTER_CACHE_DAYS = 30


def _normalize_name(name: str) -> str:
    """Normalize name for consistent matching."""
    # Remove extra whitespace, convert to title case
    name = ' '.join(name.split())
    # Handle all caps names
    if name.isupper():
        name = name.title()
    return name


def fetch_camera_roster(legislature: int = 19, use_cloudscraper: bool = False) -> list[dict]:
    """
    Fetch complete deputy roster from Camera dei Deputati.
    
    Iterates through all letters A-Z and parses HTML to extract:
    - Full name (normalized)
    - Party/Group
    - Profile URL
    
    Returns:
        List of deputy dicts with keys: full_name, party, profile_url, source
    """
    logger.info("Fetching Camera roster for legislature %d...", legislature)
    
    http_client = get_http_client(use_cloudscraper=use_cloudscraper)
    
    deputies = []
    letters = 'ABCDEFGHIKLMNOPQRSTUVZ'  # Camera uses these letters
    
    for letter in letters:
        url = f'https://www.camera.it/leg{legislature}/28?lettera={letter}'
        
        try:
            response = http_client.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all deputy entries
            # Pattern: <a href="...schedaDeputato...">SURNAME Name</a>
            # Followed by: <a href="...gruppo...">PARTY NAME</a>
            
            deputy_links = soup.find_all('a', href=re.compile(r'schedaDeputato'))
            
            for link in deputy_links:
                name = link.get_text(strip=True)
                if not name:
                    continue
                
                # Get profile URL
                profile_url = link.get('href', '')
                if not profile_url.startswith('http'):
                    profile_url = 'https://documenti.camera.it' + profile_url
                
                # Find party name (next <a> tag with gruppo in href)
                party_elem = link.find_next('a', href=re.compile(r'gruppo'))
                party = party_elem.get_text(strip=True) if party_elem else ''
                
                deputies.append({
                    'full_name': _normalize_name(name),
                    'party': party,
                    'profile_url': profile_url,
                    'source': 'camera'
                })
            
            logger.debug("Fetched %d deputies for letter %s", len(deputy_links), letter)
            
        except Exception as e:
            logger.error("Error fetching Camera roster for letter %s: %s", letter, e)
            continue
    
    logger.info("Fetched %d total deputies from Camera", len(deputies))
    return deputies


def fetch_senato_roster(legislature: int = 19, use_cloudscraper: bool = False) -> list[dict]:
    """
    Fetch complete senator roster from Senato della Repubblica.
    
    Iterates through all letters a-z and parses HTML to extract:
    - Full name (normalized)
    - Party/Group
    - Profile URL
    
    Returns:
        List of senator dicts with keys: full_name, party, profile_url, source
    """
    logger.info("Fetching Senato roster for legislature %d...", legislature)
    
    http_client = get_http_client(use_cloudscraper=use_cloudscraper)
    
    senators = []
    letters = 'abcdefghilmnopqrstuvz'  # Senato uses lowercase
    
    for letter in letters:
        url = f'https://www.senato.it/composizione/senatori/elenco-alfabetico?iniziale={letter}&leg={legislature}'
        
        try:
            response = http_client.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all senator entries
            # Pattern: <a href="/composizione/senatori/elenco-alfabetico/scheda-attivita?did=...">SURNAME Name</a>
            # Followed by party info in next <a> tag
            
            senator_links = soup.find_all('a', href=re.compile(r'scheda-attivita\?did='))
            
            for link in senator_links:
                name = link.get_text(strip=True)
                if not name:
                    continue
                
                # Get profile URL
                profile_url = link.get('href', '')
                if not profile_url.startswith('http'):
                    profile_url = 'https://www.senato.it' + profile_url
                
                # Find party name (next <a> tag with composizione in href)
                party_elem = link.find_next('a', href=re.compile(r'composizione'))
                party = party_elem.get_text(strip=True) if party_elem else ''
                
                senators.append({
                    'full_name': _normalize_name(name),
                    'party': party,
                    'profile_url': profile_url,
                    'source': 'senato'
                })
            
            logger.debug("Fetched %d senators for letter %s", len(senator_links), letter)
            
        except Exception as e:
            logger.error("Error fetching Senato roster for letter %s: %s", letter, e)
            continue
    
    logger.info("Fetched %d total senators from Senato", len(senators))
    return senators


def fetch_all_rosters(legislature: int = 19, use_cloudscraper: bool = False) -> dict:
    """
    Fetch rosters from both Camera and Senato.
    
    Returns:
        {
            'camera': [...],
            'senato': [...],
            'all_names': {'Mario Rossi', 'Giovanni Bianchi', ...},
            'name_to_info': {'Mario Rossi': {...}, ...},
            'timestamp': '2024-01-01T12:00:00',
            'legislature': 19
        }
    """
    camera = fetch_camera_roster(legislature, use_cloudscraper)
    senato = fetch_senato_roster(legislature, use_cloudscraper)
    
    # Build lookup structures
    all_names = set()
    name_to_info = {}
    
    for person in camera + senato:
        name = person['full_name']
        all_names.add(name)
        
        # If duplicate name exists (same person in different lists), prefer more complete info
        if name in name_to_info:
            # Keep entry with party if available
            if person['party'] and not name_to_info[name]['party']:
                name_to_info[name] = person
        else:
            name_to_info[name] = person
    
    return {
        'camera': camera,
        'senato': senato,
        'all_names': sorted(all_names),  # Convert set to sorted list for JSON
        'name_to_info': name_to_info,
        'timestamp': datetime.now().isoformat(),
        'legislature': legislature
    }


def load_cached_rosters() -> Optional[dict]:
    """
    Load rosters from cache if valid (< 30 days old).
    
    Returns:
        Cached rosters dict or None if cache invalid/missing
    """
    if not ROSTER_CACHE_FILE.exists():
        logger.info("No roster cache found")
        return None
    
    try:
        with open(ROSTER_CACHE_FILE, 'r', encoding='utf-8') as f:
            cached = json.load(f)
        
        # Check cache age
        cache_time = datetime.fromisoformat(cached['timestamp'])
        age = datetime.now() - cache_time
        
        if age.days > ROSTER_CACHE_DAYS:
            logger.info("Roster cache expired (%d days old)", age.days)
            return None
        
        logger.info("Loaded roster cache (%d days old)", age.days)
        # Convert list back to set for all_names
        cached['all_names'] = set(cached['all_names'])
        return cached
        
    except Exception as e:
        logger.error("Error loading roster cache: %s", e)
        return None


def save_rosters_cache(rosters: dict):
    """Save rosters to cache with timestamp."""
    CACHE_DIR.mkdir(exist_ok=True)
    
    # Convert set to list for JSON serialization
    rosters_to_save = rosters.copy()
    rosters_to_save['all_names'] = sorted(rosters['all_names'])
    
    with open(ROSTER_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(rosters_to_save, f, ensure_ascii=False, indent=2)
    
    logger.info("Saved roster cache to %s", ROSTER_CACHE_FILE)


def get_rosters(legislature: int = 19, force_refresh: bool = False, use_cloudscraper: bool = False) -> dict:
    """
    Get rosters with automatic caching.
    
    Loads from cache if valid, otherwise fetches fresh data.
    
    Args:
        legislature: Legislature number (default 19)
        force_refresh: If True, bypass cache and fetch fresh data
        use_cloudscraper: If True, use cloudscraper to bypass CloudFront blocking
    
    Returns:
        Rosters dict with all_names set and name_to_info dict
    """
    if not force_refresh:
        cached = load_cached_rosters()
        if cached and cached.get('legislature') == legislature:
            return cached
    
    logger.info("Fetching fresh rosters...")
    rosters = fetch_all_rosters(legislature, use_cloudscraper)
    save_rosters_cache(rosters)
    
    return rosters


if __name__ == '__main__':
    # Test the roster fetching
    logging.basicConfig(level=logging.INFO)
    
    rosters = get_rosters(force_refresh=True)
    
    print(f"\n=== Roster Summary ===")
    print(f"Camera deputies: {len(rosters['camera'])}")
    print(f"Senato senators: {len(rosters['senato'])}")
    print(f"Total unique names: {len(rosters['all_names'])}")
    print(f"\nSample names:")
    for name in sorted(rosters['all_names'])[:10]:
        info = rosters['name_to_info'][name]
        print(f"  - {name} ({info['party']}) [{info['source']}]")
