<script setup>
import { ref } from 'vue'

const stats = ref([
  { title: '總回測次數', value: '128', icon: 'Document', color: '#409eff', bg: 'rgba(64, 158, 255, 0.1)' },
  { title: '獲利策略', value: '89', icon: 'TrendCharts', color: '#67c23a', bg: 'rgba(103, 194, 58, 0.1)' },
  { title: '平均報酬率', value: '+15.8%', icon: 'Coin', color: '#e6a23c', bg: 'rgba(230, 162, 60, 0.1)' },
  { title: '最佳策略', value: 'MA交叉', icon: 'Trophy', color: '#f56c6c', bg: 'rgba(245, 108, 108, 0.1)' }
])

const recentBacktests = ref([
  { id: 1, name: '雙均線策略', stock: '2330.TW 台積電', return: '+18.5%', date: '2024-01-10', status: 'success' },
  { id: 2, name: 'RSI 超賣反彈', stock: 'AAPL 蘋果', return: '+12.3%', date: '2024-01-09', status: 'success' },
  { id: 3, name: 'MACD 交叉', stock: '2317.TW 鴻海', return: '-3.2%', date: '2024-01-08', status: 'danger' },
  { id: 4, name: '布林通道突破', stock: 'NVDA 輝達', return: '+25.1%', date: '2024-01-07', status: 'success' }
])
</script>

<template>
  <div class="page-container dashboard">
    <!-- 統計卡片 -->
    <div class="stats-grid">
      <el-card 
        v-for="stat in stats" 
        :key="stat.title" 
        class="stat-card" 
        shadow="hover"
      >
        <div class="stat-content">
          <div class="stat-info">
            <span class="stat-title">{{ stat.title }}</span>
            <span class="stat-value">{{ stat.value }}</span>
          </div>
          <div class="stat-icon" :style="{ color: stat.color, backgroundColor: stat.bg }">
            <el-icon size="24"><component :is="stat.icon" /></el-icon>
          </div>
        </div>
      </el-card>
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
      <el-table :data="recentBacktests" style="width: 100%" class="hidden-xs-only">
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
      <div class="mobile-list hidden-sm-and-up">
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
  gap: 24px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
}

.stat-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stat-title {
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  font-family: 'Roboto Mono', monospace;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.3s;
}

.stat-card:hover .stat-icon {
  transform: scale(1.1);
}

.section-title {
  font-size: 16px;
  font-weight: 600;
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
  padding: 20px;
  justify-content: center;
  flex-direction: column;
  gap: 8px;
}

/* Mobile List Styles */
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
  
  .stat-value {
    font-size: 20px;
  }
  
  .action-btn {
    padding: 12px;
  }
}

.mobile-item {
  padding: 12px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.mobile-item:last-child {
  border-bottom: none;
}

.mobile-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.mobile-item-title {
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.mobile-item-sub {
  color: var(--el-text-color-secondary);
  font-size: 13px;
  margin-bottom: 8px;
}

.mobile-item-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.mobile-item-date {
  color: var(--el-text-color-placeholder);
  font-size: 12px;
}
</style>
