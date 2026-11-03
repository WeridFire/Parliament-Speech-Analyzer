import { useMemo, useState } from 'react';
import { Card, CardBody, CardFooter, CardHeader, RankingList, ScopeNote, Select, Table } from '../../ui';
import { Matrix } from '../../viz/charts/Matrix';
import { useAnalysis } from './context';
import { partyDot, partyShort, sortParties } from '../../domain/parties';
import { cleanName } from '../../data/selectors';
import { dec, int } from '../../lib/format';
import { NoDataForPeriod } from '../../ui/EmptyState';

/**
 * Which groups name which leaders, ministers and foreign heads of government.
 * Rates are per 100 speeches of the mentioning group, so a large group does not
 * dominate simply by speaking more.
 */
export default function Mentions() {
  const { section, period, mode } = useAnalysis();
  const { data: mentions, fromGlobal } = section('mentions');

  const figures = useMemo(() => mentions?.figures ?? [], [mentions]);
  const [figureId, setFigureId] = useState('');
  const figure = figures.find((f) => f.id === figureId) ?? figures[0];

  const ranking = useMemo(() => {
    const max = Math.max(0.01, ...figures.map((f) => f.rate));
    return figures.slice(0, 15).map((f) => ({
      key: f.id,
      name: f.name,
      meta: `${f.group_label} · ${int(f.n)} interventi`,
      percent: (f.rate / max) * 100,
      value: dec(f.rate),
    }));
  }, [figures]);

  const matrix = useMemo(() => {
    const source = mentions?.matrix;
    if (!source?.parties?.length || !source.figures.length) return null;
    const names = Object.fromEntries(figures.map((f) => [f.id, f.short ?? f.name]));
    const order = sortParties(source.parties);
    const rows = order.map((p) => source.rates[source.parties.indexOf(p)]);
    const peak = Math.max(0.1, ...rows.flat());
    return { x: source.figures.map((id) => names[id] ?? id), y: order.map(partyShort), rows, peak };
  }, [mentions, figures]);

  if (!mentions || !figures.length) {
    return <NoDataForPeriod feature="l'analisi delle menzioni" period={period} />;
  }

  const speakers = (figure?.top_speakers ?? []).map((s) => ({
    key: s.speaker,
    name: cleanName(s.speaker),
    meta: partyShort(s.party),
    percent: null,
    value: `${int(s.n)}`,
    dot: partyDot(s.party, mode),
  }));

  return (
    <div className="grid gap-5 lg:grid-cols-2">
      <div className="lg:col-span-2">
        <ScopeNote fromGlobal={fromGlobal} period={period} />
      </div>

      <Card>
        <CardHeader title="I più nominati" subtitle="Interventi che li nominano, ogni 100 interventi" />
        <CardBody>
          <RankingList items={ranking} />
        </CardBody>
      </Card>

      <Card>
        <CardHeader
          title="Maggioranza e opposizione"
          subtitle="Quanto spesso ciascuno schieramento nomina la figura, ogni 100 interventi"
        />
        <CardBody>
          <Table
            caption="Menzioni per schieramento"
            columns={[
              { key: 'name', header: 'Figura', render: (f) => f.name },
              { key: 'maj', header: 'Magg.', numeric: true, width: '5rem', render: (f) => dec(f.by_bloc.maggioranza) },
              { key: 'opp', header: 'Opp.', numeric: true, width: '5rem', render: (f) => dec(f.by_bloc.opposizione) },
            ]}
            rows={figures.slice(0, 12)}
            getRowKey={(f) => f.id}
          />
        </CardBody>
      </Card>

      {matrix ? (
        <Card className="lg:col-span-2">
          <CardHeader title="Chi nomina chi" subtitle="Interventi del gruppo che nominano la figura, ogni 100" />
          <CardBody>
            <Matrix
              xLabels={matrix.x}
              yLabels={matrix.y}
              values={matrix.rows}
              mode={mode}
              scale="sequential"
              zmin={0}
              zmax={matrix.peak}
              valueFormat=".1f"
              height={Math.max(320, matrix.y.length * 32 + 120)}
              colorbarTitle="Ogni 100"
              title="Chi nomina chi"
            />
          </CardBody>
        </Card>
      ) : null}

      <Card className="lg:col-span-2">
        <CardHeader
          title={figure ? `Chi nomina ${figure.name}` : 'Chi nomina'}
          actions={
            <Select
              label="Figura"
              hideLabel
              value={figure?.id ?? ''}
              onChange={setFigureId}
              className="w-60"
              options={figures.map((f) => ({ value: f.id, label: f.name }))}
            />
          }
        />
        <CardBody>
          <RankingList items={speakers} />
        </CardBody>
        <CardFooter>
          ELENCO CURATO DI LEADER, MINISTRI E CAPI DI GOVERNO STRANIERI, RICONOSCIUTI PER COGNOME CON
          L&apos;INIZIALE MAIUSCOLA. UNA MENZIONE NON DICE SE È UNA CRITICA O UN SOSTEGNO, E CHI PARLA
          NON VIENE CONTATO QUANDO NOMINA SE STESSO.
        </CardFooter>
      </Card>
    </div>
  );
}
