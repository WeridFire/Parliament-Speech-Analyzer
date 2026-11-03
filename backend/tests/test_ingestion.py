"""
Tests for the ingestion layer: roster matching, HTML parsing, transport and crawl.

No network: SPARQL and HTTP are injected. The roster index is built from
literals and installed with `set_roster_index`, which is also how the parsers
are meant to be driven in a test.
"""

import pytest

from backend.core.cache import ArtifactCache
from backend.ingestion import crawler as crawler_module
from backend.ingestion.base import ChallengeBlocked, SessionRef, Speech
from backend.ingestion.camera import CameraSource, parse_camera_html
from backend.ingestion.crawler import crawl
from backend.ingestion.rosters import RosterEntry, RosterIndex, set_roster_index
from backend.ingestion.senato import SenatoSource, parse_senato_html
from backend.ingestion.transport import ResilientTransport, looks_like_challenge

from datetime import date


CHALLENGE_BODY = """
<!DOCTYPE html><html><head><title></title></head>
<body><div id="challenge-container"></div>
<noscript><h1>JavaScript is disabled</h1>
In order to continue, we need to verify that you're not a robot.</noscript></body></html>
"""


def entry(full_name, party='', chamber='camera'):
    surname, _, first = full_name.partition(' ')
    return RosterEntry(
        full_name=full_name, surname=surname, first_name=first,
        party=party, chamber=chamber, profile_url=f'http://example.invalid/{surname.lower()}',
    )


@pytest.fixture
def roster() -> RosterIndex:
    index = RosterIndex([
        entry('Meloni Giorgia', 'Fratelli d\'Italia'),
        entry('Schlein Elly', 'Partito Democratico'),
        entry('Renzi Matteo', 'Italia Viva', chamber='senate'),
        entry('Rossi Mario', 'Lega'),
        entry('Rossi Anna', 'Partito Democratico'),
    ])
    set_roster_index(index)
    yield index
    set_roster_index(None)


@pytest.fixture
def session_ref() -> SessionRef:
    return SessionRef(
        chamber='camera', session_id='677', session_date=date(2026, 6, 17),
        number=677, url='http://example.invalid/seduta/677',
    )


# =============================================================================
# ROSTER MATCHING
# =============================================================================

class TestRosterIndex:

    def test_exact_match(self, roster):
        match = roster.match('Meloni Giorgia')
        assert match.name == 'Meloni Giorgia'
        assert match.strategy == 'exact'
        assert not match.ambiguous

    def test_shouted_name_is_normalised(self, roster):
        assert roster.match('MELONI GIORGIA').name == 'Meloni Giorgia'

    def test_surname_only(self, roster):
        match = roster.match('SCHLEIN')
        assert match.name == 'Schlein Elly'
        assert match.strategy == 'surname'

    def test_reversed_order(self, roster):
        """Reports write "Nome Cognome"; the register stores "Cognome Nome"."""
        match = roster.match('Giorgia Meloni')
        assert match.name == 'Meloni Giorgia'
        assert match.strategy == 'reversed'

    def test_register_party_wins_over_scraped(self, roster):
        assert roster.match('MELONI', 'FDI').party == "Fratelli d'Italia"

    def test_unknown_name_rejected(self, roster):
        """Parser false positives must not become speakers."""
        assert roster.match('Concluso') is None
        assert roster.match('') is None

    def test_president_is_not_a_member(self, roster):
        assert roster.match('PRESIDENTE') is None
        assert roster.match('PRESIDENTESSA') is None

    def test_ambiguous_surname_is_flagged(self, roster):
        match = roster.match('ROSSI')
        assert match.ambiguous is True

    def test_party_disambiguates(self, roster):
        match = roster.match('ROSSI', 'Partito Democratico')
        assert match.name == 'Rossi Anna'
        assert match.strategy == 'party-disambiguated'
        assert not match.ambiguous

    def test_lookup_is_indexed_not_scanned(self, roster):
        assert 'meloni' in roster._by_surname
        assert roster._by_exact['Meloni Giorgia'].party == "Fratelli d'Italia"


# =============================================================================
# CAMERA PARSING
# =============================================================================

CAMERA_HTML = """
<div class="sezione">
  <p><a href="/deputati/1">Giorgia Meloni</a> (FDI). Signor Presidente, credo che
     questo provvedimento risponda a un'esigenza reale del Paese e delle imprese.
     (Applausi dei deputati del gruppo Fratelli d'Italia).</p>
  <p><a href="/deputati/2">Elly Schlein</a> (PD-IDP). Presidente, non siamo d'accordo
     con l'impianto complessivo della manovra economica presentata dal Governo.</p>
  <p><a href="/deputati/9">Nomedi Fantasia</a> (XYZ). Questo intervento non appartiene
     a nessun parlamentare presente nell'anagrafe ufficiale della Camera.</p>
  <p><a href="#">PRESIDENTE</a>. La seduta è tolta alle ore venti e trenta minuti.</p>
</div>
"""


