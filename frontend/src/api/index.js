import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  headers: {
    'Content-Type': 'application/json'
  },
  withCredentials: true
})

apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      const currentPath = window.location.pathname
      if (currentPath !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default {
  getItems() {
    return apiClient.get('/items')
  },
  
  getItem(id) {
    return apiClient.get(`/items/${id}`)
  },
  
  createItem(item) {
    return apiClient.post('/items', item)
  },
  
  deleteItem(id) {
    return apiClient.delete(`/items/${id}`)
  },
  
  healthCheck() {
    return apiClient.get('/health')
  },

  runBacktest(params) {
    return apiClient.post('/backtest/run', params)
  },

  getHistory(params) {
    return apiClient.get('/backtest/history', { params })
  },

  getBacktestResult(id) {
    return apiClient.get(`/backtest/result/${id}`)
  },

  deleteHistory(id) {
    return apiClient.delete(`/backtest/history/${id}`)
  },

  compareStrategies(strategyIds) {
    return apiClient.post('/strategy/compare', { ids: strategyIds })
  },

  optimizeStrategy(params) {
    return apiClient.post('/strategy/optimize', params)
  },

  checkAuth() {
    return apiClient.get('/auth/check')
  },

  getMe() {
    return apiClient.get('/auth/me')
  },

  logout() {
    return apiClient.post('/auth/logout')
  }
}
