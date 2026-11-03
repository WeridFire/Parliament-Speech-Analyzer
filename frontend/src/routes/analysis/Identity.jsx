import { useMemo, useState } from 'react';
import { Card, CardBody, CardFooter, CardHeader, PartyChip, RankingList, ScopeNote, SegmentedControl } from '../../ui';
import { Radar } from '../../viz/charts/Radar';
import { Matrix } from '../../viz/charts/Matrix';
import { WordCloud } from '../../viz/charts/WordCloud';
import { useAnalysis } from './context';
import { topicList, topicShort } from '../../domain/topics';
import { partyDot, partyName, partyShort, sortParties } from '../../domain/parties';
import { cleanName, topEntries, bottomEntries } from '../../data/selectors';
import { dec, pct } from '../../lib/format';
import { NoDataForPeriod } from '../../ui/EmptyState';

/** Lift beyond these bounds is clipped for colour; the hover keeps the real value. */
const LIFT_LOG_BOUND = 2;

/**
 * What each group talks about more than the chamber does, and with which words.
 */
export default function Identity() {
  const { section, clusters, period, mode } = useAnalysis();
  const { data: identity, fromGlobal } = section('identity');

  const topics = useMemo(() => topicList(clusters).filter((t) => t.id >= 0), [clusters]);
  const profile = identity?.topic_profile;
  const parties = useMemo(() => sortParties(Object.keys(profile?.by_party ?? {})), [profile]);

  const [selected, setSelected] = useState(null);
  // Parliamentary groups all speak across nearly every topic (scores 90+), so
  // the members' view is where the index actually discriminates.
  const [scope, setScope] = useState('by_deputy');
  const active = selected && parties.includes(selected) ? selected : parties[0];

  const radarSeries = useMemo(() => {
    const own = profile?.by_party?.[active];
    if (!own) return [];
    return [
      { key: active, label: partyName(active), values: topics.map((t) => own.shares[t.id] ?? 0) },
      { key: 'aula', label: "Media dell'Aula", values: topics.map((t) => profile.chamber[t.id] ?? 0) },
    ];
  }, [profile, active, topics]);

  const radarMax = useMemo(() => {
    const peak = Math.max(0, ...radarSeries.flatMap((s) => s.values));
    return Math.ceil((peak * 1.1) / 5) * 5 || 10;
  }, [radarSeries]);

  const lift = useMemo(() => {
    const values = [];
    const hover = [];
    for (const party of parties) {
      const own = profile.by_party[party];
      values.push(
        topics.map((t) => {
          const l = own.lift[t.id];
          if (!l) return -LIFT_LOG_BOUND;
          return Math.max(-LIFT_LOG_BOUND, Math.min(LIFT_LOG_BOUND, Math.log2(l)));
        }),
      );
      hover.push(
        topics.map(
          (t) =>
            `${pct(own.shares[t.id], { digits: 1 })} degli interventi del gruppo<br>` +
            `${own.lift[t.id] ? `${dec(own.lift[t.id])} volte` : 'mai, contro'} la media dell'Aula (${pct(profile.chamber[t.id], { digits: 1 })})`,
        ),
      );
    }
    return { values, hover };
  }, [parties, profile, topics]);

  const ranking = useMemo(() => {
    const source = identity?.generalism_index?.[scope];
    if (!source) return { generalists: [], specialists: [] };

    const shape = (e) => {
      const party = scope === 'by_party' ? e.name : e.raw.party;
      return {
        key: e.name,
        name: scope === 'by_party' ? partyName(e.name) : cleanName(e.name),
        meta:
          scope === 'by_party'
            ? `${e.raw.n_speeches} interventi`
            : `${partyShort(party)} · prevalente: ${topicShort(e.raw.dominant_topic, clusters)}`,
        percent: e.value,
        value: dec(e.value),
        dot: partyDot(party, mode),
      };
    };

    const opts = { valueOf: (v) => v.score, limit: 10 };
    return {
      generalists: topEntries(source, opts).map(shape),
      specialists: bottomEntries(source, opts).map(shape),
    };
  }, [identity, scope, clusters, mode]);

  if (!identity) return <NoDataForPeriod feature="l'analisi dell'identità" period={period} />;

  const keywords = identity.distinctive_keywords?.[active] ?? [];

  return (
    <div className="grid gap-5 lg:grid-cols-2">
      <div className="lg:col-span-2">
        <ScopeNote fromGlobal={fromGlobal} period={period} />
      </div>

      <Card>
        <CardHeader
          title="Profilo tematico"
          subtitle="Quota degli interventi del gruppo su ciascuna area, confrontata con la media dell'Aula"
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
            height={380}
            range={[0, radarMax]}
            title="Profilo tematico"
          />
        </CardBody>
        <CardFooter>VALORI IN PERCENTUALE SUGLI INTERVENTI CLASSIFICATI.</CardFooter>
      </Card>

      <Card>
        <CardHeader
          title="Vocabolario distintivo"
          subtitle={active ? `Le parole che ${partyName(active)} usa più degli altri gruppi` : ''}
        />
        <CardBody className="flex items-center justify-center">
          <WordCloud words={keywords} mode={mode} max={30} />
        </CardBody>
        <CardFooter>
          LOG-ODDS CON PRIOR INFORMATIVO: CONTA QUANTO UNA PAROLA È PIÙ FREQUENTE NEL GRUPPO CHE NEL
          RESTO DELL&apos;AULA, AL NETTO DEL CASO. ESCLUSI I NOMI DEI GRUPPI E IL LESSICO PROCEDURALE.
        </CardFooter>
      </Card>

      <Card className="lg:col-span-2">
        <CardHeader
          title="Su cosa ogni gruppo insiste di più"
          subtitle="Rosso: il gruppo dedica al tema più attenzione della media dell'Aula; blu: meno"
        />
        <CardBody>
          <Matrix
            xLabels={topics.map((t) => t.short)}
            yLabels={parties.map(partyShort)}
            values={lift.values}
            hoverText={lift.hover}
            mode={mode}
            scale="diverging"
            zmin={-LIFT_LOG_BOUND}
            zmax={LIFT_LOG_BOUND}
            zmid={0}
            valueFormat=".1f"
            height={Math.max(320, parties.length * 32 + 110)}
            colorbarTitle="log₂ rapporto"
            title="Sovra e sotto-rappresentazione dei temi per gruppo"
          />
        </CardBody>
        <CardFooter>
          LA SCALA È IL LOGARITMO IN BASE 2 DEL RAPPORTO: +1 = IL DOPPIO DELLA MEDIA, −1 = LA METÀ.
        </CardFooter>
      </Card>

      <Card className="lg:col-span-2">
        <CardHeader
          title="Indice di generalismo"
          subtitle="Ampiezza tematica: 100 = interviene in egual misura su tutte le aree, 0 = una sola"
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
        <CardFooter>
          CALCOLATO SOLO PER CHI HA ALMENO 20 INTERVENTI CLASSIFICATI: CON POCHI INTERVENTI
          L&apos;ENTROPIA È SOTTOSTIMATA PER COSTRUZIONE.
        </CardFooter>
      </Card>
    </div>
  );
}
