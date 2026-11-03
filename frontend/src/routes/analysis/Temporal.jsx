import { useMemo, useState } from 'react';
import { Card, CardBody, CardFooter, CardHeader, Chip } from '../../ui';
import { TrendLines } from '../../viz/charts/TrendLines';
import { useAnalysis } from './context';
import { topicList } from '../../domain/topics';
import { BLOC_LABELS } from '../../domain/metrics';
import { monthLabel } from '../../lib/format';
import { NoDataForPeriod } from '../../ui/EmptyState';
import { SERIES_CAP } from '../../viz/palette';

/**
 * How the agenda moves month by month.
 *
 * Always reads the GLOBAL temporal block: it plots time series, so scoping it
 * to a single month would collapse every line to one point. (It used to look
 * for analytics inside the core resource, where they no longer live, so this
 * tab was always empty.)
 */
export default function Temporal() {
  const { globalAnalytics, clusters, period, mode } = useAnalysis();
  const trends = globalAnalytics?.temporal?.topic_trends;

  const topics = useMemo(() => topicList(clusters).filter((t) => t.id >= 0), [clusters]);
  const periods = useMemo(() => trends?.periods ?? [], [trends]);

  /**
   * Fourteen topics, eight validated slots: show the largest overall and let
   * the reader ask for the rest - never cycle the palette. Unlike counts,
   * shares cannot be folded into an "Altri" line: the sum of seven shares sat
   * at 35-45% and flattened every real series against the axis.
   */
  const [showAll, setShowAll] = useState(false);

  const shareSeries = useMemo(() => {
    if (!periods.length) return [];
    const counts = trends.counts ?? {};
    const shares = trends.shares ?? {};

    const ranked = topics
      .map((topic) => ({ topic, total: periods.reduce((sum, p) => sum + (counts[p]?.[topic.id] ?? 0), 0) }))
      .sort((a, b) => b.total - a.total);

    const keep = showAll ? ranked : ranked.slice(0, SERIES_CAP.adjacent);

    return keep.map(({ topic }) => ({
      key: String(topic.id),
      label: topic.short,
      values: periods.map((p) => shares[p]?.[topic.id] ?? 0),
    }));
  }, [periods, topics, trends, showAll]);

  const blocSeries = useMemo(
    () =>
      ['maggioranza', 'opposizione', 'altro'].map((bloc) => ({
        key: bloc,
        label: BLOC_LABELS[bloc],
        values: periods.map((p) => trends.blocs?.[p]?.[bloc] ?? 0),
      })),
    [periods, trends],
  );

  if (!periods.length) return <NoDataForPeriod feature="l'analisi temporale" period={period} />;

  const labels = periods.map(monthLabel);

  return (
    <div className="grid gap-5 lg:grid-cols-2">
      {period?.year ? (
        <p className="text-label text-muted lg:col-span-2">
          LE TENDENZE COPRONO SEMPRE L&apos;INTERO PERIODO DISPONIBILE, INDIPENDENTEMENTE DAL FILTRO.
        </p>
      ) : null}

      <Card className="lg:col-span-2">
        <CardHeader
          title="Andamento dei temi"
          subtitle={showAll ? 'Quota degli interventi di ogni mese dedicata a ciascuna area' : `Quota degli interventi di ogni mese: le ${SERIES_CAP.adjacent} aree più frequenti`}
          actions={
            <Chip size="sm" selected={showAll} onClick={() => setShowAll((v) => !v)}>
              {showAll ? 'Mostra i principali' : 'Mostra tutti i temi'}
            </Chip>
          }
        />
        <CardBody>
          <TrendLines
            periods={labels}
            series={shareSeries}
            mode={mode}
            height={380}
            valueSuffix="%"
            yTitle="% degli interventi del mese"
            title="Andamento dei temi"
          />
        </CardBody>
        <CardFooter>
          QUOTE E NON CONTEGGI, PERCHÉ IL NUMERO DI SEDUTE CAMBIA MOLTO DA UN MESE ALL&apos;ALTRO:
          UNA QUOTA ALTA SIGNIFICA CHE QUEL MESE IL TEMA HA OCCUPATO UNA PARTE IMPORTANTE DEL
          DIBATTITO, QUALUNQUE FOSSE IL NUMERO DI SEDUTE.
          {showAll ? ' CON PIÙ DI OTTO SERIE I COLORI NON SONO PIÙ DISTINGUIBILI IN MODO AFFIDABILE.' : ''}
        </CardFooter>
      </Card>

      <Card className="lg:col-span-2">
        <CardHeader
          title="Attività in Aula"
          subtitle="Interventi al mese di maggioranza, opposizione e gruppi misti"
        />
        <CardBody>
          <TrendLines
            periods={labels}
            series={blocSeries}
            mode={mode}
            height={300}
            yTitle="Interventi"
            title="Attività in Aula"
          />
        </CardBody>
      </Card>
    </div>
  );
}
