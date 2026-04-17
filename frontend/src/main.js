// src/main.js
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css' // 引入样式
import * as ElementPlusIconsVue from '@element-plus/icons-vue' // 引入图标

import App from './App.vue'
import router from './router' // 确保路由文件存在
import './components/bi/styles.css' // 引入BI组件全局样式

// 开发环境下偶发的 ResizeObserver loop 报错会被 dev-server overlay 放大显示，
// 通常由 UI 组件（如 Element Plus 表格/布局）触发，不影响功能。这里仅屏蔽这一条特定报错，
// 避免干扰调试（不会吞掉其它真实错误）。
if (process.env.NODE_ENV === 'development') {
  const roLoopErrorRE = /ResizeObserver loop completed with undelivered notifications/i
  window.addEventListener(
    'error',
    (event) => {
      if (event?.message && roLoopErrorRE.test(event.message)) {
        event.stopImmediatePropagation()
      }
    },
    true
  )
}

const app = createApp(App)
const pinia = createPinia()

// 全局注册所有 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(pinia)
app.use(router)
app.use(ElementPlus)

app.mount('#app')