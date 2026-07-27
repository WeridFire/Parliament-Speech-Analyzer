import { createContext, useContext, useEffect, useMemo, useRef, useState } from 'react';

/**
 * Loads and caches the per-chamber datasets.
 *
 * The payload is large (camera.json is ~45 MB) and is intentionally left as-is
 * for this pass, so two things matter here:
 *
 *  1. Parsed payloads are cached per chamber for the session. The old provider
 *     re-fetched and re-parsed the whole file on every chamber toggle.
 *  2. Download progress is surfaced, so the shell can show a real skeleton with
 *     a byte count instead of an indefinite spinner.
 */

const CHAMBERS = {
  camera: { id: 'camera', file: 'camera.json', label: 'Camera', full: 'Camera dei Deputati' },
  senate: { id: 'senate', file: 'senato.json', label: 'Senato', full: 'Senato della Repubblica' },
};

export const CHAMBER_LIST = Object.values(CHAMBERS);

const DataContext = createContext(null);

/** Resolve against Vite's base so the gh-pages sub-path keeps working. */
const assetUrl = (file) => `${import.meta.env.BASE_URL}${file}`;

export function DataProvider({ chamber = 'camera', children }) {
  const [state, setState] = useState({ status: 'idle', data: null, error: null });
  const [progress, setProgress] = useState({ loaded: 0, total: 0 });
  const [available, setAvailable] = useState(() => Object.keys(CHAMBERS));

  const cache = useRef(new Map());
  const inflight = useRef(null);

  // Probe which datasets are actually deployed.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const found = await Promise.all(
        Object.values(CHAMBERS).map(async (c) => {
          try {
            const res = await fetch(assetUrl(c.file), { method: 'HEAD' });
            return res.ok ? c.id : null;
          } catch {
            return null;
          }
        }),
      );
      if (!cancelled) setAvailable(found.filter(Boolean));
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const meta = CHAMBERS[chamber];
    if (!meta) return undefined;

    if (cache.current.has(chamber)) {
      setState({ status: 'ready', data: cache.current.get(chamber), error: null });
      setProgress({ loaded: 0, total: 0 });
      return undefined;
    }

    const controller = new AbortController();
    inflight.current?.abort();
    inflight.current = controller;

    setState({ status: 'loading', data: null, error: null });
    setProgress({ loaded: 0, total: 0 });

    (async () => {
      try {
        const res = await fetch(assetUrl(meta.file), { signal: controller.signal });
        if (!res.ok) throw new Error(`${meta.file}: HTTP ${res.status}`);

        const json = await readWithProgress(res, setProgress);
        if (controller.signal.aborted) return;

        cache.current.set(chamber, json);
        setState({ status: 'ready', data: json, error: null });
      } catch (err) {
        if (err.name === 'AbortError') return;
        console.error('[data] load failed', err);
        setState({ status: 'error', data: null, error: err });
      }
    })();

    return () => controller.abort();
  }, [chamber]);

  const value = useMemo(
    () => ({
      chamber,
      chamberMeta: CHAMBERS[chamber] ?? CHAMBERS.camera,
      availableChambers: available,
      status: state.status,
      data: state.data,
      error: state.error,
      progress,
      isLoading: state.status === 'loading' || state.status === 'idle',
    }),
    [chamber, available, state, progress],
  );

  return <DataContext.Provider value={value}>{children}</DataContext.Provider>;
}

export function useData() {
  const ctx = useContext(DataContext);
  if (!ctx) throw new Error('useData must be used inside <DataProvider>');
  return ctx;
}

/**
 * Stream the body so a 45 MB download reports progress. Falls back to res.json()
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

    // Throttle: repainting on every chunk of a 45 MB file is its own bottleneck.
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
