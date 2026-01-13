<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Delete, VideoPlay, Download } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { useTheme } from '../composables/useTheme'
import api from '../api'

const { isDark } = useTheme()

// 表單資料
const backtestForm = reactive({
  strategyName: '',
  stockSymbol: '',
  startDate: '',
  endDate: '',
  initialCapital: 1000000,
  strategyType: 'MA_CROSS',
  shortPeriod: 5,
  longPeriod: 20,
  rsiPeriod: 14,
  rsiBuy: 30,
  rsiSell: 70,
  macdFast: 12,
  macdSlow: 26,
  macdSignal: 9,
  // DCA 參數
  dcaAmount: 10000,
  dcaDay: 1,
  dcaMonth: 1, // 年度投入时的月份
  dcaInterval: 'MONTHLY', // 新增：投入週期
  // 進階
  sellRatio: 100,
  // SMA Breakout 參數
  smaPeriod: 200,
  // 多股票 DCA
  useMultiStock: false, // 是否使用多股票DCA
  stockAllocations: [] // 股票配置列表
})

const strategyTypes = [
  { label: '雙均線交叉', value: 'MA_CROSS' },
  { label: 'RSI 超賣超買', value: 'RSI' },
  { label: 'MACD 交叉', value: 'MACD' },
  { label: '布林通道突破', value: 'BOLLINGER' },
  { label: '定期定額 (DCA)', value: 'DCA' },
  { label: 'SMA 突破策略', value: 'SMA_BREAKOUT' }
]

const stockOptions = [
  { label: '2330.TW 台積電', value: '2330.TW' },
  { label: '2317.TW 鴻海', value: '2317.TW' },
  { label: 'AAPL 蘋果', value: 'AAPL' },
  { label: 'NVDA 輝達', value: 'NVDA' },
  { label: 'TSLA 特斯拉', value: 'TSLA' },
  { label: 'GOOGL Google', value: 'GOOGL' },
  { label: 'MSFT 微軟', value: 'MSFT' }
]

const isLoading = ref(false)
const showResult = ref(false)
const resultData = ref(null)
const currentPage = ref(1)
const pageSize = ref(20)

// 多股票配置相關
const addStockAllocation = () => {
  backtestForm.stockAllocations.push({
    stockSymbol: '',
    allocationRatio: 0
  })
}

const removeStockAllocation = (index) => {
  backtestForm.stockAllocations.splice(index, 1)
}

const totalAllocation = computed(() => {
  return backtestForm.stockAllocations.reduce((sum, item) => sum + (item.allocationRatio || 0), 0)
})

const priceChartRef = ref(null)
const equityChartRef = ref(null)
let priceChartInstance = null
let equityChartInstance = null

// RWD
const handleResize = () => {
  priceChartInstance?.resize()
  equityChartInstance?.resize()
}

onMounted(() => window.addEventListener('resize', handleResize))
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  priceChartInstance?.dispose()
  equityChartInstance?.dispose()
})

watch(isDark, () => {
  if (showResult.value) nextTick(renderCharts)
})

