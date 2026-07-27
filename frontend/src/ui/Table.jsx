import { cn } from '../lib/cn';

/**
 * Compact data table.
 *
 * Also the accessibility relief channel for charts: several light-mode series
 * colours sit below 3:1 against the surface, which is permitted only when the
 * values are readable another way. Panels that use those colours expose their
 * numbers here or as visible direct labels.
 *
 * @param {Array} columns [{ key, header, align, width, render, numeric }]
 */
export function Table({ columns, rows, getRowKey, caption, empty = 'Nessun dato.', className }) {
  if (!rows?.length) {
    return <p className="px-1 py-6 text-center text-body text-secondary">{empty}</p>;
  }

  return (
    <div className={cn('w-full overflow-x-auto', className)}>
      <table className="w-full border-collapse text-body">
        {caption ? <caption className="sr-only">{caption}</caption> : null}
        <thead>
          <tr className="border-b border-rule-strong">
            {columns.map((c) => (
              <th
                key={c.key}
                scope="col"
                style={c.width ? { width: c.width } : undefined}
                className={cn(
                  'px-2.5 py-2 text-label font-medium text-muted first:pl-0 last:pr-0',
                  c.numeric || c.align === 'right' ? 'text-right' : 'text-left',
                )}
              >
                {String(c.header).toUpperCase()}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr
              key={getRowKey ? getRowKey(row, i) : i}
              className="border-b border-rule last:border-b-0"
            >
              {columns.map((c) => (
                <td
                  key={c.key}
                  className={cn(
                    'px-2.5 py-2 first:pl-0 last:pr-0',
                    c.numeric || c.align === 'right'
                      ? 'tabular text-right text-num text-secondary'
                      : 'text-ink',
                  )}
                >
                  {c.render ? c.render(row, i) : row[c.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
