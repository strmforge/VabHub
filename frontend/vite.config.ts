import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vuetify from 'vite-plugin-vuetify'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [
    vue(),
    vuetify({ autoImport: true })
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    host: '0.0.0.0', // 允许所有网络接口访问
    port: 5173,
    strictPort: false, // 如果端口被占用，自动尝试下一个端口
    proxy: {
      '/api': {
        target: 'http://localhost:8092',
        changeOrigin: true
      },
      // 代理静态资源目录（站点Logo）
      '/assets': {
        target: 'http://localhost:8092',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/assets/, '/static/assets')
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          'vue-vendor': ['vue', 'vue-router', 'pinia'],
          'vuetify-vendor': ['vuetify'],
          'chart-vendor': ['apexcharts', 'vue3-apexcharts']
        }
      }
    }
  }
})

