import { NavLink, Outlet, useOutletContext } from 'react-router';
import { useMemo } from 'react';
import { Page } from '../../layout/AppShell';
import { PeriodControls } from '../../layout/PeriodControls';
import { useData } from '../../data/DataProvider';
import { useAppParams } from '../../app/useAppParams';
import { useTheme } from '../../lib/useTheme';
import { analyticsFor, availablePeriods } from '../../data/selectors';
import { cn } from '../../lib/cn';

const TABS = [
  { to: 'identita', label: 'Identità' },
  { to: 'relazioni', label: 'Relazioni' },
  { to: 'tendenze', label: 'Tendenze' },
  { to: 'qualita', label: 'Qualità' },
  { to: 'parlamentari', label: 'Parlamentari' },
];

/**
 * Shell for the analytics section: one masthead, one set of period controls,
 * one tab bar. Each tab reads its slice from the outlet context, so the
 * global -> year -> month fallback ladder is resolved in exactly one place.
 */
export default function AnalysisLayout() {
  const { data, chamberMeta, availableChambers } = useData();
  const { mode } = useTheme();
  const { chamber, setChamber, period, setPeriod, params } = useAppParams();

  const periods = useMemo(() => availablePeriods(data), [data]);
  const analytics = useMemo(() => analyticsFor(data, period), [data, period]);

  const search = params.toString();
  const withParams = (to) => (search ? `${to}?${search}` : to);

  const context = {
    data,
    analytics,
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

      <Outlet context={context} />
    </Page>
  );
}

/** Typed accessor for the shared analytics context. */
export function useAnalysis() {
  return useOutletContext();
}
