import { useMemo } from 'react';
import { Chart } from '../Chart';
import { buildLayout, buildConfig, markRing } from '../plotlyTheme';
import { CHROME, seriesColor, SERIES_CAP } from '../palette';

/**
 * The semantic map — up to ~10.700 speeches positioned by PCA of their
 * embeddings.
 *
 * WHY FOCUS + CONTEXT, not "colour every group"
 * ---------------------------------------------
 * A scatter is an all-pairs form: any two marks can end up adjacent, so every
 * pair of series colours must be separable, not just neighbouring ones. That is
 * a strictly harder gate and only the first 3 palette slots clear it (measured:
 * CVD ΔE 9.2 light / 9.4 dark). Fourteen topic colours cannot be made safe —
 * the old code silently reused colours via `CLUSTER_COLORS[cluster % 10]`, so
 * clusters 10–13 were indistinguishable from 0–3 by construction.
 *
 * So the map dims everything to a neutral context layer and lights up only the
 * focused groups, capped at 3. This is also simply more legible: ten thousand
 * overlapping marks in fourteen colours is noise regardless of the palette.
 *
 * @param {Array}    points     [{ id, x, y, groupKey, groupLabel, name, party, sub }]
 * @param {string[]} focusKeys  group keys to highlight (max 3 are coloured)
 * @param {string[]} selectedIds  point ids pinned by the user
 */
export function ScatterMap({
  points,
  focusKeys = [],
  selectedIds = [],
  shapeFor,
  mode = 'light',
  height = 560,
  axisLabels = { x: 'Componente 1', y: 'Componente 2' },
  onPointClick,
  title = 'Mappa semantica',
}) {
  const { data, layout, config } = useMemo(() => {
    const c = CHROME[mode];
    if (!points?.length) return { data: [], layout: buildLayout(mode), config: buildConfig() };

    // WebGL past a few thousand marks; SVG below it keeps symbol fidelity.
    const traceType = points.length > 2500 ? 'scattergl' : 'scatter';

    const focused = focusKeys.slice(0, SERIES_CAP.allPairs);
    const colorByKey = new Map(focused.map((k, i) => [k, seriesColor(i, mode, 'allPairs')]));

    const pins = new Set(selectedIds);
    const isPinned = (p) => pins.has(p.pinKey ?? p.id);

    const hover =
      '<b>%{customdata[0]}</b><br>%{customdata[1]}<br>%{customdata[2]}<extra></extra>';

    const traces = [];

    // ---- Context layer: everything not focused, one recessive neutral ----
    const context = points.filter((p) => !colorByKey.has(p.groupKey) && !isPinned(p));
    if (context.length) {
      traces.push({
        type: traceType,
        mode: 'markers',
        name: focused.length ? 'Altri' : 'Interventi',
        x: context.map((p) => p.x),
        y: context.map((p) => p.y),
        customdata: context.map((p) => [p.name, p.groupLabel, p.sub ?? '', p.id]),
        marker: {
          color: c.muted,
          size: 5,
          opacity: focused.length ? 0.18 : 0.42,
          line: { width: 0 },
        },
        hovertemplate: hover,
        showlegend: false,
      });
    }

    // ---- Focus layer: one trace per focused group, in palette order ----
    for (const key of focused) {
      const group = points.filter((p) => p.groupKey === key && !isPinned(p));
      if (!group.length) continue;

      traces.push({
        type: traceType,
        mode: 'markers',
        name: group[0].groupLabel,
        x: group.map((p) => p.x),
        y: group.map((p) => p.y),
        customdata: group.map((p) => [p.name, p.groupLabel, p.sub ?? '', p.id]),
        marker: {
          color: colorByKey.get(key),
          size: 7,
          opacity: 0.85,
          symbol: shapeFor ? group.map((p) => shapeFor(p)) : 'circle',
          line: markRing(mode, 0.5),
        },
        hovertemplate: hover,
        showlegend: false,
      });
    }

    // ---- Pinned points: always on top, always labelled ----
    const pinned = points.filter(isPinned);
    if (pinned.length) {
      traces.push({
        type: 'scatter', // SVG so the text layer renders crisply
        mode: 'markers+text',
        name: 'Selezionati',
        x: pinned.map((p) => p.x),
        y: pinned.map((p) => p.y),
        text: pinned.map((p) => p.name),
        textposition: 'top center',
        textfont: { size: 11, color: c.ink },
        customdata: pinned.map((p) => [p.name, p.groupLabel, p.sub ?? '', p.id]),
        marker: {
          color: c.accent,
          size: 13,
          symbol: shapeFor ? pinned.map((p) => shapeFor(p)) : 'circle',
          line: markRing(mode, 2),
        },
        hovertemplate: hover,
        showlegend: false,
      });
    }

    return {
      data: traces,
      layout: buildLayout(mode, {
        showlegend: false, // the Legend primitive drives focus outside the canvas
        margin: { l: 44, r: 16, t: 8, b: 40 },
        hovermode: 'closest',
        xaxis: { title: { text: axisLabels.x }, zeroline: true, scaleanchor: 'y', scaleratio: 1 },
        yaxis: { title: { text: axisLabels.y }, zeroline: true },
      }),
      config: buildConfig({ interactive: true, filename: 'mappa-semantica' }),
    };
  }, [points, focusKeys, selectedIds, shapeFor, mode, axisLabels.x, axisLabels.y]);

  // Plotly hands back its own event shape; resolve it to the caller's point id
  // here so no route has to know about customdata indices.
  const handleClick = onPointClick
    ? (event) => {
        const id = event?.points?.[0]?.customdata?.[3];
        if (id != null) onPointClick(id);
      }
    : undefined;

  return (
    <Chart
      data={data}
      layout={layout}
      config={config}
      height={height}
      title={title}
      isEmpty={!points?.length}
      emptyMessage="Nessun intervento nel periodo selezionato."
      className="h-full"
      onClick={handleClick}
    />
  );
}
