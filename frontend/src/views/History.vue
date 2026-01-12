<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

const searchQuery = ref('')
const filterStatus = ref('')
const historyData = ref([])
const isLoading = ref(false)

// 載入歷史紀錄
const fetchHistory = async () => {
  isLoading.value = true
  try {
    const response = await api.getHistory()
    historyData.value = response.data
  } catch (error) {
    ElMessage.error('載入歷史紀錄失敗')
  } finally {
    isLoading.value = false
  }
}

onMounted(fetchHistory)

const filteredHistory = computed(() => {
  return historyData.value.filter(item => {
    const matchQuery = item.strategy.includes(searchQuery.value) || item.stock.includes(searchQuery.value)
    const matchStatus = filterStatus.value ? item.status === filterStatus.value : true
    return matchQuery && matchStatus
  })
})

const detailsVisible = ref(false)
const selectedResult = ref(null)
const detailsCurrentPage = ref(1)
const detailsPageSize = ref(20)

const viewDetails = async (row) => {
  try {
    const response = await api.getBacktestResult(row.id)
    selectedResult.value = response.data
    detailsVisible.value = true
    detailsCurrentPage.value = 1  // 重置分頁
  } catch (error) {
    ElMessage.error('載入詳情失敗')
  }
}

const paginatedDetailTrades = computed(() => {
  if (!selectedResult.value || !selectedResult.value.trades) return []
  const start = (detailsCurrentPage.value - 1) * detailsPageSize.value
  const end = start + detailsPageSize.value
  return selectedResult.value.trades.slice(start, end)
})

const exportTradesCsv = () => {
  if (!selectedResult.value || !selectedResult.value.trades) return
  
  const headers = ['日期', '操作', '價格', '股數', '金額', '餘額', '總資產', '損益']
  const rows = selectedResult.value.trades.map(t => [
    t.date,
    t.action === 'BUY' ? '買入' : '賣出',
    t.price,
    t.shares,
    t.value,
    t.balance || 0,
    t.total_assets || 0,
    t.pnl || 0
  ])
  
  const csvContent = '\uFEFF' + [headers, ...rows].map(row => row.join(',')).join('\n') // Add BOM for Excel
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `${selectedResult.value.strategy_name}_trades_${selectedResult.value.start_date}.csv`
  link.click()
}

const deleteHistory = (row) => {
  ElMessageBox.confirm('確定要刪除這筆回測紀錄嗎？', '警告', {
    confirmButtonText: '確定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(async () => {
      try {
        await api.deleteHistory(row.id)
        historyData.value = historyData.value.filter(item => item.id !== row.id)
        ElMessage.success('刪除成功')
      } catch (error) {
        ElMessage.error('刪除失敗')
      }
    })
    .catch(() => {})
}

const exportCsv = () => {
  if (historyData.value.length === 0) {
    ElMessage.warning('沒有資料可匯出')
    return
  }
  
  // 簡易 CSV 匯出
  const headers = ['日期', '策略', '股票', '報酬率', '勝率', '狀態']
  const rows = historyData.value.map(item => [
    item.date, item.strategy, item.stock, item.return_pct + '%', item.win_rate + '%', item.status
  ])
  
  const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n')
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `backtest_history_${new Date().toISOString().slice(0,10)}.csv`
  link.click()
  
  ElMessage.success('匯出成功')
}

const getStatusType = (status) => {
  const map = { 'success': 'success', 'warning': 'warning', 'danger': 'danger' }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = { 'success': '獲利', 'warning': '平盤', 'danger': '虧損' }
  return map[status] || '未知'
}
</script>

