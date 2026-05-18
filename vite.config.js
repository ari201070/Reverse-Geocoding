import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    strictPort: false,
    // Allow overriding HMR host/protocol via env for tunnel compatibility
    hmr: {
      protocol: process.env.VITE_HMR_PROTOCOL || 'ws',
      host: process.env.VITE_HMR_HOST || 'localhost',
    },
    proxy: {
      '/api': {
        target: 'http://localhost:3000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api'),
      },
    },
  },
});
