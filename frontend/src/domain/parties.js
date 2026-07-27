/**
 * The canonical party registry.
 *
 * Replaces three parallel maps (PARTY_COLORS, PARTY_ABBREVIATIONS,
 * PARTY_CONFIG) that each repeated every party 2–3 times — once for the
 * Camera's long-form name, once for the Senato's short code, once for a
 * "legacy normalized" form — and drifted apart. One record per party now, with
 * every alias listed in one place.
 *
 * On the `dot` colors: these are identity dots rendered *beside a text label*
 * (chips, list rows, tooltips), where the label carries the identity and the
 * dot only aids recognition. They are deliberately NOT chart series colors.
 * The real party brand hues fail colour-vision separation badly — measured,
 * Lega #43a047 vs PD #e53935 collapse to ΔE 2.9 under deuteranopia and AVS vs
 * Lega sit at ΔE 9.0 even with normal vision. Chart series come from
 * viz/palette.js instead; see the series caps documented there.
 */

/** Plotly marker symbols — secondary encoding so party is never colour-alone. */
const SHAPES = {
  fdi: 'diamond',
  m5s: 'star',
  fi: 'square',
  lega: 'triangle-up',
  pd: 'circle',
  avs: 'pentagon',
  azione: 'hexagon2',
  iv: 'cross',
  nm: 'bowtie',
  misto: 'hexagon',
  minling: 'triangle-down',
  piu_europa: 'diamond-wide',
  aut: 'star-diamond',
  governo: 'diamond-tall',
  presidenza: 'star-square',
  unknown: 'circle-open',
};

/**
 * coalition follows backend/config/party_normalization.py
 * (RIGHT_PARTIES / LEFT_PARTIES / CENTER_PARTIES, with Governo classified
 * as right per CLASSIFY_GOVERNO_AS_RIGHT = True).
 */
