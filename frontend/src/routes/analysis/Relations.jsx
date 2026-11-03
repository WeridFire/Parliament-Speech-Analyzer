import { useMemo } from 'react';
import { ArrowLeftRight } from 'lucide-react';
import { Card, CardBody, CardFooter, CardHeader, RankingList, ScopeNote, Table } from '../../ui';
import { Matrix } from '../../viz/charts/Matrix';
import { useAnalysis } from './context';
import { partyDot, partyName, partyShort, sortParties } from '../../domain/parties';
import { cleanName } from '../../data/selectors';
import { dec, dec2 } from '../../lib/format';
import { EmptyState, NoDataForPeriod } from '../../ui/EmptyState';

/**
 * Affinity, cohesion and cross-party pairs, all in the centred embedding space
 * (see backend/analyzers/relations/cohesion.py for why that matters: on raw
 * embeddings every pair of parties was 0.81-0.99 similar).
 */
export default function Relations() {
  const { section, period, mode } = useAnalysis();
  const { data: relations, fromGlobal } = section('relations');

  const affinity = useMemo(() => {
    const source = relations?.affinity_matrix;
    if (!source?.parties?.length) return null;

    // Reorder by bloc so the majority block reads as one square.
    const order = sortParties(source.parties);
    const index = order.map((p) => source.parties.indexOf(p));
    // The diagonal is 1 by definition and would set the colour scale.
    const values = index.map((i, r) => index.map((j, c) => (r === c ? null : source.matrix[i][j])));
    const bound = Math.max(...(source.range ?? [1]).map(Math.abs)) || 1;
    return { labels: order.map(partyShort), values, bound };
  }, [relations]);

  const cohesionRows = useMemo(() => {
    const entries = Object.entries(relations?.party_cohesion ?? {});
    const max = Math.max(0.001, ...entries.map(([, info]) => info.cohesion));
    return entries
      .map(([party, info]) => ({
        key: party,
        name: partyName(party),
        meta: `${info.n_speeches} interventi · ${info.n_speakers} oratori`,
        percent: (Math.max(0, info.cohesion) / max) * 100,
        value: dec(info.cohesion * 100),
        dot: partyDot(party, mode),
        sort: info.cohesion,
      }))
      .sort((a, b) => b.sort - a.sort);
  }, [relations, mode]);

  if (!relations) return <NoDataForPeriod feature="l'analisi delle relazioni" period={period} />;

  const bridges = (relations.cross_party_pairs ?? []).slice(0, 12);

  return (
    <div className="grid gap-5 lg:grid-cols-2">
      <div className="lg:col-span-2">
        <ScopeNote fromGlobal={fromGlobal} period={period} />
      </div>

      <Card className="lg:col-span-2">
        <CardHeader
          title="Matrice di affinità"
          subtitle="Somiglianza fra i baricentri semantici dei gruppi: rosso simili, blu distanti"
        />
        <CardBody>
          {affinity ? (
            <Matrix
              xLabels={affinity.labels}
              yLabels={affinity.labels}
              values={affinity.values}
              mode={mode}
              scale="diverging"
              zmin={-affinity.bound}
              zmax={affinity.bound}
              zmid={0}
              height={Math.max(340, affinity.labels.length * 34 + 90)}
              colorbarTitle="Affinità"
              title="Matrice di affinità"
            />
          ) : (
            <EmptyState message="Troppo pochi gruppi con interventi sufficienti." />
          )}
        </CardBody>
        <CardFooter>
          L&apos;AFFINITÀ MISURA SOVRAPPOSIZIONE DI LINGUAGGIO E DI TEMI, NON VICINANZA POLITICA. È
          CALCOLATA DOPO AVER RIMOSSO LA COMPONENTE COMUNE A TUTTI GLI INTERVENTI: 0 = COME DUE
          GRUPPI PRESI A CASO.
        </CardFooter>
      </Card>

      <Card>
        <CardHeader
          title="Omogeneità interna"
          subtitle="Quanto gli interventi di uno stesso gruppo si somigliano fra loro (×100)"
        />
        <CardBody>
          <RankingList items={cohesionRows} />
        </CardBody>
        <CardFooter>
          0 = COME DUE INTERVENTI QUALSIASI DELL&apos;AULA. RIFLETTE ANCHE QUANTI TEMI IL GRUPPO
          COPRE: CHI PARLA DI POCHI ARGOMENTI RISULTA PIÙ OMOGENEO.
        </CardFooter>
      </Card>

      <Card>
        <CardHeader
          title="Ponti fra gruppi"
          subtitle="Coppie di parlamentari di gruppi diversi con il linguaggio più simile"
          icon={ArrowLeftRight}
        />
        <CardBody>
          {bridges.length ? (
            <Table
              caption="Coppie trasversali per similarità"
              columns={[
                { key: 'a', header: 'Parlamentare', render: (r) => <Person name={r.speaker1} party={r.party1} mode={mode} /> },
                { key: 'b', header: 'Parlamentare', render: (r) => <Person name={r.speaker2} party={r.party2} mode={mode} /> },
                {
                  key: 'similarity',
                  header: 'Similarità',
                  numeric: true,
                  width: '6rem',
                  render: (r) => (
                    <span title={r.crosses_blocs ? 'Fra maggioranza e opposizione' : undefined}>
                      {r.crosses_blocs ? '⇄ ' : ''}
                      {dec2(r.similarity)}
                    </span>
                  ),
                },
              ]}
              rows={bridges}
              getRowKey={(r) => `${r.speaker1}-${r.speaker2}`}
            />
          ) : (
            <EmptyState message="Nessun parlamentare con almeno 10 interventi in gruppi diversi." />
          )}
        </CardBody>
        <CardFooter>
          ⇄ = LA COPPIA ATTRAVERSA MAGGIORANZA E OPPOSIZIONE. SOLO PARLAMENTARI CON ALMENO 10
          INTERVENTI.
        </CardFooter>
      </Card>
    </div>
  );
}

function Person({ name, party, mode }) {
  return (
    <span className="flex min-w-0 items-center gap-1.5">
      <span
        className="h-2 w-2 shrink-0 rounded-full"
        style={{ backgroundColor: partyDot(party, mode) }}
        aria-hidden="true"
      />
      <span className="truncate">{cleanName(name)}</span>
      <span className="shrink-0 text-muted">{partyShort(party)}</span>
    </span>
  );
}
