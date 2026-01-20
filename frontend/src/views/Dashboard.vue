<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'

const loading = ref(true)
const stats = ref([
  { title: '總回測次數', value: '-', icon: 'Document', gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', iconBg: 'rgba(102, 126, 234, 0.15)' },
  { title: '獲利策略', value: '-', icon: 'TrendCharts', gradient: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)', iconBg: 'rgba(17, 153, 142, 0.15)' },
  { title: '平均報酬率', value: '-', icon: 'Coin', gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', iconBg: 'rgba(240, 147, 251, 0.15)' },
  { title: '最佳策略', value: '-', icon: 'Trophy', gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', iconBg: 'rgba(79, 172, 254, 0.15)' }
])

const recentBacktests = ref([])

const strategyNameMap = {
  MA_CROSS: 'MA交叉',
  RSI: 'RSI',
  MACD: 'MACD',
  BOLLINGER: '布林通道',
  DCA: '定期定額',
  SMA_BREAKOUT: 'SMA突破'
}

const fetchDashboard = async () => {
  try {
    loading.value = true
    const response = await api.getDashboard()
    const data = response.data

    stats.value[0].value = String(data.stats.total_backtests)
    stats.value[1].value = String(data.stats.profitable_backtests)
    stats.value[2].value = data.stats.avg_return >= 0 
      ? `+${data.stats.avg_return}%` 
      : `${data.stats.avg_return}%`
    stats.value[3].value = data.stats.best_strategy 
      ? strategyNameMap[data.stats.best_strategy] || data.stats.best_strategy
      : '-'

    recentBacktests.value = data.recent_backtests.map(item => ({
      id: item.id,
      name: item.name,
      stock: item.stock,
      return: item.return_pct,
      date: item.date,
      status: item.status
    }))
  } catch (error) {
    console.error('Failed to fetch dashboard data:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchDashboard()
})
</script>

<template>
  <div class="page-container dashboard">
    <!-- 統計卡片 -->
    <div class="stats-grid">
      <div 
        v-for="(stat, index) in stats" 
        :key="stat.title" 
        class="stat-card"
        :style="{ '--card-index': index }"
      >
        <div class="stat-card-inner">
          <div class="stat-gradient" :style="{ background: stat.gradient }"></div>
          <div class="stat-content">
            <div class="stat-info">
              <span class="stat-title">{{ stat.title }}</span>
              <span class="stat-value">{{ stat.value }}</span>
            </div>
            <div class="stat-icon" :style="{ background: stat.iconBg }">
              <el-icon size="28"><component :is="stat.icon" /></el-icon>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 快速操作 -->
    <el-card class="section-card quick-actions" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="section-title">快速操作</span>
        </div>
      </template>
      <div class="action-buttons">
        <el-button type="primary" size="large" class="action-btn" @click="$router.push('/backtest')">
          <el-icon><Plus /></el-icon>
          新增回測
        </el-button>
        <el-button size="large" class="action-btn" @click="$router.push('/compare')">
          <el-icon><Histogram /></el-icon>
          策略比較
        </el-button>
        <el-button size="large" class="action-btn" @click="$router.push('/optimize')">
          <el-icon><Setting /></el-icon>
          參數最佳化
        </el-button>
      </div>
    </el-card>

    <!-- 最近回測 -->
    <el-card class="section-card recent-tests" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="section-title">最近回測紀錄</span>
          <el-button text type="primary" @click="$router.push('/history')">
            查看全部
            <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </template>
      
      <!-- 桌面版表格 -->
      <el-table :data="recentBacktests" style="width: 100%" class="hidden-xs-only" v-loading="loading">
        <template #empty>
          <el-empty description="尚無回測紀錄" :image-size="80" />
        </template>
        <el-table-column prop="name" label="策略名稱" min-width="140" />
        <el-table-column prop="stock" label="股票" min-width="140" />
        <el-table-column prop="return" label="報酬率" min-width="100">
          <template #default="{ row }">
            <el-tag :type="row.status" effect="light" round>
              {{ row.return }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="date" label="日期" min-width="120" />
        <el-table-column label="操作" width="140" align="right">
          <template #default>
            <el-button text type="primary" size="small">查看</el-button>
            <el-button text type="primary" size="small">重跑</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 手機版列表 (使用 div 模擬) -->
      <div class="mobile-list hidden-sm-and-up" v-loading="loading">
        <el-empty v-if="!loading && recentBacktests.length === 0" description="尚無回測紀錄" :image-size="80" />
        <div v-for="item in recentBacktests" :key="item.id" class="mobile-item">
          <div class="mobile-item-header">
            <span class="mobile-item-title">{{ item.name }}</span>
            <el-tag :type="item.status" effect="light" size="small" round>{{ item.return }}</el-tag>
          </div>
          <div class="mobile-item-sub">{{ item.stock }}</div>
          <div class="mobile-item-footer">
            <span class="mobile-item-date">{{ item.date }}</span>
            <div class="mobile-item-actions">
              <el-button link type="primary" size="small">查看</el-button>
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 20px;
}

.stat-card {
  position: relative;
  border-radius: var(--border-radius-lg, 12px);
  overflow: hidden;
  background: var(--app-sidebar-bg, #fff);
  box-shadow: var(--shadow-md);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  animation: fadeInUp 0.5s ease forwards;
  animation-delay: calc(var(--card-index) * 0.1s);
  opacity: 0;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-xl);
}

.stat-card-inner {
  position: relative;
}

.stat-gradient {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  opacity: 0.9;
}

.stat-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stat-title {
  color: var(--app-text-secondary, #606266);
  font-size: 14px;
  font-weight: 500;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--app-text-color);
  font-family: 'Roboto Mono', 'SF Mono', monospace;
  letter-spacing: -0.5px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--app-text-color);
  transition: transform 0.3s ease;
}

.stat-card:hover .stat-icon {
  transform: scale(1.1) rotate(5deg);
}

html.dark .stat-card {
  background: rgba(24, 24, 27, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(12px);
}

html.dark .stat-card:hover {
  border-color: rgba(255, 255, 255, 0.15);
}

.section-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--app-text-color);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.action-buttons {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.action-btn {
  flex: 1;
  min-width: 140px;
  height: auto;
  padding: 24px 20px;
  justify-content: center;
  flex-direction: column;
  gap: 10px;
  border-radius: var(--border-radius-lg, 12px);
  font-weight: 500;
  transition: all 0.25s ease;
}

.action-btn:hover {
  transform: translateY(-2px);
}

.hidden-xs-only {
  display: table;
}

.hidden-sm-and-up {
  display: none;
}

@media (max-width: 768px) {
  .hidden-xs-only {
    display: none;
  }
  
  .hidden-sm-and-up {
    display: block;
  }
  
  .stats-grid {
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }
  
  .stat-content {
    padding: 16px;
    flex-direction: column-reverse;
    align-items: flex-start;
    gap: 12px;
  }
  
  .stat-icon {
    width: 44px;
    height: 44px;
    border-radius: 12px;
  }
  
  .stat-value {
    font-size: 24px;
  }
  
  .action-btn {
    padding: 16px;
  }
}

.mobile-item {
  padding: 16px 0;
  border-bottom: 1px solid var(--app-border-color);
  transition: background-color 0.2s;
}

.mobile-item:last-child {
  border-bottom: none;
}

.mobile-item:hover {
  background-color: var(--fintech-blue-light, rgba(59, 130, 246, 0.05));
}

.mobile-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.mobile-item-title {
  font-weight: 600;
  color: var(--app-text-color);
}

.mobile-item-sub {
  color: var(--app-text-secondary, #606266);
  font-size: 13px;
  margin-bottom: 10px;
}

.mobile-item-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.mobile-item-date {
  color: var(--app-text-secondary);
  font-size: 12px;
}
</style>
