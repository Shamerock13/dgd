import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        admin: resolve(__dirname, 'admin.html'),
        catalog: resolve(__dirname, 'catalog.html')
      }
    }
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: [
      'tower',
      '.ts.net'
    ],
    proxy: {
      '/api': {
        target: 'http://DGD-Dev-Backend:8080',
        changeOrigin: true
      },
      '/media': {
        target: 'http://DGD-Dev-Backend:8080',
        changeOrigin: true
      }
    }
  }
})
