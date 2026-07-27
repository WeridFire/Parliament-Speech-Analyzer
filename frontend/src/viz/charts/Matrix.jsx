import { useMemo } from 'react';
import { Chart } from '../Chart';
import { buildLayout, buildConfig } from '../plotlyTheme';
import { CHROME, sequentialScale, divergingScale } from '../palette';

/**
 * Heatmap.
 *
 * A matrix encodes magnitude or polarity, never identity, so it takes a ramp
 * rather than categorical slots:
 *
 *   scale="sequential" — one hue, light -> dark (affinity, density)
 *   scale="diverging"  — blue <-> red with a NEUTRAL GRAY midpoint (sentiment)
 *
 * The previous sentiment heatmap used red -> #242930 -> green: red/green is the
 * worst possible pair for colour-vision deficiency, and its midpoint was a dark
 * surface colour rather than a neutral, so "no sentiment" read as "missing".
 *
 * @param {string[]}   xLabels
 * @param {string[]}   yLabels
 * @param {number[][]} values   rows = y, cols = x
 */
export function Matrix({
  xLabels,
  yLabels,
  values,
  mode = 'light',
  scale = 'sequential',
  zmin,
  zmax,
  height = 420,
  valueFormat = '.2f',
  colorbarTitle,
  xTitle,
  yTitle,
  title,
}) {
  const { data, layout, config } = useMemo(() => {
    const c = CHROME[mode];
    const diverging = scale === 'diverging';

    return {
      data: [
        {
          type: 'heatmap',
          x: xLabels,
          y: yLabels,
          z: values,
          zmin,
          zmax,
          colorscale: diverging ? divergingScale(mode) : sequentialScale(mode),
          // A hairline between cells keeps adjacent values separable.
          xgap: 1,
          ygap: 1,
          hovertemplate: `<b>%{y}</b> · %{x}<br>%{z:${valueFormat}}<extra></extra>`,
          colorbar: {
            title: colorbarTitle ? { text: colorbarTitle, side: 'right' } : undefined,
            thickness: 10,
            len: 0.75,
            outlinewidth: 0,
            tickfont: { size: 10, color: c.muted },
            tickformat: valueFormat,
          },
        },
      ],
      layout: buildLayout(mode, {
        margin: { l: 8, r: 8, t: 8, b: 8 },
        xaxis: {
          side: 'bottom',
          tickangle: -35,
          gridcolor: 'transparent',
          zeroline: false,
          title: xTitle ? { text: xTitle } : undefined,
        },
        yaxis: {
          autorange: 'reversed',
          gridcolor: 'transparent',
          zeroline: false,
          title: yTitle ? { text: yTitle } : undefined,
        },
      }),
      config: buildConfig({ filename: title ?? 'matrice' }),
    };
  }, [xLabels, yLabels, values, mode, scale, zmin, zmax, valueFormat, colorbarTitle, xTitle, yTitle, title]);

  return (
    <Chart
      data={data}
      layout={layout}
      config={config}
      height={height}
      title={title}
      isEmpty={!xLabels?.length || !yLabels?.length || !values?.length}
    />
  );
}
