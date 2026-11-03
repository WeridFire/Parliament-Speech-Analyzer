import { Info } from 'lucide-react';
import { monthLabel } from '../lib/format';

/**
 * Says so when a panel shows the whole-corpus figure instead of the selected
 * period's: some measures need more speeches than a single month has, and
 * silently showing the global number under a month heading would misreport it.
 */
export function ScopeNote({ fromGlobal, period }) {
  if (!fromGlobal || !period?.year) return null;

  const when = period.month ? monthLabel(`${period.year}-${period.month}`) : `il ${period.year}`;

  return (
    <p className="flex items-start gap-2 rounded-sm bg-sunken px-3 py-2 text-label text-secondary">
      <Info size={13} className="mt-px shrink-0 text-muted" aria-hidden="true" />
      <span>
        Per {when} non ci sono abbastanza interventi per questa misura: il dato mostrato è quello
        dell&apos;intero periodo disponibile.
      </span>
    </p>
  );
}
