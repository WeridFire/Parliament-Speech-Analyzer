import { useMemo } from 'react';
import { Chart } from '../Chart';
import { buildLayout, buildConfig } from '../plotlyTheme';
import { CHROME, STATUS, assignSeries } from '../palette';

/**
 * Multi-series line chart over ordered periods.
 *
 * 2px lines, ≥8px markers, a crosshair hover that reads every series at once.
 * Never a second y-axis: two measures of different scale become two charts.
 *
 * @param {string[]} periods  x values, already display-formatted
 * @param {Array}    series   [{ key, label, values }]
 */
export function TrendLines({
  periods,
  series,
  mode = 'light',
  height = 340,
  valueSuffix = '',
  yTitle,
  title,
}) {
  const { data, layout, config } = useMemo(() => {
    const assigned = assignSeries(series, mode, 'adjacent');

    const traces = assigned.map((s) => {
      const source = series.find((x) => x.key === s.key);
      return {
        type: 'scatter',
        mode: 'lines+markers',
        name: s.label,
        x: periods,
        y: source?.values ?? [],
        line: { color: s.color, width: 2, shape: 'linear' },
        marker: { color: s.color, size: 6 },
        hovertemplate: `${s.label}: %{y:,.1f}${valueSuffix}<extra></extra>`,
      };
    });

    return {
      data: traces,
      layout: buildLayout(mode, {
        showlegend: series.length > 1,
        hovermode: 'x unified',
        margin: { l: 52, r: 16, t: series.length > 1 ? 34 : 10, b: 56 },
        xaxis: { tickangle: -35, gridcolor: 'transparent' },
        yaxis: { title: yTitle ? { text: yTitle } : undefined, rangemode: 'tozero' },
      }),
      config: buildConfig({ filename: title ?? 'trend' }),
    };
  }, [periods, series, mode, valueSuffix, yTitle, title]);

  return (
    <Chart
      data={data}
      layout={layout}
      config={config}
      height={height}
      title={title}
      isEmpty={!periods?.length || !series?.length}
    />
  );
}

/**
 * Single-series filled area. Used for the crisis index, which is one measure
 * over time — one colour, no legend, the card title names it.
 */
export function AreaTrend({
  periods,
  values,
  mode = 'light',
  height = 260,
  tone = 'critical',
  label = 'Valore',
  valueSuffix = '',
  yTitle,
  title,
}) {
  const { data, layout, config } = useMemo(() => {
    const stroke = STATUS[tone] ?? CHROME[mode].accent;
    return {
      data: [
        {
          type: 'scatter',
          mode: 'lines',
          name: label,
          x: periods,
          y: values,
          line: { color: stroke, width: 2 },
          fill: 'tozeroy',
          fillcolor: hexToRgba(stroke, mode === 'dark' ? 0.22 : 0.14),
          hovertemplate: `%{x}<br>${label}: %{y:,.2f}${valueSuffix}<extra></extra>`,
        },
      ],
      layout: buildLayout(mode, {
        showlegend: false,
        hovermode: 'x unified',
        margin: { l: 52, r: 16, t: 10, b: 56 },
        xaxis: { tickangle: -35, gridcolor: 'transparent' },
        yaxis: { title: yTitle ? { text: yTitle } : undefined, rangemode: 'tozero' },
      }),
      config: buildConfig({ filename: title ?? 'area' }),
    };
  }, [periods, values, mode, tone, label, valueSuffix, yTitle, title]);

  return (
    <Chart
      data={data}
      layout={layout}
      config={config}
      height={height}
      title={title}
      isEmpty={!periods?.length}
    />
  );
}

function hexToRgba(hex, alpha) {
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${alpha})`;
}
