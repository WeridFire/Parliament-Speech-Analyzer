import { useMemo } from 'react';
import { Card, CardBody, CardFooter, CardHeader, RankingList, ScopeNote, StatRow, StatTile } from '../../ui';
import { Matrix } from '../../viz/charts/Matrix';
import { useAnalysis } from './context';
import { BLOC_LABELS } from '../../domain/metrics';
import { partyDot, partyName, partyShort, sortParties } from '../../domain/parties';
import { cleanName } from '../../data/selectors';
import { int, pct } from '../../lib/format';
import { EmptyState, NoDataForPeriod } from '../../ui/EmptyState';

/**
 * Reactions from the floor, read from the stage directions of the
 * stenographic report: "(Applausi dei deputati del gruppo …)". Behaviour, not
 * text similarity - a group applauding an opponent is the clearest
 * cross-party signal the reports contain.
 */
export default function Reactions() {
  const { section, period, mode, chamberMeta } = useAnalysis();
  const { data: reactions, fromGlobal } = section('reactions');

  const attributed = Boolean(reactions?.coverage?.attributed);

  const matrix = useMemo(() => {
    if (!reactions || !attributed) return null;
    const order = sortParties(reactions.parties);
    const index = order.map((p) => reactions.parties.indexOf(p));
    const values = [];
    const hover = [];
    for (const [r, i] of index.entries()) {
      values.push(
        // Own-group applause is routine and would swamp the scale.
        index.map((j, c) => (r === c ? null : (reactions.applause[i][j] / reactions.speeches[order[c]]) * 100)),
      );
      hover.push(
        index.map(
          (j, c) =>
            `${partyName(order[r])} applaude ${partyName(order[c])}<br>` +
            `${int(reactions.applause[i][j])} interventi (${pct((reactions.applause[i][j] / reactions.speeches[order[c]]) * 100, { digits: 1 })} dei suoi)`,
        ),
      );
    }
    const peak = Math.max(1, ...values.flat().filter((v) => v != null));
    return { labels: order.map(partyShort), values, hover, peak };
  }, [reactions, attributed]);

  const received = useMemo(() => {
    const entries = Object.entries(reactions?.received ?? {});
    const shape = (key) => {
      const max = Math.max(1, ...entries.map(([, r]) => r[key]));
      return entries
        .map(([party, r]) => ({
          key: party,
          name: partyName(party),
          meta: `${int(reactions.speeches[party])} interventi`,
          percent: (r[key] / max) * 100,
          value: pct(r[key], { digits: 1 }),
          tone: key === 'applause' ? 'good' : 'critical',
          dot: partyDot(party, mode),
          sort: r[key],
        }))
        .sort((a, b) => b.sort - a.sort);
    };
    return { applause: shape('applause'), dissent: shape('dissent') };
  }, [reactions, mode]);

  if (!reactions) return <NoDataForPeriod feature="l'analisi delle reazioni" period={period} />;

  const people = (list, tone) => {
    const max = Math.max(1, ...(list ?? []).map((p) => p.n));
    return (list ?? []).map((p) => ({
      key: p.speaker,
      name: cleanName(p.speaker),
      meta: `${partyShort(p.party)} · da ${p.groups.slice(0, 3).map(partyShort).join(', ')}`,
      percent: (p.n / max) * 100,
      value: int(p.n),
      tone,
      dot: partyDot(p.party, mode),
    }));
  };

  return (
    <div className="grid gap-5 lg:grid-cols-2">
      <div className="lg:col-span-2">
        <ScopeNote fromGlobal={fromGlobal} period={period} />
      </div>

      <Card>
        <CardHeader title="Interventi applauditi" subtitle="Quota degli interventi del gruppo che ricevono applausi" />
        <CardBody>
          <RankingList items={received.applause} />
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Interventi contestati" subtitle="Quota degli interventi interrotti da proteste o commenti" />
        <CardBody>
          <RankingList items={received.dissent} />
        </CardBody>
      </Card>

      {attributed ? (
        <>
          <Card className="lg:col-span-2">
            <CardHeader
              title="Chi applaude chi"
              subtitle="Righe: il gruppo che applaude. Colonne: il gruppo di chi parla. Valori ogni 100 interventi del gruppo applaudito"
            />
            <CardBody>
              <Matrix
                xLabels={matrix.labels}
                yLabels={matrix.labels}
                values={matrix.values}
                hoverText={matrix.hover}
                mode={mode}
                scale="sequential"
                zmin={0}
                zmax={matrix.peak}
                valueFormat=".1f"
                height={Math.max(340, matrix.labels.length * 34 + 90)}
                colorbarTitle="Ogni 100"
                title="Chi applaude chi"
              />
            </CardBody>
            <CardFooter>
              LA DIAGONALE — GLI APPLAUSI DEL PROPRIO GRUPPO — È ESCLUSA: È LA NORMA E NASCONDEREBBE
              TUTTO IL RESTO.
            </CardFooter>
          </Card>

          <Card className="lg:col-span-2">
            <CardHeader
              title="Applausi oltre il proprio schieramento"
              subtitle="Quota degli interventi di ciascuno schieramento applauditi da almeno un gruppo dell'altro"
            />
            <CardBody>
              <StatRow>
                {['maggioranza', 'opposizione'].map((bloc) => (
                  <StatTile
                    key={bloc}
                    label={BLOC_LABELS[bloc]}
                    value={pct(reactions.bloc_applause?.[bloc]?.rate, { digits: 1 })}
                    meta={`${int(reactions.bloc_applause?.[bloc]?.applauded_by_other_bloc)} interventi applauditi dall'altro lato`}
                  />
                ))}
              </StatRow>
            </CardBody>
          </Card>

          <Card>
            <CardHeader
              title="Applauditi da altri gruppi"
              subtitle="Parlamentari con più interventi applauditi da gruppi diversi dal proprio"
            />
            <CardBody>
              <RankingList items={people(reactions.top_cross_applauded, 'good')} />
            </CardBody>
          </Card>

          <Card>
            <CardHeader title="Più contestati" subtitle="Interventi interrotti da proteste o commenti di altri gruppi" />
            <CardBody>
              <RankingList items={people(reactions.top_contested, 'critical')} />
            </CardBody>
          </Card>
        </>
      ) : (
        <Card className="lg:col-span-2">
          <CardBody>
            <EmptyState
              message={`I resoconti del ${chamberMeta.label} non indicano quale gruppo applaude o protesta.`}
              hint="Le note riportano solo «(Applausi)» o «(Commenti)»: si può misurare quanto un gruppo viene applaudito, non da chi. La matrice «chi applaude chi» è disponibile per la Camera."
            />
          </CardBody>
        </Card>
      )}

      <p className="text-label text-muted lg:col-span-2">
        {int(reactions.coverage?.with_reactions)} interventi su {int(reactions.coverage?.speeches)} hanno
        almeno una reazione annotata; {int(reactions.coverage?.applause_events)} applausi
        {attributed ? `, di cui ${int(reactions.coverage?.applause_attributed)} attribuiti a un gruppo` : ''};{' '}
        {int(reactions.coverage?.dissent_events)} proteste o commenti.
      </p>
    </div>
  );
}
