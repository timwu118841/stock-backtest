from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.models import User, BacktestRecord
from app.core.security import get_current_user
from app.models.backtest import (
    OptimizeRequest,
    OptimizeResult,
    CompareRequest,
    BacktestRequest,
    StrategyType,
)
from app.services.backtest_engine import BacktestEngine, optimize_dca_allocation

router = APIRouter(prefix="/api/strategy", tags=["Strategy"])


@router.post("/compare")
async def compare_strategies(
    request: CompareRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if len(request.ids) < 2:
        raise HTTPException(status_code=400, detail="至少需要選擇兩個策略進行比較")

    records = (
        db.query(BacktestRecord)
        .filter(
            BacktestRecord.id.in_(request.ids),
            BacktestRecord.user_id == current_user.id,
        )
        .all()
    )

    if len(records) != len(request.ids):
        found_ids = {r.id for r in records}
        missing_ids = [id for id in request.ids if id not in found_ids]
        raise HTTPException(
            status_code=404,
            detail=f"找不到以下 ID 的回測結果: {missing_ids}",
        )

    metrics = []
    equity_curves = {"dates": [], "series": []}

    for record in records:
        metrics.append(
            {
                "id": record.id,
                "name": record.strategy_name,
                "totalReturn": record.total_return,
                "annualizedReturn": record.annualized_return,
                "sharpeRatio": record.sharpe_ratio,
                "maxDrawdown": record.max_drawdown,
                "winRate": record.win_rate,
            }
        )

        equity_data = record.equity_data
        equity_curves["series"].append(
            {"name": record.strategy_name, "data": equity_data.get("equity", [])}
        )

    if records:
        first_equity_data = records[0].equity_data
        equity_curves["dates"] = first_equity_data.get("dates", [])

    return {"metrics": metrics, "equityCurves": equity_curves}


@router.post("/optimize", response_model=OptimizeResult)
async def optimize_strategy(
    request: OptimizeRequest,
    current_user: User = Depends(get_current_user),
):
    if request.strategy_type == StrategyType.DCA:
        try:
            return optimize_dca_allocation(request)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    try:
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

        for i, p1 in enumerate(param1_values):
            for j, p2 in enumerate(param2_values):
                if p2 <= p1:
                    heatmap_data.append([i, j, None])
                    continue

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
                    engine = BacktestEngine(bt_request)
                    engine.fetch_data()
                    engine.calculate_indicators()
                    engine.generate_signals()
                    engine.run_backtest()
                    summary = engine.calculate_metrics()

                    total_return = summary.total_return
                    sharpe = summary.sharpe_ratio

                    heatmap_data.append([i, j, round(total_return, 1)])

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
