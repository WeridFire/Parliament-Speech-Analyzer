/**
 * Topic cluster registry — mirrors backend/config/topic_clusters.py.
 *
 * The `clusters` object in the JSON payload is authoritative for labels and
 * counts; this registry only supplies the short forms that long labels cannot
 * provide (axis ticks, chips, legends, radar spokes). Look-ups always fall back
 * to the payload label so a backend relabel does not need a frontend change.
 */

const SHORT = {
  0: 'Fisco',
  1: 'Lavoro',
  2: 'Sanità',
  3: 'Welfare',
  4: 'Ambiente',
  5: 'Giustizia',
  6: 'Immigrazione',
  7: 'Diritti',
  8: 'Scuola',
  9: 'Agricoltura',
  10: 'Estera/Difesa',
  11: 'Infrastrutture',
  12: 'Premierato',
  13: 'Riforme',
};

/** Full label for a cluster id, preferring the payload. */
export function topicLabel(id, clusters) {
  return clusters?.[id]?.label ?? clusters?.[String(id)]?.label ?? `Tema ${id}`;
}

/** Compact label for axis ticks and chips. */
export function topicShort(id, clusters) {
  if (SHORT[id]) return SHORT[id];
  const full = topicLabel(id, clusters);
  return full.length > 14 ? `${full.slice(0, 13)}…` : full;
}

/** Ordered [{ id, label, short, count, keywords }] from the payload. */
export function topicList(clusters) {
  if (!clusters) return [];
  return Object.entries(clusters)
    .map(([id, c]) => ({
      id: Number(id),
      label: c?.label ?? `Tema ${id}`,
      short: SHORT[Number(id)] ?? c?.label ?? `Tema ${id}`,
      count: c?.count ?? 0,
      keywords: c?.keywords ?? [],
    }))
    .sort((a, b) => a.id - b.id);
}

/**
 * The N largest topics plus a folded "Altri" bucket.
 *
 * There are 14 topics but only 8 validated categorical slots, and the topic
 * distribution is heavily skewed — in camera.json, Premierato (3.780) and
 * Riforme (2.994) alone are 63% of all speeches while Agricoltura has 102. The
 * old code did `CLUSTER_COLORS[id % 10]`, which silently gave clusters 10–13
 * the same colours as 0–3. Folding is the correct answer: never cycle.
 */
export function topTopics(clusters, limit = 7) {
  const all = topicList(clusters);
  if (all.length <= limit) return { top: all, rest: [] };

  const sorted = [...all].sort((a, b) => b.count - a.count);
  return {
    top: sorted.slice(0, limit).sort((a, b) => a.id - b.id),
    rest: sorted.slice(limit),
  };
}
