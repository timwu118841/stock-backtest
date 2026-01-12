# Vue + FastAPI 全端專案

這是一個前後端分離的全端專案，使用 Vue 3 作為前端，FastAPI 作為後端。

## 專案結構

```
fullstack-app/
├── backend/                # FastAPI 後端
│   ├── main.py            # 主應用程式
│   ├── requirements.txt   # Python 依賴
│   └── .env.example       # 環境變數範例
│
└── frontend/              # Vue 3 前端
    ├── src/
    │   ├── api/           # API 請求模組
    │   ├── App.vue        # 主元件
    │   └── main.js        # 進入點
    ├── package.json
    └── vite.config.js
```

## 快速開始

### 1. 啟動後端 (FastAPI)

```bash
cd backend

# 建立虛擬環境
python -m venv venv

# 啟用虛擬環境
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt

# 啟動伺服器
uvicorn main:app --reload --port 8000
```

後端會在 http://localhost:8000 啟動
API 文件: http://localhost:8000/docs

### 2. 啟動前端 (Vue)

```bash
cd frontend

# 安裝依賴 (如果還沒安裝)
npm install

# 啟動開發伺服器
npm run dev
```

前端會在 http://localhost:5173 啟動

## API 端點

| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/` | API 根端點 |
| GET | `/api/health` | 健康檢查 |
| GET | `/api/items` | 取得所有項目 |
| GET | `/api/items/{id}` | 取得單一項目 |
| POST | `/api/items` | 建立新項目 |
| DELETE | `/api/items/{id}` | 刪除項目 |

## 技術棧

### 後端
- FastAPI - 現代 Python Web 框架
- Uvicorn - ASGI 伺服器
- Pydantic - 資料驗證

### 前端
- Vue 3 - JavaScript 框架
- Vite - 建構工具
- Axios - HTTP 客戶端
