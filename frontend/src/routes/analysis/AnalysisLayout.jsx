import { NavLink, Outlet } from 'react-router';
import { useMemo } from 'react';
import { AlertTriangle } from 'lucide-react';
import { Page } from '../../layout/AppShell';
import { PeriodControls } from '../../layout/PeriodControls';
import { useData } from '../../data/context';
import { useAnalytics } from '../../data/resources';
import { useAppParams } from '../../app/useAppParams';
import { useTheme } from '../../lib/useTheme';
import { availablePeriods } from '../../data/selectors';
import { EmptyState, SkeletonCard } from '../../ui';
import { cn } from '../../lib/cn';

const TABS = [
  { to: 'identita', label: 'Identità' },
  { to: 'temi', label: 'Temi' },
  { to: 'schieramenti', label: 'Maggioranza e opposizione' },
  { to: 'relazioni', label: 'Relazioni' },
  { to: 'reazioni', label: 'Applausi e proteste' },
  { to: 'menzioni', label: 'Chi nomina chi' },
  { to: 'tendenze', label: 'Tendenze' },
  { to: 'linguaggio', label: 'Linguaggio' },
  { to: 'parlamentari', label: 'Parlamentari' },
];

/**
 * Shell for the analytics section: one masthead, one set of period controls,
 * one tab bar. Each tab reads its section through `section(name)`, which
 * resolves the period -> global fallback in exactly one place.
 */
export default function AnalysisLayout() {
  const { data, chamberMeta, availableChambers } = useData();
  const { mode } = useTheme();
  const { chamber, setChamber, period, setPeriod, params } = useAppParams();

  const periods = useMemo(() => availablePeriods(data), [data]);
  const { status, section, global } = useAnalytics(period);

  const search = params.toString();
  const withParams = (to) => (search ? `${to}?${search}` : to);

  const context = {
    data,
    section,
    globalAnalytics: global,
    clusters: data?.clusters ?? {},
    period,
    mode,
    chamberMeta,
  };

  return (
    <Page wide className="flex flex-col gap-6">
      <header className="flex flex-wrap items-end justify-between gap-x-8 gap-y-4">
        <div>
          <p className="text-label text-muted">ANALISI · {chamberMeta.full.toUpperCase()}</p>
          <h1 className="mt-1.5 text-display">Il discorso in aggregato</h1>
          {data?.stats?.first_date ? (
            <p className="mt-1.5 text-body text-secondary">
              {data.stats.total_speeches.toLocaleString('it-IT')} interventi dal{' '}
              {data.stats.first_date.split('-').reverse().join('/')} al{' '}
              {data.stats.last_date.split('-').reverse().join('/')}
            </p>
          ) : null}
        </div>
        <PeriodControls
          chamber={chamber}
          availableChambers={availableChambers}
          onChamberChange={setChamber}
          period={period}
          periods={periods}
          onPeriodChange={setPeriod}
        />
      </header>

      <nav
        className="-mb-px flex gap-1 overflow-x-auto border-b border-rule"
        aria-label="Tipi di analisi"
      >
        {TABS.map((tab) => (
          <NavLink
            key={tab.to}
            to={withParams(tab.to)}
            className={({ isActive }) =>
              cn(
                'shrink-0 border-b-2 px-3 py-2.5 text-body font-medium no-underline transition-colors duration-150',
                isActive
                  ? 'border-accent text-ink'
                  : 'border-transparent text-secondary hover:text-ink',
              )
            }
          >
            {tab.label}
          </NavLink>
        ))}
      </nav>

      {/* Waiting is not "no data": the tabs used to render their empty state
          while the analytics resource was still downloading. */}
      {status === 'loading' ? (
        <div className="grid gap-5 lg:grid-cols-2">
          <SkeletonCard lines={6} />
          <SkeletonCard lines={6} />
        </div>
      ) : status === 'error' ? (
        <EmptyState
          icon={AlertTriangle}
          message="Non è stato possibile caricare le analisi per questo periodo."
          hint="Ricarica la pagina; se il problema persiste i file dei dati potrebbero non essere stati generati."
        />
      ) : (
        <Outlet context={context} />
      )}
    </Page>
  );
}
