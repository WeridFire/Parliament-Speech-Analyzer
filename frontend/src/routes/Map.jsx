import { useCallback, useDeferredValue, useMemo, useState } from 'react';
import { Search, X } from 'lucide-react';
import { Page } from '../layout/AppShell';
import { PeriodControls } from '../layout/PeriodControls';
import { useData } from '../data/DataProvider';
import { useSpeeches } from '../data/resources';
import { useAppParams } from '../app/useAppParams';
import { useTheme } from '../lib/useTheme';
import {
  availablePeriods,
  cleanName,
  deputiesFor,
  partiesIn,
  speechesFor,
  toMapPoints,
} from '../data/selectors';
import { topicList } from '../domain/topics';
import { partyDot, partyShort, partyShape, resolveParty, sortParties } from '../domain/parties';
import { ScatterMap } from '../viz/charts/ScatterMap';
import { seriesColor, SERIES_CAP, OTHER_COLOR } from '../viz/palette';
import { Card, CardBody, CardHeader, Chip, Legend, SegmentedControl, Skeleton, StatTile } from '../ui';
import { int } from '../lib/format';
import { SpeechModal } from './SpeechModal';
import { cn } from '../lib/cn';

export default function MapRoute() {
  const { data, chamberMeta, availableChambers } = useData();
  const { mode } = useTheme();
  const {
    chamber, setChamber, period, setPeriod,
    view, colorBy, focus, deputies,
    update, toggleFocus, toggleDeputy, clearFocus, clearDeputies,
  } = useAppParams();

  const [openSpeech, setOpenSpeech] = useState(null);

  // Speeches are a separate resource: the deputies view never downloads them.
  const { data: speeches, status: speechStatus } = useSpeeches();

  const clusters = data?.clusters ?? {};
  const periods = useMemo(() => availablePeriods(data), [data]);

  const items = useMemo(
    () => (view === 'deputati' ? deputiesFor(data, period) : speechesFor(speeches, period)),
    [data, speeches, period, view],
  );

  const itemsLoading = view !== 'deputati' && speechStatus === 'loading';

  const points = useMemo(
    () =>
      toMapPoints({
        items,
        kind: view === 'deputati' ? 'deputies' : 'speeches',
        colorBy: colorBy === 'partito' ? 'party' : 'cluster',
        clusters,
      }),
    [items, view, colorBy, clusters],
  );

  /**
   * Legend entries double as the focus control. Counts come from the points
   * actually on screen, so they track the period filter.
   */
  const groups = useMemo(() => {
    const counts = new Map();
    for (const p of points) {
      const prev = counts.get(p.groupKey);
      if (prev) prev.count += 1;
      else counts.set(p.groupKey, { key: p.groupKey, label: p.groupLabel, count: 1 });
    }

    const ordered =
      colorBy === 'partito'
        ? sortParties(partiesIn(items)).map((raw) => `p-${resolveParty(raw).id}`)
        : topicList(clusters).map((t) => `c-${t.id}`);

    const list = ordered.map((key) => counts.get(key)).filter(Boolean);
    // Anything present in the data but absent from the registry ordering.
    for (const [key, entry] of counts) if (!ordered.includes(key)) list.push(entry);

    const focusIndex = new Map(focus.slice(0, SERIES_CAP.allPairs).map((k, i) => [k, i]));

    return list.map((entry) => ({
      ...entry,
      color: focusIndex.has(entry.key)
        ? seriesColor(focusIndex.get(entry.key), mode, 'allPairs')
        : OTHER_COLOR[mode],
      active: focus.length === 0 || focusIndex.has(entry.key),
    }));
  }, [points, items, colorBy, clusters, focus, mode]);

  const shapeFor = useCallback(
    (p) => (colorBy === 'partito' ? partyShape(p.party) : 'circle'),
    [colorBy],
  );

  const pointsById = useMemo(() => new Map(points.map((p) => [p.id, p])), [points]);

  const onPointClick = useCallback(
    (id) => {
      const point = pointsById.get(id);
      if (!point) return;
      if (view === 'deputati') toggleDeputy(point.pinKey);
      else setOpenSpeech(point.raw);
    },
    [pointsById, view, toggleDeputy],
  );

  return (
    <Page wide className="flex min-h-[calc(100dvh-3.5rem)] flex-col gap-5 py-6">
      <header className="flex flex-wrap items-end justify-between gap-x-8 gap-y-4">
        <div>
          <p className="text-label text-muted">MAPPA SEMANTICA · {chamberMeta.full.toUpperCase()}</p>
          <h1 className="mt-1.5 text-display">
            {view === 'deputati' ? 'Posizione dei parlamentari' : 'Lo spazio del discorso'}
          </h1>
        </div>
        <PeriodControls
          chamber={chamber}
          availableChambers={availableChambers}
          onChamberChange={setChamber}
          period={period}
          periods={periods}
          onPeriodChange={setPeriod}
        />
      </header>

      <div className="grid min-h-0 flex-1 gap-5 lg:grid-cols-[minmax(0,1fr)_300px]">
        <Card className="min-h-[420px]">
          <CardHeader
            title={view === 'deputati' ? 'Parlamentari' : 'Interventi'}
            subtitle={
              focus.length
                ? 'Gli elementi evidenziati sono a colori; il resto resta come contesto.'
                : 'Seleziona fino a tre voci dalla legenda per evidenziarle.'
            }
            actions={
              <div className="flex flex-wrap items-center gap-2">
                <SegmentedControl
                  size="sm"
                  value={view}
                  onChange={(v) => update({ vista: v })}
                  options={[
                    { value: 'interventi', label: 'Interventi' },
                    { value: 'deputati', label: 'Deputati' },
                  ]}
                />
                <SegmentedControl
                  size="sm"
                  value={colorBy}
                  onChange={(v) => update({ colora: v, focus: null })}
                  options={[
                    { value: 'tema', label: 'Tema' },
                    { value: 'partito', label: 'Gruppo' },
                  ]}
                />
              </div>
            }
          />
          <CardBody className="p-2 sm:p-3">
            {itemsLoading ? (
              <Skeleton className="h-140 w-full" />
            ) : (
              <ScatterMap
                points={points}
                focusKeys={focus}
                selectedIds={deputies}
                shapeFor={shapeFor}
                mode={mode}
                height={560}
                onPointClick={onPointClick}
                axisLabels={{ x: 'Dimensione semantica 1', y: 'Dimensione semantica 2' }}
              />
            )}
          </CardBody>
        </Card>

        <aside className="flex min-w-0 flex-col gap-5">
          <Card>
            <CardHeader
              title={colorBy === 'partito' ? 'Gruppi' : 'Aree tematiche'}
              subtitle={`Evidenzia fino a ${SERIES_CAP.allPairs}`}
              actions={
                focus.length ? (
                  <button
                    type="button"
                    onClick={clearFocus}
                    className="text-label text-muted hover:text-ink"
                  >
                    AZZERA
                  </button>
                ) : null
              }
            />
            <CardBody className="max-h-72 overflow-y-auto py-3">
              <Legend
                items={groups}
                orientation="vertical"
                onToggle={(key) => toggleFocus(key, SERIES_CAP.allPairs)}
              />
            </CardBody>
          </Card>

          <DeputySearch
            data={data}
            pinned={deputies}
            onToggle={toggleDeputy}
            onClear={clearDeputies}
            mode={mode}
          />

          <Card>
            <CardBody className="grid grid-cols-2 gap-4">
              <StatTile label="Sulla mappa" value={int(points.length)} />
              <StatTile
                label={colorBy === 'partito' ? 'Gruppi' : 'Temi'}
                value={int(groups.length)}
              />
            </CardBody>
          </Card>
        </aside>
      </div>

      {openSpeech ? (
        <SpeechModal speech={openSpeech} clusters={clusters} onClose={() => setOpenSpeech(null)} />
      ) : null}
    </Page>
  );
}

