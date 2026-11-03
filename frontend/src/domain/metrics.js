/**
 * Metric vocabulary: classification labels and ranking declarations.
 *
 * The backend emits classification strings (Italian, plus a few technical
 * values such as the bloc names); one map turns all of them into display labels
 * and a status tone, so no component has to know the raw vocabulary.
 */

/** tone drives the status colour: 'good' | 'warning' | 'critical' | 'neutral' */
const CLASSIFICATIONS = {
  // identity / generalism
  generalista: { label: 'Generalista', tone: 'neutral' },
  bilanciato: { label: 'Bilanciato', tone: 'neutral' },
  specialista: { label: 'Specialista', tone: 'neutral' },

  // blocs / issue ownership
  maggioranza: { label: 'Maggioranza', tone: 'neutral' },
  opposizione: { label: 'Opposizione', tone: 'neutral' },
  condiviso: { label: 'Condiviso', tone: 'neutral' },
  altro: { label: 'Altro', tone: 'neutral' },

  // readability (Gulpease)
  facile: { label: 'Facile', tone: 'good' },
  medio: { label: 'Medio', tone: 'warning' },
  difficile: { label: 'Difficile', tone: 'critical' },

  // polarization (percentile bands)
  bassa: { label: 'Bassa', tone: 'good' },
  media: { label: 'Media', tone: 'warning' },
  alta: { label: 'Alta', tone: 'critical' },
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

/** Clamp a bar width to a sane range so tiny values stay visible. */
export function barWidth(percent) {
  if (typeof percent !== 'number' || !Number.isFinite(percent)) return 0;
  return Math.max(0, Math.min(100, percent));
}

/** Display names for the two blocs. */
export const BLOC_LABELS = {
  maggioranza: 'Maggioranza e Governo',
  opposizione: 'Opposizione',
  altro: 'Misto e altri',
};

/**
 * The rankings the backend emits under `speaker.rankings`, verified against
 * backend/analyzers/speaker/analyzer.py. Only those present in the payload are
 * offered.
 */
export const SPEAKER_RANKINGS = [
  {
    id: 'most_active',
    label: 'Più attivi',
    hint: 'Numero di interventi nel periodo',
    unit: '',
    digits: 0,
  },
  {
    id: 'most_verbose',
    label: 'Interventi più lunghi',
    hint: 'Media di parole per intervento (almeno 10 interventi)',
    unit: 'parole',
    digits: 0,
  },
  {
    id: 'richest_vocabulary',
    label: 'Lessico più vario',
    hint: 'MATTR: varietà lessicale su finestre di 500 parole, indipendente dalla quantità',
    unit: '',
    digits: 2,
  },
  {
    id: 'most_data',
    label: 'Più dati citati',
    hint: 'Percentuali, cifre e importi ogni mille parole (almeno 10 interventi)',
    unit: '‰',
    digits: 1,
  },
  {
    id: 'most_questions',
    label: 'Più domande',
    hint: 'Domande ogni mille parole (almeno 10 interventi)',
    unit: '‰',
    digits: 1,
  },
  {
    id: 'most_cross_applauded',
    label: 'Applauditi da altri gruppi',
    hint: 'Interventi applauditi da almeno un gruppo diverso dal proprio',
    unit: '',
    digits: 0,
  },
];
