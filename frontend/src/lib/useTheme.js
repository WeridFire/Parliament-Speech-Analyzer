import { useCallback, useEffect, useState } from 'react';

const STORAGE_KEY = 'psa-theme'; // must match the no-flash script in index.html

const read = () =>
  document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';

/**
 * Reads and controls the active color mode.
 *
 * The <html data-theme> attribute is the single source of truth — the no-flash
 * script in index.html stamps it before first paint by folding the OS
 * preference into an explicit value, so the toggle always wins in both
 * directions and there is no dual-scope CSS to keep in sync.
 *
 * `mode` is returned as state (not just read from the DOM) because Plotly
 * cannot read CSS variables: charts take raw hex from viz/palette.js and must
 * re-render when the mode changes. See viz/plotlyTheme.js.
 */
export function useTheme() {
  const [mode, setMode] = useState(read);

  // Follow the OS only while the user has expressed no preference.
  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const onChange = (e) => {
      if (localStorage.getItem(STORAGE_KEY)) return;
      apply(e.matches ? 'dark' : 'light');
      setMode(e.matches ? 'dark' : 'light');
    };
    mq.addEventListener('change', onChange);
    return () => mq.removeEventListener('change', onChange);
  }, []);

  // Keep other tabs and any other hook instance in step.
  useEffect(() => {
    const onStorage = (e) => {
      if (e.key !== STORAGE_KEY) return;
      const next = e.newValue === 'dark' ? 'dark' : 'light';
      apply(next);
      setMode(next);
    };
    const onLocal = () => setMode(read());

    window.addEventListener('storage', onStorage);
    window.addEventListener('psa-theme-change', onLocal);
    return () => {
      window.removeEventListener('storage', onStorage);
      window.removeEventListener('psa-theme-change', onLocal);
    };
  }, []);

  const setTheme = useCallback((next) => {
    localStorage.setItem(STORAGE_KEY, next);
    apply(next);
    setMode(next);
    window.dispatchEvent(new Event('psa-theme-change'));
  }, []);

  const toggle = useCallback(() => {
    setTheme(read() === 'dark' ? 'light' : 'dark');
  }, [setTheme]);

  return { mode, isDark: mode === 'dark', setTheme, toggle };
}

function apply(mode) {
  document.documentElement.setAttribute('data-theme', mode);
  document.documentElement.style.colorScheme = mode;
}
