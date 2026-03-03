import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    strictPort: false,
    hmr: {
      protocol: 'ws',
      host: 'localhost',
    },
  },
});
