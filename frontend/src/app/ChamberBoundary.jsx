import { AlertTriangle } from 'lucide-react';
import { DataProvider, useData } from '../data/DataProvider';
import { useAppParams } from './useAppParams';
import { LoadingScreen } from '../ui';
import { Page } from '../layout/AppShell';

/**
 * Binds the URL's `fonte` param to the data provider, and renders the
 * loading/error states once for every data-dependent route.
 */
export function ChamberBoundary({ children }) {
  const { chamber } = useAppParams();
  return (
    <DataProvider chamber={chamber}>
      <DataGate>{children}</DataGate>
    </DataProvider>
  );
}

function DataGate({ children }) {
  const { status, error, progress, chamberMeta } = useData();

  if (status === 'error') {
    return (
      <Page>
        <div className="mx-auto flex max-w-lg flex-col items-center gap-3 py-20 text-center">
          <AlertTriangle size={24} className="text-critical" aria-hidden="true" />
          <h1 className="text-h2">Dati non disponibili</h1>
          <p className="text-body text-secondary">
            Non è stato possibile caricare il dataset «{chamberMeta.full}».
          </p>
          <p className="text-label text-muted">{error?.message}</p>
        </div>
      </Page>
    );
  }

  if (status !== 'ready') {
    return (
      <LoadingScreen
        message={`Caricamento · ${chamberMeta.full}`}
        detail={formatProgress(progress)}
      />
    );
  }

  return children;
}

/**
 * The Camera dataset is ~45 MB in one file, so the wait is genuinely long.
 * Reporting megabytes is more honest than an indefinite spinner.
 */
function formatProgress({ loaded, total }) {
  if (!loaded) return 'Il dataset completo pesa alcune decine di megabyte.';
  const mb = (n) => (n / 1_048_576).toFixed(1);
  return total
    ? `${mb(loaded)} di ${mb(total)} MB`
    : `${mb(loaded)} MB scaricati`;
}
