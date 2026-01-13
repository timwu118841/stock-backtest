# 股票策略回測系統 (Stock Backtesting System)

這是一個功能強大的全端股票策略回測系統，旨在幫助投資者與開發者測試、比較並優化其投資策略。系統結合了 Python 的強大計算能力（FastAPI, Pandas, yfinance）與 Vue 3 的現代化視覺化前端（Element Plus, ECharts）。

## 🚀 系統概述

本系統提供了一個直觀的介面，讓使用者可以：
- **自定義策略回測**：支援多種技術指標策略，並可調整詳細參數。
- **定期定額 (DCA)**：模擬真實的定期定額投資，支援單股票與多股票配置。
- **參數最佳化**：透過網格搜尋 (Grid Search) 找出特定策略的最佳參數組合。
- **策略比較**：視覺化對比不同回測結果的績效曲線。
- **詳細統計**：提供年化報酬率、夏普比率、最大回撤等專業金融指標。

---

## 🏗️ 系統架構

系統採用前後端分離架構：

### 後端 (Backend) - FastAPI
- **位置**: `/backend`
- **職責**: 負責數據獲取 (Yahoo Finance)、技術指標計算、回測引擎模擬、績效指標統計以及 API 端點提供。
- **核心引擎**: `BacktestEngine` 類別處理所有的模擬邏輯。

### 前端 (Frontend) - Vue 3
- **位置**: `/frontend`
- **職責**: 提供使用者介面，透過 Axios 與後端 API 通訊，並使用 ECharts 呈現動態圖表。
- **響應式設計**: 使用 Element Plus 組件庫，確保在不同裝置上的良好體驗。

---

## 🛠️ 技術棧

| 類別 | 技術 |
| :--- | :--- |
| **後端框架** | FastAPI (Python) |
| **數據分析** | Pandas, NumPy |
| **金融數據** | yfinance (Yahoo Finance API) |
| **前端框架** | Vue 3 (Composition API) |
| **構建工具** | Vite |
| **UI 組件** | Element Plus |
| **資料視覺化** | ECharts (vue-echarts) |
| **HTTP 客戶端** | Axios |

---

## 🌟 主要功能

### 1. 儀表板 (Dashboard)
查看系統概況，包括總回測次數、獲利策略比例及平均回報等摘要資訊。

### 2. 策略回測 (Backtest)
支援 6 種核心策略類型，每種策略皆可自定義參數：
- **MA_CROSS (均線交差)**: 短期均線突破長期均線買入，跌破賣出。
- **RSI (相對強弱指數)**: 超賣區買入，超買區賣出。
- **MACD (平滑異同移動平均線)**: MACD 線與訊號線交差訊號。
- **BOLLINGER (布林通道)**: 價格觸及下軌買入，觸及上軌賣出。
- **DCA (定期定額)**: 每月或每年定額買入，支援多股票權重配置。
- **SMA_BREAKOUT (SMA 突破)**: 價格突破長週期 SMA (如 200日) 買入。

### 3. 參數最佳化 (Optimize)
針對均線策略，使用者可以設定參數範圍與步長，系統會自動跑完所有組合並以 **熱圖 (Heatmap)** 呈現各組合的報酬率。

### 4. 策略比較 (Compare)
從歷史紀錄中選擇多個回測，將它們的權益曲線 (Equity Curve) 重疊在同一個圖表上進行對比。

### 5. 歷史紀錄 (History)
管理所有跑過的回測紀錄，查看詳細成交明細 (Trade Logs)，並支援導出 CSV。

---

## 📋 API 文件

所有 API 基礎 URL 為: `http://localhost:8000/api`

### 回測相關 API (`/backtest`)

#### 執行回測
- **端點**: `POST /run`
- **請求格式**:
```json
{
  "strategy_name": "我的雙均線策略",
  "stock_symbol": "AAPL",
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "initial_capital": 1000000,
  "strategy_type": "MA_CROSS",
  "short_period": 5,
  "long_period": 20
}
```
- **回應**: 包含 `summary` (績效摘要)、`price_data` (圖表數據)、`trades` (交易紀錄)。

#### 獲取歷史紀錄
- **端點**: `GET /history`
- **回應**: 簡化版的回測列表。

#### 刪除紀錄
- **端點**: `DELETE /history/{id}`

### 策略分析 API (`/strategy`)

#### 策略比較
- **端點**: `POST /compare`
- **請求格式**: `{"ids": [1, 2, 3]}`

#### 參數最佳化
- **端點**: `POST /optimize`
- **請求格式**: 包含 `param1_range` (最小/最大值) 與 `param1_step`。

---

## ⚙️ 安裝與設定

### 後端安裝步驟

1. 進入後端目錄:
   ```bash
   cd backend
   ```
2. 建立並啟用虛擬環境:
   ```bash
   python -m venv venv
   source venv/bin/activate  # macOS/Linux
   # 或 venv\Scripts\activate # Windows
   ```
3. 安裝相依套件:
   ```bash
   pip install -r requirements.txt
   ```
4. 啟動服務:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

### 前端安裝步驟

1. 進入前端目錄:
   ```bash
   cd frontend
   ```
2. 安裝套件:
   ```bash
   npm install
   ```
3. 啟動開發伺服器:
   ```bash
   npm run dev
   ```

---

## 💡 使用範例

### 範例 1：執行一個簡單的 RSI 回測
1. 在導覽列點選「策略回測」。
2. 輸入股票代碼 (如 `TSLA`)。
3. 選擇策略類型為 `RSI`。
4. 設定 RSI 週期為 `14`，買入點 `30`，賣出點 `70`。
5. 點選「執行回測」，查看下方生成的價格圖與資產增值曲線。

### 範例 2：多股票定期定額配置
1. 選擇 `DCA` 策略。
2. 開啟「多股票配置」開關。
3. 新增 `VOO (0.5)` 與 `QQQ (0.5)`。
4. 設定每月投入金額與扣款日。
5. 點選執行，系統將模擬按比例分配的投資組合績效。

---

## 🛠️ 開發指南

- **新增策略**:
  1. 在 `backend/app/models/backtest.py` 的 `StrategyType` 列舉新增類型。
  2. 在 `backend/app/services/backtest_engine.py` 的 `calculate_indicators` 與 `generate_signals` 加入邏輯。
  3. 在前端 `Backtest.vue` 的表單中加入對應的參數輸入欄位。
- **環境變數**:
  - 後端預設使用 `8000` 端口。
  - 前端 API 調用地址設定於 `frontend/src/api/index.js`。

---

## 📄 授權說明
本專案採用 MIT 授權協議。數據由 Yahoo Finance 提供，回測結果僅供參考，不構成投資建議。
