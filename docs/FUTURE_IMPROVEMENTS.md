# Future Improvements

## Authentication Security Enhancements

### Current Status
- Token 傳遞方式：URL query string (`?token=xxx`)
- Token 儲存方式：localStorage
- Token 過期時間：7 天
- Token 傳送方式：Authorization Bearer header

### Improvement 1: Use URL Fragment Instead of Query String
**Priority**: High  
**Complexity**: Low  
**Files to modify**: 
- `backend/app/routers/auth.py` (line ~118)
- `frontend/src/views/AuthCallback.vue`

**Current**:
```python
url=f"{frontend_url}/auth/callback?token={access_token}"
```

**Improved**:
```python
url=f"{frontend_url}/auth/callback#token={access_token}"
```

**Benefits**:
- Fragment 不會發送到伺服器
- 不會被記錄在伺服器 log
- 不會通過 Referer header 洩露給第三方

---

### Improvement 2: Shorter Access Token + Refresh Token
**Priority**: Medium  
**Complexity**: Medium  

**Current**:
- Access Token: 7 days

**Improved**:
- Access Token: 15-30 minutes
- Refresh Token: 7 days (stored in HttpOnly cookie)

**Implementation**:
1. 建立 `/api/auth/refresh` 端點
2. 前端 axios interceptor 自動處理 401 並 refresh
3. Refresh Token 存在 HttpOnly cookie（同源限制）

---

### Improvement 3: Token Binding (IP/User-Agent)
**Priority**: Low  
**Complexity**: Low  

**Implementation**:
1. JWT payload 中加入 client fingerprint hash
2. 驗證時比對 fingerprint

```python
# 建立 token 時
fingerprint = hash(request.client.host + request.headers.get("user-agent", ""))
data = {"sub": str(user.id), "fp": fingerprint}

# 驗證時
if payload.get("fp") != current_fingerprint:
    raise HTTPException(401, "Token fingerprint mismatch")
```

---

### Improvement 4: Token Revocation (Blacklist)
**Priority**: Low  
**Complexity**: Medium  

**Current Issue**: 登出只刪除前端 token，後端無法 invalidate 已發出的 token

**Implementation Options**:
1. Redis blacklist (推薦)
2. Database token version per user
3. Short-lived tokens (見 Improvement 2)

---

## Other Future Improvements

### Performance
- [ ] 回測結果快取 (Redis)
- [ ] 股價資料快取，減少 yfinance API 呼叫
- [ ] 分頁載入歷史紀錄

### Features
- [ ] 多用戶協作功能
- [ ] 策略分享/公開功能
- [ ] Email 通知 (回測完成)
- [ ] 定時執行回測

### DevOps
- [ ] 加入 CI/CD 測試
- [ ] 加入 Sentry 錯誤追蹤
- [ ] 加入 API rate limiting
