import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/store/user'

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/Login.vue')
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/pages/Register.vue')
  },
  {
    path: '/home',
    name: 'Home',
    component: () => import('@/pages/Home.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/contests',
    name: 'Contests',
    component: () => import('@/pages/Contests.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/contests/:id',
    name: 'ContestDetail',
    component: () => import('@/pages/ContestDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/ai-extract',
    name: 'AIExtract',
    component: () => import('@/pages/AIExtract.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next('/login')
  } else {
    next()
  }
})

export default router

