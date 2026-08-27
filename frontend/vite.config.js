import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  // GitHub Pages serves the site from /<repo>/, not the domain root, so
  // asset URLs need that prefix. The Pages workflow sets this; locally
  // it stays '/'.
  base: process.env.VITE_BASE || '/',
  server: {
    // Forward /api to the backend during development, so the browser
    // only ever talks to localhost:5173 and no CORS setup is needed.
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
