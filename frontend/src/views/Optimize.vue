<script setup>
import { ref, reactive, nextTick, watch, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { useTheme } from '../composables/useTheme'
import api from '../api'

const { isDark } = useTheme()

const form = reactive({
  strategy: 'MA_CROSS',
  stock: '2330.TW',
  startDate: '',
  endDate: '',
  param1Range: [5, 30],
  param1Step: 5,
  param2Range: [20, 60],
  param2Step: 10
})

const strategies = [
  { label: '雙均線交叉 (MA Cross)', value: 'MA_CROSS' }
]

const stockOptions = [
  { label: '2330.TW 台積電', value: '2330.TW' },
  { label: 'AAPL 蘋果', value: 'AAPL' },
  { label: 'NVDA 輝達', value: 'NVDA' }
]

const isRunning = ref(false)
const showResult = ref(false)
const heatmapChartRef = ref(null)
const optimizeResult = ref(null)
let chartInstance = null

const handleResize = () => chartInstance?.resize()
onMounted(() => window.addEventListener('resize', handleResize))
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})

watch(isDark, () => {
  if (showResult.value) nextTick(renderHeatmap)
})

// 執行最佳化
const runOptimization = async () => {
  if (!form.startDate || !form.endDate) {
    ElMessage.warning('請選擇回測日期範圍')
    return
  }

  isRunning.value = true
  showResult.value = false

  try {
    const payload = {
      strategy_type: form.strategy,
      stock_symbol: form.stock,
      start_date: form.startDate,
      end_date: form.endDate,
      param1_range: form.param1Range,
      param1_step: form.param1Step,
      param2_range: form.param2Range,
      param2_step: form.param2Step
    }

    const response = await api.optimizeStrategy(payload)
    optimizeResult.value = response.data
    showResult.value = true
    ElMessage.success('最佳化完成')
    
    await nextTick()
    renderHeatmap()

  } catch (error) {
    ElMessage.error('最佳化失敗: ' + (error.response?.data?.detail || error.message))
  } finally {
    isRunning.value = false
  }
}

const renderHeatmap = () => {
  if (!heatmapChartRef.value || !optimizeResult.value) return

  const theme = isDark.value ? 'dark' : undefined
  const textColor = isDark.value ? '#ccc' : '#333'

  if (chartInstance) chartInstance.dispose()
  chartInstance = echarts.init(heatmapChartRef.value, theme)
  
  const { heatmap_data, x_labels, y_labels } = optimizeResult.value

  chartInstance.setOption({
    backgroundColor: 'transparent',
    title: { text: '參數報酬率熱力圖 (%)', left: 'center', textStyle: { color: textColor } },
    tooltip: {
      position: 'top',
      formatter: (p) => {
        if (p.value[2] === null) return '無效組合'
        return `短週期: ${x_labels[p.value[0]]}<br/>長週期: ${y_labels[p.value[1]]}<br/>報酬率: ${p.value[2]}%`
      }
    },
    grid: { height: '70%', top: '15%', containLabel: true },
    xAxis: {
      type: 'category',
      data: x_labels,
      name: '短週期參數',
      nameLocation: 'middle',
      nameGap: 30,
      splitArea: { show: true }
    },
    yAxis: {
      type: 'category',
      data: y_labels,
      name: '長週期參數',
      nameLocation: 'middle',
      nameGap: 30,
      splitArea: { show: true }
    },
    visualMap: {
      min: -20,
      max: 50,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: '0%',
      textStyle: { color: textColor },
      inRange: {
        color: ['#f56c6c', '#e6a23c', '#f0f9eb', '#67c23a']
      }
    },
    series: [{
      name: '報酬率',
      type: 'heatmap',
      data: heatmap_data.filter(d => d[2] !== null),
      label: { show: true, fontSize: 10 },
      emphasis: {
        itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0, 0, 0, 0.5)' }
      }
    }]
  })
}
</script>

<template>
  <div class="page-container optimize">
    <!-- 設定面板 -->
    <el-card shadow="hover" class="config-card">
      <template #header>
        <div class="card-header">
          <span class="section-title">參數最佳化設定 (Grid Search)</span>
        </div>
      </template>
      
      <el-form :model="form" label-position="top">
        <el-row :gutter="24">
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="選擇策略">
              <el-select v-model="form.strategy" style="width: 100%">
                <el-option v-for="s in strategies" :key="s.value" :label="s.label" :value="s.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="股票代碼">
              <el-select v-model="form.stock" filterable allow-create style="width: 100%">
                <el-option v-for="s in stockOptions" :key="s.value" :label="s.label" :value="s.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="開始日期" required>
              <el-date-picker v-model="form.startDate" type="date" style="width: 100%" value-format="YYYY-MM-DD" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="結束日期" required>
              <el-date-picker v-model="form.endDate" type="date" style="width: 100%" value-format="YYYY-MM-DD" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">參數範圍設定</el-divider>
        
        <el-row :gutter="24">
          <el-col :xs="24" :sm="12">
            <el-form-item label="短週期範圍">
              <div class="slider-container">
                <el-slider v-model="form.param1Range" range :min="1" :max="50" show-stops :step="form.param1Step" />
              </div>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="短週期步長">
              <el-input-number v-model="form.param1Step" :min="1" :max="10" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="24">
          <el-col :xs="24" :sm="12">
            <el-form-item label="長週期範圍">
              <div class="slider-container">
                <el-slider v-model="form.param2Range" range :min="10" :max="120" show-stops :step="form.param2Step" />
              </div>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="長週期步長">
              <el-input-number v-model="form.param2Step" :min="1" :max="20" />
            </el-form-item>
          </el-col>
        </el-row>

        <div class="form-actions">
          <el-button type="primary" size="large" @click="runOptimization" :loading="isRunning" class="run-btn">
            <el-icon v-if="!isRunning"><Cpu /></el-icon>
            {{ isRunning ? '運算中...' : '開始運算' }}
          </el-button>
        </div>
      </el-form>
    </el-card>

    <!-- 結果展示 -->
    <div v-if="showResult && optimizeResult" class="result-area">
      <el-alert
        title="最佳參數組合已找到！"
        type="success"
        :description="`最佳短週期: ${optimizeResult.best_param1}, 最佳長週期: ${optimizeResult.best_param2}，報酬率: ${optimizeResult.best_return}%, 夏普比率: ${optimizeResult.best_sharpe}`"
        show-icon
        :closable="false"
        style="margin-bottom: 24px"
      />

      <el-card shadow="hover">
        <div ref="heatmapChartRef" class="chart-container"></div>
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.optimize {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.section-title {
  font-weight: 600;
  font-size: 16px;
}

.slider-container {
  padding: 0 10px;
}

.form-actions {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}

.run-btn {
  width: 100%;
  max-width: 200px;
}

.chart-container {
  width: 100%;
  height: 600px;
}

@media (max-width: 768px) {
  .chart-container { height: 400px; }
}
</style>
