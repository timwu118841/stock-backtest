<template>
  <div class="callback-container">
    <el-icon class="loading-icon" :size="48"><Loading /></el-icon>
    <p>正在登入...</p>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Loading } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

onMounted(() => {
  const token = route.query.token
  
  if (token) {
    localStorage.setItem('access_token', token)
    router.replace('/')
  } else {
    router.replace('/login')
  }
})
</script>

<style scoped>
.callback-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  color: rgba(255, 255, 255, 0.8);
}

.loading-icon {
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