<template>
  <div class="page-container history">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="section-title">回測歷史紀錄</span>
          <div class="header-actions">
            <el-input
              v-model="searchQuery"
              placeholder="搜尋策略或股票"
              prefix-icon="Search"
              class="search-input"
              clearable
            />
            <el-select v-model="filterStatus" placeholder="所有狀態" clearable class="status-select">
              <el-option label="獲利" value="success" />
              <el-option label="虧損" value="danger" />
              <el-option label="平盤" value="warning" />
            </el-select>
            <el-button @click="fetchHistory" :loading="isLoading">
              <el-icon><Refresh /></el-icon>
            </el-button>
            <el-button type="primary" @click="exportCsv" class="export-btn">
              <el-icon><Download /></el-icon>
              <span class="hidden-xs-only">匯出</span>
            </el-button>
          </div>
        </div>
      </template>

      <el-empty v-if="!isLoading && filteredHistory.length === 0" description="尚無回測紀錄" />

      <el-table v-else :data="filteredHistory" stripe style="width: 100%" v-loading="isLoading">
        <el-table-column prop="date" label="時間" min-width="150" sortable />
        <el-table-column prop="strategy" label="策略" min-width="140" />
        <el-table-column prop="stock" label="股票" width="120">
          <template #default="{ row }">
            <el-tag effect="plain">{{ row.stock }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="return_pct" label="報酬率" width="120" sortable>
          <template #default="{ row }">
            <span :class="row.return_pct >= 0 ? 'text-success' : 'text-danger'">
              {{ row.return_pct > 0 ? '+' : '' }}{{ row.return_pct }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="win_rate" label="勝率" width="100" sortable>
          <template #default="{ row }">{{ row.win_rate }}%</template>
        </el-table-column>
        <el-table-column prop="status" label="狀態" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="viewDetails(row)">
              詳情
            </el-button>
            <el-button link type="danger" size="small" @click="deleteHistory(row)">
              刪除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="filteredHistory.length > 0" class="pagination-container">
        <el-pagination
          background
          layout="prev, pager, next"
          :total="filteredHistory.length"
          :page-size="10"
          :pager-count="5"
        />
      </div>
    </el-card>

    <!-- 詳情對話框 -->
    <el-dialog v-model="detailsVisible" title="回測詳細結果" width="80%" destroy-on-close align-center>
      <div v-if="selectedResult" class="details-content">
        <!-- 績效摘要 -->
        <el-descriptions title="績效摘要" :column="3" border class="mb-4">
          <el-descriptions-item label="策略名稱">{{ selectedResult.strategy_name }}</el-descriptions-item>
          <el-descriptions-item label="股票代碼">
            <el-tag>{{ selectedResult.stock_symbol }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="回測期間">{{ selectedResult.start_date }} ~ {{ selectedResult.end_date }}</el-descriptions-item>
          
          <el-descriptions-item label="總報酬率">
            <span :class="selectedResult.summary.total_return >= 0 ? 'text-success' : 'text-danger'">
              {{ selectedResult.summary.total_return >= 0 ? '+' : '' }}{{ selectedResult.summary.total_return }}%
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="夏普比率">{{ selectedResult.summary.sharpe_ratio }}</el-descriptions-item>
          <el-descriptions-item label="最大回撤" class-name="text-danger">{{ selectedResult.summary.max_drawdown }}%</el-descriptions-item>
          
          <el-descriptions-item label="總投入成本">${{ Number(selectedResult.summary.total_cost || 0).toLocaleString() }}</el-descriptions-item>
          <el-descriptions-item label="初始資金">${{ Number(selectedResult.initial_capital).toLocaleString() }}</el-descriptions-item>
          <el-descriptions-item label="最終資金">${{ Number(selectedResult.final_capital).toLocaleString() }}</el-descriptions-item>
          <el-descriptions-item label="獲利/虧損筆數">
            <span class="text-success">{{ selectedResult.summary.profit_trades }}</span> / 
            <span class="text-danger">{{ selectedResult.summary.loss_trades }}</span>
          </el-descriptions-item>
        </el-descriptions>

        <!-- 交易明細 -->
        <div class="table-section">
          <div class="table-header">
            <h3 class="section-subtitle">交易明細 (共 {{ selectedResult.trades?.length || 0 }} 筆)</h3>
            <el-button type="primary" link @click="exportTradesCsv">
              <el-icon class="mr-1"><Download /></el-icon> 匯出 CSV
            </el-button>
          </div>
          <el-table :data="paginatedDetailTrades" stripe style="width: 100%" border>
            <el-table-column type="index" label="#" width="60" :index="(index) => (detailsCurrentPage - 1) * detailsPageSize + index + 1" />
            <el-table-column prop="date" label="日期" width="120" sortable />
            <el-table-column prop="action" label="操作" width="90">
              <template #default="{ row }">
                <el-tag 
                  v-if="row.action === 'HOLD'" 
                  type="info" 
                  size="small"
                >
                  期末
                </el-tag>
                <el-tag 
                  v-else
                  :type="row.action === 'BUY' ? 'success' : 'danger'" 
                  size="small"
                >
                  {{ row.action === 'BUY' ? '買入' : '賣出' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="price" label="價格" width="100">
               <template #default="{ row }">{{ row.price }}</template>
            </el-table-column>
            <el-table-column prop="shares" label="股數" width="90" />
            <el-table-column prop="value" label="金額" min-width="120">
              <template #default="{ row }">
                ${{ Number(row.value).toLocaleString() }}
              </template>
            </el-table-column>
            <el-table-column prop="balance" label="餘額" min-width="120">
              <template #default="{ row }">
                ${{ Number(row.balance).toLocaleString() }}
              </template>
            </el-table-column>
            <el-table-column prop="total_assets" label="總資產" min-width="120">
              <template #default="{ row }">
                ${{ Number(row.total_assets).toLocaleString() }}
              </template>
            </el-table-column>
            <el-table-column prop="pnl" label="損益" min-width="120">
              <template #default="{ row }">
                <span v-if="row.pnl !== null" :class="row.pnl >= 0 ? 'text-success' : 'text-danger'">
                  <template v-if="selectedResult.strategy_type === 'DCA'">
                    {{ row.pnl >= 0 ? '+' : '' }}{{ row.pnl }}%
                  </template>
                  <template v-else>
                    {{ row.pnl >= 0 ? '+' : '' }}${{ Number(row.pnl).toLocaleString() }}
                  </template>
                </span>
                <span v-else>-</span>
              </template>
            </el-table-column>
          </el-table>
          
          <!-- 分頁 -->
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="detailsCurrentPage"
              v-model:page-size="detailsPageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="selectedResult.trades?.length || 0"
              layout="total, sizes, prev, pager, next, jumper"
              background
            />
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.history {
  display: flex;
  flex-direction: column;
}

.section-title {
  font-weight: 600;
  font-size: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.header-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  flex: 1;
  justify-content: flex-end;
}

.search-input { width: 200px; }
.status-select { width: 110px; }

@media (max-width: 576px) {
  .card-header { flex-direction: column; align-items: stretch; }
  .header-actions { justify-content: space-between; }
  .search-input { width: 100%; order: 3; }
  .status-select { flex: 1; }
}

.text-success { color: #67c23a; font-weight: 600; }
.text-danger { color: #f56c6c; font-weight: 600; }

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 24px;
}

@media (max-width: 768px) {
  .pagination-container { justify-content: center; }
  .hidden-xs-only { display: none; }
}

.mb-4 { margin-bottom: 16px; }
.mr-1 { margin-right: 4px; }
.section-subtitle { margin: 0; font-size: 15px; font-weight: 600; color: var(--el-text-color-primary); }
.table-header { display: flex; justify-content: space-between; align-items: center; margin: 16px 0 12px; }
.pagination-container {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}
</style>
