import { useMemo } from 'react';
import { cn } from '../../lib/cn';
import { CHROME } from '../palette';
import { EmptyState } from '../../ui/EmptyState';

/**
 * Distinctive-vocabulary cloud.
 *
 * Replaces a 146-line hand-written canvas implementation (Archimedean spiral,
 * up to 1000 collision attempts per word, no re-layout on resize, and its own
 * fourth colour array). This is plain flowing text instead: it reflows
 * naturally, is selectable and screen-reader accessible, and scales with the
 * container.
 *
 * Size encodes rank, which is ordinal — so it takes a single hue stepped by
 * lightness, not the categorical slots. Colour here is redundant with size, by
 * design; the word itself always carries the meaning.
 *
 * `words` is either plain strings or the backend's `{term, z, n}` records; the
 * strength of the evidence (z) and the count are exposed as a tooltip.
 */
export function WordCloud({ words, mode = 'light', max = 40, className }) {
  const items = useMemo(() => {
    if (!words?.length) return [];
    const list = words.slice(0, max);
    const n = list.length;

    return list.map((entry, i) => {
      const rank = 1 - i / Math.max(n - 1, 1); // 1 = most distinctive
      const word = typeof entry === 'string' ? entry : entry.term;
      return {
        word,
        title: typeof entry === 'string' ? undefined : `${entry.n} occorrenze · z = ${entry.z}`,
        size: 0.8 + rank * 1.05, // rem
        weight: rank > 0.66 ? 600 : rank > 0.33 ? 500 : 400,
        opacity: 0.5 + rank * 0.5,
      };
    });
  }, [words, max]);

  if (!items.length) {
    return <EmptyState message="Nessuna parola chiave per questa selezione." />;
  }

  const ink = CHROME[mode].ink;

  return (
    <ul
      className={cn(
        'flex flex-wrap items-baseline justify-center gap-x-3 gap-y-1.5 px-2 py-1',
        className,
      )}
    >
      {items.map(({ word, title, size, weight, opacity }) => (
        <li
          key={word}
          title={title}
          className="leading-tight"
          style={{
            fontSize: `${size}rem`,
            fontWeight: weight,
            color: ink,
            opacity,
          }}
        >
          {word}
        </li>
      ))}
    </ul>
  );
}
