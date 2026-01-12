<script setup>
import { ref, onMounted, nextTick, watch, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { useTheme } from '../composables/useTheme'
import api from '../api'

const { isDark } = useTheme()

// 從後端載入的策略列表
const strategies = ref([])
const selectedStrategyIds = ref([])
const compareChartRef = ref(null)
const isLoading = ref(false)
const isComparing = ref(false)
const showResult = ref(false)
const comparisonData = ref(null)
let chartInstance = null

// 載入歷史回測紀錄作為可選策略
const fetchStrategies = async () => {
  isLoading.value = true
  try {
    const response = await api.getHistory()
    strategies.value = response.data.map(item => ({
      id: item.id,
      name: item.strategy,
      stock: item.stock,
      return: item.return_pct
    }))
  } catch (error) {
    ElMessage.error('載入策略列表失敗')
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  fetchStrategies()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})

const handleResize = () => chartInstance?.resize()

watch(isDark, () => {
  if (showResult.value) nextTick(renderChart)
})

// 執行比較
const runCompare = async () => {
  if (selectedStrategyIds.value.length < 2) {
    ElMessage.warning('請至少選擇兩個策略進行比較')
    return
  }

  isComparing.value = true

  try {
    const response = await api.compareStrategies(selectedStrategyIds.value)
    comparisonData.value = response.data
    showResult.value = true
    ElMessage.success('比較完成')
    
    await nextTick()
    renderChart()

  } catch (error) {
    ElMessage.error('比較失敗: ' + (error.response?.data?.detail || error.message))
  } finally {
    isComparing.value = false
  }
}

const renderChart = () => {
  if (!compareChartRef.value || !comparisonData.value) return

  const theme = isDark.value ? 'dark' : undefined
  if (chartInstance) chartInstance.dispose()
  chartInstance = echarts.init(compareChartRef.value, theme)
  
  const { dates, series } = comparisonData.value.equityCurves
  
  // 轉換為百分比變化
  const seriesData = series.map(s => {
    const initial = s.data[0] || 1
    return {
      name: s.name,
      type: 'line',
      data: s.data.map(v => (((v - initial) / initial) * 100).toFixed(2)),
      smooth: true,
      showSymbol: false,
      lineStyle: { width: 2 }
    }
  })

  chartInstance.setOption({
    backgroundColor: 'transparent',
    title: { text: '累積報酬率比較 (%)', left: 'center' },
    tooltip: { trigger: 'axis' },
    legend: { bottom: 0, type: 'scroll' },
    grid: { left: '3%', right: '4%', bottom: '15%', top: '15%', containLabel: true },
    xAxis: { type: 'category', data: dates, boundaryGap: false },
    yAxis: { type: 'value', axisLabel: { formatter: '{value}%' } },
    series: seriesData
  })
}

const getWinRateColor = (rate) => {
  if (rate >= 60) return 'success'
  if (rate >= 50) return 'warning'
  return 'danger'
}
</script>

<template>
  <div class="page-container compare">
    <el-card shadow="hover" class="selection-card">
      <template #header>
        <div class="card-header">
          <span class="section-title">選擇比較策略</span>
          <div class="header-actions">
            <el-button @click="fetchStrategies" :loading="isLoading">
              <el-icon><Refresh /></el-icon>
            </el-button>
            <el-button type="primary" @click="runCompare" :loading="isComparing" :disabled="selectedStrategyIds.length < 2">
              <el-icon><Histogram /></el-icon>
              <span class="hidden-xs-only">開始比較</span>
            </el-button>
          </div>
        </div>
      </template>

      <el-empty v-if="strategies.length === 0 && !isLoading" description="尚無回測紀錄，請先執行回測" />

      <el-select
        v-else
        v-model="selectedStrategyIds"
        multiple
        collapse-tags
        collapse-tags-tooltip
        placeholder="請選擇策略（可多選）"
        style="width: 100%"
        size="large"
        :loading="isLoading"
      >
        <el-option
          v-for="item in strategies"
          :key="item.id"
          :label="item.name"
          :value="item.id"
        >
          <div class="strategy-option">
            <span>{{ item.name }} ({{ item.stock }})</span>
            <span :class="item.return >= 0 ? 'text-success' : 'text-danger'">
              {{ item.return > 0 ? '+' : '' }}{{ item.return }}%
            </span>
          </div>
        </el-option>
      </el-select>
    </el-card>

    <div v-if="showResult && comparisonData" class="results-container">
      <!-- 績效比較表 -->
      <el-card shadow="hover">
        <template #header>
          <span class="section-title">績效指標對比</span>
        </template>
        <el-table :data="comparisonData.metrics" style="width: 100%" stripe>
          <el-table-column prop="name" label="策略名稱" min-width="150" fixed />
          <el-table-column prop="totalReturn" label="總報酬率" min-width="100" sortable>
            <template #default="{ row }">
              <span :class="row.totalReturn >= 0 ? 'text-success' : 'text-danger'">
                {{ row.totalReturn > 0 ? '+' : '' }}{{ row.totalReturn }}%
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="annualizedReturn" label="年化報酬" min-width="100" sortable>
             <template #default="{ row }">{{ row.annualizedReturn }}%</template>
          </el-table-column>
          <el-table-column prop="sharpeRatio" label="夏普值" min-width="90" sortable />
          <el-table-column prop="maxDrawdown" label="最大回撤" min-width="100" sortable>
            <template #default="{ row }">
              <span class="text-danger">{{ row.maxDrawdown }}%</span>
            </template>
          </el-table-column>
          <el-table-column prop="winRate" label="勝率" min-width="90" sortable>
            <template #default="{ row }">
              <el-tag :type="getWinRateColor(row.winRate)" size="small">{{ row.winRate }}%</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 曲線比較圖 -->
      <el-card shadow="hover" class="chart-card">
        <div ref="compareChartRef" class="chart-container"></div>
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.compare {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.section-title {
  font-weight: 600;
  font-size: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.strategy-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.chart-container {
  width: 100%;
  height: 500px;
}

@media (max-width: 768px) {
  .chart-container { height: 350px; }
  .hidden-xs-only { display: none; }
}

.text-success { color: #67c23a; font-weight: 600; }
.text-danger { color: #f56c6c; font-weight: 600; }
</style>
