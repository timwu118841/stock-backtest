# Backend Agent Guide

這份文件是 **Stock Backtesting App 後端** 的開發指南。
當你需要修改、擴充或維護後端代碼時，請嚴格遵守以下架構與規範。

## 1. 技術棧 (Tech Stack)

- **核心框架**: FastAPI (Python 3.10+)
- **Web 伺服器**: Uvicorn (ASGI)
- **數據驗證**: Pydantic v2
- **數據分析**: 
  - pandas (數據處理與回測計算)
  - numpy (數值計算)
- **股票數據源**: yfinance 1.0+ (Yahoo Finance API)
- **技術指標計算**: 原生實作 (使用 pandas rolling/ewm 方法)
- **跨域處理**: CORS Middleware

## 2. 目錄結構 (Directory Structure)

```
backend/
├── main.py                       # FastAPI 應用入口
├── app/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── backtest.py           # Pydantic 資料模型定義
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── backtest.py           # 回測相關路由 (POST /api/backtest/run)
│   │   └── strategy.py           # 策略相關路由
│   └── services/
│       ├── __init__.py
│       └── backtest_engine.py    # 核心回測引擎邏輯
├── requirements.txt              # Python 依賴套件
└── venv/                         # 虛擬環境 (不納入版控)
```

## 3. 核心架構與模式

### 3.1 分層架構 (Layered Architecture)

```
┌─────────────────────┐
│   Routers (API)     │  ← 處理 HTTP 請求/響應、參數驗證
├─────────────────────┤
│   Services (Logic)  │  ← 核心業務邏輯 (BacktestEngine)
├─────────────────────┤
│   Models (Data)     │  ← Pydantic 模型定義
└─────────────────────┘
```

**原則**:
- **Routers** 只負責接收請求、驗證參數、呼叫 Service、回傳結果
- **Services** 包含所有業務邏輯，不直接處理 HTTP
- **Models** 定義資料結構，確保型別安全

### 3.2 回測引擎核心邏輯 (`backtest_engine.py`)

**流程**:
1. `fetch_data()` - 從 yfinance 取得股價歷史數據
2. `calculate_indicators()` - 計算技術指標 (MA, RSI, MACD, Bollinger, SMA)
3. `generate_signals()` - 根據指標產生買賣訊號 (1=買入, -1=賣出, 0=持有)
4. `run_backtest()` - 執行回測模擬交易，計算每日權益曲線
5. `calculate_metrics()` - 計算績效指標 (總報酬、年化報酬、夏普比率、最大回撤等)

**重要實作細節**:

#### DCA 策略特殊處理
DCA (定期定額) 策略與其他策略有本質差異：

```python
# DCA 策略：每月自動補充資金 (模擬薪水投入)
if strategy == StrategyType.DCA:
    if signal == 1:  # 每月買入日
        cash += dca_amount  # 自動注入資金
        buy_shares = int(dca_amount // price)
        # ...記錄交易，計算未實現報酬率 (%)
```

**關鍵差異**:
- **其他策略**: `pnl` 顯示實現損益金額 (賣出時計算)
- **DCA 策略**: `pnl` 顯示未實現報酬率百分比 (持續持有)
- **期末結算**: DCA 策略會添加 `action="HOLD"` 的最終記錄，顯示總報酬率

#### 報酬率計算差異

```python
# DCA 策略: 相對於總投入金額計算
buy_trades = [t for t in trades if t.action == "BUY"]
total_invested = sum(t.value for t in buy_trades)
total_return = ((final_equity - total_invested) / total_invested) * 100

# 其他策略: 相對於初始資金計算
total_return = ((final_capital - initial_capital) / initial_capital) * 100
```

### 3.3 yfinance 數據處理

**重要**: yfinance 1.0 改用 `Ticker.history()` 方法，並且回傳 timezone-aware datetime。

```python
ticker = yf.Ticker(symbol)
df = ticker.history(
    start=start_date,
    end=end_date,
    auto_adjust=True,  # 自動調整股價 (考慮股利、分割)
)

# 處理時區問題
df = df.reset_index()
if hasattr(df["Date"].dtype, "tz") and df["Date"].dt.tz is not None:
    df["Date"] = df["Date"].dt.tz_localize(None)  # 移除時區
df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
```

**支援的股票格式**:
- 台股: `2330.TW` (台積電)
- 美股: `AAPL`, `GOOGL`
- 港股: `0700.HK`

## 4. API 端點規範 (API Endpoints)

### 4.1 回測執行

**POST** `/api/backtest/run`

**Request Body**:
```json
{
  "strategy_name": "測試策略",
  "stock_symbol": "2330.TW",
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "initial_capital": 1000000,
  "strategy_type": "DCA",
  "dca_amount": 10000,
  "dca_day": 1
}
```

**Response**: `BacktestResult` 物件 (包含 summary, trades, price_data, equity_data)

### 4.2 健康檢查

**GET** `/api/health`

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-12T17:30:00"
}
```

## 5. 編碼規範 (Coding Standards)

### 5.1 Python 風格
- 遵循 **PEP 8** 規範
- 使用 **Type Hints** (如 `def fetch_data(self) -> pd.DataFrame:`)
- Docstring 使用三引號 `"""說明"""`

### 5.2 錯誤處理
```python
# 使用 FastAPI HTTPException
from fastapi import HTTPException

