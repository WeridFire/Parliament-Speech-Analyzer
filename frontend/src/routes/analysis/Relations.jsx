import { useMemo } from 'react';
import { ArrowLeftRight } from 'lucide-react';
import { Card, CardBody, CardFooter, CardHeader, RankingList, Table } from '../../ui';
import { Matrix } from '../../viz/charts/Matrix';
import { useAnalysis } from './AnalysisLayout';
import { partyDot, partyName, partyShort } from '../../domain/parties';
import { classify, toPercent } from '../../domain/metrics';
import { cleanName } from '../../data/selectors';
import { dec2, pct } from '../../lib/format';
import { EmptyState, NoDataForPeriod } from '../../ui/EmptyState';
import { ClassificationTag } from '../../ui/Chip';

/**
 * Affinity, cohesion, bipartisanship and cross-party pairs.
 *
 * This tab carried five field-name bugs against the backend schema. Each fix
 * is annotated inline; all five were verified against
 * backend/analyzers/relations/*.
 */
export default function Relations() {
  const { analytics, period, mode } = useAnalysis();
  const relations = analytics?.relations;

  const affinity = relations?.affinity_matrix;
  const cohesion = relations?.party_cohesion ?? {};
  const overlap = relations?.thematic_overlap ?? {};
  const pairs = relations?.cross_party_pairs ?? [];

  const cohesionRows = useMemo(
    () =>
      Object.entries(cohesion)
        .map(([party, info]) => ({
          key: party,
          name: partyName(party),
          // FIX: was `item.n_members`, which does not exist — the backend emits
          // `n_speeches`. The old UI rendered "undefined membri".
          meta: `${info.n_speeches ?? 0} interventi`,
          // FIX: cohesion_score is 0–1 (e.g. 0.2889), not 0–100. The old code
          // used it directly as a CSS percentage width, so every bar was ~0.3%
          // wide and labelled "0%".
          percent: toPercent(info.cohesion_score, 'cohesion_score'),
          value: pct(info.cohesion_score, { fromUnit: true }),
          // FIX: the label field is `interpretation`, not `classification`.
          tone: classify(info.interpretation).tone,
          dot: partyDot(party, mode),
          raw: info,
        }))
        .sort((a, b) => (b.percent ?? 0) - (a.percent ?? 0)),
    [cohesion, mode],
  );

  const { bipartisan, polarized } = useMemo(() => {
    const items = Object.entries(overlap).map(([id, info]) => ({ id, ...info }));
    return {
      // FIX: the field is `type`, not `classification`. Filtering on
      // `classification === 'bipartisan'` never matched, so this column was
      // permanently empty and every topic fell through into "polarizzati".
      bipartisan: items
        .filter((i) => i.type === 'bipartisan')
        .sort((a, b) => (b.overlap_score ?? 0) - (a.overlap_score ?? 0)),
      polarized: items
        .filter((i) => i.type === 'left-dominated' || i.type === 'right-dominated')
        .sort((a, b) => (a.overlap_score ?? 0) - (b.overlap_score ?? 0)),
    };
  }, [overlap]);

  // FIX: the old code filtered on `p.crosses_divide`, a field the backend never
  // emits, so "Ponti Politici" always showed its empty state. The real signal is
  // that the two speakers belong to different groups, which every entry in
  // cross_party_pairs already satisfies by construction.
  const bridges = useMemo(
    () => [...pairs].sort((a, b) => (b.similarity ?? 0) - (a.similarity ?? 0)).slice(0, 10),
    [pairs],
  );

  if (!relations) return <NoDataForPeriod feature="l'analisi delle relazioni" period={period} />;

  const affinityLabels = (affinity?.parties ?? []).map(partyShort);

  return (
    <div className="grid gap-5 lg:grid-cols-2">
      <Card className="lg:col-span-2">
        <CardHeader
          title="Matrice di affinità"
          subtitle="Similarità fra i baricentri semantici dei gruppi"
        />
        <CardBody>
          <Matrix
            xLabels={affinityLabels}
            yLabels={affinityLabels}
            values={affinity?.matrix ?? []}
            mode={mode}
            scale="sequential"
            zmin={0}
            zmax={1}
            height={Math.max(340, affinityLabels.length * 34 + 90)}
            colorbarTitle="Affinità"
            title="Matrice di affinità"
          />
        </CardBody>
        <CardFooter>
          L&apos;AFFINITÀ MISURA SOVRAPPOSIZIONE DI LINGUAGGIO E DI TEMI, NON VICINANZA POLITICA.
        </CardFooter>
      </Card>

      <Card>
        <CardHeader
          title="Coesione interna"
          subtitle="Quanto sono ravvicinati gli interventi di uno stesso gruppo"
        />
        <CardBody>
          <RankingList items={cohesionRows} />
        </CardBody>
      </Card>

      <Card>
        <CardHeader
          title="Ponti fra gruppi"
          subtitle="Le coppie di parlamentari di gruppi diversi con il linguaggio più simile"
          icon={ArrowLeftRight}
        />
        <CardBody>
          {bridges.length ? (
            <Table
              caption="Coppie trasversali per similarità"
              columns={[
                {
                  key: 'a',
                  header: 'Parlamentare',
                  render: (r) => (
                    <span className="flex items-center gap-1.5">
                      <Dot party={r.party1} mode={mode} />
                      <span className="truncate">{cleanName(r.speaker1)}</span>
                      <span className="shrink-0 text-muted">{partyShort(r.party1)}</span>
                    </span>
                  ),
                },
                {
                  key: 'b',
                  header: 'Parlamentare',
                  render: (r) => (
                    <span className="flex items-center gap-1.5">
                      <Dot party={r.party2} mode={mode} />
                      <span className="truncate">{cleanName(r.speaker2)}</span>
                      <span className="shrink-0 text-muted">{partyShort(r.party2)}</span>
                    </span>
                  ),
                },
                {
                  key: 'similarity',
                  header: 'Similarità',
                  numeric: true,
                  width: '5.5rem',
                  render: (r) => dec2(r.similarity),
                },
              ]}
              rows={bridges}
              getRowKey={(r) => `${r.speaker1}-${r.speaker2}`}
            />
          ) : (
            <EmptyState message="Nessuna coppia trasversale rilevata in questo periodo." />
          )}
        </CardBody>
      </Card>

      <Card className="lg:col-span-2">
        <CardHeader
          title="Temi bipartisan e temi polarizzati"
          subtitle="Quanto equilibrata è la partecipazione degli schieramenti su ciascuna area"
        />
        <CardBody className="grid gap-x-10 gap-y-6 md:grid-cols-2">
          <div>
            <h4 className="mb-2 text-label text-muted">PIÙ BIPARTISAN</h4>
            <TopicSplitList items={bipartisan} />
          </div>
          <div>
            <h4 className="mb-2 text-label text-muted">PIÙ SBILANCIATI</h4>
            <TopicSplitList items={polarized} />
          </div>
        </CardBody>
        <CardFooter>
          UN TEMA È BIPARTISAN QUANDO ENTRAMBI GLI SCHIERAMENTI VI INTERVENGONO IN MISURA
          COMPARABILE.
        </CardFooter>
      </Card>
    </div>
  );
}

