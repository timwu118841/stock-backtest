"""
股票回測引擎 - 使用 yfinance 取得數據，pandas 進行回測計算
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

from app.models.backtest import (
    BacktestRequest,
    BacktestResult,
    BacktestSummary,
    PriceData,
    EquityData,
    TradeRecord,
    StrategyType,
    InvestmentInterval,
)


class BacktestEngine:
    """回測引擎核心類別"""

    def __init__(self, request: BacktestRequest):
        self.request = request
        self.df: Optional[pd.DataFrame] = None
        self.trades: List[TradeRecord] = []
        self.equity_curve: List[float] = []
        self.total_invested: float = 0.0  # 總投入本金 (初始 + 追加)

    def fetch_data(self) -> pd.DataFrame:
        """從 yfinance 取得股票數據"""
        symbol = self.request.stock_symbol

        # 使用 Ticker.history() 方法 (yfinance 1.0 推薦方式)
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(
                start=self.request.start_date,
                end=self.request.end_date,
                auto_adjust=True,
            )
        except Exception as e:
            raise ValueError(f"無法取得 {symbol} 的數據: {str(e)}")

        if df.empty:
            raise ValueError(f"無法取得 {symbol} 的數據，請確認股票代碼是否正確")

        # 處理 timezone-aware datetime
        df = df.reset_index()
        if hasattr(df["Date"].dtype, "tz") and df["Date"].dt.tz is not None:
            # 移除時區信息，只保留日期
            df["Date"] = df["Date"].dt.tz_localize(None)
        df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")

        self.df = df
        return df

    def calculate_indicators(self) -> None:
        """計算技術指標"""
        if self.df is None:
            raise ValueError("請先呼叫 fetch_data()")

        df = self.df
        strategy = self.request.strategy_type

        if strategy == StrategyType.MA_CROSS:
            df["MA_Short"] = (
                df["Close"].rolling(window=self.request.short_period).mean()
            )
            df["MA_Long"] = df["Close"].rolling(window=self.request.long_period).mean()

        elif strategy == StrategyType.RSI:
            delta = df["Close"].diff()
            gain = (
                (delta.where(delta > 0, 0))
                .rolling(window=self.request.rsi_period)
                .mean()
            )
            loss = (
                (-delta.where(delta < 0, 0))
                .rolling(window=self.request.rsi_period)
                .mean()
            )
            rs = gain / loss
            df["RSI"] = 100 - (100 / (1 + rs))

        elif strategy == StrategyType.MACD:
            exp1 = df["Close"].ewm(span=self.request.macd_fast, adjust=False).mean()
            exp2 = df["Close"].ewm(span=self.request.macd_slow, adjust=False).mean()
            df["MACD"] = exp1 - exp2
            df["Signal"] = (
                df["MACD"].ewm(span=self.request.macd_signal, adjust=False).mean()
            )

        elif strategy == StrategyType.BOLLINGER:
            df["BB_Mid"] = df["Close"].rolling(window=self.request.bb_period).mean()
            df["BB_Std"] = df["Close"].rolling(window=self.request.bb_period).std()
            df["BB_Upper"] = df["BB_Mid"] + (df["BB_Std"] * self.request.bb_std)
            df["BB_Lower"] = df["BB_Mid"] - (df["BB_Std"] * self.request.bb_std)

        elif strategy == StrategyType.DCA:
            # DCA 不需要技術指標，只需要日期資訊
            pass

        elif strategy == StrategyType.SMA_BREAKOUT:
            # 計算 SMA (預設 200 日)
            df["SMA"] = df["Close"].rolling(window=self.request.sma_period).mean()

        # 通用：計算日期資訊供定期注資使用
        df["Day"] = pd.to_datetime(df["Date"]).dt.day
        df["Month"] = pd.to_datetime(df["Date"]).dt.to_period("M")
        df["MonthNum"] = pd.to_datetime(df["Date"]).dt.month  # 月份數字 (1-12)
        df["Year"] = pd.to_datetime(df["Date"]).dt.to_period("Y")  # 新增年度資訊

        self.df = df

    def generate_signals(self) -> None:
        """生成買賣訊號"""
        if self.df is None:
            raise ValueError("請先呼叫 fetch_data()")

        df = self.df
        strategy = self.request.strategy_type

        df["Signal"] = 0  # 0: 無訊號, 1: 買入, -1: 賣出

        if strategy == StrategyType.MA_CROSS:
            # 短均線上穿長均線 -> 買入
            df.loc[
                (df["MA_Short"] > df["MA_Long"])
                & (df["MA_Short"].shift(1) <= df["MA_Long"].shift(1)),
                "Signal",
            ] = 1
            # 短均線下穿長均線 -> 賣出
            df.loc[
                (df["MA_Short"] < df["MA_Long"])
                & (df["MA_Short"].shift(1) >= df["MA_Long"].shift(1)),
                "Signal",
            ] = -1

        elif strategy == StrategyType.RSI:
            df.loc[
                (df["RSI"] < self.request.rsi_buy)
                & (df["RSI"].shift(1) >= self.request.rsi_buy),
                "Signal",
            ] = 1
            df.loc[
                (df["RSI"] > self.request.rsi_sell)
                & (df["RSI"].shift(1) <= self.request.rsi_sell),
                "Signal",
            ] = -1

        elif strategy == StrategyType.MACD:
            # 使用原始 MACD 欄位，避免與 Signal 欄位衝突
            macd_line = df["MACD"]
            signal_line = (
                df["Close"].ewm(span=self.request.macd_signal, adjust=False).mean()
            )  # 重新計算
            signal_line = macd_line.ewm(
                span=self.request.macd_signal, adjust=False
            ).mean()

            df["Signal"] = 0
            df.loc[
                (macd_line > signal_line)
                & (macd_line.shift(1) <= signal_line.shift(1)),
                "Signal",
            ] = 1
            df.loc[
                (macd_line < signal_line)
                & (macd_line.shift(1) >= signal_line.shift(1)),
                "Signal",
            ] = -1

        elif strategy == StrategyType.BOLLINGER:
            df.loc[df["Close"] < df["BB_Lower"], "Signal"] = 1
            df.loc[df["Close"] > df["BB_Upper"], "Signal"] = -1

        elif strategy == StrategyType.DCA:
            # DCA: 每月或每年指定日期買入（找該週期最接近指定日的交易日）
            target_day = self.request.dca_day
            target_month = self.request.dca_month  # 年度投入時使用
            interval = self.request.dca_interval
            seen_periods = set()

            for idx, row in df.iterrows():
                day = row["Day"]
                month_num = row["MonthNum"]

                if interval == InvestmentInterval.YEARLY:
                    # 年度投入：檢查是否為目標年份的目標月份和日期
                    year = row["Year"]

                    # 每年只買一次，檢查是否為目標月份
                    if year not in seen_periods and month_num == target_month:
                        # 在目標月份中，找到最接近目標日期的交易日
                        if day >= target_day:
                            df.loc[idx, "Signal"] = 1
                            seen_periods.add(year)
                        else:
                            # 檢查是否為該月最後一天
                            next_idx = idx + 1
                            if next_idx < len(df):
                                next_month = df.loc[next_idx, "MonthNum"]
                                next_year = df.loc[next_idx, "Year"]
                                # 如果下一筆資料不是同月，表示這是該月最後一筆
                                if next_month != month_num or next_year != year:
                                    df.loc[idx, "Signal"] = 1
                                    seen_periods.add(year)
                            else:
                                # 最後一筆資料
                                df.loc[idx, "Signal"] = 1
                                seen_periods.add(year)
                else:
                    # 月度投入：每月指定日期買入
                    period = row["Month"]

                    # 每個月只買一次，選擇最接近目標日的交易日
                    if period not in seen_periods and day >= target_day:
                        df.loc[idx, "Signal"] = 1
                        seen_periods.add(period)
                    # 如果月底還沒買到，就在該月最後一天買
                    elif period not in seen_periods:
                        next_idx = idx + 1
                        if next_idx < len(df):
                            next_period = df.loc[next_idx, "Month"]
                            if next_period != period:
                                df.loc[idx, "Signal"] = 1
                                seen_periods.add(period)
                        else:
                            # 最後一筆資料
                            df.loc[idx, "Signal"] = 1
                            seen_periods.add(period)

        elif strategy == StrategyType.SMA_BREAKOUT:
            # 價格上穿 SMA -> 買入
            df.loc[
                (df["Close"] > df["SMA"])
                & (df["Close"].shift(1) <= df["SMA"].shift(1)),
                "Signal",
            ] = 1
            # 價格下穿 SMA -> 賣出
            df.loc[
                (df["Close"] < df["SMA"])
                & (df["Close"].shift(1) >= df["SMA"].shift(1)),
                "Signal",
            ] = -1

        self.df = df

    def run_backtest(self) -> Tuple[List[TradeRecord], List[float]]:
        """執行回測模擬"""
        if self.df is None:
            raise ValueError("請先呼叫 fetch_data()")

        df = self.df
        strategy = self.request.strategy_type
        print(
            f"DEBUG: Starting backtest. Strategy={strategy}, DCA Amount={self.request.dca_amount}",
            flush=True,
        )

        cash = self.request.initial_capital
        shares = 0
        total_cost = 0.0
        equity_curve = []
        trades = []
        entry_price = 0.0
        self.total_invested = cash  # 初始化總投入本金
        seen_periods = set()  # 改用通用的週期追蹤

        for idx, row in df.iterrows():
            price = row["Close"]
            signal = row["Signal"]
            date = row["Date"]

            # === 通用定期注資邏輯 (適用於所有非 DCA 策略) ===
            # 如果設定了每月投入金額，則每月發薪日自動補充現金
            if strategy != StrategyType.DCA and self.request.dca_amount > 0:
                day = row.get("Day")
                month_num = row.get("MonthNum")

                if self.request.dca_interval == InvestmentInterval.YEARLY:
                    # 年度注資
                    year = row.get("Year")
                    target_month = self.request.dca_month

                    if (
                        day is not None
                        and year is not None
                        and month_num == target_month
                    ):
                        target_day = self.request.dca_day
                        is_payday = False

                        if year not in seen_periods:
                            if day >= target_day:
                                is_payday = True
                            else:
                                # 檢查是否為該月最後一筆數據
                                next_idx = idx + 1
                                if next_idx >= len(df):
                                    is_payday = True
                                else:
                                    next_month = df.iloc[next_idx]["MonthNum"]
                                    next_year = df.iloc[next_idx]["Year"]
                                    if next_month != month_num or next_year != year:
                                        is_payday = True

                        if is_payday:
                            dca_amount = self.request.dca_amount
                            cash += dca_amount
                            self.total_invested += dca_amount
                            seen_periods.add(year)
                            print(
                                f"DEBUG: Payday! Year={year}, Month={month_num}, Day={day}, Added={dca_amount}, Total Invested={self.total_invested}"
                            )
                else:
                    # 月度注資
                    period = row.get("Month")

                    # Debug print (只印第一天)
                    if idx == 0:
                        print(
                            f"DEBUG: DCA Amount={self.request.dca_amount}, Day={day}, Period={period}"
                        )

                    if day is not None and period is not None:
                        target_day = self.request.dca_day
                        is_payday = False

                        if period not in seen_periods:
                            if day >= target_day:
                                is_payday = True
                            else:
                                # 檢查是否為該週期最後一筆數據
                                next_idx = idx + 1
                                if next_idx >= len(df):
                                    is_payday = True
                                else:
                                    next_period = df.iloc[next_idx]["Month"]
                                    if next_period != period:
                                        is_payday = True

                        if is_payday:
                            dca_amount = self.request.dca_amount
                            cash += dca_amount
                            self.total_invested += dca_amount
                            seen_periods.add(period)
                            print(
                                f"DEBUG: Payday! Period={period}, Added={dca_amount}, Total Invested={self.total_invested}"
                            )

                # Debug print (只印第一天)
                if idx == 0:
                    print(
                        f"DEBUG: DCA Amount={self.request.dca_amount}, Day={day}, Period={period}"
                    )

                if day is not None and period is not None:
                    target_day = self.request.dca_day
                    is_payday = False

                    if period not in seen_periods:
                        if day >= target_day:
                            is_payday = True
                        else:
                            # 檢查是否為該週期最後一筆數據
                            next_idx = idx + 1
                            if next_idx >= len(df):
                                is_payday = True
                            else:
                                next_period = (
                                    df.iloc[next_idx]["Year"]
                                    if self.request.dca_interval
                                    == InvestmentInterval.YEARLY
                                    else df.iloc[next_idx]["Month"]
                                )
                                if next_period != period:
                                    is_payday = True

                    if is_payday:
                        dca_amount = self.request.dca_amount
                        cash += dca_amount
                        self.total_invested += dca_amount
                        seen_periods.add(period)
                        print(
                            f"DEBUG: Payday! Period={period}, Added={dca_amount}, Total Invested={self.total_invested}"
                        )

            # === 策略執行邏輯 ===
            if strategy == StrategyType.DCA:
                # DCA 策略：每月自動補充資金買入，模擬真實定期定額
                if signal == 1:
                    dca_amount = self.request.dca_amount
                    # 每月自動補充現金（模擬每月薪水投入）
                    cash += dca_amount
                    self.total_invested += dca_amount  # DCA 也要累加總投入

                    buy_shares = int(dca_amount // price)
                    if buy_shares > 0:
                        cost = buy_shares * price
                        cash -= cost
                        total_cost += cost
                        shares += buy_shares

                        # 計算平均成本和未實現報酬率
                        avg_cost = total_cost / shares if shares > 0 else 0
                        current_value = shares * price
                        unrealized_pnl_amount = current_value - total_cost
                        unrealized_pnl_pct = (
                            (unrealized_pnl_amount / total_cost * 100)
                            if total_cost > 0
                            else 0
                        )

                        trades.append(
                            TradeRecord(
                                date=date,
                                action="BUY",
                                price=round(price, 2),
                                shares=buy_shares,
                                value=round(cost, 2),
                                balance=round(cash, 2),
                                total_assets=round(cash + shares * price, 2),
                                pnl=round(unrealized_pnl_pct, 2),  # 未實現報酬率(%)
                                pnl_amount=round(
                                    unrealized_pnl_amount, 2
                                ),  # 未實現損益金額
                            )
                        )
            else:
                # 其他策略 (MA, RSI, MACD, Bollinger, SMA_BREAKOUT)

                # 買入訊號且有現金 (全倉買入)
                # 這裡原本是 shares == 0 才買，現在改為：只要有訊號且有錢就買 (加碼)
                # 但為了避免頻繁交易，通常策略是「空手才買」或是「加碼」。
                # 傳統回測通常是 shares == 0 才買。
                # 但既然有了資金注入，使用者可能希望「有錢就加碼」。
                # 不過，如果每天都出訊號，會導致每天都買一點點碎股。
                # 為了符合一般策略邏輯：
                # 1. 如果 signal == 1 且 shares == 0: 建倉 (買滿)
                # 2. 如果 signal == 1 且 shares > 0: 加碼? (通常只有突破策略會加碼)
                # 為了簡單且符合直覺：只要有 BUY 訊號，且手上有足夠現金買至少 1 股，就買入。

                can_buy = False
                if signal == 1:
                    # 如果是反轉策略(如 RSI)，通常是空手才買。但如果有新資金，應該允許加碼。
                    # 我們採取：有 BUY 訊號就用盡現金買入。
                    can_buy = True

                if can_buy:
                    buy_shares = int(cash // price)
                    if buy_shares > 0:
                        cost = buy_shares * price
                        cash -= cost

                        # 更新平均成本 (加權平均)
                        if shares > 0:
                            total_cost += cost
                        else:
                            total_cost = cost
                            entry_price = price  # 僅供參考

                        shares += buy_shares

                        trades.append(
                            TradeRecord(
                                date=date,
                                action="BUY",
                                price=round(price, 2),
                                shares=buy_shares,
                                value=round(cost, 2),
                                balance=round(cash, 2),
                                total_assets=round(cash + shares * price, 2),
                                pnl=None,
                            )
                        )

                # 賣出訊號且有持倉
                elif signal == -1 and shares > 0:
                    # 計算賣出股數 (根據 sell_ratio)
                    sell_ratio = self.request.sell_ratio
                    # 確保 sell_ratio 在合理範圍
                    if sell_ratio <= 0:
                        sell_ratio = 1.0
                    if sell_ratio > 1:
                        sell_ratio = 1.0

                    sell_shares = int(shares * sell_ratio)

                    if sell_shares > 0:
                        revenue = sell_shares * price

                        # 計算這部分賣出的成本 (按比例)
                        # 平均成本法
                        avg_cost = total_cost / shares
                        sold_cost = avg_cost * sell_shares

                        pnl = revenue - sold_cost
                        cash += revenue

                        # 更新剩餘持倉成本
                        total_cost -= sold_cost
                        shares -= sell_shares

                        trades.append(
                            TradeRecord(
                                date=date,
                                action="SELL",
                                price=round(price, 2),
                                shares=sell_shares,
                                value=round(revenue, 2),
                                balance=round(cash, 2),
                                total_assets=round(cash + shares * price, 2),
                                pnl=round(pnl, 2),
                            )
                        )

                        # 如果全部賣光，重置 total_cost (避免浮點數誤差)
                        if shares == 0:
                            total_cost = 0.0

            # 記錄當日權益

            # 記錄當日權益
            current_equity = cash + shares * price
            equity_curve.append(round(current_equity, 2))

        # 回測結束時處理
        last_date = df.iloc[-1]["Date"]
        last_price = df.iloc[-1]["Close"]

        if strategy == StrategyType.DCA:
            # DCA 策略：添加期末結算記錄，顯示最終報酬率
            if shares > 0:
                # 計算總投入金額（排除 HOLD 記錄）
                buy_trades = [t for t in trades if t.action == "BUY"]
                total_invested = sum(t.value for t in buy_trades)

                final_value = shares * last_price
                final_equity = cash + final_value

                if total_invested > 0:
                    final_pnl_amount = final_equity - total_invested
                    final_pnl_pct = (final_pnl_amount / total_invested) * 100
                else:
                    final_pnl_amount = 0
                    final_pnl_pct = 0

                trades.append(
                    TradeRecord(
                        date=last_date,
                        action="HOLD",  # 期末結算
                        price=round(last_price, 2),
                        shares=shares,
                        value=round(final_value, 2),
                        balance=round(cash, 2),
                        total_assets=round(final_equity, 2),
                        pnl=round(final_pnl_pct, 2),  # 期末總報酬率
                        pnl_amount=round(final_pnl_amount, 2),
                    )
                )
        elif strategy != StrategyType.DCA and shares > 0:
            # 其他策略：如果還有持股，強制平倉
            revenue = shares * last_price
            pnl = revenue - total_cost
            cash += revenue
            trades.append(
                TradeRecord(
                    date=last_date,
                    action="SELL",
                    price=round(last_price, 2),
                    shares=shares,
                    value=round(revenue, 2),
                    balance=round(cash, 2),
                    total_assets=round(cash, 2),
                    pnl=round(pnl, 2),
                )
            )
            shares = 0
            # 更新最後一筆權益
            equity_curve[-1] = round(cash, 2)

        # 清理 NaN/Inf 數值，避免 JSON 序列化錯誤
        equity_curve = [0.0 if np.isnan(x) or np.isinf(x) else x for x in equity_curve]

        for t in trades:
            if t.pnl is not None and (np.isnan(t.pnl) or np.isinf(t.pnl)):
                t.pnl = 0.0
            if t.pnl_amount is not None and (
                np.isnan(t.pnl_amount) or np.isinf(t.pnl_amount)
            ):
                t.pnl_amount = 0.0
            if np.isnan(t.value) or np.isinf(t.value):
                t.value = 0.0
            if np.isnan(t.balance) or np.isinf(t.balance):
                t.balance = 0.0
            if np.isnan(t.total_assets) or np.isinf(t.total_assets):
                t.total_assets = 0.0

        self.trades = trades
        self.equity_curve = equity_curve
        return trades, equity_curve

    def calculate_metrics(self) -> BacktestSummary:
        """計算績效指標"""
        if not self.equity_curve:
            raise ValueError("請先執行 run_backtest()")

        try:
            initial = self.request.initial_capital
            final = self.equity_curve[-1]

            # 對於 DCA 策略，計算方式不同
            if self.request.strategy_type == StrategyType.DCA:
                # ... (略)
                buy_trades = [t for t in self.trades if t.action == "BUY"]
                total_invested = sum(t.value for t in buy_trades)
                if total_invested > 0:
                    total_return = ((final - total_invested) / total_invested) * 100
                else:
                    total_return = 0

                # 年化報酬率
                days = len(self.equity_curve)
                years = days / 252
                if years > 0 and total_invested > 0:
                    annualized_return = (
                        (final / total_invested) ** (1 / years) - 1
                    ) * 100
                else:
                    annualized_return = 0
            else:
                # 一般策略 (含 SMA_BREAKOUT + 定期注資)
                # 使用總投入本金計算 (若有定期注資，total_invested 會大於 initial)
                base_capital = (
                    self.total_invested if self.total_invested > 0 else initial
                )

                if base_capital > 0:
                    total_return = ((final - base_capital) / base_capital) * 100
                else:
                    total_return = 0

                # 年化報酬率 (假設 252 個交易日)
                days = len(self.equity_curve)
                years = days / 252
                if years > 0 and base_capital > 0:
                    # 避免負數底數的冪運算導致複數或錯誤
                    ratio = final / base_capital
                    if ratio > 0:
                        annualized_return = (ratio ** (1 / years) - 1) * 100
                    else:
                        annualized_return = -100  # 全虧
                else:
                    annualized_return = 0

            # 計算每日報酬
            equity_series = pd.Series(self.equity_curve)
            daily_returns = equity_series.pct_change().dropna()

            # 夏普比率 (假設無風險利率為 2%)
            risk_free = 0.02 / 252
            excess_returns = daily_returns - risk_free

            std_dev = excess_returns.std()
            if std_dev > 0 and not np.isnan(std_dev):
                sharpe_ratio = (excess_returns.mean() / std_dev) * np.sqrt(252)
            else:
                sharpe_ratio = 0

            # 最大回撤
            cummax = equity_series.cummax()
            # 避免除以零
            cummax = cummax.replace(0, 1)
            drawdown = (equity_series - cummax) / cummax
            max_drawdown = drawdown.min() * 100

            # 交易統計 (略)
            # ... (這部分沒動，應該沒事) ...

            # 交易統計
            if self.request.strategy_type == StrategyType.DCA:
                # DCA 策略：統計每次買入交易（排除期末 HOLD）
                buy_trades = [t for t in self.trades if t.action == "BUY"]

                # 將每次買入視為一次交易，以未實現報酬率判斷獲利/虧損
                total_trades = len(buy_trades)
                profit_trades_list = [t for t in buy_trades if t.pnl and t.pnl > 0]
                loss_trades_list = [t for t in buy_trades if t.pnl and t.pnl <= 0]

                win_rate = (
                    (len(profit_trades_list) / total_trades * 100)
                    if total_trades > 0
                    else 0
                )
                avg_profit = (
                    np.mean([t.pnl for t in profit_trades_list])
                    if profit_trades_list
                    else 0
                )
                avg_loss = (
                    np.mean([t.pnl for t in loss_trades_list])
                    if loss_trades_list
                    else 0
                )

                profit_trades_count = len(profit_trades_list)
                loss_trades_count = len(loss_trades_list)

                # DCA 總成本 = 累積投入資金
                if self.total_invested > 0:
                    total_cost = self.total_invested
                else:
                    # 兼容舊邏輯：若沒追蹤到 total_invested (理論上不可能)，則回退
                    total_cost = sum(t.value for t in buy_trades)
            else:
                # 其他策略：統計賣出交易
                sell_trades = [t for t in self.trades if t.action == "SELL"]
                profit_trades_list = [t for t in sell_trades if t.pnl and t.pnl > 0]
                loss_trades_list = [t for t in sell_trades if t.pnl and t.pnl <= 0]

                total_trades = len(sell_trades)
                win_rate = (
                    (len(profit_trades_list) / total_trades * 100)
                    if total_trades > 0
                    else 0
                )

                avg_profit = (
                    np.mean([t.pnl for t in profit_trades_list])
                    if profit_trades_list
                    else 0
                )
                avg_loss = (
                    np.mean([t.pnl for t in loss_trades_list])
                    if loss_trades_list
                    else 0
                )

                profit_trades_count = len(profit_trades_list)
                loss_trades_count = len(loss_trades_list)

                # 其他策略總成本
                if self.request.dca_amount > 0:
                    total_cost = self.total_invested
                else:
                    total_cost = self.request.initial_capital

            # 輔助函數：處理 NaN 和 Inf
            def clean_float(val):
                if val is None:
                    return 0.0
                if np.isnan(val) or np.isinf(val):
                    return 0.0
                return float(val)

            return BacktestSummary(
                total_return=round(clean_float(total_return), 2),
                annualized_return=round(clean_float(annualized_return), 2),
                sharpe_ratio=round(clean_float(sharpe_ratio), 2),
                max_drawdown=round(clean_float(max_drawdown), 2),
                win_rate=round(clean_float(win_rate), 2),
                total_trades=total_trades,
                profit_trades=profit_trades_count,
                loss_trades=loss_trades_count,
                avg_profit=round(clean_float(avg_profit), 2),
                avg_loss=round(clean_float(avg_loss), 2),
                total_cost=round(clean_float(total_cost), 2),
            )
        except Exception as e:
            # 發生錯誤時回傳預設值，避免 API 崩潰
            print(f"Error calculating metrics: {e}")
            return BacktestSummary(
                total_return=0,
                annualized_return=0,
                sharpe_ratio=0,
                max_drawdown=0,
                win_rate=0,
                total_trades=0,
                profit_trades=0,
                loss_trades=0,
                avg_profit=0,
                avg_loss=0,
                total_cost=self.total_invested,
            )

    def get_price_data(self) -> PriceData:
        """取得價格資料供前端繪圖"""
        if self.df is None:
            raise ValueError("請先呼叫 fetch_data()")

        df = self.df

        ma_short = df.get("MA_Short", pd.Series([None] * len(df)))
        ma_long = df.get("MA_Long", pd.Series([None] * len(df)))

        def clean_val(v):
            if pd.isna(v) or v is None or np.isinf(v):
                return None
            return round(float(v), 2)

        return PriceData(
            dates=df["Date"].tolist(),
            prices=[
                clean_val(p) or 0.0 for p in df["Close"].tolist()
            ],  # Price 不應該是 None
            ma_short=[clean_val(v) for v in ma_short.tolist()],
            ma_long=[clean_val(v) for v in ma_long.tolist()],
        )

    def get_equity_data(self) -> EquityData:
        """取得權益曲線供前端繪圖"""
        if self.df is None or not self.equity_curve:
            raise ValueError("請先執行回測")

        return EquityData(dates=self.df["Date"].tolist(), equity=self.equity_curve)


def run_full_backtest(request: BacktestRequest, backtest_id: int) -> BacktestResult:
    """執行完整回測流程"""
    # 檢查是否為多股票DCA
    if request.strategy_type == StrategyType.DCA and request.stock_allocations:
        return run_multi_stock_dca(request, backtest_id)

    engine = BacktestEngine(request)

    # 1. 取得數據
    engine.fetch_data()

    # 2. 計算指標
    engine.calculate_indicators()

    # 3. 生成訊號
    engine.generate_signals()

    # 4. 執行回測
    trades, equity = engine.run_backtest()

    # 5. 計算績效
    summary = engine.calculate_metrics()

    # 6. 組裝結果
    return BacktestResult(
        id=backtest_id,
        strategy_name=request.strategy_name,
        stock_symbol=request.stock_symbol,
        strategy_type=request.strategy_type.value,
        start_date=request.start_date,
        end_date=request.end_date,
        initial_capital=request.initial_capital,
        final_capital=equity[-1] if equity else request.initial_capital,
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        summary=summary,
        price_data=engine.get_price_data(),
        equity_data=engine.get_equity_data(),
        trades=trades,
        params={
            "strategy_type": request.strategy_type.value,
            "short_period": request.short_period,
            "long_period": request.long_period,
            "rsi_period": request.rsi_period,
            "rsi_buy": request.rsi_buy,
            "rsi_sell": request.rsi_sell,
        },
    )


def run_multi_stock_dca(request: BacktestRequest, backtest_id: int) -> BacktestResult:
    """執行多股票DCA回測"""
    if not request.stock_allocations:
        raise ValueError("多股票DCA需要提供stock_allocations")

    # 為每個股票創建引擎並取得數據
    stock_engines = {}
    stock_data = {}

    for allocation in request.stock_allocations:
        symbol = allocation.stock_symbol
        # 創建該股票的請求
        stock_request = BacktestRequest(
            strategy_name=f"{request.strategy_name}_{symbol}",
            stock_symbol=symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=0,
            strategy_type=StrategyType.DCA,
            dca_amount=request.dca_amount * allocation.allocation_ratio,
            dca_day=request.dca_day,
            dca_month=request.dca_month,
            dca_interval=request.dca_interval,
        )

        engine = BacktestEngine(stock_request)
        engine.fetch_data()
        engine.calculate_indicators()
        engine.generate_signals()

        stock_engines[symbol] = engine
        stock_data[symbol] = {
            "df": engine.df,
            "ratio": allocation.allocation_ratio,
            "shares": 0,
            "total_cost": 0.0,
        }

    # 執行多股票DCA回測
    cash = request.initial_capital
    total_invested = cash
    all_trades = []
    equity_curve = []
    seen_periods = set()

    # 獲取所有日期（使用第一個股票的日期）
    first_symbol = request.stock_allocations[0].stock_symbol
    dates = stock_engines[first_symbol].df

    for idx, row in dates.iterrows():
        date = row["Date"]
        signal = row.get("Signal", 0)

        # 如果是DCA買入日
        if signal == 1:
            # 注入資金
            cash += request.dca_amount
            total_invested += request.dca_amount

            # 按比例買入各股票
            for allocation in request.stock_allocations:
                symbol = allocation.stock_symbol
                ratio = allocation.allocation_ratio
                amount = request.dca_amount * ratio

                # 找到該股票在這天的價格
                engine = stock_engines[symbol]
                stock_row = engine.df[engine.df["Date"] == date]

                if not stock_row.empty:
                    price = stock_row.iloc[0]["Close"]
                    buy_shares = int(amount // price)

                    if buy_shares > 0:
                        cost = buy_shares * price
                        cash -= cost

                        stock_data[symbol]["shares"] += buy_shares
                        stock_data[symbol]["total_cost"] += cost

                        # 計算當前該股票的未實現報酬
                        current_value = stock_data[symbol]["shares"] * price
                        unrealized_pnl_pct = (
                            (
                                (current_value - stock_data[symbol]["total_cost"])
                                / stock_data[symbol]["total_cost"]
                                * 100
                            )
                            if stock_data[symbol]["total_cost"] > 0
                            else 0
                        )

                        all_trades.append(
                            TradeRecord(
                                date=date,
                                action="BUY",
                                price=round(price, 2),
                                shares=buy_shares,
                                value=round(cost, 2),
                                balance=round(cash, 2),
                                total_assets=round(
                                    cash
                                    + sum(
                                        stock_data[s]["shares"]
                                        * stock_engines[s]
                                        .df[stock_engines[s].df["Date"] == date]
                                        .iloc[0]["Close"]
                                        for s in stock_data.keys()
                                        if not stock_engines[s]
                                        .df[stock_engines[s].df["Date"] == date]
                                        .empty
                                    ),
                                    2,
                                ),
                                pnl=round(unrealized_pnl_pct, 2),
                                stock_symbol=symbol,
                            )
                        )

        # 計算當日總資產
        total_stock_value = 0
        for symbol, data in stock_data.items():
            engine = stock_engines[symbol]
            stock_row = engine.df[engine.df["Date"] == date]
            if not stock_row.empty:
                price = stock_row.iloc[0]["Close"]
                total_stock_value += data["shares"] * price

        equity_curve.append(round(cash + total_stock_value, 2))

    # 計算績效
    final_equity = equity_curve[-1] if equity_curve else 0
    total_return = (
        ((final_equity - total_invested) / total_invested * 100)
        if total_invested > 0
        else 0
    )

    # 完整的績效計算
    # 1. 年化報酬率
    days = len(equity_curve)
    years = days / 252  # 假設252個交易日
    if years > 0 and total_invested > 0:
        ratio = final_equity / total_invested
        if ratio > 0:
            annualized_return = (ratio ** (1 / years) - 1) * 100
        else:
            annualized_return = -100
    else:
        annualized_return = 0

    # 2. 夏普比率
    equity_series = pd.Series(equity_curve)
    daily_returns = equity_series.pct_change().dropna()
    risk_free = 0.02 / 252  # 假設無風險利率 2%
    excess_returns = daily_returns - risk_free
    std_dev = excess_returns.std()
    if std_dev > 0 and not np.isnan(std_dev):
        sharpe_ratio = (excess_returns.mean() / std_dev) * np.sqrt(252)
    else:
        sharpe_ratio = 0

    # 3. 最大回撤
    cummax = equity_series.cummax()
    cummax = cummax.replace(0, 1)  # 避免除以零
    drawdown = (equity_series - cummax) / cummax
    max_drawdown = drawdown.min() * 100

    # 4. 交易統計 (DCA策略)
    buy_trades = [t for t in all_trades if t.action == "BUY"]
    profit_trades_list = [t for t in buy_trades if t.pnl and t.pnl > 0]
    loss_trades_list = [t for t in buy_trades if t.pnl and t.pnl <= 0]

    total_trades = len(buy_trades)
    win_rate = (len(profit_trades_list) / total_trades * 100) if total_trades > 0 else 0
    avg_profit = (
        np.mean([t.pnl for t in profit_trades_list]) if profit_trades_list else 0
    )
    avg_loss = np.mean([t.pnl for t in loss_trades_list]) if loss_trades_list else 0

    # 清理 NaN 和 Inf 值
    def clean_float(val):
        if val is None:
            return 0.0
        if np.isnan(val) or np.isinf(val):
            return 0.0
        return float(val)

    summary = BacktestSummary(
        total_return=round(clean_float(total_return), 2),
        annualized_return=round(clean_float(annualized_return), 2),
        sharpe_ratio=round(clean_float(sharpe_ratio), 2),
        max_drawdown=round(clean_float(max_drawdown), 2),
        win_rate=round(clean_float(win_rate), 2),
        total_trades=total_trades,
        profit_trades=len(profit_trades_list),
        loss_trades=len(loss_trades_list),
        avg_profit=round(clean_float(avg_profit), 2),
        avg_loss=round(clean_float(avg_loss), 2),
        total_cost=total_invested,
    )

    # 返回結果（构建多股票价格数据）
    first_engine = stock_engines[first_symbol]

    # 构建多股票价格数据
    multi_stock_prices = {}
    for symbol in stock_engines.keys():
        engine = stock_engines[symbol]
        prices = [
            round(float(p), 2) if not pd.isna(p) and not np.isinf(p) else 0.0
            for p in engine.df["Close"].tolist()
        ]
        multi_stock_prices[symbol] = prices

    price_data = PriceData(
        dates=first_engine.df["Date"].tolist(),
        prices=[],  # 多股票时不使用单一价格列
        ma_short=[None] * len(first_engine.df),
        ma_long=[None] * len(first_engine.df),
        multi_stock_prices=multi_stock_prices,
    )

    return BacktestResult(
        id=backtest_id,
        strategy_name=request.strategy_name,
        stock_symbol="MULTI_STOCK_DCA",
        strategy_type=request.strategy_type.value,
        start_date=request.start_date,
        end_date=request.end_date,
        initial_capital=request.initial_capital,
        final_capital=final_equity,
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        summary=summary,
        price_data=price_data,
        equity_data=EquityData(
            dates=first_engine.df["Date"].tolist(), equity=equity_curve
        ),
        trades=all_trades,
        params={
            "strategy_type": request.strategy_type.value,
            "dca_interval": request.dca_interval.value,
            "stock_allocations": [
                {"stock_symbol": a.stock_symbol, "allocation_ratio": a.allocation_ratio}
                for a in request.stock_allocations
            ],
        },
    )
