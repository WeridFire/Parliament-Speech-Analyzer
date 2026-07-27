import { useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router';

/**
 * View state lives in the URL, not in React state.
 *
 * The old app kept chamber, period, view mode, colour mode and selection in a
 * context — twelve distinct views shared one URL, so nothing was linkable, the
 * back button did nothing, and switching chamber silently reset everything.
 * Putting it in the query string makes every view shareable and gives
 * back/forward for free.
 *
 * Italian param names keep shared links readable:
 *   fonte  chamber        camera | senate
 *   anno   year           2024…
 *   mese   month          01…12
 *   vista  map view       interventi | deputati
 *   colora map colouring  tema | partito
 *   focus  highlighted groups, comma separated
 *   dep    pinned deputies, comma separated
 */

const DEFAULTS = {
  fonte: 'camera',
  vista: 'interventi',
  colora: 'tema',
};

export function useAppParams() {
  const [params, setParams] = useSearchParams();

  const get = useCallback(
    (name) => params.get(name) ?? DEFAULTS[name] ?? null,
    [params],
  );

  const getList = useCallback(
    (name) => {
      const raw = params.get(name);
      return raw ? raw.split(',').filter(Boolean) : [];
    },
    [params],
  );

  /**
   * Merge updates into the query string. `null`/`''`/default values are removed
   * so shared URLs stay short and canonical.
   */
  const update = useCallback(
    (patch, { replace = false } = {}) => {
      setParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          for (const [k, v] of Object.entries(patch)) {
            const value = Array.isArray(v) ? v.join(',') : v;
            if (value == null || value === '' || value === DEFAULTS[k]) next.delete(k);
            else next.set(k, String(value));
          }
          return next;
        },
        { replace },
      );
    },
    [setParams],
  );

  const chamber = get('fonte') === 'senate' ? 'senate' : 'camera';

  const period = useMemo(() => {
    const year = params.get('anno');
    const month = params.get('mese');
    return {
      year: year ? Number(year) : null,
      // month is only meaningful with a year, and stays zero-padded to match
      // the backend's "YYYY-MM" bucket keys.
      month: year && month ? String(month).padStart(2, '0') : null,
    };
  }, [params]);

  const selection = useMemo(
    () => ({
      view: get('vista') === 'deputati' ? 'deputati' : 'interventi',
      colorBy: get('colora') === 'partito' ? 'partito' : 'tema',
      focus: getList('focus'),
      deputies: getList('dep'),
    }),
    [get, getList],
  );

  const setChamber = useCallback(
    (next) => {
      // Period buckets differ per chamber (Senato covers 2 months, Camera 15),
      // so a period from one chamber is meaningless in the other.
      update({ fonte: next, anno: null, mese: null, focus: null, dep: null });
    },
    [update],
  );

  const setPeriod = useCallback(
    ({ year, month }) => update({ anno: year ?? null, mese: year ? (month ?? null) : null }),
    [update],
  );

  /** Focus is capped at 3 — the all-pairs colour limit for scatter forms. */
  const toggleFocus = useCallback(
    (key, max = 3) => {
      const current = getList('focus');
      const next = current.includes(key)
        ? current.filter((k) => k !== key)
        : [...current, key].slice(-max);
      update({ focus: next });
    },
    [getList, update],
  );

  const toggleDeputy = useCallback(
    (id, max = 4) => {
      const current = getList('dep');
      const next = current.includes(id)
        ? current.filter((d) => d !== id)
        : [...current, id].slice(-max);
      update({ dep: next });
    },
    [getList, update],
  );

  return {
    params,
    chamber,
    period,
    ...selection,
    update,
    setChamber,
    setPeriod,
    toggleFocus,
    toggleDeputy,
    clearFocus: useCallback(() => update({ focus: null }), [update]),
    clearDeputies: useCallback(() => update({ dep: null }), [update]),
  };
}
