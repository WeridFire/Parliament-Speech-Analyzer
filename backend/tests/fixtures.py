"""
Test Fixtures - Centralized mock data for analyzer tests.

All mock data is configurable and designed to be:
- Realistic enough to test all edge cases
- Small enough for fast tests
- Modular and reusable across all analyzer tests
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta


# =============================================================================
# CONFIGURATION
# =============================================================================

# Number of mock speeches to generate
N_SPEECHES = 50

# Number of speakers
N_SPEAKERS = 10

# Number of clusters
N_CLUSTERS = 5

# Embedding dimensions
EMBEDDING_DIM = 384

# Date range
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2024, 12, 31)


# =============================================================================
# MOCK SPEAKERS AND PARTIES
# =============================================================================

MOCK_SPEAKERS = [
    {'name': 'Mario Rossi', 'party': 'Partito Democratico'},
    {'name': 'Giulia Bianchi', 'party': 'Partito Democratico'},
    {'name': 'Luca Verdi', 'party': 'Fratelli d\'Italia'},
    {'name': 'Anna Neri', 'party': 'Fratelli d\'Italia'},
    {'name': 'Paolo Gialli', 'party': 'Lega'},
    {'name': 'Sofia Viola', 'party': 'Lega'},
    {'name': 'Marco Blu', 'party': 'Movimento 5 Stelle'},
    {'name': 'Elena Rosa', 'party': 'Movimento 5 Stelle'},
    {'name': 'Giovanni Arancio', 'party': 'Forza Italia'},
    {'name': 'Chiara Grigio', 'party': 'Forza Italia'},
]

MOCK_PARTIES = list(set(s['party'] for s in MOCK_SPEAKERS))


# =============================================================================
# MOCK TEXTS
# =============================================================================

MOCK_TEXTS = [
    # Cluster 0: Economy
    "L'economia italiana sta attraversando un momento difficile. Dobbiamo investire nel futuro e creare nuovi posti di lavoro. I dati mostrano che il PIL è cresciuto del 2% nell'ultimo trimestre.",
    "La situazione economica richiede interventi urgenti. Le imprese hanno bisogno di supporto fiscale. Proponiamo una riduzione delle tasse del 15% per le PMI.",
    "Il debito pubblico è al 140% del PIL. Non possiamo continuare così. Io personalmente credo che servano riforme strutturali immediate.",
    
    # Cluster 1: Healthcare
    "La sanità pubblica è in crisi. Gli ospedali sono al collasso. Dobbiamo assumere 50000 nuovi medici e infermieri entro il 2025.",
    "Il sistema sanitario nazionale ha bisogno di investimenti. Non è possibile che i cittadini debbano aspettare mesi per una visita specialistica.",
    "La spesa sanitaria deve aumentare. Noi vogliamo garantire a tutti l'accesso alle cure. Mai più liste d'attesa infinite.",
    
    # Cluster 2: Environment
    "Il cambiamento climatico è una minaccia reale. Dobbiamo ridurre le emissioni del 55% entro il 2030. La transizione ecologica non è rinviabile.",
    "L'ambiente è una priorità assoluta. Investiremo 10 miliardi di euro in energie rinnovabili. Il futuro è verde.",
    "La sostenibilità ambientale deve guidare ogni nostra scelta. No al nucleare, sì al solare e all'eolico.",
    
    # Cluster 3: Immigration
    "L'immigrazione è un tema complesso. Servono politiche di integrazione efficaci. Non possiamo accogliere tutti ma non possiamo nemmeno chiudere le frontiere.",
    "La sicurezza dei confini è fondamentale. Contro l'immigrazione clandestina servono controlli più rigidi.",
    "I migranti meritano dignità e rispetto. L'Europa deve fare di più. Questa situazione è inaccettabile.",
    
    # Cluster 4: Education
    "La scuola italiana ha bisogno di riforme. Gli insegnanti sono sottopagati. Dobbiamo investire nell'istruzione per il futuro dei nostri giovani.",
    "L'università deve essere accessibile a tutti. Le tasse universitarie sono troppo alte. Proponiamo borse di studio per 100000 studenti.",
    "L'educazione è la base della democrazia. Mai tagliare i fondi alla ricerca. Il sapere è il nostro patrimonio più prezioso.",
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def generate_mock_date(start: datetime, end: datetime) -> str:
    """Generate random date string in YYYY-MM-DD format."""
    delta = (end - start).days
    random_days = np.random.randint(0, delta)
    date = start + timedelta(days=random_days)
    return date.strftime('%Y-%m-%d')


def generate_mock_text(cluster: int) -> str:
    """Generate mock text for a given cluster."""
    base_idx = cluster * 3
    idx = base_idx + np.random.randint(0, 3)
    idx = idx % len(MOCK_TEXTS)
    
    # Add some variation
    text = MOCK_TEXTS[idx]
    
    # Sometimes add self-reference
    if np.random.random() < 0.3:
        text = "Io penso che " + text
    
    # Sometimes add questions
    if np.random.random() < 0.2:
        text += " Non è forse vero?"
    
    # Sometimes add negation
    if np.random.random() < 0.2:
        text = text.replace("Dobbiamo", "Non possiamo non")
    
    return text


def generate_mock_embeddings(n_speeches: int, n_clusters: int, dim: int, clusters: list) -> np.ndarray:
    """
    Generate mock embeddings with cluster structure.
    
    Embeddings for the same cluster are similar (close in embedding space).
    """
    embeddings = np.zeros((n_speeches, dim))
    
    # Generate cluster centroids
    centroids = np.random.randn(n_clusters, dim)
    centroids = centroids / np.linalg.norm(centroids, axis=1, keepdims=True)
    
    # Generate embeddings around centroids
    for i, cluster in enumerate(clusters):
        centroid = centroids[cluster]
        noise = np.random.randn(dim) * 0.3
        embedding = centroid + noise
        embeddings[i] = embedding / np.linalg.norm(embedding)
    
    return embeddings


# =============================================================================
# MAIN FIXTURES
# =============================================================================

def create_mock_dataframe(n_speeches: int = N_SPEECHES) -> pd.DataFrame:
    """
    Create a mock DataFrame with realistic political speech data.
    
    Returns:
        DataFrame with columns: deputy, group, cleaned_text, date, cluster
    """
    np.random.seed(42)  # Reproducibility
    
    data = []
    
    for i in range(n_speeches):
        speaker = MOCK_SPEAKERS[i % len(MOCK_SPEAKERS)]
        cluster = i % N_CLUSTERS
        
        data.append({
            'deputy': speaker['name'],
            'group': speaker['party'],
            'cleaned_text': generate_mock_text(cluster),
            'date': generate_mock_date(START_DATE, END_DATE),
            'cluster': cluster,
        })
    
    return pd.DataFrame(data)


def create_mock_embeddings(df: pd.DataFrame, dim: int = EMBEDDING_DIM) -> np.ndarray:
    """
    Create mock embeddings with cluster structure.
    
    Returns:
        numpy array of shape (n_speeches, dim)
    """
    np.random.seed(42)
    clusters = df['cluster'].tolist()
    return generate_mock_embeddings(len(df), N_CLUSTERS, dim, clusters)


def create_mock_cluster_centroids(dim: int = EMBEDDING_DIM) -> np.ndarray:
    """
    Create mock cluster centroids.
    
    Returns:
        numpy array of shape (n_clusters, dim)
    """
    np.random.seed(42)
    centroids = np.random.randn(N_CLUSTERS, dim)
    return centroids / np.linalg.norm(centroids, axis=1, keepdims=True)


def create_mock_cluster_labels() -> dict:
    """
    Create mock cluster labels.
    
    Returns:
        Dict mapping cluster_id -> label
    """
    return {
        0: 'Economia',
        1: 'Sanità',
        2: 'Ambiente',
        3: 'Immigrazione',
        4: 'Istruzione',
    }


# =============================================================================
# FIXTURE CLASS (for pytest)
# =============================================================================

class MockData:
    """
    Container for all mock data.
    
    Usage:
        mock = MockData()
        df = mock.df
        embeddings = mock.embeddings
    """
    
    def __init__(self, n_speeches: int = N_SPEECHES, embedding_dim: int = EMBEDDING_DIM):
        self.df = create_mock_dataframe(n_speeches)
        self.embeddings = create_mock_embeddings(self.df, embedding_dim)
        self.cluster_centroids = create_mock_cluster_centroids(embedding_dim)
        self.cluster_labels = create_mock_cluster_labels()
        self.n_speeches = n_speeches
        self.n_speakers = len(self.df['deputy'].unique())
        self.n_parties = len(self.df['group'].unique())
        self.n_clusters = len(self.cluster_labels)
    
    def get_analyzer_kwargs(self) -> dict:
        """Get common kwargs for analyzer initialization."""
        return {
            'df': self.df,
            'embeddings': self.embeddings,
            'cluster_labels': self.cluster_labels,
            'cluster_centroids': self.cluster_centroids,
            'text_col': 'cleaned_text',
            'speaker_col': 'deputy',
            'party_col': 'group',
            'cluster_col': 'cluster',
            'date_col': 'date',
        }


# Module-level singleton for quick access
_mock_data = None

def get_mock_data() -> MockData:
    """Get shared mock data instance (singleton)."""
    global _mock_data
    if _mock_data is None:
        _mock_data = MockData()
    return _mock_data


def reset_mock_data():
    """Reset mock data (useful for testing with different configs)."""
    global _mock_data
    _mock_data = None