class TestCameraParser:

    @pytest.fixture
    def speeches(self, roster, session_ref):
        return parse_camera_html(CAMERA_HTML, session_ref)

    def test_extracts_known_members(self, speeches):
        assert {s.speaker for s in speeches} == {'Meloni Giorgia', 'Schlein Elly'}

    def test_party_comes_from_the_register(self, speeches):
        meloni = next(s for s in speeches if s.speaker == 'Meloni Giorgia')
        assert meloni.party == "Fratelli d'Italia"

    def test_unknown_speaker_is_dropped(self, speeches):
        assert not any('Fantasia' in s.speaker for s in speeches)

    def test_president_is_dropped(self, speeches):
        assert not any('PRESIDENTE' in s.speaker.upper() for s in speeches)

    def test_stage_directions_are_separated(self, speeches):
        meloni = next(s for s in speeches if s.speaker == 'Meloni Giorgia')
        assert 'Applausi' not in meloni.text
        assert any('Applausi' in note for note in meloni.notes)

    def test_session_metadata_is_attached(self, speeches, session_ref):
        for speech in speeches:
            assert speech.date == session_ref.iso_date
            assert speech.session_id == '677'
            assert speech.url == session_ref.url

    def test_match_provenance_is_recorded(self, speeches):
        assert all(s.match_strategy for s in speeches)


# =============================================================================
# SENATO PARSING
# =============================================================================

SENATO_HTML = """
<div class="ressten">
  <p>RENZI (IV-C-RE). Vorrei sottolineare un punto che ritengo fondamentale per il
     futuro del nostro sistema produttivo e per le famiglie italiane.</p>
  <p>PRESIDENTE. Ha chiesto di parlare il senatore, ne ha facoltà per dieci minuti.</p>
  <p>IGNOTO (XYZ). Intervento di una persona che non compare nell'anagrafe ufficiale
     del Senato della Repubblica e va quindi scartato.</p>
  <p>RENZI (IV-C-RE). Troppo corto.</p>
</div>
"""


class TestSenatoParser:

    @pytest.fixture
    def speeches(self, roster):
        ref = SessionRef(
            chamber='senate', session_id='24350', session_date=date(2026, 7, 29),
            number=443, url='http://example.invalid/show-doc?id=24350',
        )
        return parse_senato_html(SENATO_HTML, ref)

    def test_extracts_known_senator(self, speeches):
        assert [s.speaker for s in speeches] == ['Renzi Matteo']

    def test_group_marker_is_used_for_party(self, speeches):
        """The register does not carry senators' groups, the report does."""
        assert speeches[0].party == 'IV-C-RE'

    def test_president_is_dropped(self, speeches):
        assert not any('PRESIDENTE' in s.speaker.upper() for s in speeches)

    def test_unknown_speaker_is_dropped(self, speeches):
        assert not any(s.speaker.upper().startswith('IGNOTO') for s in speeches)

    def test_short_interventions_are_dropped(self, speeches):
        assert all(len(s.text) > 30 for s in speeches)


# =============================================================================
# TRANSPORT
# =============================================================================

class TestChallengeDetection:

    def test_challenge_body_is_recognised(self):
        assert looks_like_challenge(202, CHALLENGE_BODY)

    def test_real_document_is_not(self):
        assert not looks_like_challenge(200, '<html>' + ('x' * 50_000) + '</html>')

    def test_small_ordinary_page_is_not(self):
        assert not looks_like_challenge(200, '<html><body><p>Seduta n. 1</p></body></html>')

    def test_resilient_transport_raises_without_browser(self, monkeypatch):
        transport = ResilientTransport(allow_browser=False)

        def blocked(url):
            raise ChallengeBlocked(url, 202, 'test')

        monkeypatch.setattr(transport.http, 'get', blocked)

        with pytest.raises(ChallengeBlocked):
            transport.get('http://example.invalid/doc')

        assert transport.challenges_seen == 1


# =============================================================================
# CRAWLER
# =============================================================================

class FakeSource:
    """A chamber that answers from a script, for exercising the crawl loop."""

    chamber = 'camera'

    def __init__(self, sessions, behaviour=None):
        self._sessions = sessions
        self._behaviour = behaviour or {}
        self.fetch_count = 0

    def list_sessions(self, months_back):
        return self._sessions

    def fetch_session(self, ref):
        self.fetch_count += 1
        outcome = self._behaviour.get(ref.session_id, 'ok')
        if outcome == 'blocked':
            raise ChallengeBlocked(ref.url, 202, 'test')
        if outcome == 'error':
            raise RuntimeError('parse exploded')
        if outcome == 'empty':
            return []
        return [Speech(speaker='Meloni Giorgia', party='FDI', text='x' * 60, date=ref.iso_date)]


