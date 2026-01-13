<script setup>
import { ref, reactive, nextTick, watch, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Delete, Cpu } from '@element-plus/icons-vue'
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
  param2Step: 10,
  // DCA Parameters
  dcaAmount: 10000,
  dcaInterval: 'MONTHLY',
  dcaDay: 1, // Default
  dcaMonth: 1,
  optimizationTarget: 'SHARPE', // SHARPE or ROI
  targetStocks: ['AAPL', 'MSFT'] // Default stocks
})

const strategies = [
  { label: '雙均線交叉 (MA Cross)', value: 'MA_CROSS' },
  { label: '定期定額 (DCA) 配置最佳化', value: 'DCA' }
]

const stockOptions = [
  { label: '2330.TW 台積電', value: '2330.TW' },
  { label: '2317.TW 鴻海', value: '2317.TW' },
  { label: 'AAPL 蘋果', value: 'AAPL' },
  { label: 'NVDA 輝達', value: 'NVDA' },
  { label: 'TSLA 特斯拉', value: 'TSLA' },
  { label: 'GOOGL Google', value: 'GOOGL' },
  { label: 'MSFT 微軟', value: 'MSFT' },
  { label: 'QQQ 那斯達克ETF', value: 'QQQ' },
  { label: 'SPY 標普500ETF', value: 'SPY' },
  { label: 'TLT 美國公債ETF', value: 'TLT' }
]

const isRunning = ref(false)
const showResult = ref(false)
const heatmapChartRef = ref(null)
const pieChartRef = ref(null)
const optimizeResult = ref(null)
let chartInstance = null
let pieChartInstance = null

const handleResize = () => {
  chartInstance?.resize()
  pieChartInstance?.resize()
}
onMounted(() => window.addEventListener('resize', handleResize))
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
  pieChartInstance?.dispose()
})

watch(isDark, () => {
  if (showResult.value) {
    nextTick(() => {
      renderHeatmap()
      renderPieChart()
    })
  }
})

// Add/Remove Stocks
const addStock = () => {
  form.targetStocks.push('')
}
const removeStock = (index) => {
  form.targetStocks.splice(index, 1)
}

// 執行最佳化
const runOptimization = async () => {
  if (!form.startDate || !form.endDate) {
    ElMessage.warning('請選擇回測日期範圍')
    return
  }
  
  if (form.strategy === 'DCA' && form.targetStocks.length < 2) {
    ElMessage.warning('DCA 最佳化至少需要選擇兩支股票')
    return
  }

  isRunning.value = true
  showResult.value = false

  try {
    const payload = {
      strategy_type: form.strategy,
      stock_symbol: form.strategy === 'DCA' ? 'MULTI' : form.stock,
      start_date: form.startDate,
      end_date: form.endDate,
      param1_range: form.param1Range,
      param1_step: form.param1Step,
      param2_range: form.param2Range,
      param2_step: form.param2Step,
      // DCA Params
      dca_amount: form.dcaAmount,
      dca_interval: form.dcaInterval,
      dca_day: form.dcaDay,
      dca_month: form.dcaMonth,
      optimization_target: form.optimizationTarget,
      stocks: form.targetStocks.filter(s => s)
    }

    const response = await api.optimizeStrategy(payload)
    optimizeResult.value = response.data
    showResult.value = true
    ElMessage.success('最佳化完成')
    
    await nextTick()
    if (form.strategy === 'DCA') {
      renderPieChart()
    } else {
      renderHeatmap()
    }

  } catch (error) {
    ElMessage.error('最佳化失敗: ' + (error.response?.data?.detail || error.message))
  } finally {
    isRunning.value = false
  }
}