const REGISTRY = [
  {
    id: 'fdi',
    name: "Fratelli d'Italia",
    short: 'FdI',
    coalition: 'right',
    dot: { light: '#1b4f9c', dark: '#5b8fd6' },
    shape: SHAPES.fdi,
    aliases: ["FRATELLI D'ITALIA", "Fratelli d'Italia", 'FdI'],
  },
  {
    id: 'm5s',
    name: 'MoVimento 5 Stelle',
    short: 'M5S',
    coalition: 'left',
    dot: { light: '#a88400', dark: '#f2ce3c' },
    shape: SHAPES.m5s,
    aliases: ['MOVIMENTO 5 STELLE', 'MoVimento 5 Stelle', 'Movimento 5 Stelle', 'M5S'],
  },
  {
    id: 'fi',
    name: 'Forza Italia',
    short: 'FI',
    coalition: 'right',
    dot: { light: '#2e86d9', dark: '#6fb3ed' },
    shape: SHAPES.fi,
    aliases: [
      'FORZA ITALIA - BERLUSCONI PRESIDENTE - PPE',
      'Forza Italia',
      'FI-BP-PPE',
      'FI',
    ],
  },
  {
    id: 'lega',
    name: 'Lega',
    short: 'Lega',
    coalition: 'right',
    dot: { light: '#2e7d32', dark: '#6bb56f' },
    shape: SHAPES.lega,
    aliases: ['LEGA - SALVINI PREMIER', 'Lega - Salvini Premier', 'LEGA', 'Lega', "LSP-PSd'Az"],
  },
  {
    id: 'pd',
    name: 'Partito Democratico',
    short: 'PD',
    coalition: 'left',
    dot: { light: '#c62828', dark: '#e8706e' },
    shape: SHAPES.pd,
    aliases: [
      'PARTITO DEMOCRATICO - ITALIA DEMOCRATICA E PROGRESSISTA',
      'Partito Democratico - Italia Democratica e Progressista',
      'Partito Democratico',
      'PD-IDP',
      'PD',
    ],
  },
  {
    id: 'avs',
    name: 'Alleanza Verdi e Sinistra',
    short: 'AVS',
    coalition: 'left',
    dot: { light: '#557b2f', dark: '#9ccc65' },
    shape: SHAPES.avs,
    aliases: ['ALLEANZA VERDI E SINISTRA', 'Alleanza Verdi e Sinistra', 'AVS'],
  },
  {
    id: 'azione',
    name: 'Azione — Renew Europe',
    short: 'Az-RE',
    coalition: 'center',
    dot: { light: '#7b1fa2', dark: '#ba7bd4' },
    shape: SHAPES.azione,
    aliases: [
      'AZIONE-POPOLARI EUROPEISTI RIFORMATORI-RENEW EUROPE',
      'Azione-Popolari Europeisti Riformatori-Renew Europe',
      'Azione-IV-RE',
      'AZ-PER-RE',
      'Azione-RE',
      'Azione',
    ],
  },
  {
    id: 'iv',
    name: 'Italia Viva',
    short: 'IV',
    coalition: 'center',
    dot: { light: '#d84315', dark: '#ff8a65' },
    shape: SHAPES.iv,
    aliases: ['ITALIA VIVA', 'Italia Viva', 'IV-C-RE', 'IV'],
  },
  {
    id: 'nm',
    name: 'Noi Moderati',
    short: 'NM',
    coalition: 'right',
    dot: { light: '#00695f', dark: '#4dd0c1' },
    shape: SHAPES.nm,
    aliases: [
      "NOI MODERATI(NOI CON L'ITALIA, CORAGGIO ITALIA, UDC, ITALIA AL CENTRO)-MAIE-CENTRO POPOLARE",
      "NOI MODERATI (NOI CON L'ITALIA, CORAGGIO ITALIA, UDC E ITALIA AL CENTRO)-MAIE-CENTRO POPOLARE",
      "Cd'I-NM(UDC-CI-NcI-IaC)-MAIE",
      'NM(N-C-U-I',
      'Noi Moderati',
      'NM',
    ],
  },
  {
    id: 'minling',
    name: 'Misto — Minoranze Linguistiche',
    short: 'MinL',
    coalition: 'center',
    dot: { light: '#5c6b73', dark: '#94a7b0' },
    shape: SHAPES.minling,
    aliases: ['MISTO-MINORANZE LINGUISTICHE', 'Misto-Minoranze Linguistiche'],
  },
  {
    id: 'piu_europa',
    name: 'Misto — +Europa',
    short: '+Eu',
    coalition: 'left', // backend party_normalization.py lists +Europa under LEFT_PARTIES
    dot: { light: '#ad1457', dark: '#f06292' },
    shape: SHAPES.piu_europa,
    aliases: ['MISTO-+Europa', 'Misto-+Europa', '+Europa'],
  },
  {
    id: 'aut',
    name: 'Per le Autonomie (SVP-PATT, Cb)',
    short: 'Aut',
    // Autonomist crossbench: the backend classifies it as neither left, right
    // nor center, so it is not forced into one here either.
    coalition: 'none',
    dot: { light: '#00796b', dark: '#4db6ac' },
    shape: SHAPES.aut,
    aliases: ['Aut (SVP-PATT, Cb)', 'AUT (SVP-PATT, CB)', 'Aut', 'SVP-PATT'],
  },
  {
    id: 'misto',
    name: 'Gruppo Misto',
    short: 'Misto',
    coalition: 'center',
    dot: { light: '#6e7278', dark: '#9aa0a6' },
    shape: SHAPES.misto,
    aliases: ['MISTO', 'Misto'],
  },
  {
    id: 'governo',
    name: 'Governo',
    short: 'Gov',
    coalition: 'right',
    dot: { light: '#455a64', dark: '#90a4ae' },
    shape: SHAPES.governo,
    aliases: ['GOVERNO', 'Governo'],
  },
  {
    id: 'presidenza',
    name: 'Presidenza',
    short: 'Pres',
    coalition: 'none',
    dot: { light: '#6d4c41', dark: '#bcaaa4' },
    shape: SHAPES.presidenza,
    aliases: ['PRESIDENZA', 'Presidenza'],
  },
];

