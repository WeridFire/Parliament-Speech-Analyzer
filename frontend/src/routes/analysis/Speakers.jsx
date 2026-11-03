import { useDeferredValue, useMemo, useState } from 'react';
import { Search } from 'lucide-react';
import { Card, CardBody, CardHeader, RankingList, ScopeNote, Select, StatTile } from '../../ui';
import { Radar } from '../../viz/charts/Radar';
import { useAnalysis } from './context';
import { partyDot, partyName, partyShort } from '../../domain/parties';
import { BLOC_LABELS, SPEAKER_RANKINGS } from '../../domain/metrics';
import { cleanName } from '../../data/selectors';
import { dec, dec2, int, pct } from '../../lib/format';
import { EmptyState, NoDataForPeriod } from '../../ui/EmptyState';
import { cn } from '../../lib/cn';

/**
 * Individual speaker profiles and the backend rankings.
 */
export default function Speakers() {
  const { section, period, mode } = useAnalysis();
  const { data: speaker, fromGlobal } = section('speaker');

  const bySpeaker = useMemo(() => speaker?.by_speaker ?? {}, [speaker]);
  const rankings = useMemo(() => speaker?.rankings ?? {}, [speaker]);

  const names = useMemo(
    () => Object.keys(bySpeaker).sort((a, b) => bySpeaker[b].n_speeches - bySpeaker[a].n_speeches),
    [bySpeaker],
  );
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState(null);
  const deferred = useDeferredValue(query);

  // The whole roster, filtered: a few hundred rows render without trouble, and
  // capping the list (it was cut at 12) hid most members from anyone scrolling.
  const results = useMemo(() => {
    const q = deferred.trim().toLowerCase();
    return q ? names.filter((n) => n.toLowerCase().includes(q)) : names;
  }, [names, deferred]);

  const active = selected && bySpeaker[selected] ? selected : results[0];

  // Only offer rankings the backend actually emitted.
  const availableRankings = useMemo(
    () => SPEAKER_RANKINGS.filter((r) => Array.isArray(rankings[r.id]) && rankings[r.id].length),
    [rankings],
  );
  const [rankingId, setRankingId] = useState(null);
  const activeRanking = availableRankings.find((r) => r.id === rankingId) ?? availableRankings[0];

  const rankingRows = useMemo(() => {
    if (!activeRanking) return [];
    const rows = rankings[activeRanking.id] ?? [];
    const max = Math.max(...rows.map(([, v]) => v), 1e-9);
    const format = activeRanking.digits === 2 ? dec2 : activeRanking.digits === 1 ? dec : int;
    return rows.map(([name, value]) => {
      const party = bySpeaker[name]?.party;
      return {
        key: name,
        name: cleanName(name),
        meta: party ? partyShort(party) : undefined,
        percent: (value / max) * 100,
        value: `${format(value)}${activeRanking.unit ? ` ${activeRanking.unit}` : ''}`,
        dot: party ? partyDot(party, mode) : undefined,
      };
    });
  }, [activeRanking, rankings, bySpeaker, mode]);

  if (!speaker) return <NoDataForPeriod feature="le statistiche individuali" period={period} />;

  return (
    <div className="grid gap-5 lg:grid-cols-[320px_minmax(0,1fr)]">
      <div className="lg:col-span-2">
        <ScopeNote fromGlobal={fromGlobal} period={period} />
      </div>

      <Card className="lg:row-span-2">
        <CardHeader title="Parlamentari" subtitle={`${names.length} con almeno 5 interventi`} />
        <CardBody className="py-3">
          <div className="relative">
            <Search
              size={14}
              className="pointer-events-none absolute top-1/2 left-2.5 -translate-y-1/2 text-muted"
              aria-hidden="true"
            />
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Cognome…"
              aria-label="Cerca un parlamentare"
              className="w-full rounded-sm border border-rule bg-surface py-1.5 pr-2.5 pl-8 text-body text-ink transition-colors duration-150 hover:border-rule-strong"
            />
          </div>

          <ul className="mt-2 max-h-160 overflow-y-auto">
            {results.map((name) => (
              <li key={name}>
                <button
                  type="button"
                  onClick={() => setSelected(name)}
                  className={cn(
                    'flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-left transition-colors duration-150',
                    name === active ? 'bg-accent-soft' : 'hover:bg-hover',
                  )}
                >
                  <span
                    className="h-2 w-2 shrink-0 rounded-full"
                    style={{ backgroundColor: partyDot(bySpeaker[name].party, mode) }}
                    aria-hidden="true"
                  />
                  <span className="min-w-0 flex-1 truncate text-body text-ink">{cleanName(name)}</span>
                  <span className="tabular shrink-0 text-label text-muted">{bySpeaker[name].n_speeches}</span>
                </button>
              </li>
            ))}
            {!results.length ? <EmptyState message="Nessun risultato." /> : null}
          </ul>
        </CardBody>
      </Card>

      {active ? (
        <SpeakerProfile name={active} stats={bySpeaker[active]} mode={mode} />
      ) : (
        <Card>
          <CardBody>
            <EmptyState message="Seleziona un parlamentare per vederne il profilo." />
          </CardBody>
        </Card>
      )}

      <Card>
        <CardHeader
          title="Classifiche"
          subtitle={activeRanking?.hint}
          actions={
            availableRankings.length > 1 ? (
              <Select
                label="Classifica"
                hideLabel
                value={activeRanking?.id ?? ''}
                onChange={setRankingId}
                className="w-60"
                options={availableRankings.map((r) => ({ value: r.id, label: r.label }))}
              />
            ) : null
          }
        />
        <CardBody>
          <RankingList items={rankingRows} />
        </CardBody>
      </Card>
    </div>
  );
}

