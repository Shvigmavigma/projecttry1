import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth' // <-- импортируем хранилище

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: () => import('@/views/Login.vue') },
  { path: '/register', component: () => import('@/views/Register.vue') },
  { path: '/main', component: () => import('@/views/MainMenu.vue'), meta: { requiresAuth: true } },
  { path: '/my-projects', component: () => import('@/views/UserProjects.vue'), meta: { requiresAuth: true } },
  { path: '/users', component: () => import('@/views/AllUsers.vue'), meta: { requiresAuth: true } },
  { path: '/projects', component: () => import('@/views/AllProjects.vue'), meta: { requiresAuth: true } },
  { path: '/profile', component: () => import('@/views/Profile.vue'), meta: { requiresAuth: true } },
  { path: '/project/new', component: () => import('@/views/ProjectEdit.vue'), meta: { requiresAuth: true } },
  { path: '/project/edit/:id', component: () => import('@/views/ProjectEdit.vue'), meta: { requiresAuth: true } }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Защита маршрутов: если требуется авторизация, а пользователь не залогинен – редирект на логин
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  authStore.loadUserFromStorage() // восстанавливаем пользователя из localStorage
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else {
    next()
  }
})

export default router