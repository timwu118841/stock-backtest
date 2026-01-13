"""
Stock Backtesting API - FastAPI Backend
"""

import os
from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from app.routers import backtest, strategy


def get_cors_origins() -> List[str]:
    origins = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    frontend_url = os.getenv("FRONTEND_URL")
    if frontend_url:
        origins.append(frontend_url)
        origins.append("https://*.vercel.app")

    return origins


app = FastAPI(
    title="Stock Backtesting API",
    description="股票策略回測系統後端 API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊路由
app.include_router(backtest.router)
app.include_router(strategy.router)


@app.get("/")
async def root():
    """API 根端點"""
    return {"message": "歡迎使用股票回測系統 API", "status": "running", "docs": "/docs"}


@app.get("/api/health")
async def health_check():
    """健康檢查端點"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
