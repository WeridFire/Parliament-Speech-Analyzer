import { cn } from '../lib/cn';
import { Meter, Rank } from './Meter';
import { EmptyState } from './EmptyState';

/**
 * The ranked-list primitive.
 *
 * This markup was previously re-inlined in all five analytics tabs, each with
 * its own gold/silver/bronze badge styling, its own score-bar gradient and its
 * own value formatting. One component now.
 *
 * @param {Array} items  [{ key, name, meta, value, percent, tone, color, dot }]
 *                       `percent` is 0–100 and drives the bar; `value` is the
 *                       already-formatted display string. Callers normalise via
 *                       metrics.toPercent() so scale handling stays in one place.
 */
export function RankingList({ items, emptyMessage = 'Nessun dato disponibile.', className }) {
  if (!items?.length) return <EmptyState message={emptyMessage} />;

  return (
    <ol className={cn('flex flex-col', className)}>
      {items.map((item, i) => (
        <li
          key={item.key ?? item.name}
          className="flex items-center gap-3 border-b border-rule py-2 last:border-b-0"
        >
          <Rank position={i + 1} />

          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-1.5">
              {item.dot ? (
                <span
                  className="h-2 w-2 shrink-0 rounded-full"
                  style={{ backgroundColor: item.dot }}
                  aria-hidden="true"
                />
              ) : null}
              <span className="truncate text-body font-medium text-ink" title={item.name}>
                {item.name}
              </span>
            </div>
            {item.meta ? (
              <span className="mt-0.5 block truncate text-label text-muted" title={item.meta}>
                {item.meta}
              </span>
            ) : null}
          </div>

          <div className="flex w-32 shrink-0 items-center gap-2 sm:w-40">
            {typeof item.percent === 'number' ? (
              <Meter
                value={item.percent}
                tone={item.tone}
                color={item.color}
                className="flex-1"
                label={`${item.name}: ${item.value}`}
              />
            ) : (
              <span className="flex-1" />
            )}
            {/* Values are always visible text, never colour-only — this is also
                the relief channel for series colours below 3:1 on light. */}
            <span className="tabular w-14 shrink-0 text-right text-num text-secondary">
              {item.value}
            </span>
          </div>
        </li>
      ))}
    </ol>
  );
}