/**
 * Type-ahead over the deputy roster. Pinned deputies are highlighted and
 * labelled on the map in both views.
 */
function DeputySearch({ data, pinned, onToggle, onClear, mode }) {
  const [query, setQuery] = useState('');
  const deferred = useDeferredValue(query);

  const roster = useMemo(() => data?.deputies ?? [], [data]);

  const results = useMemo(() => {
    const q = deferred.trim().toLowerCase();
    if (q.length < 2) return [];
    return roster
      .filter((d) => (d.name ?? d.deputy ?? '').toLowerCase().includes(q))
      .slice(0, 8);
  }, [roster, deferred]);

  return (
    <Card>
      <CardHeader
        title="Cerca un parlamentare"
        actions={
          pinned.length ? (
            <button type="button" onClick={onClear} className="text-label text-muted hover:text-ink">
              AZZERA
            </button>
          ) : null
        }
      />
      <CardBody className="py-3">
        <div className="relative">
          <Search
            size={14}
            className="pointer-events-none absolute top-1/2 left-2.5 -translate-y-1/2 text-muted"
            aria-hidden="true"
          />
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Cognome…"
            aria-label="Cerca un parlamentare"
            className="w-full rounded-sm border border-rule bg-surface py-1.5 pr-2.5 pl-8 text-body text-ink transition-colors duration-150 hover:border-rule-strong"
          />
        </div>

        {results.length > 0 && (
          <ul className="mt-2 flex flex-col">
            {results.map((d) => {
              const active = pinned.includes(d.deputy);
              return (
                <li key={d.deputy}>
                  <button
                    type="button"
                    onClick={() => onToggle(d.deputy)}
                    className={cn(
                      'flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-left transition-colors duration-150',
                      active ? 'bg-accent-soft' : 'hover:bg-hover',
                    )}
                  >
                    <span
                      className="h-2 w-2 shrink-0 rounded-full"
                      style={{ backgroundColor: partyDot(d.party, mode) }}
                      aria-hidden="true"
                    />
                    <span className="min-w-0 flex-1 truncate text-body text-ink">
                      {cleanName(d.name ?? d.deputy)}
                    </span>
                    <span className="shrink-0 text-label text-muted">{partyShort(d.party)}</span>
                  </button>
                </li>
              );
            })}
          </ul>
        )}

        {pinned.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5 border-t border-rule pt-3">
            {pinned.map((key) => (
              <Chip key={key} size="sm" selected onClick={() => onToggle(key)} title="Rimuovi">
                {cleanName(key)}
                <X size={11} aria-hidden="true" />
              </Chip>
            ))}
          </div>
        )}
      </CardBody>
    </Card>
  );
}
