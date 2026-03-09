import { createApp } from 'vue'
import { createPinia } from 'pinia'
// 1. 引入 Element Plus 核心库
import ElementPlus from 'element-plus'
// 2. 引入 Element Plus 样式
import 'element-plus/dist/index.css'

import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(createPinia())
app.use(router)
// 3. 注册 Element Plus
app.use(ElementPlus)

app.mount('#app')