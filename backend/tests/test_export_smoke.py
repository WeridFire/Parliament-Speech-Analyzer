"""
End-to-end smoke test for the export pipeline.

Runs `export_data.main()` over mock speeches with the network and the embedding
model stubbed out, then asserts the payload it produces is structurally sound and
that no analyzer failed. The unit tests cover analyzers in isolation; this covers
the wiring between them - which is where the alignment and orchestration bugs
live.

Deliberately single-source: `main()` only reaches for ProcessPoolExecutor when a
run spans several chambers, and patches do not survive into worker processes.
"""

import json

import numpy as np
import pandas as pd
import pytest

from backend import export_data
from backend.config import TOPIC_CLUSTERS


N_SPEECHES = 60
EMBEDDING_DIM = 16

# Long enough to clear MIN_WORDS (30) after cleaning strips procedural phrases.
BODY_SENTENCES = [
    "La situazione economica del paese richiede interventi strutturali immediati e "
    "una visione di lungo periodo che tenga insieme crescita, occupazione e sostenibilita "
    "dei conti pubblici nei prossimi anni di legislatura ordinaria.",
    "Il servizio sanitario nazionale attraversa una fase di grande difficolta con liste "
    "di attesa insostenibili per i cittadini e una carenza strutturale di personale medico "
    "e infermieristico in tutte le regioni italiane senza eccezioni.",
    "La transizione ecologica non puo essere rinviata ulteriormente perche il cambiamento "
    "climatico produce effetti concreti sul territorio, sulle imprese agricole e sulla "
    "sicurezza delle comunita che vivono nelle aree piu fragili del paese.",
]


@pytest.fixture(scope='module')
def mock_raw_speeches() -> pd.DataFrame:
    """Raw scraper-shaped frame, before cleaning and filtering."""
    rows = []
    for i in range(N_SPEECHES):
        year = 2023 if i < N_SPEECHES // 2 else 2024
        month = (i % 6) + 1
        rows.append({
            'date': f'{year}-{month:02d}-{(i % 27) + 1:02d}',
            'deputy': f'ROSSI Mario_{i % 6} [Partito {"A" if i % 2 == 0 else "B"}]',
            'speaker_base': f'ROSSI Mario_{i % 6}',
            'group': f'Partito {"A" if i % 2 == 0 else "B"}',
            'text': BODY_SENTENCES[i % len(BODY_SENTENCES)],
            'source': 'camera',
            'url': f'https://example.invalid/seduta/{i}',
            'role': '',
            'role_category': '',
            'profile_url': '',
        })
    return pd.DataFrame(rows)


class StubSentenceTransformer:
    """Stands in for the embedding model when topic descriptions are encoded."""

    def encode(self, texts, **kwargs):
        return _deterministic_embeddings(len(texts), offset=1000)


def _deterministic_embeddings(n: int, offset: int = 0) -> np.ndarray:
    """Reproducible, non-degenerate vectors - no model, no download."""
    rng = np.random.default_rng(offset + n)
    vectors = rng.normal(size=(n, EMBEDDING_DIM))
    return vectors / np.linalg.norm(vectors, axis=1, keepdims=True)


@pytest.fixture(scope='module')
def exported_payload(tmp_path_factory, mock_raw_speeches):
    """
    Run the real pipeline against stubs once and return the parsed output.

    Module-scoped on purpose: this drives the whole export, so running it per
    test costs minutes. `pytest.MonkeyPatch` is used directly because the
    `monkeypatch` fixture is function-scoped.
    """
    backend_dir = tmp_path_factory.mktemp('project') / 'backend'
    backend_dir.mkdir()

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(export_data, 'SCRIPT_DIR', backend_dir)
        mp.setattr(
            export_data, 'load_cached_speeches',
            lambda source, max_age_days=None: mock_raw_speeches.copy(),
        )
        mp.setattr(export_data, 'load_cached_embeddings', lambda source, fingerprint: None)
        mp.setattr(export_data, 'save_embeddings_cache', lambda embeddings, source, fingerprint: None)
        mp.setattr(export_data, 'get_embedding_model', lambda *a, **k: StubSentenceTransformer())
        mp.setattr(
            export_data, 'generate_embeddings',
            lambda texts, model_name=None: _deterministic_embeddings(len(texts)),
        )

        export_data.main(source='camera')

    data_dir = backend_dir.parent / 'frontend' / 'public' / 'data'
    manifest_path = data_dir / 'manifest.json'
    assert manifest_path.exists(), "pipeline produced no manifest"

    def load(relative):
        with open(data_dir / relative, 'r', encoding='utf-8') as f:
            return json.load(f)

    manifest = load('manifest.json')
    chamber = manifest['chambers']['camera']
    resources = chamber['resources']

    return {
        'dir': data_dir,
        'manifest': manifest,
        'chamber': chamber,
        'core': load(resources['core']['path']),
        'speeches': load(resources['speeches']['path']),
        'analytics': {
            'global': load(resources['analytics']['global']['path']),
            'by_year': {
                period: load(ref['path'])
                for period, ref in resources['analytics']['by_year'].items()
            },
            'by_month': {
                period: load(ref['path'])
                for period, ref in resources['analytics']['by_month'].items()
            },
        },
    }


# =============================================================================
# STRUCTURE
# =============================================================================

