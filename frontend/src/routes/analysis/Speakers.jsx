import { useDeferredValue, useMemo, useState } from 'react';
import { Search } from 'lucide-react';
import { Card, CardBody, CardHeader, RankingList, Select, StatTile, Table } from '../../ui';
import { Radar } from '../../viz/charts/Radar';
import { useAnalysis } from './AnalysisLayout';
import { partyDot, partyShort, resolveParty } from '../../domain/parties';
import { SPEAKER_RANKINGS } from '../../domain/metrics';
import { cleanName } from '../../data/selectors';
import { dec, dec2, int, pct } from '../../lib/format';
import { EmptyState, NoDataForPeriod } from '../../ui/EmptyState';
import { ClassificationTag } from '../../ui/Chip';
import { cn } from '../../lib/cn';

/**
 * Individual speaker profiles and the four backend rankings.
 */
export default function Speakers() {
  const { analytics, clusters, period, mode } = useAnalysis();
  const speaker = analytics?.speaker;

  const bySpeaker = speaker?.by_speaker ?? {};
  const rankings = speaker?.rankings ?? {};

  const names = useMemo(() => Object.keys(bySpeaker).sort(), [bySpeaker]);
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState(null);
  const deferred = useDeferredValue(query);

  const results = useMemo(() => {
    const q = deferred.trim().toLowerCase();
    if (!q) return names.slice(0, 12);
    return names.filter((n) => n.toLowerCase().includes(q)).slice(0, 12);
  }, [names, deferred]);

  const active = selected && bySpeaker[selected] ? selected : results[0];

  // Only offer rankings the backend actually emitted. The old tab configured a
  // dozen categories, most of which did not exist in the data, and omitted
  // `most_active`, which does.
  const availableRankings = useMemo(
    () => SPEAKER_RANKINGS.filter((r) => Array.isArray(rankings[r.id]) && rankings[r.id].length),
    [rankings],
  );
  const [rankingId, setRankingId] = useState(null);
  const activeRanking =
    availableRankings.find((r) => r.id === rankingId) ?? availableRankings[0];

  const rankingRows = useMemo(() => {
    if (!activeRanking) return [];
    const rows = rankings[activeRanking.id] ?? [];
    const max = Math.max(...rows.map(([, v]) => v), 1);
    return rows.map(([name, value]) => {
      const party = bySpeaker[name] ? partyOf(name) : null;
      return {
        key: name,
        name: cleanName(name),
        meta: party ? partyShort(party) : undefined,
        percent: (value / max) * 100,
        value:
          activeRanking.unit === '%'
            ? pct(value)
            : `${activeRanking.digits === 2 ? dec2(value) : activeRanking.digits === 1 ? dec(value) : int(value)}${
                activeRanking.unit ? ` ${activeRanking.unit}` : ''
              }`,
        dot: party ? partyDot(party, mode) : undefined,
      };
    });
  }, [activeRanking, rankings, bySpeaker, mode]);

  if (!speaker) return <NoDataForPeriod feature="le statistiche individuali" period={period} />;

  return (
    <div className="grid gap-5 lg:grid-cols-[320px_minmax(0,1fr)]">
      <Card className="lg:row-span-2">
        <CardHeader title="Parlamentari" subtitle={`${names.length} con dati sufficienti`} />
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

          <ul className="mt-2 max-h-[26rem] overflow-y-auto">
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
                    style={{ backgroundColor: partyDot(partyOf(name), mode) }}
                    aria-hidden="true"
                  />
                  <span className="min-w-0 flex-1 truncate text-body text-ink">
                    {cleanName(name)}
                  </span>
                </button>
              </li>
            ))}
            {!results.length ? <EmptyState message="Nessun risultato." /> : null}
          </ul>
        </CardBody>
      </Card>

      {active ? (
        <SpeakerProfile name={active} stats={bySpeaker[active]} clusters={clusters} mode={mode} />
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
                className="w-56"
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

/** "SURNAME Name [PD-IDP]" -> "PD-IDP" */
function partyOf(deputyKey) {
  const m = /\[([^\]]+)\]\s*$/.exec(deputyKey ?? '');
  return m ? m[1] : '';
}

function SpeakerProfile({ name, stats, clusters, mode }) {
  const { verbosity, linguistic, consistency, vocabulary, intervention, network, topic_leadership } =
    stats ?? {};

  /**
   * Six-axis linguistic profile, normalised to 0–1. Rates are per 1.000 words
   * and unbounded in principle, so each is capped at a sane ceiling rather than
   * scaled to the observed max — otherwise the shape would change meaning every
   * time the filter changes.
   */
  const radar = useMemo(() => {
    if (!linguistic && !verbosity) return [];
    const norm = (v, ceiling) => Math.min((v ?? 0) / ceiling, 1);
    return [
      {
        key: name,
        label: cleanName(name),
        values: [
          norm(linguistic?.question_rate, 20),
          norm(linguistic?.self_reference_rate, 30),
          norm(linguistic?.negation_rate, 30),
          norm(linguistic?.data_citation_rate, 20),
          norm(verbosity?.avg_words_per_sentence, 60),
          norm(vocabulary?.type_token_ratio, 1) ,
        ],
      },
    ];
  }, [name, linguistic, verbosity, vocabulary]);

  return (
    <Card>
      <CardHeader
        title={cleanName(name)}
        subtitle={resolveParty(partyOf(name)).name}
        actions={
          consistency?.classification ? (
            <ClassificationTag value={consistency.classification} />
          ) : null
        }
      />
      <CardBody className="flex flex-col gap-6">
        <div className="grid grid-cols-2 gap-x-5 gap-y-4 sm:grid-cols-4">
          <StatTile label="Interventi" value={int(stats?.n_speeches)} />
          <StatTile
            label="Parole/intervento"
            value={int(verbosity?.avg_words_per_speech)}
          />
          <StatTile
            label="Ricchezza lessicale"
            value={dec2(vocabulary?.type_token_ratio)}
            meta={vocabulary?.classification ? undefined : 'sotto soglia'}
          />
          <StatTile
            label="Regolarità"
            value={pct(intervention?.regularity_score)}
            meta={
              intervention?.active_months
                ? `${intervention.active_months}/${intervention.total_months} mesi attivi`
                : undefined
            }
          />
        </div>

        {radar.length ? (
          <div>
            <h4 className="mb-1 text-label text-muted">PROFILO LINGUISTICO</h4>
            <Radar
              axes={['Domande', 'Prima persona', 'Negazioni', 'Dati citati', 'Periodo lungo', 'Lessico vario']}
              series={radar}
              mode={mode}
              height={320}
              title="Profilo linguistico"
            />
          </div>
        ) : null}

        {/*
          FIX: this section previously gated on `topic_leadership.topics_led_labels`
          and `dominant_topic_label`, neither of which the backend emits — it
          produces `best_topic`, `best_topic_label` and `best_similarity`. The
          whole block therefore never rendered.
        */}
        {topic_leadership?.best_topic_label ? (
          <div className="border-t border-rule pt-4">
            <h4 className="mb-1 text-label text-muted">AREA DI COMPETENZA</h4>
            <p className="text-body text-ink">
              {topic_leadership.best_topic_label}
              <span className="ml-2 text-muted">
                similarità {dec2(topic_leadership.best_similarity)}
              </span>
            </p>
          </div>
        ) : null}

        {network && (network.mentions_given || network.mentions_received) ? (
          <div className="border-t border-rule pt-4">
            <h4 className="mb-2 text-label text-muted">RETE DELLE CITAZIONI</h4>
            <Table
              caption="Citazioni date e ricevute"
              columns={[
                { key: 'label', header: 'Direzione' },
                { key: 'count', header: 'Numero', numeric: true, width: '6rem' },
                { key: 'who', header: 'Principali' },
              ]}
              rows={[
                {
                  label: 'Cita',
                  count: int(network.mentions_given),
                  who: topNames(network.top_mentioned),
                },
                {
                  label: 'È citato da',
                  count: int(network.mentions_received),
                  who: topNames(network.mentioned_by),
                },
              ]}
              getRowKey={(r) => r.label}
            />
          </div>
        ) : null}
      </CardBody>
    </Card>
  );
}

function topNames(pairs) {
  if (!pairs?.length) return '—';
  return pairs
    .slice(0, 3)
    .map(([n]) => cleanName(n))
    .join(', ');
}
