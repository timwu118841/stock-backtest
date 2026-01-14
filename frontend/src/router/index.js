import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { title: '登入', public: true }
  },
  {
    path: '/auth/callback',
    name: 'AuthCallback',
    component: () => import('../views/AuthCallback.vue'),
    meta: { title: '登入中...', public: true }
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue'),
    meta: { title: '主控台' }
  },
  {
    path: '/backtest',
    name: 'Backtest',
    component: () => import('../views/Backtest.vue'),
    meta: { title: '策略回測' }
  },
  {
    path: '/compare',
    name: 'Compare',
    component: () => import('../views/Compare.vue'),
    meta: { title: '策略比較' }
  },
  {
    path: '/optimize',
    name: 'Optimize',
    component: () => import('../views/Optimize.vue'),
    meta: { title: '參數最佳化' }
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('../views/History.vue'),
    meta: { title: '歷史紀錄' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

let authChecked = false

router.beforeEach(async (to, from, next) => {
  document.title = `${to.meta.title || '股票回測'} - Stock Backtester`

  if (to.meta.public) {
    next()
    return
  }

  const { isAuthenticated, checkAuth } = useAuth()

  if (!authChecked) {
    await checkAuth()
    authChecked = true
  }

  if (!isAuthenticated.value) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else {
    next()
  }
})

export default router
