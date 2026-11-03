import { useCallback, useEffect, useMemo, useState } from 'react';
import { useData } from './context';

/**
 * On-demand access to the dataset's non-core resources.
 *
 * The payload is split so the shell can paint before the heavy parts arrive:
 * `core.json` loads with the chamber, while speeches (~11 MB) and each
 * analytics period load only when a view asks for them. These hooks are the
 * asking.
 *
 * They live outside DataProvider.jsx so that file exports only its component,
 * which keeps fast refresh working.
 */

/** Fetch one resource by path. Returns `{ data, status }` rather than suspending. */
export function useResource(path) {
  const { fetchResource } = useData();
  const [state, setState] = useState({ status: path ? 'loading' : 'idle', data: null });

  useEffect(() => {
    if (!path) {
      setState({ status: 'idle', data: null });
      return undefined;
    }

    let cancelled = false;
    setState({ status: 'loading', data: null });

    fetchResource(path)
      .then((data) => {
        if (!cancelled) setState({ status: 'ready', data });
      })
      .catch((err) => {
        console.error('[data] resource failed', path, err);
        if (!cancelled) setState({ status: 'error', data: null });
      });

    return () => {
      cancelled = true;
    };
  }, [path, fetchResource]);

  return state;
}

/** The speeches list — the biggest resource, so only the map pays for it. */
export function useSpeeches() {
  const { resources } = useData();
  return useResource(resources?.speeches?.path);
}

/**
 * Analytics for the selected period, plus the global block to fall back on.
 *
 * Fallback is per section, not per file: a month can carry its own speaker
 * statistics while party affinity - which needs a larger sample - was only
 * computed for the whole corpus. The previous version picked one file and,
 * when the month's file lacked a section, the tab showed "no data" even though
 * the global figure existed (and the methodology page promised it would be
 * shown). It also silently substituted the year's file for a missing month.
 *
 * Returns { status, section(name) -> { data, fromGlobal }, global }.
 */
export function useAnalytics(period) {
  const { resources } = useData();
  const analytics = resources?.analytics;

  const periodPath = useMemo(() => {
    if (!analytics || !period?.year) return null;
    const key = period.month ? `${period.year}-${period.month}` : String(period.year);
    const bucket = period.month ? analytics.by_month : analytics.by_year;
    return bucket?.[key]?.path ?? null;
  }, [analytics, period?.year, period?.month]);

  const globalState = useResource(analytics?.global?.path);
  const periodState = useResource(periodPath);

  const scoped = Boolean(period?.year);
  const status =
    globalState.status === 'error' || periodState.status === 'error'
      ? 'error'
      : globalState.status === 'loading' || periodState.status === 'loading'
        ? 'loading'
        : 'ready';

  const section = useCallback(
    (name) => {
      const own = scoped ? periodState.data?.[name] : globalState.data?.[name];
      if (own) return { data: own, fromGlobal: false };
      const fallback = scoped ? globalState.data?.[name] : null;
      return { data: fallback ?? null, fromGlobal: Boolean(fallback) };
    },
    [scoped, periodState.data, globalState.data],
  );

  return { status, section, global: globalState.data };
}
