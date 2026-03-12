import { createRouter, createWebHistory } from 'vue-router'
// 【关键修改】这里必须引入 Chat.vue，绝对不能是 Upload.vue
import ChatView from '@/views/Chat.vue'

const routes = [
  {
    path: '/',
    name: 'Chat',
    component: ChatView
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router