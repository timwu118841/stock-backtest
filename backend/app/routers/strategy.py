"""
策略比較與參數最佳化 API
"""

from fastapi import APIRouter, HTTPException
from typing import List
import numpy as np

from app.models.backtest import (
    OptimizeRequest,
    OptimizeResult,
    CompareRequest,
    BacktestRequest,
    StrategyType,
)
from app.services.backtest_engine import BacktestEngine, optimize_dca_allocation
from app.routers.backtest import backtest_results_db

router = APIRouter(prefix="/api/strategy", tags=["Strategy"])


@router.post("/compare")
async def compare_strategies(request: CompareRequest):
    """
    比較多個回測策略的績效
    """
    if len(request.ids) < 2:
        raise HTTPException(status_code=400, detail="至少需要選擇兩個策略進行比較")

    # 從資料庫取得結果
    results = []
    for id in request.ids:
        found = None
        for r in backtest_results_db:
            if r.id == id:
                found = r
                break
        if not found:
            raise HTTPException(status_code=404, detail=f"找不到 ID 為 {id} 的回測結果")
        results.append(found)

    # 組裝比較資料
    metrics = []
    equity_curves = {"dates": [], "series": []}

    for r in results:
        metrics.append(
            {
                "id": r.id,
                "name": r.strategy_name,
                "totalReturn": r.summary.total_return,
                "annualizedReturn": r.summary.annualized_return,
                "sharpeRatio": r.summary.sharpe_ratio,
                "maxDrawdown": r.summary.max_drawdown,
                "winRate": r.summary.win_rate,
            }
        )

        equity_curves["series"].append(
            {"name": r.strategy_name, "data": r.equity_data.equity}
        )

    # 使用第一個結果的日期作為 X 軸
    if results:
        equity_curves["dates"] = results[0].equity_data.dates

    return {"metrics": metrics, "equityCurves": equity_curves}


@router.post("/optimize", response_model=OptimizeResult)
async def optimize_strategy(request: OptimizeRequest):
    """
    執行策略參數最佳化

    - DCA: 執行資產配置最佳化 (Monte Carlo)
    - 其他: 執行參數網格搜尋 (Grid Search)
    """
    if request.strategy_type == StrategyType.DCA:
        try:
            return optimize_dca_allocation(request)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    try:
        # 建立參數網格
        param1_values = list(
            range(
                request.param1_range[0],
                request.param1_range[1] + 1,
                request.param1_step,
            )
        )
        param2_values = list(
            range(
                request.param2_range[0],
                request.param2_range[1] + 1,
                request.param2_step,
            )
        )

        heatmap_data = []
        best_return = -float("inf")
        best_sharpe = 0
        best_param1 = param1_values[0]
        best_param2 = param2_values[0]

        # 網格搜尋
        for i, p1 in enumerate(param1_values):
            for j, p2 in enumerate(param2_values):
                # 確保長週期大於短週期
                if p2 <= p1:
                    heatmap_data.append([i, j, None])
                    continue

                # 建立回測請求
                bt_request = BacktestRequest(
                    strategy_name=f"Optimize_{p1}_{p2}",
                    stock_symbol=request.stock_symbol,
                    start_date=request.start_date,
                    end_date=request.end_date,
                    strategy_type=request.strategy_type,
                    short_period=p1,
                    long_period=p2,
                )

                try:
                    # 執行回測
                    engine = BacktestEngine(bt_request)
                    engine.fetch_data()
                    engine.calculate_indicators()
                    engine.generate_signals()
                    engine.run_backtest()
                    summary = engine.calculate_metrics()

                    total_return = summary.total_return
                    sharpe = summary.sharpe_ratio

                    heatmap_data.append([i, j, round(total_return, 1)])

                    # 更新最佳參數
                    if total_return > best_return:
                        best_return = total_return
                        best_sharpe = sharpe
                        best_param1 = p1
                        best_param2 = p2

                except Exception:
                    heatmap_data.append([i, j, None])

        return OptimizeResult(
            best_param1=best_param1,
            best_param2=best_param2,
            best_return=round(best_return, 2),
            best_sharpe=round(best_sharpe, 2),
            heatmap_data=heatmap_data,
            x_labels=param1_values,
            y_labels=param2_values,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"最佳化失敗: {str(e)}")
