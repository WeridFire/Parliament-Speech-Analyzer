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
    
    # Not found in roster
    # logger.debug("Participant name not in official roster: %s", name)
    return None