function TopicSplitList({ items }) {
  if (!items.length) {
    return <EmptyState message="Nessun tema in questa categoria per il periodo selezionato." />;
  }

  return (
    <ul className="flex flex-col">
      {items.slice(0, 7).map((item) => (
        <li key={item.id} className="border-b border-rule py-2.5 last:border-b-0">
          <div className="flex items-baseline justify-between gap-3">
            <span className="truncate text-body font-medium text-ink">{item.label}</span>
            {/* FIX: the old code compared against 'left-leaning', a value the
                backend never emits, so every row rendered "DX →" regardless. */}
            <ClassificationTag value={item.type} />
          </div>

          {/* Stacked split. A 2px surface gap keeps the segments separable, and
              each segment is labelled, so nothing rests on colour alone. */}
          <div className="mt-2 flex h-1.5 gap-0.5 overflow-hidden rounded-full">
            <Segment pct={item.left_pct} className="bg-[#2a78d6]" />
            <Segment pct={item.center_pct} className="bg-muted" />
            <Segment pct={item.right_pct} className="bg-[#eb6834]" />
          </div>

          <div className="mt-1.5 flex justify-between text-label text-muted">
            <span>SX {pct(item.left_pct)}</span>
            <span>CENTRO {pct(item.center_pct)}</span>
            <span>DX {pct(item.right_pct)}</span>
          </div>
        </li>
      ))}
    </ul>
  );
}

function Segment({ pct: value, className }) {
  if (!value) return null;
  return <span className={className} style={{ width: `${value}%` }} aria-hidden="true" />;
}

function Dot({ party, mode }) {
  return (
    <span
      className="h-2 w-2 shrink-0 rounded-full"
      style={{ backgroundColor: partyDot(party, mode) }}
      aria-hidden="true"
    />
  );
}