// 執行回測 - 呼叫真實 API
const runBacktest = async () => {
  if (!backtestForm.strategyName || !backtestForm.startDate || !backtestForm.endDate) {
    ElMessage.warning('請填寫所有必填欄位')
    return
  }

  // 驗證股票代碼或多股票配置
  if (backtestForm.strategyType === 'DCA' && backtestForm.useMultiStock) {
    if (!backtestForm.stockAllocations || backtestForm.stockAllocations.length === 0) {
      ElMessage.warning('請添加至少一支股票')
      return
    }
    if (Math.abs(totalAllocation.value - 100) > 0.1) {
      ElMessage.warning(`配置比例總和必須為100%，目前為${totalAllocation.value.toFixed(1)}%`)
      return
    }
  } else if (!backtestForm.stockSymbol) {
    ElMessage.warning('請選擇股票代碼')
    return
  }

  isLoading.value = true
  currentPage.value = 1  // 重置分頁

  try {
    // 轉換為後端 API 格式 (snake_case)
    const payload = {
      strategy_name: backtestForm.strategyName,
      stock_symbol: backtestForm.stockSymbol || 'MULTI',
      start_date: backtestForm.startDate,
      end_date: backtestForm.endDate,
      initial_capital: backtestForm.initialCapital || 0,
      strategy_type: backtestForm.strategyType,
      short_period: backtestForm.shortPeriod,
      long_period: backtestForm.longPeriod,
      rsi_period: backtestForm.rsiPeriod,
      rsi_buy: backtestForm.rsiBuy,
      rsi_sell: backtestForm.rsiSell,
      macd_fast: backtestForm.macdFast,
      macd_slow: backtestForm.macdSlow,
      macd_signal: backtestForm.macdSignal,
      // DCA 參數
      dca_amount: backtestForm.dcaAmount,
      dca_day: backtestForm.dcaDay,
      dca_month: backtestForm.dcaMonth,
      dca_interval: backtestForm.dcaInterval,
      // 進階
      sell_ratio: backtestForm.sellRatio / 100,
      // SMA Breakout 參數
      sma_period: backtestForm.smaPeriod
    }

    // 多股票DCA配置
    if (backtestForm.strategyType === 'DCA' && backtestForm.useMultiStock && backtestForm.stockAllocations.length > 0) {
      payload.stock_allocations = backtestForm.stockAllocations.map(item => ({
        stock_symbol: item.stockSymbol,
        allocation_ratio: item.allocationRatio / 100
      }))
    }

    const response = await api.runBacktest(payload)
    resultData.value = response.data
    showResult.value = true
    ElMessage.success('回測完成！')
    
    await nextTick()
    renderCharts()

  } catch (error) {
    const msg = error.response?.data?.detail || error.message
    ElMessage.error('回測失敗：' + msg)
  } finally {
    isLoading.value = false
  }
}

const renderCharts = () => {
  if (!resultData.value) return

  const theme = isDark.value ? 'dark' : undefined
  const data = resultData.value
  
  // 定义股票颜色
  const stockColors = [
    '#409eff', // 蓝色
    '#67c23a', // 绿色
    '#e6a23c', // 橙色
    '#f56c6c', // 红色
    '#9c27b0', // 紫色
    '#00bcd4', // 青色
    '#ff5722', // 深橙
    '#795548', // 棕色
  ]
  
  // 價格圖表
  if (priceChartRef.value) {
    if (priceChartInstance) priceChartInstance.dispose()
    priceChartInstance = echarts.init(priceChartRef.value, theme)
    
    let series = []
    let legendData = []
    
    // 检查是否为多股票DCA
    if (data.price_data.multi_stock_prices) {
      // 多股票模式：为每支股票创建一条线
      const stocks = Object.keys(data.price_data.multi_stock_prices)
      stocks.forEach((symbol, index) => {
        const prices = data.price_data.multi_stock_prices[symbol]
        const color = stockColors[index % stockColors.length]
        
        series.push({
          name: symbol,
          type: 'line',
          data: prices,
          showSymbol: false,
          lineStyle: { width: 2 },
          itemStyle: { color: color }
        })
        
        legendData.push(symbol)
      })
    } else {
      // 单股票模式：显示价格和均线
      series = [
        { name: '股價', type: 'line', data: data.price_data.prices, showSymbol: false, itemStyle: { color: '#409eff' } },
        { name: 'MA Short', type: 'line', data: data.price_data.ma_short, showSymbol: false, lineStyle: { width: 1 }, itemStyle: { color: '#67c23a' } },
        { name: 'MA Long', type: 'line', data: data.price_data.ma_long, showSymbol: false, lineStyle: { width: 1 }, itemStyle: { color: '#e6a23c' } }
      ]
      legendData = ['股價', 'MA Short', 'MA Long']
    }
    
    priceChartInstance.setOption({
      backgroundColor: 'transparent',
      title: { 
        text: data.price_data.multi_stock_prices ? '多股票價格走勢' : '股價與移動平均線', 
        left: 'center' 
      },
      tooltip: { 
        trigger: 'axis',
        formatter: function(params) {
          let result = params[0].axisValue + '<br/>'
          params.forEach(item => {
            result += `${item.marker}${item.seriesName}: $${Number(item.value).toLocaleString()}<br/>`
          })
          return result
        }
      },
      legend: { data: legendData, bottom: 0 },
      grid: { left: '3%', right: '4%', bottom: '12%', containLabel: true },
      xAxis: { type: 'category', data: data.price_data.dates, boundaryGap: false },
      yAxis: { type: 'value', scale: true },
      series: series
    })
  }
  
  // 權益曲線
  if (equityChartRef.value) {
    if (equityChartInstance) equityChartInstance.dispose()
    equityChartInstance = echarts.init(equityChartRef.value, theme)
    
    equityChartInstance.setOption({
      backgroundColor: 'transparent',
      title: { text: '權益曲線', left: 'center' },
      tooltip: { trigger: 'axis', formatter: (params) => `${params[0].axisValue}<br/>權益: $${Number(params[0].value).toLocaleString()}` },
      grid: { left: '3%', right: '4%', bottom: '10%', containLabel: true },
      xAxis: { type: 'category', data: data.equity_data.dates, boundaryGap: false },
      yAxis: { type: 'value', scale: true },
      series: [{
        name: '權益',
        type: 'line',
        data: data.equity_data.equity,
        showSymbol: false,
        lineStyle: { width: 2 },
        itemStyle: { color: '#67c23a' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(103, 194, 58, 0.3)' },
            { offset: 1, color: 'rgba(103, 194, 58, 0.05)' }
          ])
        }
      }]
    })
  }
}

