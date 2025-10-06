import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    strictPort: true, // 端口被占用时报错，不自动切换
    host: true, // 监听所有地址
    proxy: {
      // API代理 - 可选配置，如果使用CORS则不需要
      '/api': {
        target: 'http://127.0.0.1:9090',
        changeOrigin: true,
      },
      // 静态文件代理 - 用于背景图片等资源
      '/static': {
        target: 'http://127.0.0.1:9090',
        changeOrigin: true,
      },
    },
  },
})
