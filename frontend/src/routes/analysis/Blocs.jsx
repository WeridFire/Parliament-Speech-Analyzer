import { useMemo } from 'react';
import { Card, CardBody, CardFooter, CardHeader, ScopeNote, StatRow, StatTile } from '../../ui';
import { ClassificationTag } from '../../ui/Chip';
import { WordCloud } from '../../viz/charts/WordCloud';
import { seriesColor } from '../../viz/palette';
import { useAnalysis } from './context';
import { BLOC_LABELS } from '../../domain/metrics';
import { dec, int, pct } from '../../lib/format';
import { NoDataForPeriod } from '../../ui/EmptyState';

/**
 * Majority (with the government) against the opposition: which topics each
 * side makes its own, and the words that separate them.
 */
export default function Blocs() {
  const { section, period, mode } = useAnalysis();
  const { data: blocs, fromGlobal } = section('blocs');

  const colors = useMemo(
    () => ({ maggioranza: seriesColor(0, mode), opposizione: seriesColor(1, mode) }),
    [mode],
  );

  const ownership = useMemo(() => {
    const rows = (blocs?.ownership ?? []).filter((e) => e.ratio != null);
    const bound = Math.max(1, ...rows.map((e) => Math.abs(e.ratio)));
    return { rows, bound };
  }, [blocs]);

  if (!blocs) return <NoDataForPeriod feature="il confronto fra maggioranza e opposizione" period={period} />;

  const summary = blocs.summary ?? {};

  return (
    <div className="grid gap-5 lg:grid-cols-2">
      <div className="lg:col-span-2">
        <ScopeNote fromGlobal={fromGlobal} period={period} />
      </div>

      <Card className="lg:col-span-2">
        <CardHeader title="Chi occupa l'Aula" subtitle="Volume degli interventi dei due schieramenti" />
        <CardBody>
          <StatRow>
            {['maggioranza', 'opposizione'].flatMap((bloc) => [
              <StatTile
                key={`${bloc}-share`}
                label={BLOC_LABELS[bloc]}
                value={pct(summary[bloc]?.share, { digits: 0 })}
                meta={`${int(summary[bloc]?.n_speeches)} interventi`}
              />,
              <StatTile
                key={`${bloc}-speakers`}
                label="Oratori"
                value={int(summary[bloc]?.n_speakers)}
                meta={`${int(summary[bloc]?.avg_words)} parole per intervento`}
              />,
            ])}
          </StatRow>
        </CardBody>
      </Card>

      <Card className="lg:col-span-2">
        <CardHeader
          title="A chi appartiene ogni tema"
          subtitle="Quota dell'attenzione di ciascuno schieramento dedicata al tema"
        />
        <CardBody>
          <div className="mb-3 flex justify-between text-label text-muted">
            <span className="flex items-center gap-1.5">
              <Swatch color={colors.opposizione} /> PIÙ ATTENZIONE DALL&apos;OPPOSIZIONE
            </span>
            <span className="flex items-center gap-1.5">
              PIÙ ATTENZIONE DALLA MAGGIORANZA <Swatch color={colors.maggioranza} />
            </span>
          </div>
          <ul className="flex flex-col">
            {ownership.rows.map((e) => (
              <OwnershipRow key={e.topic} entry={e} bound={ownership.bound} colors={colors} />
            ))}
          </ul>
        </CardBody>
        <CardFooter>
          CONTA LA QUOTA DEI PROPRI INTERVENTI, NON IL NUMERO: L&apos;OPPOSIZIONE PARLA DI PIÙ IN
          ASSOLUTO, E A CONTEGGI GREZZI SAREBBE «PADRONA» DI QUASI OGNI TEMA. UN TEMA È DI UNO
          SCHIERAMENTO QUANDO GLI DEDICA ALMENO 1,4 VOLTE L&apos;ATTENZIONE DELL&apos;ALTRO.
        </CardFooter>
      </Card>

      {['maggioranza', 'opposizione'].map((bloc) => (
        <Card key={bloc}>
          <CardHeader
            title={bloc === 'maggioranza' ? 'Il lessico della maggioranza' : "Il lessico dell'opposizione"}
            subtitle={`Parole che ${BLOC_LABELS[bloc].toLowerCase()} usa più dell'altro schieramento`}
          />
          <CardBody className="flex items-center justify-center">
            <WordCloud words={blocs.keywords?.[bloc]} mode={mode} max={25} />
          </CardBody>
        </Card>
      ))}
    </div>
  );
}

function OwnershipRow({ entry, bound, colors }) {
  const width = (Math.abs(entry.ratio) / bound) * 50;
  const toMajority = entry.ratio > 0;

  return (
    <li className="grid grid-cols-[minmax(0,10rem)_minmax(0,1fr)] items-center gap-3 border-b border-rule py-2 last:border-b-0 sm:grid-cols-[minmax(0,12rem)_minmax(0,1fr)_9rem]">
      <div className="min-w-0">
        <span className="block truncate text-body font-medium text-ink" title={entry.label}>
          {entry.label}
        </span>
        <span className="text-label text-muted">
          MAGG. {dec(entry.maggioranza)}% · OPP. {dec(entry.opposizione)}%
        </span>
      </div>
      <div className="relative h-3" role="img" aria-label={`${entry.label}: rapporto ${dec(2 ** entry.ratio)}`}>
        <span className="absolute inset-y-0 left-1/2 w-px bg-rule-strong" aria-hidden="true" />
        <span
          className="absolute inset-y-0.5 rounded-xs"
          style={{
            backgroundColor: toMajority ? colors.maggioranza : colors.opposizione,
            left: toMajority ? '50%' : `${50 - width}%`,
            width: `${width}%`,
          }}
          aria-hidden="true"
        />
      </div>
      <div className="hidden justify-end sm:flex">
        <ClassificationTag value={entry.owner} />
      </div>
    </li>
  );
}

function Swatch({ color }) {
  return <span className="h-2 w-2 shrink-0 rounded-full" style={{ backgroundColor: color }} aria-hidden="true" />;
}
