import { cn } from '../lib/cn';
import { barWidth } from '../domain/metrics';

const TONE_VAR = {
  good: 'var(--status-good)',
  warning: 'var(--status-warning)',
  serious: 'var(--status-serious)',
  critical: 'var(--status-critical)',
  neutral: 'var(--accent)',
};

/**
 * A horizontal magnitude bar.
 *
 * `value` is always 0–100 — callers normalise with metrics.toPercent() first,
 * declaring whether the source metric is 0–1 or already a percentage. The old
 * code passed `cohesion_score` (0–1) straight into `width: ${v}%`, which made
 * every cohesion bar 0.3% wide.
 *
 * `color` accepts a raw hex so chart-adjacent lists can match a series colour;
 * otherwise the tone maps to a status token.
 */
export function Meter({ value, tone = 'neutral', color, className, label }) {
  const width = barWidth(value);
  return (
    <div
      className={cn('h-1.5 w-full overflow-hidden rounded-full bg-sunken', className)}
      role="img"
      aria-label={label}
    >
      <div
        className="h-full rounded-full transition-[width] duration-150"
        style={{ width: `${width}%`, backgroundColor: color ?? TONE_VAR[tone] }}
      />
    </div>
  );
}

/** Position badge for ranked lists. Top three get emphasis, the rest stay quiet. */
export function Rank({ position, className }) {
  const top = position <= 3;
  return (
    <span
      className={cn(
        'tabular inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-xs text-num',
        top
          ? 'bg-accent font-semibold text-accent-ink'
          : 'bg-sunken font-medium text-muted',
        className,
      )}
      aria-hidden="true"
    >
      {position}
    </span>
  );
}
