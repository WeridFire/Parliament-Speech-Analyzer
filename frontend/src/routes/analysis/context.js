import { useOutletContext } from 'react-router';

/**
 * Typed accessor for the shared analytics context set by AnalysisLayout.
 * Lives in its own module so the layout file exports only components.
 */
export function useAnalysis() {
  return useOutletContext();
}
