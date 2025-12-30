"""
Government roles configuration for speaker identification.

This module defines patterns for identifying government members in parliamentary speeches.
"""

import re

# Government roles that appear in stenographic reports
# Format: "COGNOME, role. text..."
GOVERNMENT_ROLES = {
    # Executive
    'presidente del consiglio',
    'presidente del consiglio dei ministri',
    
    # Ministers
    'ministro',
    'ministra',
    'vice ministro',
    'viceministro',
    'viceministra',
    
    # Undersecretaries
    'sottosegretario',
    'sottosegretaria',
    'sottosegretario di stato',
    'sottosegretaria di stato',
    
    # Parliamentary roles (non-government)
    'segretario',
    'segretaria',
    'relatore',
    'relatrice',
    'questore',
    
    # Presidency
    'presidente',
    'vice presidente',
    'vicepresidente',
}

# Role categories for analytics/display
ROLE_CATEGORIES = {
    'governo': {
        'presidente del consiglio',
        'presidente del consiglio dei ministri',
        'ministro',
        'ministra',
        'vice ministro',
        'viceministro',
        'viceministra',
        'sottosegretario',
        'sottosegretaria',
        'sottosegretario di stato',
        'sottosegretaria di stato',
    },
    'presidenza': {
        'presidente',
        'vice presidente',
        'vicepresidente',
    },
    'ufficio': {
        'segretario',
        'segretaria',
        'relatore',
        'relatrice',
        'questore',
    },
}


def get_role_category(role: str) -> str:
    """
    Get the category for a given role.
    
    Args:
        role: The role string (e.g., "ministro", "sottosegretario di stato")
    
    Returns:
        Category name: "governo", "presidenza", "ufficio", or "altro"
    """
    role_lower = role.lower().strip()
    
    for category, roles in ROLE_CATEGORIES.items():
        if role_lower in roles or any(r in role_lower for r in roles):
            return category
    
    return 'altro'


def normalize_role(role: str) -> str:
    """
    Normalize role string for consistent storage.
    
    Args:
        role: Raw role string from HTML
    
    Returns:
        Normalized role string (lowercase, trimmed)
    """
    return role.lower().strip()


def build_role_pattern() -> str:
    """
    Build a regex pattern to match any government/institutional role.
    
    Returns:
        Regex pattern string for use in re.compile()
    """
    # Escape special regex characters and join with |
    escaped_roles = [role.replace(' ', r'\s+') for role in GOVERNMENT_ROLES]
    return '|'.join(escaped_roles)
