import { createRouter, createWebHistory } from 'vue-router'
import ChatView from '@/views/Chat.vue'
import BIWorkbench from '@/views/BIWorkbench.vue'
import Dashboard from '@/views/Dashboard.vue'

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
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router