function SpeakerProfile({ name, stats, mode }) {
  const { verbosity, linguistic, vocabulary, top_topics: topTopics, reactions } = stats ?? {};

  /**
   * Linguistic profile, normalised to 0–1. Rates are per 1.000 words and
   * unbounded in principle, so each is capped at a fixed ceiling rather than
   * scaled to the observed max — otherwise the shape would change meaning every
   * time the filter changes.
   */
  const radar = useMemo(() => {
    if (!linguistic) return [];
    const norm = (v, ceiling) => Math.min((v ?? 0) / ceiling, 1);
    return [
      {
        key: name,
        label: cleanName(name),
        values: [
          norm(linguistic.question_rate, 15),
          norm(linguistic.self_reference_rate, 30),
          norm(linguistic.negation_rate, 50),
          norm(linguistic.data_citation_rate, 10),
          norm(verbosity?.avg_sentence_words, 50),
          norm(vocabulary?.mattr, 1),
        ],
      },
    ];
  }, [name, linguistic, verbosity, vocabulary]);

  return (
    <Card>
      <CardHeader
        title={cleanName(name)}
        subtitle={`${partyName(stats.party)} · ${BLOC_LABELS[stats.bloc] ?? ''}`}
      />
      <CardBody className="flex flex-col gap-6">
        <div className="grid grid-cols-2 gap-x-5 gap-y-4 sm:grid-cols-4">
          <StatTile label="Interventi" value={int(stats.n_speeches)} meta={`in ${stats.speaking_days} giornate`} />
          <StatTile
            label="Mesi attivi"
            value={`${stats.active_months}/${stats.total_months}`}
            meta="mesi con almeno un intervento"
          />
          <StatTile label="Parole/intervento" value={int(verbosity?.avg_words)} />
          <StatTile
            label="Varietà lessicale"
            value={vocabulary ? dec2(vocabulary.mattr) : '—'}
            meta={vocabulary ? 'MATTR, finestre di 500 parole' : 'servono almeno 1.000 parole'}
          />
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <div>
            <h4 className="mb-1 text-label text-muted">PROFILO LINGUISTICO</h4>
            <Radar
              axes={['Domande', 'Prima persona', 'Negazioni', 'Dati citati', 'Frasi lunghe', 'Lessico vario']}
              series={radar}
              mode={mode}
              height={300}
              title="Profilo linguistico"
            />
          </div>

          <div className="flex flex-col gap-5">
            <div>
              <h4 className="mb-2 text-label text-muted">TEMI PRINCIPALI</h4>
              {topTopics?.length ? (
                <ul className="flex flex-col">
                  {topTopics.map((t) => (
                    <li key={t.topic} className="flex items-baseline justify-between gap-3 border-b border-rule py-1.5 last:border-b-0">
                      <span className="truncate text-body text-ink">{t.label}</span>
                      <span className="tabular shrink-0 text-num text-secondary">
                        {pct(t.share)} · {int(t.n)}
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-body text-secondary">Nessun intervento classificato.</p>
              )}
            </div>

            <div>
              <h4 className="mb-2 text-label text-muted">REAZIONI DELL&apos;AULA</h4>
              <p className="text-body text-secondary">
                <span className="tabular text-ink">{int(reactions?.applauded_by_others)}</span> interventi
                applauditi da altri gruppi ·{' '}
                <span className="tabular text-ink">{int(reactions?.contested)}</span> contestati
              </p>
            </div>
          </div>
        </div>
      </CardBody>
    </Card>
  );
}
