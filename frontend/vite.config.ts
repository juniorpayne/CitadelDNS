import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 56159,
    host: '0.0.0.0',
    cors: true,
  },
});
