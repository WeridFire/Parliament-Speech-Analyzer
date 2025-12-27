export const CLUSTER_COLORS = [
    '#667eea', '#e94560', '#4ade80', '#fbbf24', '#a855f7',
    '#60a5fa', '#f472b6', '#22d3d8', '#fb923c', '#84cc16'
];

// Party colors using normalized names from backend
export const PARTY_COLORS = {
    // Main parties
    'PD': '#e53935',
    "Fratelli d'Italia": '#1565c0',
    'M5S': '#fdd835',
    'Forza Italia': '#42a5f5',
    'Lega': '#43a047',
    'Italia Viva': '#ff7043',
    'AVS': '#66bb6a',
    'Azione-RE': '#9c27b0',
    'Noi Moderati': '#00acc1',
    // Misto groups
    'Misto': '#9e9e9e',
    'Misto-PiùEuropa': '#7e57c2',
    'Misto-MinoranzeLing': '#78909c',
    // Fallback
    'Unknown Group': '#616161'
};

export const PARTY_CONFIG = {
    'PD': { shape: 'circle', color: '#e53935', label: 'PD' },
    "Fratelli d'Italia": { shape: 'diamond', color: '#1565c0', label: 'FdI' },
    'M5S': { shape: 'star', color: '#fdd835', label: 'M5S' },
    'Forza Italia': { shape: 'square', color: '#42a5f5', label: 'FI' },
    'Lega': { shape: 'triangle-up', color: '#43a047', label: 'Lega' },
    'Italia Viva': { shape: 'cross', color: '#ff7043', label: 'IV' },
    'AVS': { shape: 'pentagon', color: '#66bb6a', label: 'AVS' },
    'Azione-RE': { shape: 'hexagon2', color: '#9c27b0', label: 'Az-RE' },
    'Noi Moderati': { shape: 'bowtie', color: '#00acc1', label: 'NM' },
    'Misto': { shape: 'hexagon', color: '#9e9e9e', label: 'Misto' },
    'Misto-PiùEuropa': { shape: 'hexagon', color: '#7e57c2', label: '+Eu' },
    'Misto-MinoranzeLing': { shape: 'hexagon', color: '#78909c', label: 'MinL' },
    'Unknown Group': { shape: 'circle', color: '#616161', label: '?' }
};

