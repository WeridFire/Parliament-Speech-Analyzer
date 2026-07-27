/**
 * Display formatting. All UI copy is Italian, so every formatter is pinned to
 * it-IT (thousands separator ".", decimal comma) rather than the browser locale.
 */

const LOCALE = 'it-IT';

const integerFmt = new Intl.NumberFormat(LOCALE, { maximumFractionDigits: 0 });
const decimalFmt = new Intl.NumberFormat(LOCALE, {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});
const decimal2Fmt = new Intl.NumberFormat(LOCALE, {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

/** 10736 -> "10.736" */
export const int = (v) => (isNum(v) ? integerFmt.format(v) : '—');

/** 46.87 -> "46,9" */
export const dec = (v) => (isNum(v) ? decimalFmt.format(v) : '—');

/** 0.2889 -> "0,29" */
export const dec2 = (v) => (isNum(v) ? decimal2Fmt.format(v) : '—');

/**
 * Percentages. The backend is inconsistent about scale — `rebel_pct` and
 * `generalism.score` are already 0–100, while `cohesion_score` and
 * `similarity` are 0–1. Callers state which they have; nothing is guessed.
 */
export const pct = (v, { fromUnit = false, digits = 0 } = {}) => {
  if (!isNum(v)) return '—';
  const n = fromUnit ? v * 100 : v;
  return `${new Intl.NumberFormat(LOCALE, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(n)}%`;
};

/** Signed score for sentiment: -0.214 -> "−0,21" (true minus sign). */
export const signed = (v, digits = 2) => {
  if (!isNum(v)) return '—';
  const s = new Intl.NumberFormat(LOCALE, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
    signDisplay: 'always',
  }).format(v);
  return s.replace('-', '−');
};

const MONTHS = [
  'gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno',
  'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre',
];

/** "2026-02" -> "febbraio 2026" */
export const monthLabel = (key) => {
  if (!key) return '';
  const [y, m] = String(key).split('-');
  const name = MONTHS[Number(m) - 1];
  return name ? `${name} ${y}` : key;
};

/** "02" -> "Febbraio" */
export const monthName = (mm) => {
  const name = MONTHS[Number(mm) - 1];
  return name ? name[0].toUpperCase() + name.slice(1) : String(mm ?? '');
};

/** "2024-12-02" -> "2 dicembre 2024". Tolerates DD/MM/YYYY. */
export const dateLabel = (raw) => {
  const p = parseDate(raw);
  if (!p) return raw ?? '';
  return `${p.day} ${MONTHS[p.month - 1]} ${p.year}`;
};

/**
 * Parse the two date shapes present in the data into {year, month, day}.
 * Shared by the period filter so date handling exists in exactly one place —
 * it was previously inlined twice inside StateContext.
 */
export function parseDate(raw) {
  if (!raw || typeof raw !== 'string') return null;

  if (raw.includes('-')) {
    const parts = raw.split('-');
    if (parts[0]?.length === 4) {
      return { year: +parts[0], month: +parts[1], day: +parts[2] || 1 };
    }
    return { year: +parts[2], month: +parts[1], day: +parts[0] || 1 };
  }

  if (raw.includes('/')) {
    const parts = raw.split('/');
    return { year: +parts[2], month: +parts[1], day: +parts[0] || 1 };
  }

  return null;
}

/** Truncate on a word boundary, with a real ellipsis. */
export const truncate = (text, max = 320) => {
  if (!text || text.length <= max) return text ?? '';
  const cut = text.slice(0, max);
  const lastSpace = cut.lastIndexOf(' ');
  return `${cut.slice(0, lastSpace > max * 0.6 ? lastSpace : max).trimEnd()}…`;
};

function isNum(v) {
  return typeof v === 'number' && Number.isFinite(v);
}
