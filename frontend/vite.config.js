import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  base: '/Parliament-Speech-Analyzer/',
  plugins: [react(), tailwindcss()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          react: ['react', 'react-dom', 'react-router'],
        },
      },
    },
    // Plotly (~4.8 MB) is reached only through the dynamic import in
    // viz/Chart.jsx, so Rollup gives it its own async chunk. Naming it in
    // manualChunks would pull it into the entry graph and Vite would emit a
    // <link rel="modulepreload"> for it — fetching all 4.8 MB on first paint
    // and defeating the lazy boundary. Leave the split to the dynamic import.
    modulePreload: {
      resolveDependencies: (_url, deps) => deps.filter((d) => !d.includes('plotly')),
    },
    chunkSizeWarningLimit: 6000,
  },
})
