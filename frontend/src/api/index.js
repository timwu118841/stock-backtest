import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json'
  }
})

export default {
  // === 基本項目 API ===
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

  // === 回測功能 API ===
  
  // 執行回測
  runBacktest(params) {
    return apiClient.post('/backtest/run', params)
  },

  // 取得歷史回測紀錄
  getHistory(params) {
    return apiClient.get('/backtest/history', { params })
  },

  // 取得單一回測詳情
  getBacktestResult(id) {
    return apiClient.get(`/backtest/result/${id}`)
  },

  // 刪除回測紀錄
  deleteHistory(id) {
    return apiClient.delete(`/backtest/history/${id}`)
  },

  // === 策略比較與最佳化 API ===

  // 執行策略比較
  compareStrategies(strategyIds) {
    return apiClient.post('/strategy/compare', { ids: strategyIds })
  },

  // 執行參數最佳化
  optimizeStrategy(params) {
    return apiClient.post('/strategy/optimize', params)
  }
}
