import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://backend:5050',
        changeOrigin: true
      },
      '/uploads': {
        target: 'http://backend:5050',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    minify: 'terser',
    // 关键：不设置 manualChunks，避免循环依赖
    rollupOptions: {
      output: {
        // 让 Vite 自动处理分块
        manualChunks: undefined
      }
    }
  }
})