import { useMemo } from 'react';
import { Chart } from '../Chart';
import { buildPolarLayout, buildConfig } from '../plotlyTheme';
import { seriesColor } from '../palette';

/**
 * Scatterpolar radar.
 *
 * Capped at 3 overlapping series: filled polygons stack on top of each other,
 * so every pair can touch — the all-pairs rule applies, and only the first 3
 * slots clear it. Comparing more than three is a small-multiples job.
 *
 * @param {string[]} axes    spoke labels
 * @param {Array}    series  [{ key, label, values }] — values 0..1
 */
export function Radar({ axes, series, mode = 'light', height = 340, range = [0, 1], title }) {
  const { data, layout, config } = useMemo(() => {
    const capped = series.slice(0, 3);

    const traces = capped.map((s, i) => {
      const color = seriesColor(i, mode, 'allPairs');
      // Close the polygon by repeating the first point.
      const r = [...s.values, s.values[0]];
      const theta = [...axes, axes[0]];

      return {
        type: 'scatterpolar',
        name: s.label,
        r,
        theta,
        fill: 'toself',
        fillcolor: hexToRgba(color, capped.length > 1 ? 0.12 : 0.18),
        line: { color, width: 2 },
        marker: { color, size: 5 },
        hovertemplate: `<b>%{theta}</b><br>${s.label}: %{r:.2f}<extra></extra>`,
      };
    });

    return {
      data: traces,
      layout: buildPolarLayout(mode, {
        showlegend: capped.length > 1,
        polar: { radialaxis: { range, tickformat: '.1f' } },
      }),
      config: buildConfig({ filename: title ?? 'radar' }),
    };
  }, [axes, series, mode, range, title]);

  return (
    <Chart
      data={data}
      layout={layout}
      config={config}
      height={height}
      title={title}
      isEmpty={!axes?.length || !series?.length}
    />
  );
}

function hexToRgba(hex, alpha) {
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${alpha})`;
}
