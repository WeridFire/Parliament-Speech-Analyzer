import { createContext, useContext } from 'react';

/**
 * The data context and its accessor, kept apart from DataProvider.jsx so that
 * file exports only its component and fast refresh keeps working.
 */
export const DataContext = createContext(null);

export function useData() {
  const ctx = useContext(DataContext);
  if (!ctx) throw new Error('useData must be used inside <DataProvider>');
  return ctx;
}

export const CHAMBER_LABELS = {
  camera: { id: 'camera', label: 'Camera', full: 'Camera dei Deputati' },
  senato: { id: 'senato', label: 'Senato', full: 'Senato della Repubblica' },
};

export const CHAMBER_LIST = Object.values(CHAMBER_LABELS);
