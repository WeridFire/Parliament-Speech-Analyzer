import { NavLink, Outlet, useLocation } from 'react-router';
import { cn } from '../lib/cn';
import { ThemeToggle } from './ThemeToggle';
import { useAppParams } from '../app/useAppParams';

const NAV = [
  { to: '/mappa', label: 'Mappa' },
  { to: '/analisi', label: 'Analisi' },
  { to: '/metodo', label: 'Metodo' },
];

/**
 * The application frame: a single hairline masthead over a routed outlet.
 *
 * Replaces the previous arrangement of two fixed 300px sidebars in a
 * `height:100vh; overflow:hidden` flex row with no media queries at all, which
 * made the map unusable below roughly 1000px.
 */
export function AppShell() {
  const { pathname } = useLocation();
  const { params } = useAppParams();

  // Carry chamber/period across navigation so switching tabs keeps context.
  const search = params.toString();
  const withParams = (to) => (search ? `${to}?${search}` : to);

  return (
    <div className="flex min-h-dvh flex-col bg-plane">
      <a
        href="#contenuto"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:rounded-sm focus:bg-surface focus:px-3 focus:py-2 focus:text-body"
      >
        Salta al contenuto
      </a>

      <header className="sticky top-0 z-30 border-b border-rule bg-plane/95 backdrop-blur-sm">
        <div className="mx-auto flex h-14 w-full max-w-[1600px] items-center gap-3 px-4 sm:gap-6 sm:px-6">
          <NavLink
            to={withParams('/')}
            className="flex min-w-0 shrink-0 items-center gap-2.5 no-underline"
          >
            <Mark />
            <span className="hidden text-label text-muted sm:inline">
              PARLAMENTO · ANALISI DEL DISCORSO
            </span>
          </NavLink>

          <nav className="flex min-w-0 flex-1 items-center gap-1" aria-label="Sezioni">
            {NAV.map((item) => {
              const active = pathname.startsWith(item.to);
              return (
                <NavLink
                  key={item.to}
                  to={withParams(item.to)}
                  className={cn(
                    'rounded-sm px-2.5 py-1.5 text-body font-medium no-underline transition-colors duration-150',
                    active ? 'bg-accent-soft text-ink' : 'text-secondary hover:bg-hover hover:text-ink',
                  )}
                >
                  {item.label}
                </NavLink>
              );
            })}
          </nav>

          <ThemeToggle className="shrink-0" />
        </div>
      </header>

      <main id="contenuto" className="min-h-0 flex-1">
        <Outlet />
      </main>
    </div>
  );
}

/** The wordmark: three bars over a rule — data, and a colonnade. */
function Mark() {
  return (
    <svg width="20" height="20" viewBox="0 0 32 32" aria-hidden="true" className="shrink-0">
      <g fill="currentColor" className="text-ink">
        <rect x="5" y="14" width="5" height="11" />
        <rect x="13.5" y="7" width="5" height="18" />
        <rect x="22" y="11" width="5" height="14" />
      </g>
      <rect x="4" y="27" width="24" height="1.6" className="fill-accent" />
    </svg>
  );
}

/** Standard page container — one max-width and one gutter for every route. */
export function Page({ children, className, wide = false }) {
  return (
    <div
      className={cn(
        'mx-auto w-full px-4 py-8 sm:px-6 sm:py-10',
        wide ? 'max-w-[1600px]' : 'max-w-[1200px]',
        className,
      )}
    >
      {children}
    </div>
  );
}
