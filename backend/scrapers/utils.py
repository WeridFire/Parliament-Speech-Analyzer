"""
Shared utilities for scrapers to reduce code duplication.
"""

import logging
import re
import time
from dataclasses import dataclass
from typing import Optional, Any
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from backend.utils import retry
from backend.scrapers.rosters import get_rosters

logger = logging.getLogger(__name__)

# Constants
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

@dataclass
class Speech:
    """Represents a single speech from a parliamentary session."""
    speaker: str
    party: str
    text: str
    date: str
    session_number: int
    url: str  # Direct link to the speech/session
    notes: list  # Parliamentary notes like (Applausi), (Interruzioni)
    role: str = ""  # Government/institutional role (e.g., "ministro", "presidente")
    role_category: str = ""  # Category: "governo", "presidenza", "ufficio", "altro"
    profile_url: str = ""  # Link to official profile page


def get_http_client(use_cloudscraper: bool = False) -> Any:
    """
    Factory function to get HTTP client (requests or cloudscraper).
    
    Args:
        use_cloudscraper: If True, use cloudscraper to bypass CloudFront blocking
    
    Returns:
        HTTP client module (requests or cloudscraper)
    """
    if use_cloudscraper:
        try:
            import cloudscraper
            logger.info("Using cloudscraper to bypass CloudFront protection")
            return cloudscraper.create_scraper()
        except ImportError:
            logger.warning("cloudscraper not installed, falling back to requests. Install with: pip install cloudscraper")
            return requests
    return requests


def normalize_name(name: str) -> str:
    """Normalize name for matching (title case, clean whitespace)."""
    name = ' '.join(name.split())
    if name.isupper():
        name = name.title()
    return name


_ROSTERS = None


def _get_rosters_lazy(use_cloudscraper: bool = False):
    """Lazy load rosters for validation."""
    global _ROSTERS
    if _ROSTERS is None:
        logger.info("Loading deputy/senator rosters for validation...")
        _ROSTERS = get_rosters(use_cloudscraper=use_cloudscraper)
    return _ROSTERS


def check_rosters_available() -> bool:
    """
    Check if rosters have been loaded and contain data.
    
    Returns:
        True if rosters are loaded and have names, False if empty/unavailable
    """
    global _ROSTERS
    if _ROSTERS is None:
        return False
    # Check if we have actual roster data (not just empty dicts)
    all_names = _ROSTERS.get('all_names')
    if all_names is None:
        return False
    # Handle both set and list format
    return len(all_names) > 0


def validate_participant(name: str, party: str = "", source_type: str = 'all', use_cloudscraper: bool = False) -> Optional[dict]:
    """
    Validate participant name against official roster and enrich with profile info.
    
    Args:
        name: Name as extracted (may be "SURNAME" or "SURNAME Name")
        party: Party as extracted (optional)
        source_type: 'camera', 'senato', or 'all' (default)
        use_cloudscraper: If True, use cloudscraper if roster needs to be fetched
    
    Returns:
        Dict with validated info: {name, party, profile_url} or None if invalid
    """
    # Skip special roles
    if name.upper() in ['PRESIDENTE', 'PRESIDENTESSA']:
        return None
    
    rosters = _get_rosters_lazy(use_cloudscraper=use_cloudscraper)
    
    # Normalize name for matching
    name_normalized = normalize_name(name)
    
    # Direct match
    if name_normalized in rosters['all_names']:
        info = rosters['name_to_info'][name_normalized]
        return {
            'name': info['full_name'],
            'party': info['party'] or party,  # Prefer roster party
            'profile_url': info.get('profile_url', '')
        }
    
    # Try case-insensitive match
    for roster_name in rosters['all_names']:
        if roster_name.lower() == name_normalized.lower():
            info = rosters['name_to_info'][roster_name]
            return {
                'name': info['full_name'],
                'party': info['party'] or party,
                'profile_url': info.get('profile_url', '')
            }
    
    # Try surname-based match with multiple strategies
    # Camera uses "NOME COGNOME" but roster has "COGNOME Nome"
    name_parts = name_normalized.split()
    candidates = []
    
    for roster_name in rosters['all_names']:
        roster_parts = roster_name.split()
        if not roster_parts:
            continue
            
        roster_surname = roster_parts[0].lower()  # Roster format: COGNOME Nome
        
        # Strategy 1: Direct surname match (e.g., "MALAN" matches "Malan Lucio")
        if len(name_parts) == 1:
            if roster_surname == name_parts[0].lower():
                candidates.append(roster_name)
        # Strategy 2: Full name with reversed order (Camera: NOME COGNOME -> Roster: COGNOME Nome)
        elif len(name_parts) >= 2:
            # Try matching last word of input as surname
            input_last = name_parts[-1].lower()  # Likely surname in Camera format
            input_first = name_parts[0].lower()  # Likely first name
            
            if len(roster_parts) >= 2:
                roster_first = roster_parts[1].lower() if len(roster_parts) > 1 else ""
                
                # Match: input "Giuseppe Conte" -> roster "Conte Giuseppe"
                if roster_surname == input_last and roster_first == input_first:
                    candidates.append(roster_name)
                # Match: input "Conte Giuseppe" -> roster "Conte Giuseppe" (same order)
                elif roster_surname == input_first and roster_first == input_last:
                    candidates.append(roster_name)
    
    if len(candidates) == 1:
        # Unique match found
        info = rosters['name_to_info'][candidates[0]]
        return {
            'name': info['full_name'],
            'party': info['party'] or party,
            'profile_url': info.get('profile_url', '')
        }
    elif len(candidates) > 1:
        # Multiple matches - try to disambiguate by party if provided
        if party:
            for candidate in candidates:
                info = rosters['name_to_info'][candidate]
                if party.lower() in (info.get('party', '') or '').lower():
                    return {
                        'name': info['full_name'],
                        'party': info['party'] or party,
                        'profile_url': info.get('profile_url', '')
                    }
        # Can't disambiguate - return first match but log warning
        info = rosters['name_to_info'][candidates[0]]
        logger.debug("Multiple roster matches for '%s': %s, using first", name, candidates)
        return {
            'name': info['full_name'],
            'party': info['party'] or party,
            'profile_url': info.get('profile_url', '')
        }
    
    # Not found in roster
    # logger.debug("Participant name not in official roster: %s", name)
    return None
