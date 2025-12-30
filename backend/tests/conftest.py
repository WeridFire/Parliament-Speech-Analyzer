"""
Test Configuration - Shared pytest fixtures and settings.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.tests.fixtures import MockData, get_mock_data, reset_mock_data
import numpy as np
import pandas as pd


# =============================================================================
# PYTEST CONFIGURATION
# =============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "slow: mark test as slow to run")


# =============================================================================
# PYTEST FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def mock_data() -> MockData:
    """
    Session-scoped mock data fixture.
    
    Reused across all tests in the session for efficiency.
    """
    return MockData()


@pytest.fixture(scope="function")
def fresh_mock_data() -> MockData:
    """
    Function-scoped mock data fixture.
    
    Creates fresh mock data for each test function.
    """
    return MockData()


@pytest.fixture(scope="session")
def mock_df(mock_data):
    """Mock DataFrame fixture."""
    return mock_data.df


@pytest.fixture(scope="session")
def mock_embeddings(mock_data):
    """Mock embeddings fixture."""
    return mock_data.embeddings


@pytest.fixture(scope="session")
def mock_cluster_centroids(mock_data):
    """Mock cluster centroids fixture."""
    return mock_data.cluster_centroids


@pytest.fixture(scope="session")
def mock_cluster_labels(mock_data):
    """Mock cluster labels fixture."""
    return mock_data.cluster_labels


@pytest.fixture(scope="session")
def analyzer_kwargs(mock_data):
    """Common kwargs for analyzer initialization."""
    return mock_data.get_analyzer_kwargs()


@pytest.fixture
def sample_embeddings() -> np.ndarray:
    """
    Small sample embeddings for pipeline tests.
    Shape: (10, 50)
    """
    np.random.seed(42)
    return np.random.rand(10, 50).astype(np.float32)


@pytest.fixture
def sample_speeches_df() -> pd.DataFrame:
    """
    Small sample DataFrame for pipeline tests.
    """
    return pd.DataFrame({
        'deputy': [f'Deputy {i}' for i in range(10)],
        'group': ['Party A'] * 5 + ['Party B'] * 5,
        'text': [f'Speech text {i}' for i in range(10)],
        'date': '2024-01-01'
    })


@pytest.fixture
def camera_html_sample() -> str:
    """Sample HTML for Camera parsing tests."""
    return """
    <div class="sezione">
        <p>
            <a href="#">MELONI</a> (FDI). Signor Presidente, questo è un intervento di prova.
            (Applausi dei deputati del gruppo Fratelli d'Italia).
        </p>
        <p>
            <a href="#">SCHLEIN</a> (PD-IDP). Presidente, non siamo d'accordo.
        </p>
        <p>
            <a href="#">PRESIDENTE</a>. La seduta è tolta.
        </p>
    </div>
    """


@pytest.fixture
def senate_html_sample() -> str:
    """Sample HTML for Senate parsing tests."""
    return """
    <div class="ressten">
        <p>MELONI (FDI). Signor Presidente, intervenendo in questa seduta...</p>
        <p>RENZI (IV-C-RE). Vorrei sottolineare un punto fondamentale.</p>
        <p>PRESIDENTE. Ha chiesto di parlare il senatore...</p>
    </div>
    """


# =============================================================================
# TEST HELPERS
# =============================================================================

def assert_valid_result(result: dict, required_keys: list[str] = None):
    """Assert that result is a valid non-empty dict."""
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    assert len(result) > 0, "Result should not be empty"
    
    if required_keys:
        for key in required_keys:
            assert key in result, f"Missing required key: {key}"


def assert_valid_score(score: float, min_val: float = 0, max_val: float = 100):
    """Assert that score is within expected range."""
    assert isinstance(score, (int, float)), f"Expected number, got {type(score)}"
    assert min_val <= score <= max_val, f"Score {score} not in range [{min_val}, {max_val}]"


def assert_valid_speaker_data(data: dict, mock_data: MockData):
    """Assert that speaker data contains valid speaker names."""
    for speaker in data.keys():
        if speaker not in ('rankings', 'by_topic', 'topic_leaders', 'error'):
            assert speaker in mock_data.df['deputy'].values, f"Unknown speaker: {speaker}"
