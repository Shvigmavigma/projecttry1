import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: () => import('@/views/Login.vue') },
  { path: '/register', component: () => import('@/views/Register.vue') },
  { path: '/main', component: () => import('@/views/MainMenu.vue'), meta: { requiresAuth: true } },
  { path: '/users', component: () => import('@/views/AllUsers.vue'), meta: { requiresAuth: true } },
  { path: '/user/:id', component: () => import('@/views/UserDetails.vue'), meta: { requiresAuth: true } },
  { path: '/profile', component: () => import('@/views/Profile.vue'), meta: { requiresAuth: true } },
  { path: '/profile/edit', component: () => import('@/views/ProfileEdit.vue'), meta: { requiresAuth: true } },
  { path: '/my-projects', component: () => import('@/views/UserProjects.vue'), meta: { requiresAuth: true } },
  { path: '/projects', component: () => import('@/views/AllProjects.vue'), meta: { requiresAuth: true } },
  { path: '/project/new', component: () => import('@/views/ProjectEdit.vue'), meta: { requiresAuth: true } },
  { path: '/project/edit/:id', component: () => import('@/views/ProjectEdit.vue'), meta: { requiresAuth: true } }, 
  { path: '/project/:projectId/task/:taskIndex', component: () => import('@/views/TaskDetails.vue'), meta: { requiresAuth: true } },
  { path: '/project/:id', component: () => import('@/views/ProjectDetails.vue'), meta: { requiresAuth: true } },
  { path: '/project/:projectId/task/:taskIndex/edit', component: () => import('@/views/TaskEdit.vue'), meta: { requiresAuth: true } },

]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from) => {
  const authStore = useAuthStore()
  authStore.loadUserFromStorage()
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return '/login'
  }
  return true
})

export default router