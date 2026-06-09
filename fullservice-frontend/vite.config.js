import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vuetify from 'vite-plugin-vuetify'
import { fileURLToPath, URL } from 'node:url'

// Vite konfigürasyonu:
//  • dev: http://localhost:5173 üzerinde HMR'lı çalışır; /api/* istekleri
//    backend'in çalıştığı 8770'e proxy'lenir, böylece CORS dert olmaz.
//  • build: `dist/` üretir; backend bunu kardeş klasörden statik servis eder
//    (bkz. fullservice-backend/common/config.py → DASHBOARD_DIR).
export default defineConfig({
  base: './',
  plugins: [
    vue(),
    vuetify({ autoImport: true }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8770',
        changeOrigin: true,
      },
    },
  },
})
