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
 */
export function WordCloud({ words, mode = 'light', max = 40, className }) {
  const items = useMemo(() => {
    if (!words?.length) return [];
    const list = words.slice(0, max);
    const n = list.length;

    return list.map((word, i) => {
      const rank = 1 - i / Math.max(n - 1, 1); // 1 = most distinctive
      return {
        word,
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
      {items.map(({ word, size, weight, opacity }) => (
        <li
          key={word}
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
