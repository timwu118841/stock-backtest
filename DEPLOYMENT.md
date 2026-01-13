# 🚀 Stock Backtest 系統部署指南

## 免費部署方案架構

- **前端**: Vercel (免費)
- **後端**: Render Free Tier (免費)
- **總成本**: $0/月

---

## 📋 部署前準備

### 1. 確認 GitHub Repository
確保你的代碼已經推送到 GitHub：

```bash
git remote -v
git push origin master
```

如果還沒有連接 GitHub：
```bash
git remote add origin https://github.com/你的用戶名/stock-backtest.git
git branch -M master
git push -u origin master
```

---

## 🔧 步驟 1: 部署後端到 Render

### 1.1 創建 Render 帳號
1. 前往 https://render.com
2. 使用 GitHub 帳號登入
3. 授權 Render 訪問你的 repositories

### 1.2 創建 Web Service
1. 點擊 **"New +"** → **"Web Service"**
2. 連接你的 GitHub repository: `stock-backtest`
3. 配置如下：

   **基本設定:**
   - **Name**: `stock-backtest-api`
   - **Region**: Singapore (最接近台灣)
   - **Branch**: `master`
   - **Root Directory**: `backend`
   
   **Build & Deploy:**
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   
   **Instance Type:**
   - 選擇 **"Free"** (免費層)

4. 點擊 **"Advanced"** 設定環境變數：
   ```
   DEBUG = False
   PYTHON_VERSION = 3.11.0
   ```

5. 點擊 **"Create Web Service"**

### 1.3 等待部署完成
- 首次部署約需 5-10 分鐘
- 完成後會得到 URL: `https://stock-backtest-api.onrender.com`
- 測試健康檢查: `https://stock-backtest-api.onrender.com/api/health`

---

## 🎨 步驟 2: 部署前端到 Vercel

### 2.1 創建 Vercel 帳號
1. 前往 https://vercel.com
2. 使用 GitHub 帳號登入
3. 授權 Vercel 訪問你的 repositories

### 2.2 導入項目
1. 點擊 **"Add New..."** → **"Project"**
2. 選擇 `stock-backtest` repository
3. 配置如下：

   **Framework Preset**: Vite
   **Root Directory**: `frontend`
   
   **Build Settings:**
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - Install Command: `npm install`

4. 點擊 **"Environment Variables"** 添加：
   ```
   VITE_API_BASE_URL = https://stock-backtest-api.onrender.com/api
   ```
   ⚠️ 替換成你在步驟 1.3 獲得的實際 Render URL

5. 點擊 **"Deploy"**

### 2.3 等待部署完成
- 首次部署約需 2-3 分鐘
- 完成後會得到 URL: `https://stock-backtest.vercel.app`

---

## 🔗 步驟 3: 配置 CORS (重要!)

### 3.1 更新後端環境變數
1. 回到 Render Dashboard
2. 進入你的 `stock-backtest-api` service
3. 點擊 **"Environment"**
4. 添加新變數：
   ```
   FRONTEND_URL = https://stock-backtest.vercel.app
   ```
   ⚠️ 替換成你在步驟 2.3 獲得的實際 Vercel URL
5. 點擊 **"Save Changes"**
6. 服務會自動重新部署 (約 1-2 分鐘)

---

## ✅ 步驟 4: 測試部署

### 4.1 測試後端
訪問: `https://stock-backtest-api.onrender.com/docs`
- 應該看到 FastAPI 自動生成的 API 文檔
- 測試 `/api/health` 端點

### 4.2 測試前端
訪問: `https://stock-backtest.vercel.app`
- 應該能正常載入 Vue 應用
- 測試「策略回測」功能
- 輸入股票代碼 (如 `AAPL`) 執行回測

### 4.3 測試前後端連接
1. 在前端執行一個回測
2. 打開瀏覽器開發者工具 (F12) → Network
3. 檢查 API 請求是否成功 (狀態碼 200)
4. 如果看到 CORS 錯誤，返回步驟 3 重新檢查環境變數

---

## 🎉 完成！

你的應用已經成功部署：

- **前端**: https://stock-backtest.vercel.app
- **後端 API**: https://stock-backtest-api.onrender.com
- **API 文檔**: https://stock-backtest-api.onrender.com/docs

---

## ⚙️ 維護與更新

### 自動部署
每次 `git push` 到 master 分支，Vercel 和 Render 都會自動重新部署。

### 查看日誌
- **Render**: Dashboard → Service → Logs
- **Vercel**: Dashboard → Project → Deployments → 點擊部署 → Function Logs

### 喚醒休眠的後端
免費層後端會在 15 分鐘無活動後休眠。首次訪問需要 5-10 秒喚醒。

可選方案：使用 [UptimeRobot](https://uptimerobot.com) 每 5 分鐘 ping 一次健康檢查端點保持活躍（免費）。

---

## ❓ 常見問題

**Q: 後端請求很慢？**  
A: 免費層會休眠，首次請求需要喚醒。可以使用 UptimeRobot 等服務定期 ping 保持活躍。

**Q: CORS 錯誤？**  
A: 檢查後端環境變數 `FRONTEND_URL` 是否正確設定為 Vercel URL。

**Q: Vercel 部署失敗？**  
A: 確認 `frontend/package.json` 中的 dependencies 都已安裝，並檢查 build logs。

**Q: yfinance 數據獲取失敗？**  
A: Render 免費層可能會限制某些外部 API 請求頻率，稍後重試。

**Q: 如何使用自訂域名？**  
A: 
- **Vercel**: Dashboard → Project → Settings → Domains → 添加你的域名
- **Render**: Dashboard → Service → Settings → Custom Domain → 添加你的域名

---

## 🔒 安全建議

1. **不要將真實的 `.env` 文件提交到 Git**（已在 `.gitignore` 中）
2. **定期檢查依賴更新**：`npm audit` 和 `pip list --outdated`
3. **監控部署日誌**：檢查是否有異常請求或錯誤

---

## 📊 性能優化建議（進階）

1. **啟用 Vercel Analytics**：免費追蹤網站性能
2. **使用 Render 付費層**：消除冷啟動問題（$7/月）
3. **添加 Redis 緩存**：緩存股票數據減少 yfinance API 調用
4. **實現請求限流**：防止濫用

---

## 📝 文件清單

本次部署創建的配置文件：

- `backend/Dockerfile` - Docker 容器配置
- `backend/render.yaml` - Render 平台配置
- `backend/.env.production` - 生產環境變數範本
- `frontend/vercel.json` - Vercel 部署配置
- `frontend/.env.production` - 前端環境變數範本
- `DEPLOYMENT.md` - 本文檔

修改的文件：

- `backend/main.py` - 添加動態 CORS 支援
- `frontend/src/api/index.js` - 支援環境變數配置 API 端點
