import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';

/**
 * Loads the chunked dataset.
 *
 * The backend used to emit one file per chamber — camera.json was 45 MB — and
 * this provider had to stream the whole thing before the shell could render.
 * It now emits a manifest plus separate resources, so:
 *
 *  1. First paint needs only `manifest.json` + that chamber's `core.json`
 *     (deputies, clusters, stats): a couple of MB instead of forty-five.
 *  2. Speeches and each analytics period are fetched the first time a view
 *     actually asks for them, through `useSpeeches()` / `useAnalytics()`.
 *  3. Every resource is cached by path for the session, so switching chamber or
 *     period never refetches something already held.
 */

const DataContext = createContext(null);

const DATA_ROOT = 'data';

/** Resolve against Vite's base so the gh-pages sub-path keeps working. */
const assetUrl = (path) => `${import.meta.env.BASE_URL}${DATA_ROOT}/${path}`;

const CHAMBER_LABELS = {
  camera: { id: 'camera', label: 'Camera', full: 'Camera dei Deputati' },
  senato: { id: 'senato', label: 'Senato', full: 'Senato della Repubblica' },
};

/** The manifest keys chambers by file stem; routes still say 'senate'. */
const CHAMBER_ALIASES = { senate: 'senato', senato: 'senato', camera: 'camera' };

export const CHAMBER_LIST = Object.values(CHAMBER_LABELS);

export function DataProvider({ chamber = 'camera', children }) {
  const chamberKey = CHAMBER_ALIASES[chamber] ?? chamber;

  const [manifest, setManifest] = useState(null);
  const [state, setState] = useState({ status: 'idle', core: null, error: null });
  const [progress, setProgress] = useState({ loaded: 0, total: 0 });

  // path -> Promise<json>, so concurrent callers share one request.
  const cache = useRef(new Map());

  const fetchResource = useCallback((path, { withProgress = false } = {}) => {
    if (!path) return Promise.resolve(null);

    if (!cache.current.has(path)) {
      const request = fetch(assetUrl(path))
        .then((res) => {
          if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
          return withProgress ? readWithProgress(res, setProgress) : res.json();
        })
        .catch((err) => {
          // Do not cache a failure: a retry should be able to succeed.
          cache.current.delete(path);
          throw err;
        });

      cache.current.set(path, request);
    }

    return cache.current.get(path);
  }, []);

  // The manifest is small and shared by every chamber, so it loads once.
  useEffect(() => {
    let cancelled = false;

    fetchResource('manifest.json')
      .then((json) => {
        if (!cancelled) setManifest(json);
      })
      .catch((err) => {
        console.error('[data] manifest failed', err);
        if (!cancelled) setState({ status: 'error', core: null, error: err });
      });

    return () => {
      cancelled = true;
    };
  }, [fetchResource]);

  const chamberEntry = manifest?.chambers?.[chamberKey] ?? null;

  useEffect(() => {
    if (!manifest) return undefined;

    if (!chamberEntry) {
      setState({
        status: 'error',
        core: null,
        error: new Error(`Unknown chamber "${chamberKey}"`),
      });
      return undefined;
    }

    let cancelled = false;
    setState({ status: 'loading', core: null, error: null });
    setProgress({ loaded: 0, total: 0 });

    fetchResource(chamberEntry.resources.core.path, { withProgress: true })
      .then((core) => {
        if (!cancelled) setState({ status: 'ready', core, error: null });
      })
      .catch((err) => {
        console.error('[data] core failed', err);
        if (!cancelled) setState({ status: 'error', core: null, error: err });
      });

    return () => {
      cancelled = true;
    };
  }, [manifest, chamberEntry, chamberKey, fetchResource]);

  const value = useMemo(
    () => ({
      chamber: chamberKey,
      chamberMeta: CHAMBER_LABELS[chamberKey] ?? CHAMBER_LABELS.camera,
      availableChambers: manifest ? Object.keys(manifest.chambers) : [],
      manifest,
      resources: chamberEntry?.resources ?? null,
      periods: chamberEntry?.periods ?? { years: [], months: [] },
      status: state.status,
      // `data` is the chamber's core resource: deputies, clusters, stats.
      // Speeches and analytics come from the hooks below.
      data: state.core,
      error: state.error,
      progress,
      isLoading: state.status === 'loading' || state.status === 'idle',
      fetchResource,
    }),
    [chamberKey, manifest, chamberEntry, state, progress, fetchResource],
  );

  return <DataContext.Provider value={value}>{children}</DataContext.Provider>;
}

export function useData() {
  const ctx = useContext(DataContext);
  if (!ctx) throw new Error('useData must be used inside <DataProvider>');
  return ctx;
}

/**
 * Stream a body so a large resource reports progress. Falls back to res.json()
 * when the stream or Content-Length is unavailable.
 */
async function readWithProgress(res, onProgress) {
  const total = Number(res.headers.get('Content-Length')) || 0;

  if (!res.body?.getReader) return res.json();

  const reader = res.body.getReader();
  const chunks = [];
  let loaded = 0;
  let lastTick = 0;

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
    loaded += value.length;

    const now = performance.now();
    if (now - lastTick > 120) {
      lastTick = now;
      onProgress({ loaded, total });
    }
  }
  onProgress({ loaded, total: total || loaded });

  const merged = new Uint8Array(loaded);
  let offset = 0;
  for (const chunk of chunks) {
    merged.set(chunk, offset);
    offset += chunk.length;
  }

  return JSON.parse(new TextDecoder('utf-8').decode(merged));
}
