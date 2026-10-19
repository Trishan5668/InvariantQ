import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    allowedHosts: true,
    proxy: {
      '/api': {
        target: process.env.INVARIANTQ_API_TARGET || 'http://127.0.0.1:8000',
        changeOrigin: true,
        configure: (proxy) => {
          proxy.on('error', (error, _request, response) => {
            console.error(`[vite] backend proxy error: ${error.message}`);
            if (response && !response.headersSent) {
              const payload = JSON.stringify({
                status: 'error',
                message: 'InvariantQ backend is unavailable. Start the Python server on port 8000.',
              });
              response.writeHead(503, {
                'Content-Type': 'application/json; charset=utf-8',
                'Content-Length': Buffer.byteLength(payload),
              });
              response.end(payload);
            }
          });
        },
      },
    },
  },
});
