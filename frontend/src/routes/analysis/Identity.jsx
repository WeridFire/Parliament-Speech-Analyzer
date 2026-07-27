import { useMemo, useState } from 'react';
import { Card, CardBody, CardHeader, PartyChip, RankingList, SegmentedControl, Table } from '../../ui';
import { Radar } from '../../viz/charts/Radar';
import { WordCloud } from '../../viz/charts/WordCloud';
import { useAnalysis } from './AnalysisLayout';
import { topicList, topicShort } from '../../domain/topics';
import { partyDot, partyName, sortParties } from '../../domain/parties';
import { cleanName, topEntries, bottomEntries } from '../../data/selectors';
import { dec2, pct } from '../../lib/format';
import { NoDataForPeriod } from '../../ui/EmptyState';

/**
 * Thematic fingerprints, generalism and distinctive vocabulary.
 */
export default function Identity() {
  const { analytics, clusters, period, mode } = useAnalysis();
  const identity = analytics?.identity;

  const fingerprints = identity?.thematic_fingerprints?.by_party ?? {};
  const generalism = identity?.generalism_index ?? {};
  const keywords = identity?.distinctive_keywords ?? {};

  const parties = useMemo(() => sortParties(Object.keys(fingerprints)), [fingerprints]);
  const [selected, setSelected] = useState(null);
  const [scope, setScope] = useState('by_party');

  const active = selected && parties.includes(selected) ? selected : parties[0];
  const topics = useMemo(() => topicList(clusters), [clusters]);

  const radarSeries = useMemo(() => {
    if (!active || !fingerprints[active]) return [];
    const fp = fingerprints[active];
    return [
      {
        key: active,
        label: partyName(active),
        values: topics.map((t) => fp[t.id] ?? fp[String(t.id)] ?? 0),
      },
    ];
  }, [active, fingerprints, topics]);

  const ranking = useMemo(() => {
    const source = generalism[scope];
    if (!source) return { generalists: [], specialists: [] };

    const shape = (e) => ({
      key: e.name,
      name: scope === 'by_party' ? partyName(e.name) : cleanName(e.name),
      meta:
        scope === 'by_party'
          ? `${e.raw.n_speeches} interventi`
          : `Tema prevalente: ${topicShort(e.raw.dominant_topic, clusters)}`,
      // generalism.score is already 0–100.
      percent: e.value,
      value: pct(e.value),
      dot: scope === 'by_party' ? partyDot(e.name, mode) : undefined,
    });

    const opts = { valueOf: (v) => v.score, filter: (e) => (e.raw.n_speeches ?? 0) >= 5, limit: 10 };
    return {
      generalists: topEntries(source, opts).map(shape),
      specialists: bottomEntries(source, opts).map(shape),
    };
  }, [generalism, scope, clusters, mode]);

  if (!identity) return <NoDataForPeriod feature="l'analisi dell'identità" period={period} />;

  return (
    <div className="grid gap-5 lg:grid-cols-2">
      <Card>
        <CardHeader
          title="Impronta tematica"
          subtitle="Similarità semantica del gruppo con ciascuna area, da 0 a 1"
        />
        <CardBody>
          <div className="mb-4 flex flex-wrap gap-1.5">
            {parties.map((p) => (
              <PartyChip
                key={p}
                party={p}
                mode={mode}
                size="sm"
                selected={p === active}
                onClick={() => setSelected(p)}
              />
            ))}
          </div>
          <Radar
            axes={topics.map((t) => t.short)}
            series={radarSeries}
            mode={mode}
            height={360}
            title="Impronta tematica"
          />
        </CardBody>
      </Card>

      <Card>
        <CardHeader
          title="Vocabolario distintivo"
          subtitle={active ? partyName(active) : 'Seleziona un gruppo'}
        />
        <CardBody className="flex items-center justify-center">
          <WordCloud words={active ? keywords[active] : []} mode={mode} max={36} />
        </CardBody>
      </Card>

      <Card className="lg:col-span-2">
        <CardHeader
          title="Indice di generalismo"
          subtitle="Ampiezza tematica: 100 = interviene su tutte le aree, 0 = una sola"
          actions={
            <SegmentedControl
              size="sm"
              value={scope}
              onChange={setScope}
              options={[
                { value: 'by_party', label: 'Gruppi' },
                { value: 'by_deputy', label: 'Parlamentari' },
              ]}
            />
          }
        />
        <CardBody className="grid gap-x-10 gap-y-6 md:grid-cols-2">
          <div>
            <h4 className="mb-2 text-label text-muted">PIÙ GENERALISTI</h4>
            <RankingList items={ranking.generalists} />
          </div>
          <div>
            <h4 className="mb-2 text-label text-muted">PIÙ SPECIALIZZATI</h4>
            <RankingList items={ranking.specialists} />
          </div>
        </CardBody>
      </Card>

      <Card className="lg:col-span-2">
        <CardHeader
          title="Impronta tematica per gruppo"
          subtitle="Gli stessi valori del radar, in forma tabellare"
        />
        <CardBody>
          <Table
            caption="Similarità semantica per gruppo e area tematica"
            columns={[
              { key: 'party', header: 'Gruppo', render: (r) => r.party },
              ...topics.map((t) => ({
                key: String(t.id),
                header: t.short,
                numeric: true,
                render: (r) => dec2(r.values[t.id]),
              })),
            ]}
            rows={parties.map((p) => ({
              party: partyName(p),
              values: Object.fromEntries(
                topics.map((t) => [t.id, fingerprints[p]?.[t.id] ?? fingerprints[p]?.[String(t.id)] ?? 0]),
              ),
            }))}
            getRowKey={(r) => r.party}
          />
        </CardBody>
      </Card>
    </div>
  );
}