def make_sessions(n):
    return [
        SessionRef(chamber='camera', session_id=str(i), session_date=date(2026, 6, i + 1),
                   number=i, url=f'http://example.invalid/{i}')
        for i in range(1, n + 1)
    ]


class TestCrawler:

    @pytest.fixture
    def cache(self, tmp_path, monkeypatch):
        monkeypatch.setattr('backend.utils.cache.CACHE_DIR', tmp_path)
        return ArtifactCache(root=tmp_path)

    def test_collects_all_sessions(self, cache):
        source = FakeSource(make_sessions(4))
        speeches, report = crawl(source, months_back=2, cache=cache, max_workers=2)

        assert len(speeches) == 4
        assert report.known == 4
        assert report.parsed == 4
        assert report.coverage == 100.0
        assert report.ok

    def test_second_run_uses_the_cache(self, cache):
        """A resumed run must not refetch what it already has."""
        sessions = make_sessions(3)
        first = FakeSource(sessions)
        crawl(first, months_back=2, cache=cache, max_workers=2)

        second = FakeSource(sessions)
        speeches, report = crawl(second, months_back=2, cache=cache, max_workers=2)

        assert second.fetch_count == 0
        assert report.from_cache == 3
        assert len(speeches) == 3

    def test_blocked_sessions_are_counted_not_swallowed(self, cache):
        source = FakeSource(make_sessions(3), {'1': 'blocked', '2': 'blocked'})
        speeches, report = crawl(source, months_back=2, cache=cache, max_workers=2)

        assert report.blocked == 2
        assert report.parsed == 1
        assert not report.ok, "a partially blocked run must not look healthy"

    def test_failures_are_recorded(self, cache):
        source = FakeSource(make_sessions(3), {'2': 'error'})
        _, report = crawl(source, months_back=2, cache=cache, max_workers=2)

        assert report.failed == 1
        assert any('parse exploded' in e for e in report.errors)

    def test_empty_sitting_is_fetched_but_not_parsed(self, cache):
        source = FakeSource(make_sessions(2), {'1': 'empty'})
        _, report = crawl(source, months_back=2, cache=cache, max_workers=2)

        assert report.fetched == 2
        assert report.parsed == 1

    def test_limit_caps_the_run(self, cache):
        source = FakeSource(make_sessions(10))
        _, report = crawl(source, months_back=2, cache=cache, limit=3)

        assert report.known == 3
        assert source.fetch_count == 3

    @pytest.fixture
    def pool_spy(self, monkeypatch):
        """Records the pool size the crawl actually asked for."""
        seen = {}
        real_pool = crawler_module.ThreadPoolExecutor

        def spy(max_workers, *args, **kwargs):
            seen['max_workers'] = max_workers
            return real_pool(max_workers, *args, **kwargs)

        monkeypatch.setattr(crawler_module, 'ThreadPoolExecutor', spy)
        return seen

    def test_source_declares_its_own_concurrency(self, cache, pool_spy):
        """
        A source that cannot be fetched in parallel is fetched in the calling
        thread: the browser transport is bound to the thread that started it,
        and a one-worker pool is still a different thread.
        """
        import threading

        threads = set()
        source = FakeSource(make_sessions(2))
        source.max_workers = 1
        original = source.fetch_session

        def fetch(ref):
            threads.add(threading.get_ident())
            return original(ref)

        source.fetch_session = fetch
        crawl(source, months_back=2, cache=cache)

        assert 'max_workers' not in pool_spy
        assert threads == {threading.get_ident()}

    def test_explicit_workers_override_the_source(self, cache, pool_spy):
        source = FakeSource(make_sessions(2))
        source.max_workers = 1
        crawl(source, months_back=2, cache=cache, max_workers=2)

        assert pool_spy['max_workers'] == 2

    def test_senate_is_serial_and_camera_is_not(self):
        """The browser transport is thread-bound, so the Senate runs on one."""
        assert SenatoSource.max_workers == 1
        assert CameraSource.max_workers > 1

    def test_transport_is_released(self, cache):
        """The browser transport owns a subprocess; the crawl must close it."""
        class Closable:
            closed = False

            def close(self):
                self.closed = True

        source = FakeSource(make_sessions(2))
        source.transport = Closable()
        crawl(source, months_back=2, cache=cache)

        assert source.transport.closed

    def test_listing_failure_is_reported(self, cache):
        class Broken(FakeSource):
            def list_sessions(self, months_back):
                raise RuntimeError('open data down')

        _, report = crawl(Broken([]), months_back=2, cache=cache)

        assert report.known == 0
        assert not report.ok
        assert any('open data down' in e for e in report.errors)


