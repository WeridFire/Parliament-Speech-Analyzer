import { useMemo } from 'react';
import { Chart } from '../Chart';
import { buildLayout, buildConfig } from '../plotlyTheme';
import { CHROME, STATUS, assignSeries } from '../palette';

/**
 * Bar chart for 1–8 series over shared categories.
 *
 * Uses the adjacent pairlist (only neighbouring bars touch), so the full 8
 * slots are available; `assignSeries` folds anything beyond into "Altri".
 *
 * A single series takes slot 1 and no legend — the card title names it. Two or
 * more always get a legend, so identity never rests on colour alone.
 *
 * @param {string[]} categories
 * @param {Array}    series      [{ key, label, values, color?, tone? }]
 * @param {'v'|'h'}  orientation
 */
export function CategoryBars({
  categories,
  series,
  mode = 'light',
  orientation = 'v',
  height = 320,
  valueSuffix = '',
  valueFormat = ',.1f',
  stacked = false,
  title,
  layout: layoutOverrides,
}) {
  const { data, layout, config } = useMemo(() => {
    const c = CHROME[mode];
    const horizontal = orientation === 'h';
    const assigned = assignSeries(series, mode, 'adjacent');

    const traces = assigned.map((s) => {
      const source = series.find((x) => x.key === s.key);
      const values = source?.values ?? [];

      // A per-category tone overrides the series colour: bars that MEAN
      // good/bad (sentiment sign) wear status tokens rather than categorical.
      const colors = source?.tones
        ? source.tones.map((t) => STATUS[t] ?? s.color)
        : s.color;

      return {
        type: 'bar',
        name: s.label,
        orientation,
        [horizontal ? 'y' : 'x']: categories,
        [horizontal ? 'x' : 'y']: values,
        marker: {
          color: colors,
          // 2px surface gap keeps adjacent and stacked fills separable.
          line: { color: c.surface, width: 1 },
        },
        hovertemplate: `<b>%{${horizontal ? 'y' : 'x'}}</b><br>${s.label}: %{${
          horizontal ? 'x' : 'y'
        }:${valueFormat}}${valueSuffix}<extra></extra>`,
      };
    });

    return {
      data: traces,
      layout: buildLayout(mode, {
        barmode: stacked ? 'stack' : 'group',
        bargap: 0.28,
        bargroupgap: 0.12,
        showlegend: series.length > 1,
        margin: horizontal
          ? { l: 4, r: 24, t: series.length > 1 ? 34 : 8, b: 32 }
          : { l: 48, r: 16, t: series.length > 1 ? 34 : 8, b: 64 },
        xaxis: horizontal
          ? { zeroline: true }
          : { tickangle: -35, gridcolor: 'transparent', automargin: true },
        yaxis: horizontal
          ? { gridcolor: 'transparent', automargin: true }
          : { zeroline: true },
        ...layoutOverrides,
      }),
      config: buildConfig({ filename: title ?? 'grafico-barre' }),
    };
  }, [categories, series, mode, orientation, stacked, valueSuffix, valueFormat, title, layoutOverrides]);

  return (
    <Chart
      data={data}
      layout={layout}
      config={config}
      height={height}
      title={title}
      isEmpty={!categories?.length || !series?.length}
    />
  );
}
