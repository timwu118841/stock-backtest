"""
回測相關 API 端點
"""

from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime

from app.models.backtest import (
    BacktestRequest,
    BacktestResult,
    BacktestHistoryItem,
    OptimizeRequest,
    OptimizeResult,
    CompareRequest,
)
from app.services.backtest_engine import run_full_backtest, BacktestEngine

router = APIRouter(prefix="/api/backtest", tags=["Backtest"])

# 模擬資料庫 - 存儲回測結果
backtest_results_db: List[BacktestResult] = []
next_backtest_id = 1


@router.post("/run", response_model=BacktestResult)
async def run_backtest(request: BacktestRequest):
    """
    執行策略回測

    - 從 yfinance 取得股票歷史數據
    - 根據策略類型計算技術指標
    - 模擬交易並計算績效指標
    """
    global next_backtest_id

    try:
        result = run_full_backtest(request, next_backtest_id)

        # 存入模擬資料庫
        backtest_results_db.append(result)
        next_backtest_id += 1

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"回測執行失敗: {str(e)}")


@router.get("/history", response_model=List[BacktestHistoryItem])
async def get_history():
    """取得所有回測歷史紀錄"""
    history = []

    for result in reversed(backtest_results_db):  # 最新的排前面
        # 判斷狀態
        if result.summary.total_return > 5:
            status = "success"
        elif result.summary.total_return >= 0:
            status = "warning"
        else:
            status = "danger"

        history.append(
            BacktestHistoryItem(
                id=result.id,
                date=result.created_at,
                strategy=result.strategy_name,
                stock=result.stock_symbol,
                return_pct=result.summary.total_return,
                win_rate=result.summary.win_rate,
                status=status,
            )
        )

    return history


@router.get("/result/{backtest_id}", response_model=BacktestResult)
async def get_backtest_result(backtest_id: int):
    """取得單一回測詳細結果"""
    for result in backtest_results_db:
        if result.id == backtest_id:
            return result

    raise HTTPException(status_code=404, detail="找不到該回測紀錄")


@router.delete("/history/{backtest_id}")
async def delete_history(backtest_id: int):
    """刪除回測紀錄"""
    global backtest_results_db

    original_len = len(backtest_results_db)
    backtest_results_db = [r for r in backtest_results_db if r.id != backtest_id]

    if len(backtest_results_db) == original_len:
        raise HTTPException(status_code=404, detail="找不到該回測紀錄")

    return {"message": "刪除成功", "id": backtest_id}


@router.post("/debug")
async def debug_backtest(request: BacktestRequest):
    """調試端點：返回訊號統計信息"""
    try:
        engine = BacktestEngine(request)
        engine.fetch_data()
        engine.calculate_indicators()
        engine.generate_signals()

        df = engine.df
        signal_stats = {
            "total_days": len(df),
            "buy_signals": int((df["Signal"] == 1).sum()),
            "sell_signals": int((df["Signal"] == -1).sum()),
            "first_signal_date": None,
            "last_signal_date": None,
            "sample_signals": [],
        }

        # 找出有訊號的日期
        signal_dates = df[df["Signal"] != 0][["Date", "Signal", "Close"]].head(20)
        if not signal_dates.empty:
            signal_stats["sample_signals"] = signal_dates.to_dict("records")
            all_signals = df[df["Signal"] != 0]
            if not all_signals.empty:
                signal_stats["first_signal_date"] = all_signals.iloc[0]["Date"]
                signal_stats["last_signal_date"] = all_signals.iloc[-1]["Date"]

        return signal_stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"調試失敗: {str(e)}")
