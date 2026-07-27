import { useMemo, useState } from 'react';
import { Card, CardBody, CardFooter, CardHeader, Chip, RankingList } from '../../ui';
import { TrendLines, AreaTrend } from '../../viz/charts/TrendLines';
import { useAnalysis } from './AnalysisLayout';
import { topicList } from '../../domain/topics';
import { cleanName, topEntries } from '../../data/selectors';
import { monthLabel, dec, int } from '../../lib/format';
import { NoDataForPeriod } from '../../ui/EmptyState';
import { SERIES_CAP } from '../../viz/palette';

/**
 * Topic trends, the crisis index, and topic-switching behaviour.
 *
 * Note this tab always reads the GLOBAL temporal block: it plots time series,
 * so scoping it to a single month would collapse every line to one point.
 */
export default function Temporal() {
  const { data, clusters, period, mode } = useAnalysis();
  const temporal = data?.analytics?.global?.temporal ?? data?.analytics?.temporal;

  const topics = useMemo(() => topicList(clusters), [clusters]);
  const periods = temporal?.topic_trends?.periods ?? [];
  const trendData = temporal?.topic_trends?.global ?? {};

  /**
   * Fourteen topics, eight validated slots. Show the seven largest by total
   * volume and fold the rest into "Altri" — never cycle the palette, which is
   * what the old `TOPIC_COLORS[i % 10]` did.
   */
  const [showAll, setShowAll] = useState(false);

  const trendSeries = useMemo(() => {
    if (!periods.length) return [];

    const totals = topics.map((t) => ({
      topic: t,
      total: periods.reduce((sum, p) => sum + (trendData[p]?.[t.id] ?? 0), 0),
    }));
    const ranked = [...totals].sort((a, b) => b.total - a.total);

    const keep = showAll ? ranked : ranked.slice(0, SERIES_CAP.adjacent - 1);
    const rest = showAll ? [] : ranked.slice(SERIES_CAP.adjacent - 1);

    const series = keep.map(({ topic }) => ({
      key: String(topic.id),
      label: topic.short,
      values: periods.map((p) => trendData[p]?.[topic.id] ?? 0),
    }));

    if (rest.length) {
      series.push({
        key: '__rest__',
        label: `Altri ${rest.length} temi`,
        values: periods.map((p) =>
          rest.reduce((sum, { topic }) => sum + (trendData[p]?.[topic.id] ?? 0), 0),
        ),
      });
    }

    return series;
  }, [periods, topics, trendData, showAll]);

  const crisis = temporal?.crisis_index;
  const crisisPeriods = crisis?.periods ?? [];
  const crisisValues = useMemo(
    () => crisisPeriods.map((p) => crisis?.global?.[p]?.crisis_rate ?? 0),
    [crisis, crisisPeriods],
  );

  const surfing = temporal?.topic_surfing ?? {};

  const surfers = useMemo(
    () =>
      topEntries(surfing, {
        valueOf: (v) => v.topic_changes,
        filter: (e) => (e.raw.n_periods ?? 0) >= 2,
        limit: 10,
      }).map((e) => ({
        key: e.name,
        name: cleanName(e.name),
        meta: e.raw.most_surfed_to_label
          ? `Verso: ${e.raw.most_surfed_to_label}`
          : `${e.raw.n_periods} periodi attivi`,
        percent: null,
        value: `${int(e.value)} cambi`,
      })),
    [surfing],
  );

  const steady = useMemo(
    () =>
      topEntries(surfing, {
        valueOf: (v) => v.consistency_score,
        filter: (e) => (e.raw.n_periods ?? 0) >= 2,
        limit: 10,
      }).map((e) => ({
        key: e.name,
        name: cleanName(e.name),
        meta: `${e.raw.n_periods} periodi attivi`,
        percent: e.value,
        value: `${dec(e.value)}%`,
        tone: 'good',
      })),
    [surfing],
  );

  if (!temporal || !periods.length) {
    return <NoDataForPeriod feature="l'analisi temporale" period={period} />;
  }

  const labels = periods.map(monthLabel);

  return (
    <div className="grid gap-5 lg:grid-cols-2">
      <Card className="lg:col-span-2">
        <CardHeader
          title="Andamento dei temi"
          subtitle="Numero di interventi per area tematica, mese per mese"
          actions={
            <Chip size="sm" selected={showAll} onClick={() => setShowAll((v) => !v)}>
              {showAll ? 'Mostra i principali' : 'Mostra tutti i temi'}
            </Chip>
          }
        />
        <CardBody>
          <TrendLines
            periods={labels}
            series={trendSeries}
            mode={mode}
            height={380}
            yTitle="Interventi"
            title="Andamento dei temi"
          />
        </CardBody>
        {showAll ? (
          <CardFooter>
            CON PIÙ DI OTTO SERIE I COLORI NON SONO PIÙ DISTINGUIBILI IN MODO AFFIDABILE: USA
            QUESTA VISTA PER LEGGERE LA FORMA COMPLESSIVA, NON PER CONFRONTARE SINGOLI TEMI.
          </CardFooter>
        ) : null}
      </Card>

      <Card className="lg:col-span-2">
        <CardHeader
          title="Indice di crisi"
          subtitle="Ricorrenze di lessico emergenziale ogni mille parole"
        />
        <CardBody>
          <AreaTrend
            periods={crisisPeriods.map(monthLabel)}
            values={crisisValues}
            mode={mode}
            height={260}
            tone="critical"
            label="Tasso"
            yTitle="per 1.000 parole"
            title="Indice di crisi"
          />
        </CardBody>
        {crisis?.crisis_keywords?.length ? (
          <CardFooter>
            BASATO SU {crisis.crisis_keywords.length} TERMINI, FRA CUI:{' '}
            {crisis.crisis_keywords.slice(0, 8).join(' · ').toUpperCase()}
          </CardFooter>
        ) : null}
      </Card>

      <Card>
        <CardHeader
          title="Chi cambia tema più spesso"
          subtitle="Numero di cambi dell'area prevalente da un mese all'altro"
        />
        <CardBody>
          <RankingList items={surfers} />
        </CardBody>
      </Card>

      <Card>
        <CardHeader
          title="Chi resta sul proprio tema"
          subtitle="Costanza dell'area prevalente nel tempo"
        />
        <CardBody>
          <RankingList items={steady} />
        </CardBody>
      </Card>
    </div>
  );
}
