import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { HashRouter } from 'react-router';
import App from './App';
import './styles/base.css';

/**
 * HashRouter rather than BrowserRouter: the site deploys to GitHub Pages under
 * a project sub-path, where a real path route would 404 on direct load without
 * a server-side rewrite. Hash routing needs no such configuration.
 */
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <HashRouter>
      <App />
    </HashRouter>
  </StrictMode>,
);
