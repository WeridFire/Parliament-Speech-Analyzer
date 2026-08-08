/**
 * Metric vocabulary: classification labels and scale declarations.
 *
 * Two problems this file exists to solve:
 *
 * 1. The backend emits classification strings in a MIX of Italian and English
 *    — `vocabulary.classification` is 'ricco' but `consistency.classification`
 *    is 'very_consistent', and `faction_label` is 'maverick'. The old
 *    SpeakerProfileCard keyed its label map on English only, so Italian values
 *    like 'ricco' fell through and leaked raw into the UI. One map covers both
 *    vocabularies.
 *
 * 2. Scales are inconsistent. `rebel_pct` and `generalism.score` are already
 *    0–100; `cohesion_score`, `similarity` and `overlap_score` are 0–1. The old
 *    RelationsTab rendered `width: ${cohesion_score}%` on a 0–1 value, so every
 *    cohesion bar was ~0.3% wide and labelled "0%". SCALES declares which is
 *    which so no component has to guess.
 */

/** tone drives the status colour: 'good' | 'warning' | 'critical' | 'neutral' */
const CLASSIFICATIONS = {
  // identity / generalism
  generalista: { label: 'Generalista', tone: 'neutral' },
  bilanciato: { label: 'Bilanciato', tone: 'neutral' },
  specialista: { label: 'Specialista', tone: 'neutral' },

  // relations / cohesion
  compatto: { label: 'Compatto', tone: 'good' },
  moderato: { label: 'Moderato', tone: 'warning' },
  frammentato: { label: 'Frammentato', tone: 'critical' },

  // relations / thematic overlap  (field is `type`, not `classification`)
  bipartisan: { label: 'Bipartisan', tone: 'good' },
  'left-dominated': { label: 'Prevalenza sinistra', tone: 'neutral' },
  'right-dominated': { label: 'Prevalenza destra', tone: 'neutral' },
  mixed: { label: 'Misto', tone: 'neutral' },

  // readability (Gulpease)
  facile: { label: 'Facile', tone: 'good' },
  medio: { label: 'Medio', tone: 'warning' },
  difficile: { label: 'Difficile', tone: 'critical' },

  // polarization
  bassa: { label: 'Bassa', tone: 'good' },
  media: { label: 'Media', tone: 'warning' },
  alta: { label: 'Alta', tone: 'critical' },

  // vocabulary richness
  ricco: { label: 'Ricco', tone: 'good' },
  ripetitivo: { label: 'Ripetitivo', tone: 'critical' },

  // consistency  (backend emits English here)
  very_consistent: { label: 'Molto coerente', tone: 'good' },
  consistent: { label: 'Coerente', tone: 'good' },
  variable: { label: 'Variabile', tone: 'warning' },
  inconsistent: { label: 'Incoerente', tone: 'critical' },

  // factions  (English)
  mainstream: { label: 'Allineato', tone: 'neutral' },
  bridge: { label: 'Ponte', tone: 'neutral' },
  maverick: { label: 'Battitore libero', tone: 'warning' },

  // sentiment
  positivo: { label: 'Positivo', tone: 'good' },
  neutro: { label: 'Neutro', tone: 'neutral' },
  negativo: { label: 'Negativo', tone: 'critical' },

  // temporal orientation
  futuro: { label: 'Orientato al futuro', tone: 'neutral' },
  passato: { label: 'Orientato al passato', tone: 'neutral' },

  // rhetoric style  (mixed vocabularies)
  populist: { label: 'Populista', tone: 'neutral' },
  anti_establishment: { label: 'Anti-establishment', tone: 'neutral' },
  emotional: { label: 'Emotivo', tone: 'neutral' },
  institutional: { label: 'Istituzionale', tone: 'neutral' },
  neutrale: { label: 'Neutrale', tone: 'neutral' },
};

/**
 * Human label + tone for any backend classification string.
 * Unknown values are title-cased rather than dropped, so a new backend
 * category shows up readable instead of blank.
 */
export function classify(value) {
  if (!value) return { label: '—', tone: 'neutral' };
  const hit = CLASSIFICATIONS[value];
  if (hit) return hit;
  const label = String(value).replace(/_/g, ' ');
  return { label: label[0].toUpperCase() + label.slice(1), tone: 'neutral' };
}

/**
 * Scale declarations. `unit` means 0–1, `pct` means already 0–100.
 * Anything rendered as a bar or a percentage must consult this.
 */
export const SCALES = {
  divergence_pct: 'pct',
  generalism_score: 'pct',
  consistency_score: 'pct',
  regularity_score: 'pct',
  activity_ratio: 'pct',
  burst_score: 'pct',
  // Lexicon metrics emit {raw, pct, n}: `pct` is a percentile, `raw` has its
  // own unit and no ceiling, so only `pct` belongs on a 0-100 scale.
  polarization_pct: 'pct',
  readability_score: 'pct',
  overlap_score: 'pct',

  cohesion_score: 'unit',
  similarity: 'unit',
  affinity: 'unit',
  fingerprint: 'unit',
  type_token_ratio: 'unit',
  hapax_ratio: 'unit',
  conformity: 'unit',
};

/** Normalise any declared metric to 0–100 for bars and percentage labels. */
export function toPercent(value, metric) {
  if (typeof value !== 'number' || !Number.isFinite(value)) return null;
  return SCALES[metric] === 'unit' ? value * 100 : value;
}

/** Clamp a bar width to a sane range so tiny values stay visible. */
export function barWidth(percent) {
  if (typeof percent !== 'number' || !Number.isFinite(percent)) return 0;
  return Math.max(0, Math.min(100, percent));
}

/**
 * The four rankings the backend actually emits under `speaker.rankings`.
 * The old SpeakerStatsTab configured a dozen categories, most of which did not
 * exist in the data, while omitting `most_active`, which does.
 * Verified against backend/analyzers/speaker/*.
 */
export const SPEAKER_RANKINGS = [
  {
    id: 'most_verbose',
    label: 'Più prolissi',
    hint: 'Media di parole per intervento',
    unit: 'parole',
    digits: 0,
  },
  {
    id: 'most_active',
    label: 'Più attivi',
    hint: 'Media di interventi al mese',
    unit: 'interventi/mese',
    digits: 1,
  },
  {
    id: 'most_consistent',
    label: 'Più coerenti',
    hint: 'Stabilità tematica nel tempo',
    unit: '%',
    digits: 0,
  },
  {
    id: 'richest_vocabulary',
    label: 'Vocabolario più ricco',
    hint: 'Rapporto tipo/token',
    unit: '',
    digits: 2,
  },
];
