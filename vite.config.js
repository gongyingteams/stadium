import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// 后端服务地址 (开发态 Vite 反向代理目标；生产态由 Nginx location /api/ 反代)
const BACKEND_TARGET = process.env.VITE_BACKEND_TARGET || 'http://127.0.0.1:8000'

// 开发态同源代理: 前端一律请求相对路径 /api，由 dev-server 转发到后端。
// 这样无论用 localhost 还是局域网 IP 打开页面，浏览器访问的都是"当前站点同源"的 /api，
// 不再出现"其它电脑去请求自己电脑的 localhost:8000"导致配置/Logo 拉取失败的问题。
const proxy = {
  '/api': {
    target: BACKEND_TARGET,
    changeOrigin: true,
    ws: true
  },
  '/uploads': {
    target: BACKEND_TARGET,
    changeOrigin: true
  }
}

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  server: {
    port: 3001,
    open: false,
    host: '0.0.0.0',
    proxy
  },
  preview: {
    port: 3001,
    open: false,
    host: '0.0.0.0',
    proxy
  }
})
