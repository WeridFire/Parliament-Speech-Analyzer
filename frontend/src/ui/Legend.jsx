import { cn } from '../lib/cn';

/**
 * Chart legend.
 *
 * Present whenever a chart carries two or more series — identity must never
 * rest on colour alone. A single-series chart takes no legend; its title names
 * the series.
 *
 * When `onToggle` is supplied the legend doubles as the series filter used by
 * the map's focus+context interaction.
 *
 * @param {Array} items [{ key, label, color, shape, active, count }]
 */
export function Legend({ items, onToggle, className, orientation = 'horizontal' }) {
  if (!items?.length) return null;

  return (
    <ul
      className={cn(
        'flex gap-x-4 gap-y-1.5',
        orientation === 'vertical' ? 'flex-col' : 'flex-wrap items-center',
        className,
      )}
    >
      {items.map((item) => {
        const interactive = typeof onToggle === 'function';
        const dimmed = interactive && item.active === false;
        const Tag = interactive ? 'button' : 'span';

        return (
          <li key={item.key}>
            <Tag
              type={interactive ? 'button' : undefined}
              onClick={interactive ? () => onToggle(item.key) : undefined}
              aria-pressed={interactive ? item.active !== false : undefined}
              className={cn(
                'flex min-w-0 items-center gap-1.5 text-left text-label transition-opacity duration-150',
                dimmed ? 'opacity-40' : 'opacity-100',
                interactive && 'hover:opacity-100',
              )}
            >
              <span
                className="h-2.5 w-2.5 shrink-0 rounded-xs"
                style={{ backgroundColor: item.color }}
                aria-hidden="true"
              />
              <span className="truncate text-secondary" title={item.label}>
                {item.label}
              </span>
              {typeof item.count === 'number' ? (
                <span className="tabular shrink-0 text-muted">{item.count}</span>
              ) : null}
            </Tag>
          </li>
        );
      })}
    </ul>
  );
}
