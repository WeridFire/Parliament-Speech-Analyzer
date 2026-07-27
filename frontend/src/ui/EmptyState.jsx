import { Inbox } from 'lucide-react';
import { cn } from '../lib/cn';
import { monthLabel } from '../lib/format';

/**
 * Shown when a panel has nothing to render. Because the backend applies
 * per-metric minimum-speech thresholds (≥2, ≥3 or ≥5 depending on the
 * analyzer), an empty panel is often legitimate rather than an error — the
 * copy says so instead of looking broken.
 */
export function EmptyState({ message = 'Nessun dato disponibile.', hint, icon: Icon = Inbox, className }) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-2 px-4 py-10 text-center',
        className,
      )}
    >
      <Icon size={22} className="text-muted opacity-60" aria-hidden="true" />
      <p className="text-body text-secondary">{message}</p>
      {hint ? <p className="max-w-sm text-label text-muted">{hint}</p> : null}
    </div>
  );
}

/** Empty state for a period filter that selected a window with no coverage. */
export function NoDataForPeriod({ feature = 'questa analisi', period }) {
  const when = period?.month
    ? monthLabel(`${period.year}-${period.month}`)
    : period?.year
      ? `il ${period.year}`
      : 'il periodo selezionato';

  return (
    <EmptyState
      message={`Nessun dato per ${feature} in ${when}.`}
      hint="Il periodo potrebbe non raggiungere la soglia minima di interventi richiesta da questa metrica. Prova un intervallo più ampio."
    />
  );
}
