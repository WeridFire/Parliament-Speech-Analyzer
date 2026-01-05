export const CLUSTER_COLORS = [
    '#667eea', '#e94560', '#4ade80', '#fbbf24', '#a855f7',
    '#60a5fa', '#f472b6', '#22d3d8', '#fb923c', '#84cc16'
];

// Party colors using actual names from backend data
export const PARTY_COLORS = {
    // Camera dei Deputati - Actual names
    "FRATELLI D'ITALIA": '#1565c0',
    'MOVIMENTO 5 STELLE': '#fdd835',
    'FORZA ITALIA - BERLUSCONI PRESIDENTE - PPE': '#42a5f5',
    'LEGA - SALVINI PREMIER': '#43a047',
    'PARTITO DEMOCRATICO - ITALIA DEMOCRATICA E PROGRESSISTA': '#e53935',
    'ALLEANZA VERDI E SINISTRA': '#66bb6a',
    'AZIONE-POPOLARI EUROPEISTI RIFORMATORI-RENEW EUROPE': '#9c27b0',
    'NOI MODERATI(NOI CON L\'ITALIA, CORAGGIO ITALIA, UDC, ITALIA AL CENTRO)-MAIE-CENTRO POPOLARE': '#00acc1',
    'MISTO': '#9e9e9e',
    'MISTO-MINORANZE LINGUISTICHE': '#78909c',

    // Senato - Actual names  
    'FdI': '#1565c0',
    'M5S': '#fdd835',
    'FI-BP-PPE': '#42a5f5',
    'LSP-PSd\'Az': '#43a047',
    'PD-IDP': '#e53935',
    'Azione-IV-RE': '#9c27b0',
    'Cd\'I-NM(UDC-CI-NcI-IaC)-MAIE': '#00acc1',
    'Misto': '#9e9e9e',

    // Normalized names (legacy)
    'PD': '#e53935',
    "Fratelli d'Italia": '#1565c0',
    'Forza Italia': '#42a5f5',
    'Lega': '#43a047',
    'Italia Viva': '#ff7043',
    'AVS': '#66bb6a',
    'Azione-RE': '#9c27b0',
    'Noi Moderati': '#00acc1',

    // Institutions
    'Governo': '#607d8b',
    'Presidenza': '#795548',

    // Fallback
    'Unknown Group': '#616161'
};

// Party abbreviations for display
export const PARTY_ABBREVIATIONS = {
    // Camera
    "FRATELLI D'ITALIA": 'FdI',
    'MOVIMENTO 5 STELLE': 'M5S',
    'FORZA ITALIA - BERLUSCONI PRESIDENTE - PPE': 'FI',
    'LEGA - SALVINI PREMIER': 'Lega',
    'PARTITO DEMOCRATICO - ITALIA DEMOCRATICA E PROGRESSISTA': 'PD',
    'ALLEANZA VERDI E SINISTRA': 'AVS',
    'AZIONE-POPOLARI EUROPEISTI RIFORMATORI-RENEW EUROPE': 'Az-RE',
    'NOI MODERATI(NOI CON L\'ITALIA, CORAGGIO ITALIA, UDC, ITALIA AL CENTRO)-MAIE-CENTRO POPOLARE': 'NM',
    'MISTO': 'Misto',
    'MISTO-MINORANZE LINGUISTICHE': 'MinL',

    // Senato
    'FdI': 'FdI',
    'M5S': 'M5S',
    'FI-BP-PPE': 'FI',
    'LSP-PSd\'Az': 'Lega',
    'PD-IDP': 'PD',
    'Azione-IV-RE': 'Az-RE',
    'Cd\'I-NM(UDC-CI-NcI-IaC)-MAIE': 'NM',
    'Misto': 'Misto',

    // Institutions
    'Governo': 'Gov',
    'Presidenza': 'Pres',
};

// Helper function to get party abbreviation
export const getPartyAbbreviation = (partyName) => {
    if (!partyName) return '?';
    // Check direct match
    if (PARTY_ABBREVIATIONS[partyName]) {
        return PARTY_ABBREVIATIONS[partyName];
    }
    // Check partial match
    for (const [key, abbrev] of Object.entries(PARTY_ABBREVIATIONS)) {
        if (partyName.includes(key) || key.includes(partyName)) {
            return abbrev;
        }
    }
    // Fallback: first 3 chars uppercase
    return partyName.substring(0, 3).toUpperCase();
};

// Helper function to get party color with fallback
export const getPartyColor = (partyName) => {
    if (!partyName) return '#616161';
    // Check direct match
    if (PARTY_COLORS[partyName]) {
        return PARTY_COLORS[partyName];
    }
    // Check partial match (case-insensitive)
    const lowerParty = partyName.toLowerCase();
    for (const [key, color] of Object.entries(PARTY_COLORS)) {
        if (lowerParty.includes(key.toLowerCase()) || key.toLowerCase().includes(lowerParty)) {
            return color;
        }
    }
    // Fallback gray
    return '#888888';
};

export const PARTY_CONFIG = {
    "FRATELLI D'ITALIA": { shape: 'diamond', color: '#1565c0', label: 'FdI' },
    'MOVIMENTO 5 STELLE': { shape: 'star', color: '#fdd835', label: 'M5S' },
    'FORZA ITALIA - BERLUSCONI PRESIDENTE - PPE': { shape: 'square', color: '#42a5f5', label: 'FI' },
    'LEGA - SALVINI PREMIER': { shape: 'triangle-up', color: '#43a047', label: 'Lega' },
    'PARTITO DEMOCRATICO - ITALIA DEMOCRATICA E PROGRESSISTA': { shape: 'circle', color: '#e53935', label: 'PD' },
    'ALLEANZA VERDI E SINISTRA': { shape: 'pentagon', color: '#66bb6a', label: 'AVS' },
    'AZIONE-POPOLARI EUROPEISTI RIFORMATORI-RENEW EUROPE': { shape: 'hexagon2', color: '#9c27b0', label: 'Az-RE' },
    'NOI MODERATI(NOI CON L\'ITALIA, CORAGGIO ITALIA, UDC, ITALIA AL CENTRO)-MAIE-CENTRO POPOLARE': { shape: 'bowtie', color: '#00acc1', label: 'NM' },
    'MISTO': { shape: 'hexagon', color: '#9e9e9e', label: 'Misto' },

    // Senato
    'FdI': { shape: 'diamond', color: '#1565c0', label: 'FdI' },
    'M5S': { shape: 'star', color: '#fdd835', label: 'M5S' },
    'FI-BP-PPE': { shape: 'square', color: '#42a5f5', label: 'FI' },
    'LSP-PSd\'Az': { shape: 'triangle-up', color: '#43a047', label: 'Lega' },
    'PD-IDP': { shape: 'circle', color: '#e53935', label: 'PD' },

    // Legacy
    'PD': { shape: 'circle', color: '#e53935', label: 'PD' },
    "Fratelli d'Italia": { shape: 'diamond', color: '#1565c0', label: 'FdI' },
    'Forza Italia': { shape: 'square', color: '#42a5f5', label: 'FI' },
    'Lega': { shape: 'triangle-up', color: '#43a047', label: 'Lega' },
    'AVS': { shape: 'pentagon', color: '#66bb6a', label: 'AVS' },

    // Institutions
    'Governo': { shape: 'diamond', color: '#607d8b', label: 'Gov' },
    'Presidenza': { shape: 'star', color: '#795548', label: 'Pres' },
    'Misto': { shape: 'hexagon', color: '#9e9e9e', label: 'Misto' },
    'Unknown Group': { shape: 'circle', color: '#616161', label: '?' }
};