# =============================================================================
# REGRESSIONS
# =============================================================================

SENATO_LISTING = """
<table>
<tr>
  <td class="tab2">Martedì 23 Dicembre 2025</td>
  <td class="tab2" style="font-weight: bold"> 375</td>
  <td class="tab2"><a href="/show-doc?leg=19&amp;tipodoc=Resaula&amp;id=1491441&amp;idoggetto=0"
     title="Resoconto 375.html">html</a></td>
  <td class="tab2"><a href="//www.senato.it/service/PDF/PDFServer/BGT/1491441.pdf"
     title="Resoconto 375.pdf">pdf</a></td>
</tr>
<tr>
  <td class="tab2">Martedì 23 Dicembre 2025</td>
  <td class="tab2"> 376</td>
  <td class="tab2"><a href="/show-doc?leg=19&amp;tipodoc=Resaula&amp;id=1491505&amp;idoggetto=0"
     title="Resoconto 376.html">html</a></td>
</tr>
</table>
"""


class TestSenatoDocumentIds:
    """The open-data sitting id is not the senato.it document id."""

    def test_listing_maps_sitting_numbers_to_documents(self):
        from backend.ingestion.senato import parse_report_listing

        assert parse_report_listing(SENATO_LISTING) == {375: '1491441', 376: '1491505'}

    def test_sessions_use_the_document_id(self, monkeypatch):
        from backend.ingestion import senato as senato_module

        class FakeClient:
            def select(self, query):
                return [{
                    'seduta': 'http://dati.senato.it/sedutaassemblea/24374',
                    'data': '2025-12-23',
                    'numero': '375',
                }]

        class FakeTransport:
            def get(self, url):
                return SENATO_LISTING

        monkeypatch.setattr(senato_module, 'senato_client', lambda: FakeClient())
        [ref] = SenatoSource(transport=FakeTransport()).list_sessions(months_back=2)

        assert ref.session_id == '24374'
        assert 'id=1491441' in ref.url
        assert '24374' not in ref.url


class TestRosterMembership:
    """A dissolved group's open membership must not beat the newer one."""

    def test_most_recent_open_membership_wins(self):
        from backend.ingestion.rosters import _group_label_date, _membership_rank

        old = {'current': True, 'since': _group_label_date('AZIONE - ITALIA VIVA - RENEW EUROPE (13.10.2022)')}
        new = {'current': True, 'since': _group_label_date('AZIONE-POPOLARI EUROPEISTI RIFORMATORI-RENEW EUROPE (14.02.2024)')}
        closed = {'current': False, 'since': '2025-01-01'}

        assert _membership_rank(new) > _membership_rank(old)
        assert _membership_rank(old) > _membership_rank(closed)

    def test_partial_roster_fetch_keeps_the_other_chamber(self, tmp_path, monkeypatch):
        from backend.ingestion import rosters as rosters_module

        cache = ArtifactCache(tmp_path)
        key = rosters_module.CacheKey(kind='rosters', source='leg19')
        cache.save_json(key, [vars(entry('Rossi Mario', 'PD')), vars(entry('Bianchi Anna', chamber='senate'))])

        def down(legislature):
            raise RuntimeError('502')

        monkeypatch.setattr(rosters_module, 'fetch_camera_roster', down)
        monkeypatch.setattr(rosters_module, 'fetch_senato_roster', lambda legislature: [entry('Verdi Luca', chamber='senate')])

        index = rosters_module.build_roster_index(cache=cache, force_refresh=True)

        assert 'Rossi Mario' in index.all_names
        assert 'Verdi Luca' in index.all_names


class TestRecords:

    def test_stage_directions_survive_into_the_record(self):
        speech = Speech(
            speaker='Rossi Mario', party='PD', text='Testo', date='2025-01-01',
            notes=['Applausi dei deputati del gruppo Partito Democratico'],
        )
        assert speech.as_record('camera')['notes'] == ['Applausi dei deputati del gruppo Partito Democratico']

    def test_offline_corpus_comes_from_cached_sittings(self, tmp_path):
        from backend.ingestion import load_cached_sittings

        cache = ArtifactCache(tmp_path)
        speech = Speech(speaker='Rossi Mario', party='PD', text='Testo', date='2025-01-01')
        cache.save_json(crawler_module._session_key(make_sessions(1)[0]), [vars(speech)])

        df = load_cached_sittings('camera', cache=cache)

        assert len(df) == 1
        assert df.loc[0, 'deputy'] == 'Rossi Mario [PD]'
