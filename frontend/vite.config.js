import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => ({
  plugins: [react()],

  // Development proxy — routes API calls to local backend
  server: {
    port: 5173,
    proxy: mode === 'development' ? {
      '/auth':        { target: 'http://localhost:8000', changeOrigin: true },
      '/analyze':     { target: 'http://localhost:8000', changeOrigin: true },
      '/leaderboard': { target: 'http://localhost:8000', changeOrigin: true },
      '/scores':      { target: 'http://localhost:8000', changeOrigin: true },
      '/health':      { target: 'http://localhost:8000', changeOrigin: true },
      '/ws':          { target: 'ws://localhost:8000',   ws: true },
    } : {},
  },

  // Production build optimizations
  build: {
    outDir: 'dist',
    sourcemap: false,           // disable in prod for smaller bundles
    minify: 'esbuild',
    rollupOptions: {
      output: {
        // Split vendor libraries into a separate chunk (better caching)
        manualChunks: {
          'vendor-react':  ['react', 'react-dom', 'react-router-dom'],
          'vendor-axios':  ['axios'],
        },
      },
    },
    chunkSizeWarningLimit: 800,
  },
}))
