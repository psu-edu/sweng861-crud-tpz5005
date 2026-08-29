import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    strictPort: true,
    proxy: {
      // Forwards to fix non-fatal console errors
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,

      },
      '/health': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    }
  },
});