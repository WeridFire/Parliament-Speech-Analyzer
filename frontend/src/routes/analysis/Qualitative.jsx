import { useMemo, useState } from 'react';
import { Card, CardBody, CardFooter, CardHeader, RankingList, Select } from '../../ui';
import { CategoryBars } from '../../viz/charts/CategoryBars';
import { Matrix } from '../../viz/charts/Matrix';
import { useAnalysis } from './AnalysisLayout';
import { partyDot, partyName, partyShort } from '../../domain/parties';
import { topicShort } from '../../domain/topics';
import { cleanName } from '../../data/selectors';
import { dec, signed } from '../../lib/format';
import { NoDataForPeriod } from '../../ui/EmptyState';
import { ClassificationTag } from '../../ui/Chip';

/**
 * Sentiment, readability and polarization.
 */
export default function Qualitative() {
  const { analytics, clusters, period, mode } = useAnalysis();
  const sentiment = analytics?.sentiment;

  const byCluster = sentiment?.topic_sentiment?.by_cluster ?? {};
  const partyTopic = sentiment?.party_topic_sentiment;
  const readability = sentiment?.readability?.by_party ?? {};
  const polarization = sentiment?.polarization;
  const rankings = sentiment?.sentiment_rankings ?? {};

  const topicIds = useMemo(() => Object.keys(rankings), [rankings]);
  const [topic, setTopic] = useState('');
  const activeTopic = topic && rankings[topic] ? topic : topicIds[0];

  /**
   * Sentiment MEANS good/bad, so these bars wear status tokens rather than
   * categorical slots — a series that carries valence never borrows a series
   * colour.
   */
  const clusterBars = useMemo(() => {
    const entries = Object.entries(byCluster).sort(
      (a, b) => (b[1].avg_sentiment ?? 0) - (a[1].avg_sentiment ?? 0),
    );
    return {
      categories: entries.map(([id, v]) => v.label ?? topicShort(Number(id), clusters)),
      series: [
        {
          key: 'sentiment',
          label: 'Sentiment medio',
          values: entries.map(([, v]) => v.avg_sentiment ?? 0),
          tones: entries.map(([, v]) =>
            (v.avg_sentiment ?? 0) > 0.05 ? 'good' : (v.avg_sentiment ?? 0) < -0.05 ? 'critical' : 'warning',
          ),
        },
      ],
    };
  }, [byCluster, clusters]);

  const readabilityRows = useMemo(
    () =>
      Object.entries(readability)
        .map(([party, info]) => ({
          key: party,
          name: partyName(party),
          meta: `${info.n_speeches ?? 0} interventi`,
          percent: info.avg_score,
          value: dec(info.avg_score),
          tone: info.avg_score >= 80 ? 'good' : info.avg_score >= 55 ? 'warning' : 'critical',
          dot: partyDot(party, mode),
        }))
        .sort((a, b) => (b.percent ?? 0) - (a.percent ?? 0)),
    [readability, mode],
  );

  const polarizers = useMemo(
    () =>
      (polarization?.top_polarizers ?? []).slice(0, 10).map((p) => ({
        key: `${p.speaker}-${p.party}`,
        name: cleanName(p.speaker),
        meta: partyShort(p.party),
        percent: p.score,
        value: dec(p.score),
        tone: 'critical',
        dot: partyDot(p.party, mode),
      })),
    [polarization, mode],
  );

  if (!sentiment) return <NoDataForPeriod feature="l'analisi qualitativa" period={period} />;

  const ranking = activeTopic ? rankings[activeTopic] : null;

  return (
    <div className="grid gap-5 lg:grid-cols-2">
      <Card className="lg:col-span-2">
        <CardHeader
          title="Sentiment per area tematica"
          subtitle="Da −1 (interamente negativo) a +1 (interamente positivo)"
        />
        <CardBody>
          <CategoryBars
            categories={clusterBars.categories}
            series={clusterBars.series}
            mode={mode}
            height={340}
            valueFormat=".2f"
            title="Sentiment per area tematica"
          />
        </CardBody>
        <CardFooter>
          IL SENTIMENT È CALCOLATO SU LESSICI DI TERMINI POSITIVI E NEGATIVI: NON RICONOSCE IRONIA,
          CITAZIONI O NEGAZIONI COMPLESSE.
        </CardFooter>
      </Card>

      {partyTopic ? (
        <Card className="lg:col-span-2">
          <CardHeader
            title="Sentiment per gruppo e tema"
            subtitle="Scala divergente: blu negativo, grigio neutro, rosso positivo"
          />
          <CardBody>
            <Matrix
              xLabels={(partyTopic.topic_ids ?? []).map((id) => topicShort(id, clusters))}
              yLabels={(partyTopic.parties ?? []).map(partyShort)}
              values={partyTopic.matrix ?? []}
              mode={mode}
              scale="diverging"
              zmin={-0.5}
              zmax={0.5}
              height={Math.max(320, (partyTopic.parties?.length ?? 0) * 30 + 110)}
              colorbarTitle="Sentiment"
              title="Sentiment per gruppo e tema"
            />
          </CardBody>
        </Card>
      ) : null}

      <Card>
        <CardHeader
          title="Leggibilità"
          subtitle="Indice Gulpease: sotto 55 il testo è difficile"
        />
        <CardBody>
          <RankingList items={readabilityRows} />
        </CardBody>
      </Card>

      <Card>
        <CardHeader
          title="Polarizzazione del linguaggio"
          subtitle="Contrapposizioni «noi/loro» ogni mille parole"
          actions={
            polarization?.by_party?.classification ? (
              <ClassificationTag value={polarization.by_party.classification} />
            ) : null
          }
        />
        <CardBody>
          <RankingList items={polarizers} />
        </CardBody>
      </Card>

      {ranking ? (
        <Card className="lg:col-span-2">
          <CardHeader
            title="Toni estremi per tema"
            subtitle={ranking.label}
            actions={
              <Select
                label="Tema"
                hideLabel
                value={activeTopic}
                onChange={setTopic}
                className="w-56"
                options={topicIds.map((id) => ({
                  value: id,
                  label: rankings[id]?.label ?? topicShort(Number(id), clusters),
                }))}
              />
            }
          />
          <CardBody className="grid gap-x-10 gap-y-6 md:grid-cols-2">
            <div>
              <h4 className="mb-2 text-label text-muted">TONI PIÙ POSITIVI</h4>
              <RankingList items={toRows(ranking.most_positive, mode, 'good')} />
            </div>
            <div>
              <h4 className="mb-2 text-label text-muted">TONI PIÙ NEGATIVI</h4>
              <RankingList items={toRows(ranking.most_negative, mode, 'critical')} />
            </div>
          </CardBody>
        </Card>
      ) : null}
    </div>
  );
}

function toRows(list, mode, tone) {
  return (list ?? []).slice(0, 8).map((r) => ({
    key: `${r.speaker}-${r.party}`,
    name: cleanName(r.speaker),
    meta: `${partyShort(r.party)} · ${r.n_speeches ?? 0} interventi`,
    // Sentiment is signed, so a bar length would misrepresent it — the value
    // alone carries the meaning.
    percent: null,
    value: signed(r.score),
    tone,
    dot: partyDot(r.party, mode),
  }));
}
