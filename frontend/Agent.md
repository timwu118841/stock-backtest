# Frontend Agent Guide

這份文件是 **Stock Backtesting App 前端** 的開發指南。
當你需要修改、擴充或維護前端代碼時，請嚴格遵守以下架構與規範。

## 1. 技術棧 (Tech Stack)

- **核心框架**: Vue 3 (Composition API + `<script setup>`)
- **建構工具**: Vite
- **UI 框架**: Element Plus
- **圖表庫**: ECharts 5 (原生引入，不使用 vue-echarts)
- **路由**: Vue Router 4
- **HTTP 客戶端**: Axios
- **CSS 架構**: 原生 CSS + CSS Variables (支援 Dark Mode) + Scoped CSS

## 2. 目錄結構 (Directory Structure)

```
frontend/
├── src/
│   ├── api/
│   │   └── index.js          # 集中管理所有 API 請求
│   ├── assets/               # 靜態資源
│   ├── components/           # 共用元件
│   ├── composables/          # 組合式函數 (Hooks)
│   │   └── useTheme.js       # 主題切換邏輯
│   ├── router/
│   │   └── index.js          # 路由定義
│   ├── views/                # 頁面組件
│   │   ├── Dashboard.vue     # 主控台
│   │   ├── Backtest.vue      # 策略回測 (含複雜表單與圖表)
│   │   ├── Compare.vue       # 策略比較
│   │   ├── Optimize.vue      # 參數最佳化 (熱力圖)
│   │   └── History.vue       # 歷史紀錄列表
│   ├── App.vue               # 根組件 (Layout 佈局邏輯)
│   ├── main.js               # 入口文件
│   └── style.css             # 全域樣式與 CSS 變數定義
└── package.json
```

## 3. 核心架構與模式

### 3.1 主題系統 (Dark Mode)
專案使用 CSS Variables 實現深色模式。
- **狀態管理**: `src/composables/useTheme.js` 管理 `isDark` 狀態，並自動切換 `html` 標籤的 class (`.dark`)。
- **樣式定義**: 所有顏色必須使用 `src/style.css` 中定義的變數，**嚴禁寫死 Hex 色碼**。

**常用變數**:
```css
background-color: var(--app-bg-color);       /* 背景色 */
color: var(--app-text-color);                /* 文字顏色 */
background-color: var(--app-sidebar-bg);     /* 側邊欄背景 */
border-color: var(--app-border-color);       /* 邊框顏色 */
```

### 3.2 響應式設計 (RWD)
- **容器**: 使用 `.page-container` 包裹頁面內容，它會根據螢幕寬度自動調整 Padding。
- **Grid 系統**: 使用 Element Plus 的 `<el-row>` 與 `<el-col>`。
  - 手機: `:xs="24"` (全寬)
  - 平板: `:sm="12"` (半寬)
  - 桌面: `:md="8"` 或 `:lg="6"`
- **隱藏邏輯**: 使用 CSS class `.hidden-xs-only` (手機隱藏) 或 `.hidden-sm-and-up` (桌面隱藏) 來切換不同裝置的顯示內容。

### 3.3 圖表處理 (ECharts)
所有圖表必須遵循以下生命週期模式以確保效能與 RWD 支援：

```javascript
import * as echarts from 'echarts'
import { useTheme } from '../composables/useTheme'

const { isDark } = useTheme()
const chartRef = ref(null)
let chartInstance = null

// 1. 初始化與 RWD 監聽
onMounted(() => {
  window.addEventListener('resize', handleResize)
})

// 2. 清理資源
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})

// 3. 監聽主題變更並重繪
watch(isDark, () => {
  nextTick(renderChart)
})

const renderChart = () => {
  if (chartInstance) chartInstance.dispose() // 必須銷毀舊實例以切換主題
  // 初始化時傳入主題 (undefined 為 light, 'dark' 為 dark)
  chartInstance = echarts.init(chartRef.value, isDark.value ? 'dark' : undefined)
  
  chartInstance.setOption({
    backgroundColor: 'transparent', // 必須透明以適配卡片背景
    // ... options
  })
}

const handleResize = () => chartInstance?.resize()
```

## 4. 編碼規範 (Coding Standards)

1.  **Vue 風格**: 統一使用 `<script setup>` 語法。
2.  **API 呼叫**: 
    - 不要在組件內直接使用 `axios`。
    - 必須在 `src/api/index.js` 定義方法，再於組件中引入。
3.  **UI 組件**:
    - 全部使用 Element Plus 組件 (`el-card`, `el-button`, `el-table` 等)。
    - 卡片必須添加 `shadow="hover"`。
4.  **變數命名**:
    - 響應式變數: 使用 `const count = ref(0)`。
    - 函數: 使用動詞開頭，如 `fetchData`, `handleResize`。

## 5. 新增頁面流程

1.  在 `src/views/` 建立 `.vue` 檔案。
2.  使用 `<template><div class="page-container">...</template>` 結構。
3.  在 `src/router/index.js` 註冊路由。
4.  在 `src/App.vue` 的 `menuItems` 陣列中加入導航連結。

## 6. 維護注意事項

- **API 模擬**: 目前專案可能包含 `setTimeout` 模擬延遲，對接真實後端時請移除模擬代碼，直接回傳 API 結果。
- **依賴管理**: 若新增 npm 套件，請確保不與 Element Plus 或 Vite 衝突。
