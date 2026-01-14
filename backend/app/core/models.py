from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    google_id = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    picture = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    backtests = relationship(
        "BacktestRecord", back_populates="user", cascade="all, delete-orphan"
    )


class BacktestRecord(Base):
    __tablename__ = "backtest_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    strategy_name = Column(String(255), nullable=False)
    stock_symbol = Column(String(50), nullable=False)
    strategy_type = Column(String(50), nullable=False)
    start_date = Column(String(20), nullable=False)
    end_date = Column(String(20), nullable=False)

    initial_capital = Column(Float, nullable=False)
    final_capital = Column(Float, nullable=False)

    total_return = Column(Float, nullable=False)
    annualized_return = Column(Float, nullable=False)
    sharpe_ratio = Column(Float, nullable=False)
    max_drawdown = Column(Float, nullable=False)
    win_rate = Column(Float, nullable=False)
    total_trades = Column(Integer, nullable=False)
    profit_trades = Column(Integer, nullable=False)
    loss_trades = Column(Integer, nullable=False)
    avg_profit = Column(Float, nullable=False)
    avg_loss = Column(Float, nullable=False)
    total_cost = Column(Float, default=0.0)

    price_data = Column(JSON, nullable=False)
    equity_data = Column(JSON, nullable=False)
    trades = Column(JSON, nullable=False)
    params = Column(JSON, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="backtests")
