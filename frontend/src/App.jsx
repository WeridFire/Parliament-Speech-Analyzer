import { Navigate, Route, Routes } from 'react-router';
import { AppShell } from './layout/AppShell';
import { ChamberBoundary } from './app/ChamberBoundary';
import Home from './routes/Home';
import MapRoute from './routes/Map';
import Method from './routes/Method';
import AnalysisLayout from './routes/analysis/AnalysisLayout';
import Identity from './routes/analysis/Identity';
import Relations from './routes/analysis/Relations';
import Temporal from './routes/analysis/Temporal';
import Qualitative from './routes/analysis/Qualitative';
import Speakers from './routes/analysis/Speakers';

/**
 * Routing only. Every data-dependent branch sits under ChamberBoundary, which
 * reads `?fonte=` and owns the loading and error states.
 *
 * Replaces `useState('home' | 'mappa' | 'analytics')` — twelve views at one URL
 * with no history and no shareable state.
 */
export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Home />} />
        <Route path="metodo" element={<Method />} />

        <Route
          path="mappa"
          element={
            <ChamberBoundary>
              <MapRoute />
            </ChamberBoundary>
          }
        />

        <Route
          path="analisi"
          element={
            <ChamberBoundary>
              <AnalysisLayout />
            </ChamberBoundary>
          }
        >
          <Route index element={<Navigate to="identita" replace />} />
          <Route path="identita" element={<Identity />} />
          <Route path="relazioni" element={<Relations />} />
          <Route path="tendenze" element={<Temporal />} />
          <Route path="qualita" element={<Qualitative />} />
          <Route path="parlamentari" element={<Speakers />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
