/**
 * Chart colour. Raw hex per mode, because Plotly cannot read CSS variables.
 *
 * Everything here was checked with the dataviz validator against this app's
 * own surfaces — not eyeballed. Re-run before changing any value:
 *
 *   node scripts/validate_palette.js "<hex,…>" --mode light --surface "#FDFCFA"
 *   node scripts/validate_palette.js "<hex,…>" --mode dark  --surface "#16181C"
 *   …plus --pairs all for scatter / bubble / small-multiple forms.
 *
 * Results on these surfaces:
 *   light, adjacent : worst CVD ΔE 9.1 · normal-vision 19.6 · PASS
 *   dark,  adjacent : worst CVD ΔE 8.4 · normal-vision 19.3 · PASS, all ≥3:1
 *   light, all-pairs, first 3 slots : CVD 9.2 · normal 24.0 · PASS
 *   dark,  all-pairs, first 3 slots : CVD 9.4 · normal 20.9 · PASS
 *
 * What this replaces: four overlapping arrays (CLUSTER_COLORS, TOPIC_COLORS,
 * DEFAULT_COLORS and the wordcloud's own list). CLUSTER_COLORS failed outright
 * — #84cc16 vs #fb923c measured ΔE 0.8 under deuteranopia, i.e. identical —
 * and was indexed `cluster % 10` across 14 clusters, so clusters 10–13 reused
 * the colours of 0–3.
 */

/** Fixed hue order. Assign in sequence; never cycle, never reorder. */
const SERIES = {
  light: ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#4a3aa7', '#e34948'],
  dark: ['#3987e5', '#d95926', '#199e70', '#c98500', '#d55181', '#008300', '#9085e9', '#e66767'],
};

/**
 * Hard series caps.
 *
 * ADJACENT — bar, line, stacked: only neighbouring marks touch, so 8 slots
 *   clear the gates.
 * ALL_PAIRS — scatter, bubble, small multiples: any two marks can sit side by
 *   side, which is a strictly harder test. Only the first 3 slots pass it. This
 *   is why the semantic map uses focus+context (dim everything, light up the
 *   selection) rather than colouring 14 topics at once.
 *
 * Past the cap the answer is folding to "Altri" or faceting — never an
 * additional generated hue.
 */
export const SERIES_CAP = { adjacent: 8, allPairs: 3 };

/** Ordered series colours for the given mode, capped by chart form. */
export function seriesColors(mode = 'light', form = 'adjacent') {
  return SERIES[mode].slice(0, SERIES_CAP[form] ?? SERIES_CAP.adjacent);
}

/** Colour for slot `i`. Throws past the cap rather than silently wrapping. */
export function seriesColor(i, mode = 'light', form = 'adjacent') {
  const cap = SERIES_CAP[form] ?? SERIES_CAP.adjacent;
  if (i >= cap) {
    throw new Error(
      `Series slot ${i} exceeds the ${form} cap of ${cap}. Fold the remainder into "Altri" or facet — do not cycle the palette.`,
    );
  }
  return SERIES[mode][i];
}

/** Neutral used for the folded "Altri" bucket and for context marks. */
export const OTHER_COLOR = { light: '#8a8d93', dark: '#85888e' };

/** Chart chrome, mirroring the CSS tokens in styles/theme.css. */
export const CHROME = {
  light: {
    surface: '#fdfcfa',
    plane: '#f7f5f2',
    ink: '#16181c',
    secondary: '#55585e',
    muted: '#8a8d93',
    grid: '#e4e0d9',
    axis: '#cfcabf',
    accent: '#1f3a5f',
  },
  dark: {
    surface: '#16181c',
    plane: '#0f1113',
    ink: '#f2f0ec',
    secondary: '#b8bac0',
    muted: '#85888e',
    grid: '#292c31',
    axis: '#3a3e45',
    accent: '#7fa3c9',
  },
};

/** Status scale — reserved meaning, never reused as "series 4". */
export const STATUS = {
  good: '#0ca30c',
  warning: '#fab219',
  serious: '#ec835a',
  critical: '#d03b3b',
};

/**
 * Sequential ramp for magnitude (affinity matrix, density). One hue,
 * light -> dark. In dark mode the anchor flips so "near zero" recedes toward
 * the surface rather than glowing.
 */
const BLUE_RAMP = [
  '#cde2fb', '#b7d3f6', '#9ec5f4', '#86b6ef', '#6da7ec',
  '#5598e7', '#3987e5', '#2a78d6', '#256abf', '#1c5cab',
  '#184f95', '#104281', '#0d366b',
];

/** Plotly colorscale for a 0..1 magnitude. */
export function sequentialScale(mode = 'light') {
  const stops = mode === 'dark' ? [...BLUE_RAMP].reverse() : BLUE_RAMP;
  const anchor = mode === 'dark' ? CHROME.dark.surface : CHROME.light.surface;
  const ramp = mode === 'dark' ? stops.slice(3) : stops;
  return [
    [0, anchor],
    ...ramp.map((hex, i) => [(i + 1) / ramp.length, hex]),
  ];
}

/**
 * Diverging scale for polarity (sentiment). Blue <-> red with a NEUTRAL GRAY
 * midpoint, equal arms.
 *
 * The old sentiment heatmap used red -> #242930 -> green, which was wrong
 * twice: red/green is the single worst pair for colour-vision deficiency, and
 * the midpoint must read as "nothing" rather than as a dark surface colour.
 */
export function divergingScale(mode = 'light') {
  const mid = mode === 'dark' ? '#383835' : '#f0efec';
  return [
    [0.0, '#104281'],
    [0.15, '#256abf'],
    [0.3, '#5598e7'],
    [0.42, '#9ec5f4'],
    [0.5, mid],
    [0.58, '#f0a3a3'],
    [0.7, '#e66767'],
    [0.85, '#d03b3b'],
    [1.0, '#8f2020'],
  ];
}

/**
 * Assign colours to N named series, folding everything past the cap into a
 * single "Altri" entry. The one supported way to exceed the cap.
 *
 * @returns {Array<{key,label,color,folded}>}
 */
export function assignSeries(items, mode = 'light', form = 'adjacent') {
  const cap = SERIES_CAP[form] ?? SERIES_CAP.adjacent;
  const colors = SERIES[mode];

  if (items.length <= cap) {
    return items.map((it, i) => ({ ...it, color: colors[i], folded: false }));
  }

  const kept = items.slice(0, cap - 1).map((it, i) => ({ ...it, color: colors[i], folded: false }));
  const rest = items.slice(cap - 1);
  return [
    ...kept,
    {
      key: '__other__',
      label: 'Altri',
      color: OTHER_COLOR[mode],
      folded: true,
      members: rest,
    },
  ];
}
