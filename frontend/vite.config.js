import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit()],
  css: {
    codeSplit: false,
  },
  build: {
    cssCodeSplit: false,
    rollupOptions: {
      output: {
        assetFileNames: (assetInfo) => {
          if (assetInfo.name === 'app.css' || assetInfo.name.endsWith('.css') && !assetInfo.name.includes('.')) {
            return '_app/immutable/assets/app.css';
          }
          return '_app/immutable/assets/[name].[hash][extname]';
        },
      },
    },
  },
  server: {
    port: 2025,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/uploads': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