const renderPieChart = () => {
  if (!pieChartRef.value || !optimizeResult.value || !optimizeResult.value.best_allocation) return

  const theme = isDark.value ? 'dark' : undefined
  const textColor = isDark.value ? '#ccc' : '#333'

  if (pieChartInstance) pieChartInstance.dispose()
  pieChartInstance = echarts.init(pieChartRef.value, theme)

  const allocation = optimizeResult.value.best_allocation
  const data = Object.entries(allocation).map(([name, value]) => ({
    name,
    value: Math.round(value * 1000) / 10 // Convert to percentage with 1 decimal
  }))

  pieChartInstance.setOption({
    backgroundColor: 'transparent',
    title: { text: '最佳資產配置比例 (%)', left: 'center', textStyle: { color: textColor } },
    tooltip: { trigger: 'item', formatter: '{b}: {c}% ({d}%)' },
    legend: { bottom: '5%', left: 'center', textStyle: { color: textColor } },
    series: [
      {
        name: '配置比例',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: isDark.value ? '#1e1e1e' : '#fff',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}: {c}%'
        },
        data: data
      }
    ]
  })
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
          <el-col :xs="24" :sm="12" :md="6" v-if="form.strategy !== 'DCA'">
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
        
        <!-- DCA Configuration -->
        <div v-if="form.strategy === 'DCA'">
           <el-divider content-position="left">DCA 配置參數</el-divider>
           <el-row :gutter="24">
             <el-col :xs="24" :sm="12">
               <el-form-item label="投入週期">
                 <el-radio-group v-model="form.dcaInterval">
                   <el-radio label="MONTHLY">每月</el-radio>
                   <el-radio label="YEARLY">每年</el-radio>
                 </el-radio-group>
               </el-form-item>
             </el-col>
             <el-col :xs="24" :sm="12">
               <el-form-item label="每次投入金額">
                 <el-input-number v-model="form.dcaAmount" :min="1000" :step="1000" style="width: 100%" />
               </el-form-item>
             </el-col>
           </el-row>

           <el-row :gutter="24">
             <el-col :xs="24" :sm="12" v-if="form.dcaInterval === 'YEARLY'">
               <el-form-item label="投入月份">
                 <el-select v-model="form.dcaMonth" style="width: 100%">
                   <el-option :value="1" label="1月" />
                   <el-option :value="2" label="2月" />
                   <el-option :value="3" label="3月" />
                   <el-option :value="4" label="4月" />
                   <el-option :value="5" label="5月" />
                   <el-option :value="6" label="6月" />
                   <el-option :value="7" label="7月" />
                   <el-option :value="8" label="8月" />
                   <el-option :value="9" label="9月" />
                   <el-option :value="10" label="10月" />
                   <el-option :value="11" label="11月" />
                   <el-option :value="12" label="12月" />
                 </el-select>
               </el-form-item>
             </el-col>
             <el-col :xs="24" :sm="12">
               <el-form-item label="投入日期 (每月/每年)">
                 <el-input-number v-model="form.dcaDay" :min="1" :max="31" style="width: 100%" />
               </el-form-item>
             </el-col>
           </el-row>

           <el-row :gutter="24">
             <el-col :xs="24">
               <el-form-item label="最佳化目標">
                 <el-radio-group v-model="form.optimizationTarget">
                   <el-radio-button label="SHARPE">夏普比率 (風險調整後回報)</el-radio-button>
                   <el-radio-button label="ROI">總報酬率 (單純獲利)</el-radio-button>
                 </el-radio-group>
               </el-form-item>
             </el-col>
           </el-row>
           
           <div class="stock-list-container">
             <div class="stock-list-header">
               <span>資產池 (至少2支)</span>
               <el-button type="primary" size="small" @click="addStock">
                 <el-icon><Plus /></el-icon> 新增股票
               </el-button>
             </div>
             
             <el-row :gutter="12" v-for="(stock, index) in form.targetStocks" :key="index" class="mb-2">
               <el-col :xs="20" :sm="22">
                  <el-select v-model="form.targetStocks[index]" filterable allow-create placeholder="選擇股票代碼" style="width: 100%">
                    <el-option v-for="s in stockOptions" :key="s.value" :label="s.label" :value="s.value" />
                  </el-select>
               </el-col>
               <el-col :xs="4" :sm="2">
                 <el-button type="danger" circle @click="removeStock(index)" :disabled="form.targetStocks.length <= 2">
                   <el-icon><Delete /></el-icon>
                 </el-button>
               </el-col>
             </el-row>
           </div>
        </div>

        <div v-else>
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
        </div>

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
        :description="optimizeResult.best_allocation ? 
          `最佳Sharpe: ${optimizeResult.best_sharpe}, 報酬率: ${optimizeResult.best_return}%` : 
          `最佳短週期: ${optimizeResult.best_param1}, 最佳長週期: ${optimizeResult.best_param2}，報酬率: ${optimizeResult.best_return}%, 夏普比率: ${optimizeResult.best_sharpe}`"
        show-icon
        :closable="false"
        style="margin-bottom: 24px"
      />

      <el-card shadow="hover">
        <div v-if="form.strategy === 'DCA'" ref="pieChartRef" class="chart-container"></div>
        <div v-else ref="heatmapChartRef" class="chart-container"></div>
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
