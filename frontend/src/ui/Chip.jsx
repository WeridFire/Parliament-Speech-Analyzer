import { cn } from '../lib/cn';
import { partyDot, partyShort, partyName } from '../domain/parties';
import { classify } from '../domain/metrics';

/**
 * Selectable / static pill. `dot` renders a small identity swatch before the
 * label — the label always carries the meaning, the swatch only aids
 * recognition, so nothing is encoded by colour alone.
 */
export function Chip({
  children,
  selected = false,
  onClick,
  dot,
  title,
  size = 'md',
  className,
  ...rest
}) {
  const interactive = typeof onClick === 'function';
  const Tag = interactive ? 'button' : 'span';

  return (
    <Tag
      type={interactive ? 'button' : undefined}
      onClick={onClick}
      title={title}
      aria-pressed={interactive ? selected : undefined}
      className={cn(
        'inline-flex items-center gap-1.5 rounded-sm border font-medium whitespace-nowrap transition-colors duration-150',
        size === 'sm' ? 'px-1.5 py-0.5 text-label' : 'px-2.5 py-1 text-body',
        selected
          ? 'border-accent bg-accent-soft text-ink'
          : 'border-rule bg-surface text-secondary',
        interactive && !selected && 'hover:border-rule-strong hover:bg-hover hover:text-ink',
        className,
      )}
      {...rest}
    >
      {dot ? (
        <span
          className="h-2 w-2 shrink-0 rounded-full"
          style={{ backgroundColor: dot }}
          aria-hidden="true"
        />
      ) : null}
      {children}
    </Tag>
  );
}

/** Chip bound to the party registry — one place decides swatch and short name. */
export function PartyChip({ party, mode = 'light', short = true, ...rest }) {
  return (
    <Chip dot={partyDot(party, mode)} title={partyName(party)} {...rest}>
      {short ? partyShort(party) : partyName(party)}
    </Chip>
  );
}

const TONE_CLASS = {
  good: 'text-good',
  warning: 'text-warning',
  serious: 'text-serious',
  critical: 'text-critical',
  neutral: 'text-secondary',
};

/**
 * Renders a backend classification string as a readable Italian label.
 * Status tone is carried by a filled dot plus the word itself, never by
 * colour alone.
 */
export function ClassificationTag({ value, className }) {
  const { label, tone } = classify(value);
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 text-label whitespace-nowrap',
        TONE_CLASS[tone],
        className,
      )}
    >
      <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-current" aria-hidden="true" />
      {label.toUpperCase()}
    </span>
  );
}
