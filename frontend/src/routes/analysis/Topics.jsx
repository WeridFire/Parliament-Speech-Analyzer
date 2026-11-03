import { useMemo, useState } from 'react';
import { Card, CardBody, CardFooter, CardHeader, RankingList, ScopeNote, Select } from '../../ui';
import { CategoryBars } from '../../viz/charts/CategoryBars';
import { WordCloud } from '../../viz/charts/WordCloud';
import { useAnalysis } from './context';
import { topicShort } from '../../domain/topics';
import { partyDot, partyName, partyShort } from '../../domain/parties';
import { cleanName } from '../../data/selectors';
import { dec, int, pct } from '../../lib/format';
import { NoDataForPeriod } from '../../ui/EmptyState';

/**
 * Who carries each topic: the members who intervene on it most, the groups
 * that invest in it beyond their size, and the words that characterise it.
 */
export default function Topics() {
  const { section, clusters, period, mode } = useAnalysis();
  const { data: topicsData, fromGlobal } = section('topics');

  const entries = useMemo(
    () =>
      Object.entries(topicsData?.by_topic ?? {})
        .map(([id, info]) => ({ id, ...info }))
        .sort((a, b) => b.n - a.n),
    [topicsData],
  );

  const [topicId, setTopicId] = useState('');
  const topic = entries.find((e) => e.id === topicId) ?? entries[0];

  const overview = useMemo(
    () => ({
      categories: entries.map((e) => topicShort(Number(e.id), clusters)),
      series: [{ key: 'share', label: 'Quota degli interventi', values: entries.map((e) => e.share) }],
    }),
    [entries, clusters],
  );

  const speakers = useMemo(() => {
    const list = topic?.top_speakers ?? [];
    const max = Math.max(1, ...list.map((s) => s.n));
    return list.map((s) => ({
      key: s.speaker,
      name: cleanName(s.speaker),
      meta: `${partyShort(s.party)} · ${pct(s.focus)} dei suoi interventi`,
      percent: (s.n / max) * 100,
      value: `${int(s.n)}`,
      dot: partyDot(s.party, mode),
    }));
  }, [topic, mode]);

  const parties = useMemo(
    () =>
      (topic?.parties ?? [])
        .filter((p) => p.lift != null)
        .sort((a, b) => b.lift - a.lift)
        .map((p) => ({
          key: p.party,
          name: partyName(p.party),
          meta: `${int(p.n)} interventi · ${pct(p.share, { digits: 1 })} del tema`,
          // Lift 2 (twice the expected share) fills the bar.
          percent: Math.min(100, p.lift * 50),
          value: `×${dec(p.lift)}`,
          tone: p.lift >= 1.25 ? 'good' : p.lift <= 0.8 ? 'critical' : 'neutral',
          dot: partyDot(p.party, mode),
        })),
    [topic, mode],
  );

  if (!topicsData || !topic) return <NoDataForPeriod feature="l'analisi dei temi" period={period} />;

  return (
    <div className="grid gap-5 lg:grid-cols-2">
      <div className="lg:col-span-2">
        <ScopeNote fromGlobal={fromGlobal} period={period} />
      </div>

      <Card className="lg:col-span-2">
        <CardHeader
          title="Peso dei temi"
          subtitle="Quota degli interventi classificati dedicata a ciascuna area"
        />
        <CardBody>
          <CategoryBars
            categories={overview.categories}
            series={overview.series}
            mode={mode}
            height={300}
            valueSuffix="%"
            title="Peso dei temi"
          />
        </CardBody>
      </Card>

      <Card className="lg:col-span-2">
        <CardHeader
          title={topic.label}
          subtitle={`${int(topic.n)} interventi · ${pct(topic.share, { digits: 1 })} del totale`}
          actions={
            <Select
              label="Tema"
              hideLabel
              value={topic.id}
              onChange={setTopicId}
              className="w-60"
              options={entries.map((e) => ({ value: e.id, label: e.label }))}
            />
          }
        />
        <CardBody className="grid gap-x-10 gap-y-6 lg:grid-cols-3">
          <div>
            <h4 className="mb-2 text-label text-muted">CHI NE PARLA DI PIÙ</h4>
            <RankingList items={speakers} emptyMessage="Nessuno con almeno tre interventi sul tema." />
          </div>
          <div>
            <h4 className="mb-2 text-label text-muted">GRUPPI: ATTENZIONE RISPETTO ALLA LORO TAGLIA</h4>
            <RankingList items={parties} />
          </div>
          <div>
            <h4 className="mb-2 text-label text-muted">PAROLE DEL TEMA</h4>
            <WordCloud words={topic.keywords} mode={mode} max={15} />
          </div>
        </CardBody>
        <CardFooter>
          ×1 = IL GRUPPO OCCUPA IL TEMA QUANTO IL SUO PESO NEL DIBATTITO; ×2 = IL DOPPIO. LE PAROLE SONO
          QUELLE PIÙ CARATTERISTICHE DEL TEMA RISPETTO AGLI ALTRI, E MOSTRANO COSA L&apos;ASSEGNAZIONE
          AUTOMATICA HA EFFETTIVAMENTE RACCOLTO SOTTO QUESTA ETICHETTA.
        </CardFooter>
      </Card>
    </div>
  );
}
