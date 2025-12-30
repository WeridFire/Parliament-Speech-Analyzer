"""
Party normalization and coalition configuration.
"""

# Party name normalization - maps various spellings to canonical names
# This unifies party names between Camera and Senato
PARTY_NORMALIZATION = {
    # Forza Italia
    'FI-BP-PPE': 'Forza Italia',
    'FI-PPE': 'Forza Italia',
    'FORZA ITALIA': 'Forza Italia',
    
    # Fratelli d'Italia
    'FdI': "Fratelli d'Italia",
    'FDI': "Fratelli d'Italia",
    'FDI-AN': "Fratelli d'Italia",
    
    # Lega
    'LEGA': 'Lega',
    "LSP-PSd'Az": 'Lega',
    'LSP': 'Lega',
    
    # Partito Democratico
    'PD-IDP': 'PD',
    'PD': 'PD',
    
    # Movimento 5 Stelle
    'M5S': 'M5S',
    
    # Italia Viva / Centro
    'IV-C-RE': 'Italia Viva',
    'IV': 'Italia Viva',
    
    # Azione / Renew Europe
    'AZ-PER-RE': 'Azione-RE',
    'Misto-Az-RE': 'Azione-RE',
    'AZIONE-PER': 'Azione-RE',
    
    # AVS (Alleanza Verdi Sinistra)
    'AVS': 'AVS',
    'Misto-AVS': 'AVS',
    
    # Noi Moderati
    'NM(N-C-U-I': 'Noi Moderati',
    'NM(N-C-U-I)': 'Noi Moderati',
    'NM': 'Noi Moderati',
    
    # Gruppo Misto
    'MISTO': 'Misto',
    'Misto': 'Misto',
    'MISTO-+EUROPA': 'Misto-PiùEuropa',
    'MISTO-MIN.LING.': 'Misto-MinoranzeLing',
}


# =============================================================================
# POLITICAL COALITIONS (for left/right polarization analysis)
# =============================================================================

# Whether to classify "Governo" as right-wing in polarization analysis
CLASSIFY_GOVERNO_AS_RIGHT = True

# Right-wing coalition (Governo Meloni)
RIGHT_PARTIES = {
    "Fratelli d'Italia", "FdI", "FDI",
    "Lega", "LEGA",
    "Forza Italia", "FI", "FI-PPE", "FI-BP-PPE",
    "Noi Moderati", "NM", "NM(N-C-U-I)", "NM(N-C-U-I",
}

# Add Governo to right-wing if configured
if CLASSIFY_GOVERNO_AS_RIGHT:
    RIGHT_PARTIES.add("Governo")

# Left-wing / Opposition parties
LEFT_PARTIES = {
    "Partito Democratico", "PD", "PD-IDP",
    "Movimento 5 Stelle", "M5S",
    "AVS", "Alleanza Verdi Sinistra", "Misto-AVS",
    "+Europa", "Misto-PiùEuropa", "MISTO-+EUROPA",
}

# Center parties (often swing/third pole)
CENTER_PARTIES = {
    "Azione", "Azione-RE", "Azione-IV-RE", "IV-C-RE",
    "Italia Viva", "IV",
    "Misto", "MISTO",
}
