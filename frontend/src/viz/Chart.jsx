import { Suspense, lazy } from 'react';
import { cn } from '../lib/cn';
import { Skeleton } from '../ui/Skeleton';
import { EmptyState } from '../ui/EmptyState';

/**
 * Lazy Plotly boundary.
 *
 * Plotly is ~5 MB — the whole of the old 5.14 MB bundle. Every chart file used
 * to import it at module scope and call createPlotlyComponent itself, so the
 * home page paid for it too. Loading it behind React.lazy plus the manualChunks
 * split in vite.config.js keeps it out of the entry chunk; it arrives only when
 * a chart first mounts.
 */
const PlotlyPlot = lazy(async () => {
  const [{ default: Plotly }, { default: createPlotlyComponent }] = await Promise.all([
    import('plotly.js-dist-min'),
    import('react-plotly.js/factory'),
  ]);
  return { default: createPlotlyComponent(Plotly) };
});

/**
 * @param {Array}   data     Plotly traces, already coloured by the caller
 * @param {object}  layout   from buildLayout()/buildPolarLayout()
 * @param {object}  config   from buildConfig()
 * @param {number}  height   px
 * @param {boolean} isEmpty  render the empty state instead of an axis-only chart
 * @param {string}  title    accessible name for the figure
 */
export function Chart({
  data,
  layout,
  config,
  height = 320,
  isEmpty = false,
  emptyMessage = 'Nessun dato da visualizzare.',
  title,
  className,
  onClick,
}) {
  if (isEmpty || !data?.length) {
    return (
      <div className={cn('flex items-center justify-center', className)} style={{ height }}>
        <EmptyState message={emptyMessage} />
      </div>
    );
  }

  return (
    <figure className={cn('m-0 w-full', className)} aria-label={title}>
      <Suspense fallback={<Skeleton className="w-full rounded-sm" style={{ height }} />}>
        <PlotlyPlot
          data={data}
          layout={layout}
          config={config}
          onClick={onClick}
          useResizeHandler
          style={{ width: '100%', height: `${height}px` }}
        />
      </Suspense>
    </figure>
  );
}
