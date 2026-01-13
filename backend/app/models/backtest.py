"""
Pydantic models for backtest API
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class StrategyType(str, Enum):
    MA_CROSS = "MA_CROSS"
    RSI = "RSI"
    MACD = "MACD"
    BOLLINGER = "BOLLINGER"
    DCA = "DCA"  # 定期定額
    SMA_BREAKOUT = "SMA_BREAKOUT"  # SMA 突破策略


class InvestmentInterval(str, Enum):
    MONTHLY = "MONTHLY"  # 每月投入
    YEARLY = "YEARLY"  # 每年投入


class StockAllocation(BaseModel):
    """股票配置（用於多股票DCA）"""

    stock_symbol: str
    allocation_ratio: float = Field(ge=0, le=1)  # 分配比例 0-1

    @field_validator("allocation_ratio")
    @classmethod
    def validate_ratio(cls, v):
        if v < 0 or v > 1:
            raise ValueError("allocation_ratio must be between 0 and 1")
        return v


class BacktestRequest(BaseModel):
    """回測請求參數"""

    strategy_name: str
    stock_symbol: str
    start_date: str  # YYYY-MM-DD
    end_date: str
    initial_capital: float = Field(default=1000000, ge=0)  # 最低為 0
    strategy_type: StrategyType = StrategyType.MA_CROSS

    # MA Cross 參數
    short_period: int = 5
    long_period: int = 20

    # RSI 參數
    rsi_period: int = 14
    rsi_buy: int = 30
    rsi_sell: int = 70

    # MACD 參數
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9

    # Bollinger 參數
    bb_period: int = 20
    bb_std: float = 2.0

    # DCA 定期定額參數
    dca_amount: float = 10000  # 每次投入金額
    dca_day: int = 1  # 每月第幾天買入 (1-31)
    dca_month: int = 1  # 每年第幾月買入 (1-12)，僅用於年度投入
    dca_interval: InvestmentInterval = InvestmentInterval.MONTHLY  # 投入週期

    # 多股票 DCA 參數
    stock_allocations: Optional[List[StockAllocation]] = None  # 多股票配置

    @field_validator("stock_allocations")
    @classmethod
    def validate_allocations(cls, v):
        if v is not None and len(v) > 0:
            total_ratio = sum(item.allocation_ratio for item in v)
            if abs(total_ratio - 1.0) > 0.001:  # 允許小誤差
                raise ValueError(
                    f"Stock allocation ratios must sum to 1.0, got {total_ratio}"
                )
        return v

    # 進階交易設定
    sell_ratio: float = 1.0  # 賣出比例 (0.1 ~ 1.0)，預設 1.0 (全賣)

    # SMA Breakout 參數
    sma_period: int = 200  # SMA 週期


class TradeRecord(BaseModel):
    """單筆交易紀錄"""

    date: str
    action: str  # BUY / SELL
    price: float
    shares: int
    value: float
    fee: float = 0.0  # 手續費
    tax: float = 0.0  # 交易稅
    balance: float  # 帳戶餘額 (現金)
    total_assets: float  # 總資產
    pnl: Optional[float] = None  # 對於 DCA：未實現報酬率(%)；對於其他策略：實現損益金額
    pnl_amount: Optional[float] = None  # 未實現損益金額（僅供參考）
    stock_symbol: Optional[str] = None  # 股票代碼（多股票DCA時使用）


class BacktestSummary(BaseModel):
    """回測績效摘要"""

    total_return: float
    annualized_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    profit_trades: int
    loss_trades: int
    avg_profit: float
    avg_loss: float
    total_cost: Optional[float] = 0.0  # 總投入成本 (特別是 DCA)


class PriceData(BaseModel):
    """價格資料"""

    dates: List[str]
    prices: List[float]  # 单股票时使用
    ma_short: List[Optional[float]]
    ma_long: List[Optional[float]]
    # 多股票DCA时使用
    multi_stock_prices: Optional[Dict[str, List[float]]] = (
        None  # {stock_symbol: [prices]}
    )


class EquityData(BaseModel):
    """權益曲線資料"""

    dates: List[str]
    equity: List[float]


class BacktestResult(BaseModel):
    """回測結果"""

    id: int
    strategy_name: str
    stock_symbol: str
    strategy_type: str
    start_date: str
    end_date: str
    initial_capital: float
    final_capital: float
    created_at: str
    summary: BacktestSummary
    price_data: PriceData
    equity_data: EquityData
    trades: List[TradeRecord]
    params: Dict[str, Any]


class BacktestHistoryItem(BaseModel):
    """歷史紀錄列表項目 (簡化版)"""

    id: int
    date: str
    strategy: str
    stock: str
    return_pct: float
    win_rate: float
    status: str  # success / warning / danger


class OptimizeRequest(BaseModel):
    """參數最佳化請求"""

    strategy_type: StrategyType
    stock_symbol: str
    start_date: str
    end_date: str
    param1_range: List[int]  # [min, max]
    param1_step: int
    param2_range: List[int]
    param2_step: int


class OptimizeResult(BaseModel):
    """最佳化結果"""

    best_param1: int
    best_param2: int
    best_return: float
    best_sharpe: float
    heatmap_data: List[List[Any]]  # [[x, y, value], ...]
    x_labels: List[int]
    y_labels: List[int]


class CompareRequest(BaseModel):
    """策略比較請求"""

    ids: List[int]
