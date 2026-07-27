import { CHROME } from './palette';

/**
 * The single Plotly theme.
 *
 * Replaces eight hand-copied layout objects — every chart file previously
 * re-declared paper_bgcolor, plot_bgcolor, tickfonts and gridcolors by hand,
 * with three different greys for "muted" and two different grid opacities.
 *
 * Charts always use the sans stack, never the display serif.
 */

const FONT_SANS =
  "'Inter Variable', ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif";

/** Merge that keeps nested layout sections (xaxis, polar, legend…) intact. */
function deepMerge(base, extra) {
  if (!extra) return base;
  const out = { ...base };
  for (const [k, v] of Object.entries(extra)) {
    out[k] =
      v && typeof v === 'object' && !Array.isArray(v) && base[k] && typeof base[k] === 'object'
        ? deepMerge(base[k], v)
        : v;
  }
  return out;
}

/**
 * Base layout for a mode. Grid and axes are recessive; the marks carry the
 * chart.
 *
 * @param {'light'|'dark'} mode
 * @param {object} overrides  merged deeply over the base
 */
export function buildLayout(mode = 'light', overrides) {
  const c = CHROME[mode];

  const axis = {
    color: c.muted,
    gridcolor: c.grid,
    linecolor: c.axis,
    zerolinecolor: c.axis,
    tickfont: { family: FONT_SANS, size: 11, color: c.muted },
    titlefont: { family: FONT_SANS, size: 11, color: c.secondary },
    automargin: true,
  };

  return deepMerge(
    {
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
      font: { family: FONT_SANS, size: 12, color: c.secondary },
      margin: { l: 48, r: 16, t: 12, b: 40 },
      hoverlabel: {
        bgcolor: c.surface,
        bordercolor: c.axis,
        font: { family: FONT_SANS, size: 12, color: c.ink },
        align: 'left',
      },
      legend: {
        font: { family: FONT_SANS, size: 11, color: c.secondary },
        bgcolor: 'transparent',
        orientation: 'h',
        yanchor: 'bottom',
        y: 1.02,
        x: 0,
      },
      xaxis: { ...axis },
      yaxis: { ...axis },
      colorway: undefined, // series colours are assigned explicitly, never auto
      dragmode: 'pan',
      transition: { duration: 0 },
    },
    overrides,
  );
}

/** Polar (radar) layout — same chrome, different container. */
export function buildPolarLayout(mode = 'light', overrides) {
  const c = CHROME[mode];
  return buildLayout(
    mode,
    deepMerge(
      {
        margin: { l: 60, r: 60, t: 30, b: 30 },
        polar: {
          bgcolor: 'transparent',
          radialaxis: {
            gridcolor: c.grid,
            linecolor: c.axis,
            tickfont: { family: FONT_SANS, size: 10, color: c.muted },
            angle: 90,
          },
          angularaxis: {
            gridcolor: c.grid,
            linecolor: c.axis,
            tickfont: { family: FONT_SANS, size: 10, color: c.secondary },
          },
        },
      },
      overrides,
    ),
  );
}

/**
 * Shared config. The mode bar is off everywhere except the map, where pan and
 * zoom are the point.
 */
export function buildConfig({ interactive = false, filename = 'grafico' } = {}) {
  return {
    displayModeBar: interactive,
    displaylogo: false,
    responsive: true,
    scrollZoom: interactive,
    modeBarButtonsToRemove: ['select2d', 'lasso2d', 'autoScale2d', 'toggleSpikelines'],
    toImageButtonOptions: { format: 'png', filename, scale: 2 },
    locale: 'it',
  };
}

/**
 * A 2px surface-coloured ring so overlapping marks stay separable, and the
 * matching gap between adjacent fills.
 */
export function markRing(mode = 'light', width = 1.5) {
  return { color: CHROME[mode].surface, width };
}
