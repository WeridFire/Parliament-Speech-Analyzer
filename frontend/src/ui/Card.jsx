import { cn } from '../lib/cn';

/**
 * The panel primitive. Replaces ~25 hand-built card headers that each
 * re-declared their own padding, border and title styling across the tabs.
 *
 * Hierarchy comes from the hairline rule and whitespace — no shadow, no
 * gradient, no elevation.
 */
export function Card({ as: Tag = 'section', className, children, ...rest }) {
  return (
    <Tag
      className={cn(
        'flex min-w-0 flex-col overflow-hidden rounded-md border border-rule bg-surface',
        className,
      )}
      {...rest}
    >
      {children}
    </Tag>
  );
}

/**
 * @param {string}      title     required — every card is named
 * @param {string}      subtitle  one line of context under the title
 * @param {ReactNode}   actions   right-aligned controls (chips, selects)
 * @param {ElementType} icon      lucide icon, rendered muted at 15px
 */
export function CardHeader({ title, subtitle, actions, icon: Icon, className }) {
  return (
    <header
      className={cn(
        'flex flex-wrap items-start justify-between gap-x-4 gap-y-3 border-b border-rule px-5 py-4',
        className,
      )}
    >
      <div className="min-w-0">
        <h3 className="flex items-center gap-2 text-h3">
          {Icon ? <Icon size={15} className="shrink-0 text-muted" aria-hidden="true" /> : null}
          <span className="truncate">{title}</span>
        </h3>
        {subtitle ? <p className="mt-1 text-body text-secondary">{subtitle}</p> : null}
      </div>
      {actions ? <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div> : null}
    </header>
  );
}

export function CardBody({ className, children, ...rest }) {
  return (
    <div className={cn('min-w-0 flex-1 p-5', className)} {...rest}>
      {children}
    </div>
  );
}

/** Footnote strip for provenance, thresholds and caveats. */
export function CardFooter({ className, children }) {
  return (
    <footer
      className={cn(
        'border-t border-rule bg-sunken px-5 py-2.5 text-label text-muted',
        className,
      )}
    >
      {children}
    </footer>
  );
}
