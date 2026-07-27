import { cn } from '../lib/cn';

/**
 * A single headline number. Per the viz guidance, a lone magnitude is a stat
 * tile, not a chart — these replace several one-value "charts" in the old
 * dashboard.
 */
export function StatTile({ label, value, unit, meta, className }) {
  return (
    <div className={cn('min-w-0', className)}>
      <div className="text-label text-muted">{label.toUpperCase()}</div>
      <div className="mt-1 flex items-baseline gap-1">
        <span className="font-serif text-h2 leading-none font-semibold text-ink">{value}</span>
        {unit ? <span className="text-body text-muted">{unit}</span> : null}
      </div>
      {meta ? <div className="mt-1 truncate text-label text-muted">{meta}</div> : null}
    </div>
  );
}

/** Evenly divided row of stat tiles, separated by hairlines. */
export function StatRow({ children, className }) {
  return (
    <div
      className={cn(
        'grid grid-cols-2 gap-x-5 gap-y-4 sm:grid-cols-4 sm:divide-x sm:divide-rule',
        className,
      )}
    >
      {children}
    </div>
  );
}
