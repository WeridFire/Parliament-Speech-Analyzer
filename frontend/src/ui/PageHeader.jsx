import { cn } from '../lib/cn';

/**
 * The editorial page masthead: eyebrow, serif display title, standfirst, and a
 * hairline rule. This is the one place the serif display size is used.
 */
export function PageHeader({ eyebrow, title, description, actions, className }) {
  return (
    <div className={cn('border-b border-rule pb-5', className)}>
      <div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-4">
        <div className="min-w-0">
          {eyebrow ? (
            <p className="mb-1.5 text-label text-muted">{eyebrow.toUpperCase()}</p>
          ) : null}
          <h1 className="text-display">{title}</h1>
          {description ? (
            <p className="mt-2 max-w-2xl text-body text-secondary">{description}</p>
          ) : null}
        </div>
        {actions ? (
          <div className="flex shrink-0 flex-wrap items-center gap-3">{actions}</div>
        ) : null}
      </div>
    </div>
  );
}

/** Section divider inside a long page. */
export function SectionHeading({ title, description, actions, className }) {
  return (
    <div className={cn('flex flex-wrap items-end justify-between gap-x-6 gap-y-2', className)}>
      <div className="min-w-0">
        <h2 className="text-h2">{title}</h2>
        {description ? <p className="mt-1 text-body text-secondary">{description}</p> : null}
      </div>
      {actions ? <div className="flex shrink-0 items-center gap-2">{actions}</div> : null}
    </div>
  );
}
