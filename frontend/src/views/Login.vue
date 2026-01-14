<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <h1 class="title">股票策略回測系統</h1>
          <p class="subtitle">Stock Backtesting System</p>
        </div>
      </template>
      
      <div class="login-content">
        <div class="welcome-text">
          <el-icon :size="48" class="chart-icon"><TrendCharts /></el-icon>
          <p>歡迎使用股票策略回測系統</p>
          <p class="description">
            測試、比較並優化您的投資策略<br>
            支援多種技術指標與定期定額策略
          </p>
        </div>

        <el-divider />

        <el-button 
          type="primary" 
          size="large" 
          class="google-btn"
          :loading="isLoading"
          @click="handleGoogleLogin"
        >
          <svg class="google-icon" viewBox="0 0 24 24" width="20" height="20">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          使用 Google 帳號登入
        </el-button>

        <p class="security-note">
          <el-icon><Lock /></el-icon>
          您的資料將安全儲存，僅供您個人使用
        </p>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { TrendCharts, Lock } from '@element-plus/icons-vue'
import { useAuth } from '@/composables/useAuth'
import { useRouter, useRoute } from 'vue-router'
import { onMounted } from 'vue'

const router = useRouter()
const route = useRoute()
const { isLoading, isAuthenticated, checkAuth, loginWithGoogle } = useAuth()

onMounted(async () => {
  await checkAuth()
  if (isAuthenticated.value) {
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  }
})

const handleGoogleLogin = () => {
  loginWithGoogle()
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 420px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  backdrop-filter: blur(10px);
}

.login-card :deep(.el-card__header) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding: 24px;
}

.login-card :deep(.el-card__body) {
  padding: 32px;
}

.card-header {
  text-align: center;
}

.title {
  font-size: 1.75rem;
  font-weight: 700;
  color: #e94560;
  margin: 0 0 8px 0;
}

.subtitle {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.6);
  margin: 0;
}

.login-content {
  text-align: center;
}

.welcome-text {
  margin-bottom: 16px;
}

.chart-icon {
  color: #e94560;
  margin-bottom: 16px;
}

.welcome-text p {
  color: rgba(255, 255, 255, 0.9);
  font-size: 1.1rem;
  margin: 0 0 8px 0;
}

.description {
  font-size: 0.9rem !important;
  color: rgba(255, 255, 255, 0.6) !important;
  line-height: 1.6;
}

.login-content :deep(.el-divider) {
  border-color: rgba(255, 255, 255, 0.1);
  margin: 24px 0;
}

.google-btn {
  width: 100%;
  height: 48px;
  font-size: 1rem;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: #fff;
  border-color: #fff;
  color: #333;
}

.google-btn:hover {
  background: #f5f5f5;
  border-color: #f5f5f5;
  color: #333;
}

.google-icon {
  flex-shrink: 0;
}

.security-note {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: 20px;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
}

@media (max-width: 480px) {
  .login-card {
    max-width: 100%;
  }
  
  .title {
    font-size: 1.5rem;
  }
}
</style>