class TestPayloadStructure:

    def test_manifest_indexes_every_resource(self, exported_payload):
        resources = exported_payload['chamber']['resources']
        assert set(resources) == {'core', 'speeches', 'analytics'}

        for ref in (resources['core'], resources['speeches']):
            assert ref['bytes'] > 0
            assert ref['digest']
            assert (exported_payload['dir'] / ref['path']).exists()

    def test_core_holds_what_first_paint_needs(self, exported_payload):
        assert set(exported_payload['core']) >= {
            'deputies', 'deputies_by_period', 'clusters',
            'rebels', 'all_divergence_scores', 'stats',
        }

    def test_speeches_are_a_separate_resource(self, exported_payload):
        """Speeches are the bulk of the payload and must be lazily loadable."""
        assert 'speeches' not in exported_payload['core']
        assert len(exported_payload['speeches']) == N_SPEECHES
        assert exported_payload['core']['stats']['total_speeches'] == N_SPEECHES

    def test_speech_records_are_complete(self, exported_payload):
        for speech in exported_payload['speeches']:
            assert speech['deputy']
            assert speech['party']
            assert speech['date']
            assert isinstance(speech['cluster'], int)
            assert np.isfinite(speech['x']) and np.isfinite(speech['y'])

    def test_speech_text_is_single_and_original_case(self, exported_payload):
        """`text`/`snippet` used to duplicate the speech, lowercased and not."""
        for speech in exported_payload['speeches']:
            assert 'snippet' not in speech
            assert speech['text']
        assert any(s['text'] != s['text'].lower() for s in exported_payload['speeches'])

    def test_topic_scores_match_configured_topics(self, exported_payload):
        expected = len(TOPIC_CLUSTERS)
        for speech in exported_payload['speeches']:
            assert len(speech['topic_scores']) == expected

    def test_assignment_confidence_is_exported(self, exported_payload):
        for speech in exported_payload['speeches']:
            assert 'cluster_conf' in speech
            assert speech['cluster_conf'] >= 0

    def test_deputies_are_aggregated(self, exported_payload):
        deputies = exported_payload['core']['deputies']
        assert deputies
        assert sum(d['n_speeches'] for d in deputies) <= N_SPEECHES

    def test_divergence_replaces_rebel_naming(self, exported_payload):
        for deputy in exported_payload['core']['deputies']:
            assert 'divergence_pct' in deputy
            assert 'rebel_pct' not in deputy


# =============================================================================
# ANALYTICS
# =============================================================================

class TestAnalytics:

    def test_no_analyzer_reported_an_error(self, exported_payload):
        failures = {
            name: block['error']
            for name, block in exported_payload['analytics']['global'].items()
            if isinstance(block, dict) and 'error' in block
        }
        assert not failures, f"analyzers failed: {failures}"

    def test_run_report_is_exported(self, exported_payload):
        """A partial run must be visible in the payload, not silent."""
        run = exported_payload['core']['stats']['analytics_run']
        assert run['failed_analyzers'] == []

    def test_expected_analyzers_ran(self, exported_payload):
        assert set(exported_payload['analytics']['global']) >= {
            'identity', 'sentiment', 'temporal', 'relations',
            'speaker', 'rhetoric', 'factions', 'alliances', 'topics',
        }

    def test_period_buckets_exist(self, exported_payload):
        analytics = exported_payload['analytics']
        assert analytics['by_year'], "no per-year analytics"
        assert set(analytics['by_year']) == {'2023', '2024'}

    def test_period_analytics_omit_corpus_level_metrics(self, exported_payload):
        """
        Analyzers that measure change over time, or need a large sample, decline
        to run on a period slice instead of publishing noise.
        """
        for period, block in exported_payload['analytics']['by_year'].items():
            assert 'temporal' not in block, f"{period}: temporal is a global-only metric"
            assert 'topics' not in block, f"{period}: cluster labels are corpus-level"

    def test_period_analytics_have_no_errors(self, exported_payload):
        for period, block in exported_payload['analytics']['by_year'].items():
            failures = [
                name for name, result in block.items()
                if isinstance(result, dict) and 'error' in result
            ]
            assert not failures, f"{period}: analyzers failed: {failures}"


# =============================================================================
# PERIOD CONSISTENCY
# =============================================================================

class TestPeriodConsistency:

    def test_deputy_periods_do_not_exceed_the_corpus(self, exported_payload):
        by_year = exported_payload['core']['deputies_by_period']['by_year']
        total = sum(d['n_speeches'] for deputies in by_year.values() for d in deputies)
        assert total <= N_SPEECHES

    def test_available_periods_match_buckets(self, exported_payload):
        by_period = exported_payload['core']['deputies_by_period']
        assert set(by_period['available_periods']['years']) == {
            int(y) for y in by_period['by_year']
        }
        assert set(by_period['available_periods']['months']) == set(by_period['by_month'])

    def test_manifest_periods_match_analytics_resources(self, exported_payload):
        periods = exported_payload['chamber']['periods']
        analytics = exported_payload['chamber']['resources']['analytics']
        assert set(periods['years']) == set(analytics['by_year'])
        assert set(periods['months']) == set(analytics['by_month'])

    def test_clusters_referenced_by_speeches_are_described(self, exported_payload):
        described = {int(cid) for cid in exported_payload['core']['clusters']}
        used = {s['cluster'] for s in exported_payload['speeches']}
        assert used <= described, f"undescribed clusters in payload: {used - described}"
