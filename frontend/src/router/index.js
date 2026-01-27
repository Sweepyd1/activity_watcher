import { createRouter, createWebHistory } from 'vue-router'

import AuthView from '@/views/AuthView.vue'
import ProfileView from '@/views/ProfileView.vue'
import StatisticsView from '@/views/StatisticsView.vue'
import Main from '@/views/Main.vue'
const routes = [
  {
    path: '/',
    name: "Main",
     component: Main
  },
  {
    path: '/auth',
    name: 'Auth',
    component: AuthView
  },
  {
    path: '/profile',
    name: 'Profile',
    component: ProfileView
  },
  {
    path: '/statistics',
    name: 'Statistics',
    component: StatisticsView
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router