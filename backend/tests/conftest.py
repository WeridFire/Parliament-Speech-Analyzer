"""
Shared pytest fixtures for backend tests.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path


@pytest.fixture
def sample_speeches_df():
    """DataFrame with sample speeches for testing."""
    return pd.DataFrame([
        {
            'deputy': 'ROSSI [PD-IDP]',
            'group': 'PD-IDP',
            'text': 'Signor Presidente, il governo deve agire con urgenza sulla questione economica.',
            'cleaned_text': 'il governo deve agire con urgenza sulla questione economica',
            'date': '2024-12-01',
            'source': 'senate'
        },
        {
            'deputy': 'BIANCHI [FdI]',
            'group': 'FdI',
            'text': 'La nostra proposta di legge mira a ridurre le tasse per le famiglie italiane.',
            'cleaned_text': 'nostra proposta legge mira ridurre tasse famiglie italiane',
            'date': '2024-12-01',
            'source': 'senate'
        },
        {
            'deputy': 'VERDI [M5S]',
            'group': 'M5S',
            'text': 'Dobbiamo proteggere l\'ambiente e investire nelle energie rinnovabili.',
            'cleaned_text': 'dobbiamo proteggere ambiente investire energie rinnovabili',
            'date': '2024-12-02',
            'source': 'camera'
        },
        {
            'deputy': 'NERI [IV-C-RE]',
            'group': 'IV-C-RE',
            'text': 'La riforma della giustizia è una priorità per questo parlamento.',
            'cleaned_text': 'riforma giustizia priorità parlamento',
            'date': '2024-12-02',
            'source': 'camera'
        },
    ])


@pytest.fixture
def sample_embeddings():
    """Fake embeddings for testing (4 speeches, 384 dims like MiniLM)."""
    np.random.seed(42)  # Reproducible
    return np.random.rand(4, 384).astype(np.float32)


@pytest.fixture
def sample_embeddings_clustered():
    """Embeddings designed to form 2 clear clusters."""
    np.random.seed(42)
    # Cluster 1: speeches 0, 1
    cluster1 = np.random.rand(2, 384) * 0.1
    # Cluster 2: speeches 2, 3
    cluster2 = np.random.rand(2, 384) * 0.1 + 0.9
    return np.vstack([cluster1, cluster2]).astype(np.float32)


@pytest.fixture
def camera_html_sample():
    """Sample HTML from Camera stenographic report."""
    return """
    <div class="sezione">
        <p><a href="#">ROSSI MARCO</a> (PD-IDP). Signor Presidente, questa proposta 
        è fondamentale per il futuro del paese. Dobbiamo agire con decisione.</p>
        <p><a href="#">BIANCHI LUIGI</a> (FdI). Non sono d'accordo con il collega. 
        La nostra posizione è chiara: prima gli italiani.</p>
        <p><a href="#">PRESIDENTE</a>. Grazie, onorevole. La seduta è sospesa.</p>
    </div>
    """


@pytest.fixture
def senate_html_sample():
    """Sample HTML from Senate stenographic report."""
    return """
    <div>
        <p>BOCCIA (PD-IDP). Signora Presidente, vorrei sottolineare l'importanza 
        di questa misura per le famiglie italiane. (Applausi)</p>
        <p>PRESIDENTE. Ha facoltà di parlare il senatore Gasparri.</p>
        <p>GASPARRI (FdI). Grazie, Presidente. Il nostro gruppo voterà a favore 
        di questo emendamento. (Commenti)</p>
    </div>
    """


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Temporary cache directory for testing."""
    cache_dir = tmp_path / ".cache"
    cache_dir.mkdir()
    return cache_dir
