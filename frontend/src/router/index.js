import { createRouter, createWebHistory } from 'vue-router'
import Chat from '../components/Chat.vue'
import MonitoringDashboard from '../components/MonitoringDashboard.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: Chat
  },
  {
    path: '/chat',
    name: 'chat',
    component: Chat
  },
  {
    path: '/monitoring',
    name: 'monitoring',
    component: MonitoringDashboard
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
