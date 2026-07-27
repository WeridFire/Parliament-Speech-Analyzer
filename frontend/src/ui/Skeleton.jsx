import { cn } from '../lib/cn';

/**
 * Loading placeholder.
 *
 * These datasets are large (camera.json is ~45 MB and is parsed in one go), so
 * the wait is real and a bare spinner understated it. A skeleton communicates
 * both that something is coming and roughly what shape it will be.
 */
export function Skeleton({ className, ...rest }) {
  return (
    <div
      className={cn('animate-pulse rounded-xs bg-sunken', className)}
      aria-hidden="true"
      {...rest}
    />
  );
}

/** Card-shaped placeholder used while a panel's data resolves. */
export function SkeletonCard({ lines = 4, className }) {
  return (
    <div className={cn('rounded-md border border-rule bg-surface p-5', className)}>
      <Skeleton className="h-3.5 w-40" />
      <div className="mt-5 flex flex-col gap-3">
        {Array.from({ length: lines }).map((_, i) => (
          <Skeleton key={i} className="h-3" style={{ width: `${90 - i * 12}%` }} />
        ))}
      </div>
    </div>
  );
}

/** Full-page loading state with a live region for assistive tech. */
export function LoadingScreen({ message = 'Caricamento dei dati…', detail }) {
  return (
    <div
      className="flex min-h-[60vh] flex-col items-center justify-center gap-4 px-6 text-center"
      role="status"
      aria-live="polite"
    >
      <div className="flex gap-1.5" aria-hidden="true">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="h-6 w-1.5 animate-pulse rounded-full bg-rule-strong"
            style={{ animationDelay: `${i * 140}ms` }}
          />
        ))}
      </div>
      <p className="text-body text-secondary">{message}</p>
      {detail ? <p className="max-w-md text-label text-muted">{detail}</p> : null}
    </div>
  );
}
