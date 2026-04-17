import { createRouter, createWebHistory } from 'vue-router'
import ChatView from '@/views/Chat.vue'
import BIWorkbench from '@/views/BIWorkbench.vue'

const routes = [
  {
    path: '/',
    name: 'BIWorkbench',
    component: BIWorkbench
  },
  {
    path: '/chat',
    name: 'Chat',
    component: ChatView
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router