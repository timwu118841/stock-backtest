# 🎯 部署快速檢查清單

## ✅ 已完成的配置

### 📦 新建的文件（共6個）
- ✅ `backend/Dockerfile` - Docker 容器配置
- ✅ `backend/render.yaml` - Render 平台自動部署配置
- ✅ `backend/.env.production` - 後端生產環境變數範本
- ✅ `frontend/vercel.json` - Vercel 部署配置（SPA路由支援）
- ✅ `frontend/.env.production` - 前端生產環境變數範本
- ✅ `DEPLOYMENT.md` - 詳細部署指南文檔

### 🔧 修改的文件（共2個）
- ✅ `backend/main.py` - 添加動態 CORS 支援（支援生產環境域名）
- ✅ `frontend/src/api/index.js` - 支援環境變數配置 API 端點

---

## 🚀 下一步：開始部署

### 第一步：推送到 GitHub
```bash
git add .
git commit -m "feat: 添加免費雲端部署配置 (Vercel + Render)

- 新增 Dockerfile 和 render.yaml 支援 Render 部署
- 新增 vercel.json 支援 Vercel 部署
- 更新 CORS 配置支援生產環境域名
- 添加環境變數範本和完整部署文檔"

git push origin master
```

### 第二步：部署後端到 Render
1. 前往 https://render.com 使用 GitHub 登入
2. New + → Web Service
3. 選擇 `stock-backtest` repository
4. 配置：
   - Name: `stock-backtest-api`
   - Region: Singapore
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Instance Type: **Free**
5. 環境變數：
   ```
   DEBUG = False
   PYTHON_VERSION = 3.11.0
   ```
6. 點擊 Create Web Service
7. ⏳ 等待 5-10 分鐘，獲得後端 URL

### 第三步：部署前端到 Vercel
1. 前往 https://vercel.com 使用 GitHub 登入
2. Add New → Project
3. 選擇 `stock-backtest` repository
4. 配置：
   - Framework: Vite
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`
5. 環境變數（⚠️ 重要）：
   ```
   VITE_API_BASE_URL = https://stock-backtest-api.onrender.com/api
   ```
   （替換成第二步獲得的實際 Render URL）
6. 點擊 Deploy
7. ⏳ 等待 2-3 分鐘，獲得前端 URL

### 第四步：配置後端 CORS（⚠️ 必須完成）
1. 回到 Render Dashboard
2. 進入 `stock-backtest-api` service
3. Environment 標籤
4. 添加新變數：
   ```
   FRONTEND_URL = https://stock-backtest.vercel.app
   ```
   （替換成第三步獲得的實際 Vercel URL）
5. Save Changes（服務會自動重啟）

### 第五步：測試部署
1. 訪問前端：`https://stock-backtest.vercel.app`
2. 訪問 API 文檔：`https://stock-backtest-api.onrender.com/docs`
3. 在前端執行一次回測測試（例如 AAPL 股票）
4. 打開開發者工具檢查網絡請求是否成功

---

## 📊 部署成本
- **前端（Vercel）**: $0/月（100GB 免費流量）
- **後端（Render）**: $0/月（750小時免費運行）
- **總計**: **完全免費** 🎉

---

## ⚠️ 免費層限制
- **Render 後端會在 15 分鐘無活動後休眠**
- 首次訪問需要 5-10 秒喚醒
- 建議使用 [UptimeRobot](https://uptimerobot.com) 每 5 分鐘 ping 一次保持活躍

---

## 📝 完整文檔
詳細步驟和故障排除請參考：`DEPLOYMENT.md`

---

## ✨ 預期結果
部署成功後你將獲得：
- ✅ 全球訪問的股票回測系統
- ✅ 自動 HTTPS 加密
- ✅ Git push 自動部署
- ✅ 免費的生產環境

準備好了就開始第一步推送代碼吧！🚀
