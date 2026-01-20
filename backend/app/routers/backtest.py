from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.models import User, BacktestRecord
from app.core.security import get_current_user
from app.models.backtest import (
    BacktestRequest,
    BacktestResult,
    BacktestHistoryItem,
    BacktestSummary,
    PriceData,
    EquityData,
    TradeRecord,
    DashboardStats,
    DashboardRecentItem,
    DashboardResponse,
)
from app.services.backtest_engine import run_full_backtest, BacktestEngine

router = APIRouter(prefix="/api/backtest", tags=["Backtest"])


def db_record_to_result(record: BacktestRecord) -> BacktestResult:
    return BacktestResult(
        id=record.id,
        strategy_name=record.strategy_name,
        stock_symbol=record.stock_symbol,
        strategy_type=record.strategy_type,
        start_date=record.start_date,
        end_date=record.end_date,
        initial_capital=record.initial_capital,
        final_capital=record.final_capital,
        created_at=record.created_at.isoformat() if record.created_at else "",
        summary=BacktestSummary(
            total_return=record.total_return,
            annualized_return=record.annualized_return,
            sharpe_ratio=record.sharpe_ratio,
            max_drawdown=record.max_drawdown,
            win_rate=record.win_rate,
            total_trades=record.total_trades,
            profit_trades=record.profit_trades,
            loss_trades=record.loss_trades,
            avg_profit=record.avg_profit,
            avg_loss=record.avg_loss,
            total_cost=record.total_cost,
        ),
        price_data=PriceData(**record.price_data),
        equity_data=EquityData(**record.equity_data),
        trades=[TradeRecord(**t) for t in record.trades],
        params=record.params,
    )


@router.post("/run", response_model=BacktestResult)
async def run_backtest(
    request: BacktestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        max_id = db.query(BacktestRecord.id).order_by(BacktestRecord.id.desc()).first()
        next_id = (max_id[0] + 1) if max_id else 1

        result = run_full_backtest(request, next_id)

        record = BacktestRecord(
            user_id=current_user.id,
            strategy_name=result.strategy_name,
            stock_symbol=result.stock_symbol,
            strategy_type=result.strategy_type,
            start_date=result.start_date,
            end_date=result.end_date,
            initial_capital=result.initial_capital,
            final_capital=result.final_capital,
            total_return=result.summary.total_return,
            annualized_return=result.summary.annualized_return,
            sharpe_ratio=result.summary.sharpe_ratio,
            max_drawdown=result.summary.max_drawdown,
            win_rate=result.summary.win_rate,
            total_trades=result.summary.total_trades,
            profit_trades=result.summary.profit_trades,
            loss_trades=result.summary.loss_trades,
            avg_profit=result.summary.avg_profit,
            avg_loss=result.summary.avg_loss,
            total_cost=result.summary.total_cost or 0.0,
            price_data=result.price_data.model_dump(),
            equity_data=result.equity_data.model_dump(),
            trades=[t.model_dump() for t in result.trades],
            params=result.params,
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        return db_record_to_result(record)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"回測執行失敗: {str(e)}")


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    records = (
        db.query(BacktestRecord)
        .filter(BacktestRecord.user_id == current_user.id)
        .order_by(BacktestRecord.created_at.desc())
        .all()
    )

    total_backtests = len(records)
    profitable_backtests = sum(1 for r in records if r.total_return > 0)
    avg_return = (
        sum(r.total_return for r in records) / total_backtests
        if total_backtests > 0
        else 0
    )

    best_record = max(records, key=lambda r: r.total_return) if records else None

    stats = DashboardStats(
        total_backtests=total_backtests,
        profitable_backtests=profitable_backtests,
        avg_return=round(avg_return, 2),
        best_strategy=best_record.strategy_type if best_record else None,
        best_strategy_return=round(best_record.total_return, 2)
        if best_record
        else None,
    )

    recent_records = records[:5]
    recent_backtests = []
    for record in recent_records:
        if record.total_return > 5:
            status = "success"
        elif record.total_return >= 0:
            status = "warning"
        else:
            status = "danger"

        return_str = (
            f"+{record.total_return:.1f}%"
            if record.total_return >= 0
            else f"{record.total_return:.1f}%"
        )
        recent_backtests.append(
            DashboardRecentItem(
                id=record.id,
                name=record.strategy_name,
                stock=record.stock_symbol,
                return_pct=return_str,
                date=record.created_at.strftime("%Y-%m-%d")
                if record.created_at
                else "",
                status=status,
            )
        )

    return DashboardResponse(stats=stats, recent_backtests=recent_backtests)


@router.get("/history", response_model=List[BacktestHistoryItem])
async def get_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    records = (
        db.query(BacktestRecord)
        .filter(BacktestRecord.user_id == current_user.id)
        .order_by(BacktestRecord.created_at.desc())
        .all()
    )

    history = []
    for record in records:
        if record.total_return > 5:
            status = "success"
        elif record.total_return >= 0:
            status = "warning"
        else:
            status = "danger"

        history.append(
            BacktestHistoryItem(
                id=record.id,
                date=record.created_at.isoformat() if record.created_at else "",
                strategy=record.strategy_name,
                stock=record.stock_symbol,
                return_pct=record.total_return,
                win_rate=record.win_rate,
                status=status,
            )
        )

    return history


@router.get("/result/{backtest_id}", response_model=BacktestResult)
async def get_backtest_result(
    backtest_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = (
        db.query(BacktestRecord)
        .filter(
            BacktestRecord.id == backtest_id, BacktestRecord.user_id == current_user.id
        )
        .first()
    )

    if not record:
        raise HTTPException(status_code=404, detail="找不到該回測紀錄")

    return db_record_to_result(record)


@router.delete("/history/{backtest_id}")
async def delete_history(
    backtest_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = (
        db.query(BacktestRecord)
        .filter(
            BacktestRecord.id == backtest_id, BacktestRecord.user_id == current_user.id
        )
        .first()
    )

    if not record:
        raise HTTPException(status_code=404, detail="找不到該回測紀錄")

    db.delete(record)
    db.commit()

    return {"message": "刪除成功", "id": backtest_id}


@router.post("/debug")
async def debug_backtest(
    request: BacktestRequest,
    current_user: User = Depends(get_current_user),
):
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
