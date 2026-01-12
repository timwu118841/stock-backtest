import { createRouter, createWebHistory } from 'vue-router'

const routes = [
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

router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title || '股票回測'} - Stock Backtester`
  next()
})

export default router