const UNKNOWN = {
  id: 'unknown',
  name: 'Gruppo non identificato',
  short: '—',
  coalition: 'none',
  dot: { light: '#8a8d93', dark: '#85888e' },
  shape: SHAPES.unknown,
  aliases: ['Unknown Group', 'UNKNOWN GROUP'],
};

export const PARTIES = REGISTRY;

const BY_ID = new Map(REGISTRY.map((p) => [p.id, p]));

/** Squash case, accents and punctuation so alias lookup survives formatting drift. */
const key = (s) =>
  String(s)
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, '');

const BY_ALIAS = new Map();
for (const party of [...REGISTRY, UNKNOWN]) {
  for (const alias of party.aliases) BY_ALIAS.set(key(alias), party);
  BY_ALIAS.set(key(party.name), party);
  BY_ALIAS.set(key(party.short), party);
}

/**
 * Distinctive leading tokens, checked only after exact lookup fails. Ordered
 * most-specific first. This replaces the old getPartyColor() substring scan,
 * which compared every key against every name in both directions and so
 * mis-matched short names against unrelated long ones.
 */
const PREFIX_RULES = [
  [/^FRATELLIDITALIA/, 'fdi'],
  [/^MOVIMENTO5STELLE/, 'm5s'],
  [/^FORZAITALIA/, 'fi'],
  [/^LEGA/, 'lega'],
  [/^PARTITODEMOCRATICO/, 'pd'],
  [/^ALLEANZAVERDI/, 'avs'],
  [/^AZIONE/, 'azione'],
  [/^ITALIAVIVA/, 'iv'],
  [/^NOIMODERATI/, 'nm'],
  // The two named Misto sub-groups must be tested before bare ^MISTO, or they
  // would silently collapse into the generic Gruppo Misto bucket.
  [/^MISTOMINORANZE/, 'minling'],
  [/^MISTOEUROPA/, 'piu_europa'],
  [/^MISTO/, 'misto'],
  [/^AUTSVPPATT/, 'aut'],
];

const cache = new Map();

/**
 * Resolve any raw party string from either chamber to a registry record.
 * Unrecognised groups get a synthetic record that preserves the original text
 * rather than guessing — so new groups degrade to "shown but uncoloured"
 * instead of silently borrowing another party's identity.
 */
export function resolveParty(raw) {
  if (!raw) return UNKNOWN;
  if (cache.has(raw)) return cache.get(raw);

  const k = key(raw);
  let found = BY_ALIAS.get(k);

  if (!found) {
    for (const [re, id] of PREFIX_RULES) {
      if (re.test(k)) {
        found = BY_ID.get(id);
        break;
      }
    }
  }

  if (!found) {
    const trimmed = String(raw).trim();
    found = {
      ...UNKNOWN,
      name: trimmed,
      short: trimmed.length <= 6 ? trimmed : `${trimmed.slice(0, 5)}…`,
    };
  }

  cache.set(raw, found);
  return found;
}

export const partyName = (raw) => resolveParty(raw).name;
export const partyShort = (raw) => resolveParty(raw).short;
export const partyShape = (raw) => resolveParty(raw).shape;
export const partyCoalition = (raw) => resolveParty(raw).coalition;

/** Identity dot colour for the given mode. Never use this for a chart series. */
export const partyDot = (raw, mode = 'light') => resolveParty(raw).dot[mode];

/** Stable display order: coalition, then registry order. */
const COALITION_ORDER = { right: 0, center: 1, left: 2, none: 3 };
export function sortParties(rawNames) {
  return [...rawNames].sort((a, b) => {
    const pa = resolveParty(a);
    const pb = resolveParty(b);
    const ca = COALITION_ORDER[pa.coalition] ?? 3;
    const cb = COALITION_ORDER[pb.coalition] ?? 3;
    if (ca !== cb) return ca - cb;
    return pa.name.localeCompare(pb.name, 'it');
  });
}
