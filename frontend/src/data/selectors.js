import { parseDate } from '../lib/format';
import { resolveParty } from '../domain/parties';

/**
 * Pure derivations over the payload. No React, no formatting decisions — so
 * each one is trivially testable and memoisable by the caller.
 */

/** The period a view is scoped to. `{ year: null, month: null }` means global. */
export const GLOBAL_PERIOD = { year: null, month: null };

export const periodKey = (p) =>
  p?.year && p?.month ? `${p.year}-${p.month}` : p?.year ? String(p.year) : 'global';

/** Years and months the backend says it has coverage for. */
export function availablePeriods(core) {
  return (
    core?.deputies_by_period?.available_periods ?? { years: [], months: [] }
  );
}

/**
 * Speeches restricted to the selected period.
 *
 * Takes the speeches list rather than the whole payload: speeches are now a
 * separately fetched resource (see `useSpeeches`), so a view that never opens
 * the map never downloads them.
 */
export function speechesFor(speeches, period) {
  const all = speeches ?? [];
  if (!period?.year) return all;

  const year = Number(period.year);
  const month = period.month ? Number(period.month) : null;

  return all.filter((s) => {
    const d = parseDate(s.date);
    if (!d) return false;
    if (d.year !== year) return false;
    if (month && d.month !== month) return false;
    return true;
  });
}

/**
 * Deputies for the period, taken from the backend's precomputed buckets.
 * MIN_SPEECHES guards against single-intervention deputies dominating the map
 * with meaningless positions.
 */
export function deputiesFor(core, period, minSpeeches = 5) {
  const byPeriod = core?.deputies_by_period;
  let list = core?.deputies ?? [];

  if (byPeriod) {
    if (period?.year && period?.month && byPeriod.by_month?.[`${period.year}-${period.month}`]) {
      list = byPeriod.by_month[`${period.year}-${period.month}`];
    } else if (period?.year && byPeriod.by_year?.[String(period.year)]) {
      list = byPeriod.by_year[String(period.year)];
    } else if (byPeriod.global) {
      list = byPeriod.global;
    }
  }

  return (list ?? []).filter((d) => (d.n_speeches ?? 0) >= minSpeeches);
}

/**
 * Normalise speeches or deputies into the ScatterMap point shape.
 *
 * `text` now holds the original-case speech: the backend used to ship a
 * lowercased, procedurally-stripped copy under that name alongside a full one
 * called `snippet`, and this layer had to know which was which.
 */
export function toMapPoints({ items, kind, colorBy, clusters }) {
  return items.map((item, i) => {
    const party = resolveParty(item.party);
    const isCluster = colorBy === 'cluster';
    const clusterLabel =
      item.cluster_label ?? clusters?.[item.cluster]?.label ?? `Tema ${item.cluster}`;

    return {
      id: kind === 'speeches' ? `s-${i}` : `d-${item.deputy}`,
      // Pinning is by person, so a pinned deputy highlights every one of their
      // speeches in the interventi view as well as their dot in deputati view.
      pinKey: item.deputy,
      x: item.x,
      y: item.y,
      groupKey: isCluster ? `c-${item.cluster}` : `p-${party.id}`,
      groupLabel: isCluster ? clusterLabel : party.name,
      name: cleanName(item.deputy ?? item.name),
      party: item.party,
      partyId: party.id,
      cluster: item.cluster,
      sub:
        kind === 'speeches'
          ? `${party.short} · ${item.date ?? ''}`
          : `${party.short} · ${item.n_speeches ?? 0} interventi`,
      raw: item,
    };
  });
}

/** "VARCHI Maria Carolina [Fratelli d'Italia]" -> "VARCHI Maria Carolina" */
export function cleanName(deputy) {
  if (!deputy) return '';
  return String(deputy).replace(/\s*[[(][^\])]*[\])]\s*$/, '').trim();
}

/** Distinct party strings present in a list of speeches or deputies. */
export function partiesIn(items) {
  const seen = new Set();
  for (const it of items ?? []) if (it.party) seen.add(it.party);
  return [...seen];
}

/**
 * Count speeches per cluster for a set of parties, as a percentage of each
 * party's own total. Used by the party comparison view.
 *
 * The previous implementation re-scanned all 10.736 speeches once per selected
 * party per render; this does a single pass for all of them.
 */
export function clusterDistributionByParty(speeches, partyNames, clusterIds) {
  const wanted = new Set(partyNames);
  const totals = new Map(partyNames.map((p) => [p, 0]));
  const counts = new Map(partyNames.map((p) => [p, new Map()]));

  for (const s of speeches ?? []) {
    if (!wanted.has(s.party)) continue;
    totals.set(s.party, totals.get(s.party) + 1);
    const byCluster = counts.get(s.party);
    byCluster.set(s.cluster, (byCluster.get(s.cluster) ?? 0) + 1);
  }

  return partyNames.map((party) => {
    const total = totals.get(party) || 1;
    const byCluster = counts.get(party);
    return {
      party,
      total: totals.get(party),
      values: clusterIds.map((id) => ((byCluster.get(id) ?? 0) / total) * 100),
    };
  });
}

/** Sort an object of {name: value} into a capped, descending array of pairs. */
export function topEntries(obj, { limit = 10, valueOf = (v) => v, filter } = {}) {
  if (!obj) return [];
  return Object.entries(obj)
    .map(([name, raw]) => ({ name, raw, value: valueOf(raw) }))
    .filter((e) => typeof e.value === 'number' && Number.isFinite(e.value))
    .filter((e) => (filter ? filter(e) : true))
    .sort((a, b) => b.value - a.value)
    .slice(0, limit);
}

/** Same, ascending. */
export function bottomEntries(obj, opts = {}) {
  const all = topEntries(obj, { ...opts, limit: Number.POSITIVE_INFINITY });
  return all.reverse().slice(0, opts.limit ?? 10);
}
