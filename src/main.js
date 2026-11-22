import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import SvgIcon from '@/components/SvgIcon.vue'
import './styles/themes.css'
import './styles/index.css'

const app = createApp(App)

// 全局注册 Element Plus 官方矢量图标库
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

// 全局注册手绘纯矢量 SVG 图标组件
app.component('SvgIcon', SvgIcon)

app.mount('#app')

