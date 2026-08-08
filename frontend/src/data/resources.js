import { useEffect, useMemo, useState } from 'react';
import { useData } from './DataProvider';

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
 * Analytics for a period, falling back to the global block.
 *
 * `hasOwn` reports whether the requested period had its own analytics, which is
 * how the UI can distinguish "this month" from "global, because this month was
 * too thin for these metrics to mean anything".
 */
export function useAnalytics(period) {
  const { resources } = useData();

  const { path, hasOwn } = useMemo(() => {
    const analytics = resources?.analytics;
    if (!analytics) return { path: null, hasOwn: false };

    if (period?.year && period?.month) {
      const ref = analytics.by_month?.[`${period.year}-${period.month}`];
      if (ref) return { path: ref.path, hasOwn: true };
    }
    if (period?.year) {
      const ref = analytics.by_year?.[String(period.year)];
      if (ref) return { path: ref.path, hasOwn: true };
    }
    return { path: analytics.global?.path ?? null, hasOwn: !period?.year };
  }, [resources, period?.year, period?.month]);

  const state = useResource(path);
  return { ...state, hasOwn };
}