const resetForm = () => {
  backtestForm.strategyName = ''
  backtestForm.stockSymbol = ''
  backtestForm.startDate = ''
  backtestForm.endDate = ''
  showResult.value = false
  currentPage.value = 1
}

const paginatedTrades = computed(() => {
  if (!resultData.value || !resultData.value.trades) return []
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return resultData.value.trades.slice(start, end)
})

const exportTradesCsv = () => {
  if (!resultData.value || !resultData.value.trades) return
  
  const headers = ['日期', '操作', '價格', '股數', '金額', '餘額', '總資產', '損益']
  const rows = resultData.value.trades.map(t => [
    t.date,
    t.action === 'BUY' ? '買入' : '賣出',
    t.price,
    t.shares,
    t.value,
    t.balance || 0,
    t.total_assets || 0,
    t.pnl || 0
  ])
  
  const csvContent = '\uFEFF' + [headers, ...rows].map(row => row.join(',')).join('\n')
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `${resultData.value.strategy_name}_trades.csv`
  link.click()
}
</script>

<template>
  <div class="page-container backtest">
    <!-- 參數設定 -->
    <el-card class="form-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="section-title">回測參數設定</span>
          <el-button @click="resetForm" :disabled="isLoading">重置</el-button>
        </div>
      </template>

      <el-form :model="backtestForm" label-position="top">
        <el-row :gutter="24">
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="策略名稱" required>
              <el-input v-model="backtestForm.strategyName" placeholder="輸入名稱" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="策略類型">
              <el-select v-model="backtestForm.strategyType" placeholder="選擇策略" style="width: 100%">
                <el-option v-for="item in strategyTypes" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="初始資金">
              <el-input-number v-model="backtestForm.initialCapital" :min="0" :step="100000" style="width: 100%" />
            </el-form-item>
          </el-col>
        
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="開始日期" required>
              <el-date-picker v-model="backtestForm.startDate" type="date" placeholder="選擇日期" style="width: 100%" value-format="YYYY-MM-DD" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="結束日期" required>
              <el-date-picker v-model="backtestForm.endDate" type="date" placeholder="選擇日期" style="width: 100%" value-format="YYYY-MM-DD" />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 策略參數 -->
        <div v-if="backtestForm.strategyType === 'MA_CROSS'" class="strategy-params">
          <el-divider content-position="left">均線參數</el-divider>
          <el-row :gutter="24">
            <el-col :xs="12" :sm="8">
              <el-form-item label="短週期">
                <el-input-number v-model="backtestForm.shortPeriod" :min="1" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :xs="12" :sm="8">
              <el-form-item label="長週期">
                <el-input-number v-model="backtestForm.longPeriod" :min="1" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <div v-if="backtestForm.strategyType === 'RSI'" class="strategy-params">
          <el-divider content-position="left">RSI 參數</el-divider>
          <el-row :gutter="24">
            <el-col :xs="24" :sm="8">
              <el-form-item label="RSI 週期">
                <el-input-number v-model="backtestForm.rsiPeriod" :min="1" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :xs="12" :sm="8">
              <el-form-item label="買入閾值">
                <el-input-number v-model="backtestForm.rsiBuy" :min="0" :max="100" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :xs="12" :sm="8">
              <el-form-item label="賣出閾值">
                <el-input-number v-model="backtestForm.rsiSell" :min="0" :max="100" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- 通用資金與交易設定 (適用於所有策略) -->
        <div class="strategy-params">
          <el-divider content-position="left">資金與交易設定</el-divider>
          
          <!-- DCA 策略專用：多股票配置開關 -->
          <el-row v-if="backtestForm.strategyType === 'DCA'" :gutter="24">
            <el-col :xs="24">
              <el-form-item>
                <el-checkbox v-model="backtestForm.useMultiStock">使用多股票配置</el-checkbox>
                <div class="form-help-text">
                  啟用後可同時投資多支股票，並設定各股票的配置比例
                </div>
              </el-form-item>
            </el-col>
          </el-row>

          <!-- 單股票選擇（非多股票DCA時顯示） -->
          <el-row v-if="!(backtestForm.strategyType === 'DCA' && backtestForm.useMultiStock)" :gutter="24">
            <el-col :xs="24" :sm="12">
              <el-form-item label="股票代碼" required>
                <el-select v-model="backtestForm.stockSymbol" placeholder="選擇股票" filterable allow-create style="width: 100%">
                  <el-option v-for="item in stockOptions" :key="item.value" :label="item.label" :value="item.value" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <!-- 多股票配置列表 -->
          <div v-if="backtestForm.strategyType === 'DCA' && backtestForm.useMultiStock" class="multi-stock-config">
            <el-row :gutter="24">
              <el-col :xs="24">
                <div class="stock-allocation-header">
                  <span>股票配置列表</span>
                  <el-button type="primary" size="small" @click="addStockAllocation">
                    <el-icon class="mr-1"><Plus /></el-icon>
                    添加股票
                  </el-button>
                </div>
              </el-col>
            </el-row>

            <div v-for="(item, index) in backtestForm.stockAllocations" :key="index" class="stock-allocation-item">
              <el-row :gutter="12">
                <el-col :xs="14" :sm="16">
                  <el-form-item :label="`股票 ${index + 1}`">
                    <el-select v-model="item.stockSymbol" placeholder="選擇股票" filterable allow-create style="width: 100%">
                      <el-option v-for="opt in stockOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :xs="8" :sm="6">
                  <el-form-item label="比例 (%)">
                    <el-input-number v-model="item.allocationRatio" :min="0" :max="100" :step="5" style="width: 100%" />
                  </el-form-item>
                </el-col>
                <el-col :xs="2" :sm="2">
                  <el-button type="danger" size="small" @click="removeStockAllocation(index)" style="margin-top: 30px">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </el-col>
              </el-row>
            </div>

            <el-row v-if="backtestForm.stockAllocations.length > 0" :gutter="24">
              <el-col :xs="24">
                <el-alert 
                  :type="Math.abs(totalAllocation - 100) < 0.1 ? 'success' : 'warning'" 
                  :closable="false"
                  show-icon
                >
                  總配置比例: {{ totalAllocation.toFixed(1) }}% 
                  <span v-if="Math.abs(totalAllocation - 100) >= 0.1">(需要等於100%)</span>
                </el-alert>
              </el-col>
            </el-row>
          </div>
          
          <!-- 投入週期選擇 -->
          <el-row v-if="backtestForm.strategyType === 'DCA'" :gutter="24">
            <el-col :xs="24" :sm="12">
              <el-form-item label="投入週期">
                <el-radio-group v-model="backtestForm.dcaInterval">
                  <el-radio label="MONTHLY">每月</el-radio>
                  <el-radio label="YEARLY">每年</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
          </el-row>

          <!-- 定期定額設定 -->
          <el-row :gutter="24">
            <el-col :xs="24" :sm="12">
              <el-form-item :label="backtestForm.strategyType === 'DCA' ? (backtestForm.dcaInterval === 'YEARLY' ? '每年投入金額' : '每月投入金額') : '每月存入資金'">
                <el-input-number v-model="backtestForm.dcaAmount" :min="0" :step="1000" style="width: 100%" />
                <div class="form-help-text" v-if="backtestForm.strategyType !== 'DCA'">
                  設為 0 代表只使用初始資金
                </div>
              </el-form-item>
            </el-col>
            
            <!-- 年度投入：顯示月份選擇 -->
            <el-col :xs="12" :sm="6" v-if="backtestForm.strategyType === 'DCA' && backtestForm.dcaInterval === 'YEARLY'">
              <el-form-item label="投入月份">
                <el-select v-model="backtestForm.dcaMonth" style="width: 100%">
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
            
            <el-col :xs="12" :sm="6" v-if="backtestForm.strategyType === 'DCA' && backtestForm.dcaInterval === 'YEARLY'">
              <el-form-item label="投入日期">
                <el-input-number v-model="backtestForm.dcaDay" :min="1" :max="31" style="width: 100%" />
              </el-form-item>
            </el-col>
            
            <!-- 月度投入：只顯示日期選擇 -->
            <el-col :xs="24" :sm="12" v-if="backtestForm.strategyType === 'DCA' && backtestForm.dcaInterval === 'MONTHLY'">
              <el-form-item label="每月買入日 (1-31)">
                <el-input-number v-model="backtestForm.dcaDay" :min="1" :max="31" style="width: 100%" />
              </el-form-item>
            </el-col>
            
            <!-- 非DCA策略 -->
            <el-col :xs="24" :sm="12" v-if="backtestForm.strategyType !== 'DCA'">
              <el-form-item label="每月存錢日 (1-31)">
                <el-input-number v-model="backtestForm.dcaDay" :min="1" :max="31" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>

          <!-- 賣出比例設定 (DCA 不顯示) -->
          <el-row :gutter="24" v-if="backtestForm.strategyType !== 'DCA'">
            <el-col :xs="24" :sm="12">
              <el-form-item label="賣出比例 (%)">
                <el-slider v-model="backtestForm.sellRatio" :min="10" :max="100" :step="10" show-input />
                <div class="form-help-text">
                  觸發賣出訊號時，賣出目前持倉的比例 (100% = 全賣)
                </div>
              </el-form-item>
            </el-col>
          </el-row>

          <!-- 策略提示 -->
          <el-alert v-if="backtestForm.strategyType === 'DCA'" type="info" :closable="false" show-icon class="mt-2">
            DCA 策略會在每月指定日期自動買入固定金額，持續累積持股，不會賣出。
          </el-alert>
          <el-alert v-else type="info" :closable="false" show-icon class="mt-2">
            當「買入訊號」出現時，使用帳戶內所有累積現金買入。
            當「賣出訊號」出現時，依據設定的比例賣出持股。
          </el-alert>
        </div>

        <div v-if="backtestForm.strategyType === 'SMA_BREAKOUT'" class="strategy-params">
          <el-divider content-position="left">SMA 突破參數</el-divider>
          <el-row :gutter="24">
            <el-col :xs="24" :sm="12">
              <el-form-item label="SMA 週期 (天)">
                <el-input-number v-model="backtestForm.smaPeriod" :min="1" :max="500" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-alert type="info" :closable="false" show-icon>
            當價格上穿 SMA 時買入，下穿時賣出。建議使用 200 日均線作為長期趨勢判斷。
          </el-alert>
        </div>

        <div class="form-actions">
          <el-button type="primary" size="large" @click="runBacktest" :loading="isLoading" class="run-btn">
            <el-icon class="el-icon--left" v-if="!isLoading"><VideoPlay /></el-icon>
            {{ isLoading ? '回測運算中...' : '開始回測' }}
          </el-button>
        </div>
      </el-form>
    </el-card>

    <!-- 回測結果 -->
    <div v-if="showResult && resultData" class="results-section">
      <!-- 績效指標 -->
      <div class="metrics-grid">
        <el-card shadow="hover" class="metric-card">
          <div class="metric-label">總投入成本</div>
          <div class="metric-value">
            ${{ Number(resultData.summary.total_cost || 0).toLocaleString() }}
          </div>
        </el-card>
        <el-card shadow="hover" class="metric-card">
          <div class="metric-label">最終總資產</div>
          <div class="metric-value">
            ${{ Number(resultData.final_capital).toLocaleString() }}
          </div>
        </el-card>
        <el-card shadow="hover" class="metric-card">
          <div class="metric-label">總報酬率</div>
          <div class="metric-value" :class="resultData.summary.total_return >= 0 ? 'text-success' : 'text-danger'">
            {{ resultData.summary.total_return >= 0 ? '+' : '' }}{{ resultData.summary.total_return }}%
          </div>
        </el-card>
        <el-card shadow="hover" class="metric-card">
          <div class="metric-label">年化報酬率</div>
          <div class="metric-value" :class="resultData.summary.annualized_return >= 0 ? 'text-success' : 'text-danger'">
            {{ resultData.summary.annualized_return >= 0 ? '+' : '' }}{{ resultData.summary.annualized_return }}%
          </div>
        </el-card>
        <el-card shadow="hover" class="metric-card">
          <div class="metric-label">夏普比率</div>
          <div class="metric-value">{{ resultData.summary.sharpe_ratio }}</div>
        </el-card>
        <el-card shadow="hover" class="metric-card">
          <div class="metric-label">最大回撤</div>
          <div class="metric-value text-danger">{{ resultData.summary.max_drawdown }}%</div>
        </el-card>
        <el-card shadow="hover" class="metric-card">
          <div class="metric-label">勝率</div>
          <div class="metric-value">{{ resultData.summary.win_rate }}%</div>
        </el-card>
        <el-card shadow="hover" class="metric-card">
          <div class="metric-label">總交易次數</div>
          <div class="metric-value">{{ resultData.summary.total_trades }}</div>
        </el-card>
        <el-card shadow="hover" class="metric-card">
          <div class="metric-label">獲利 / 虧損</div>
          <div class="metric-value">
            <span class="text-success">{{ resultData.summary.profit_trades }}</span> / 
            <span class="text-danger">{{ resultData.summary.loss_trades }}</span>
          </div>
        </el-card>
      </div>

      <!-- 圖表 -->
      <el-card shadow="hover" class="chart-card">
        <div ref="priceChartRef" class="chart-container"></div>
      </el-card>

      <el-card shadow="hover" class="chart-card">
        <div ref="equityChartRef" class="chart-container"></div>
      </el-card>

      <!-- 交易明細 -->
      <el-card shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="section-title">交易明細 (共 {{ resultData.trades?.length || 0 }} 筆)</span>
            <el-button type="primary" link @click="exportTradesCsv">
              <el-icon class="mr-1"><Download /></el-icon> 匯出 CSV
            </el-button>
          </div>
        </template>
        <el-table :data="paginatedTrades" stripe border>
          <el-table-column type="index" label="#" width="60" :index="(index) => (currentPage - 1) * pageSize + index + 1" />
          <el-table-column prop="date" label="日期" width="120" />
          <el-table-column prop="stock_symbol" label="股票" width="100" v-if="resultData.stock_symbol === 'MULTI_STOCK_DCA'" />
          <el-table-column prop="action" label="操作" width="80">
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
          <el-table-column prop="price" label="價格" width="100" />
          <el-table-column prop="shares" label="股數" width="80" />
          <el-table-column prop="value" label="金額" width="120">
            <template #default="{ row }">
              ${{ Number(row.value).toLocaleString() }}
            </template>
          </el-table-column>
          <el-table-column prop="balance" label="餘額" width="120">
            <template #default="{ row }">
              ${{ Number(row.balance).toLocaleString() }}
            </template>
          </el-table-column>
          <el-table-column prop="total_assets" label="總資產" width="120">
            <template #default="{ row }">
              ${{ Number(row.total_assets).toLocaleString() }}
            </template>
          </el-table-column>
          <el-table-column prop="pnl" label="損益" width="120">
            <template #default="{ row }">
              <span v-if="row.pnl !== null" :class="row.pnl >= 0 ? 'text-success' : 'text-danger'">
                <template v-if="backtestForm.strategyType === 'DCA'">
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
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="resultData.trades?.length || 0"
            layout="total, sizes, prev, pager, next, jumper"
            background
          />
        </div>
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.backtest {
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

.form-actions {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}

.run-btn {
  width: 100%;
  max-width: 240px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

@media (min-width: 768px) {
  .metrics-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (min-width: 1024px) {
  .metrics-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (min-width: 1400px) {
  .metrics-grid {
    grid-template-columns: repeat(5, 1fr);
  }
}

.metric-card { text-align: center; }
.metric-label { font-size: 13px; color: var(--el-text-color-secondary); margin-bottom: 8px; }
.metric-value { font-size: 22px; font-weight: 600; font-family: 'Roboto Mono', monospace; }

.text-success { color: #67c23a; }
.text-danger { color: #f56c6c; }

.chart-card { margin-bottom: 24px; }
.chart-container { width: 100%; height: 400px; }

@media (max-width: 768px) {
  .chart-container { height: 300px; }
}

.mr-1 { margin-right: 4px; }

.pagination-container {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}

.multi-stock-config {
  margin-top: 16px;
  padding: 16px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
}

.stock-allocation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  font-weight: 600;
}

.stock-allocation-item {
  margin-bottom: 12px;
  padding: 12px;
  background: var(--el-bg-color);
  border-radius: 6px;
  border: 1px solid var(--el-border-color);
}

.form-help-text {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}
</style>
