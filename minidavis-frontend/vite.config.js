import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Vite dev proxy workaround: proxies API calls to FastAPI running on port 8000.
    // If VITE_API_URL is set to empty string (""), fetch requests use relative paths and route through this proxy.
    proxy: {
      '/health': 'http://localhost:8000',
      '/state': 'http://localhost:8000',
      '/reset': 'http://localhost:8000',
      '/step': 'http://localhost:8000',
    },
  },
});