if df.empty:
    raise HTTPException(
        status_code=400,
        detail=f"無法取得 {symbol} 的數據，請確認股票代碼是否正確"
    )
```

### 5.3 Pydantic 模型使用
- 所有 API 輸入必須定義為 Pydantic Model (如 `BacktestRequest`)
- 所有 API 輸出必須符合 Pydantic Model (如 `BacktestResult`)
- 使用 `Optional[T]` 標註可選欄位
- 使用 `Enum` 定義固定選項 (如 `StrategyType`)

### 5.4 數據處理原則
- **避免資料洩漏**: 回測邏輯中不得使用未來資料 (No look-ahead bias)
- **正確使用 `.shift()`**: 訊號生成時必須比較當日與前一日指標
  ```python
  # 正確: 短均線由下向上穿越長均線
  df.loc[
      (df["MA_Short"] > df["MA_Long"]) &
      (df["MA_Short"].shift(1) <= df["MA_Long"].shift(1)),
      "Signal"
  ] = 1
  ```
- **處理 NaN 值**: 技術指標初期會產生 NaN，需妥善處理

## 6. 新增策略流程

### 步驟 1: 在 `models/backtest.py` 定義策略類型
```python
class StrategyType(str, Enum):
    NEW_STRATEGY = "NEW_STRATEGY"
```

### 步驟 2: 在 `BacktestRequest` 添加策略參數
```python
new_param1: int = 10
new_param2: float = 1.5
```

### 步驟 3: 在 `backtest_engine.py` 實作邏輯

```python
# 3.1 calculate_indicators() 添加指標計算
elif strategy == StrategyType.NEW_STRATEGY:
    df["Indicator"] = df["Close"].rolling(window=self.request.new_param1).mean()

# 3.2 generate_signals() 添加訊號生成
elif strategy == StrategyType.NEW_STRATEGY:
    df.loc[condition, "Signal"] = 1  # 買入
    df.loc[condition, "Signal"] = -1  # 賣出

# 3.3 run_backtest() 添加特殊交易邏輯 (如需要)
# 一般策略使用標準 buy/sell 邏輯，不需修改
```

### 步驟 4: 測試
```bash
curl -X POST http://localhost:8000/api/backtest/run \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_type": "NEW_STRATEGY",
    "stock_symbol": "2330.TW",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "new_param1": 20
  }'
```

## 7. 維護注意事項

### 7.1 資料快取
目前每次回測都重新抓取數據。若需要最佳化效能，可考慮：
- 使用 Redis 快取歷史數據 (TTL = 1 day)
- 使用 SQLite 儲存回測歷史

### 7.2 yfinance 限制
- **速率限制**: Yahoo Finance 有 API 呼叫頻率限制，避免短時間大量請求
- **數據延遲**: 即時數據有 15 分鐘延遲
- **數據缺失**: 部分冷門股票可能無數據

### 7.3 效能最佳化
- **參數最佳化**: 熱力圖運算會執行數百次回測，考慮使用多進程 (multiprocessing)
- **向量化運算**: 優先使用 pandas 向量化操作，避免迴圈

### 7.4 虛擬環境管理
```bash
# 啟動虛擬環境
source venv/bin/activate

# 安裝依賴
pip install -r requirements.txt

# 更新依賴清單
pip freeze > requirements.txt

# 啟動開發伺服器
uvicorn main:app --reload --port 8000
```

## 8. 常見問題 (FAQ)

**Q: DCA 策略為什麼 initial_capital 是 0？**  
A: DCA 模擬每月薪水投入，不需要初始資金。每次買入時會自動補充 `dca_amount`。

**Q: 為什麼最大回撤是負數？**  
A: 回撤以百分比表示下跌幅度，負數表示虧損。例如 -10.5% 表示最大虧損 10.5%。

**Q: 如何支援更多股票市場？**  
A: yfinance 支援全球主要市場，只需使用正確的股票代碼後綴 (如 `.TW`, `.HK`, `.L`)。

**Q: 期末結算 (HOLD) 記錄的目的？**  
A: 對於 DCA 等持續持有策略，期末結算記錄顯示回測結束時的總報酬率，方便與摘要數據對照。

## 9. 測試與除錯

### 9.1 手動測試範例

```bash
# 測試 DCA 策略 (台股)
curl -X POST http://localhost:8000/api/backtest/run \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_name": "台積電定期定額",
    "stock_symbol": "2330.TW",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "initial_capital": 0,
    "strategy_type": "DCA",
    "dca_amount": 10000,
    "dca_day": 1
  }'

# 測試 MA Cross 策略 (美股)
curl -X POST http://localhost:8000/api/backtest/run \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_name": "蘋果均線策略",
    "stock_symbol": "AAPL",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "initial_capital": 100000,
    "strategy_type": "MA_CROSS",
    "short_period": 5,
    "long_period": 20
  }'
```

### 9.2 檢查後端日誌

```bash
# 查看 uvicorn 輸出
tail -f /tmp/backend.log

# 或直接運行 (前台模式)
uvicorn main:app --reload --port 8000
```

### 9.3 API 文件
FastAPI 自動生成互動式文件：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

**最後更新**: 2026-01-12  
**維護者**: Backend Development Team
