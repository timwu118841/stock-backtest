<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useTheme } from './composables/useTheme'
import { useAuth } from './composables/useAuth'

const { isDark, toggleTheme } = useTheme()
const { user, isAuthenticated, logout } = useAuth()
const route = useRoute()

// 響應式狀態
const isCollapse = ref(false)
const isMobile = ref(false)
const drawerVisible = ref(false)

const menuItems = [
  { index: '/', icon: 'DataAnalysis', title: '主控台' },
  { index: '/backtest', icon: 'TrendCharts', title: '策略回測' },
  { index: '/compare', icon: 'Histogram', title: '策略比較' },
  { index: '/optimize', icon: 'Setting', title: '參數最佳化' },
  { index: '/history', icon: 'Clock', title: '歷史紀錄' }
]

const activeMenu = computed(() => route.path)

// 監聽視窗大小調整
const checkScreenSize = () => {
  const width = window.innerWidth
  isMobile.value = width < 768
  if (isMobile.value) {
    isCollapse.value = true // 手機版不使用側邊欄縮放，而是用 Drawer
  } else {
    isCollapse.value = width < 1024
    drawerVisible.value = false
  }
}

onMounted(() => {
  checkScreenSize()
  window.addEventListener('resize', checkScreenSize)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkScreenSize)
})

const toggleSidebar = () => {
  if (isMobile.value) {
    drawerVisible.value = !drawerVisible.value
  } else {
    isCollapse.value = !isCollapse.value
  }
}

const handleLogout = async () => {
  await logout()
  window.location.href = '/login'
}

const isLoginPage = computed(() => route.path === '/login')
</script>

<template>
  <div v-if="isLoginPage" class="login-wrapper">
    <router-view />
  </div>
  <el-container v-else class="app-wrapper">
    <!-- 桌面版側邊欄 -->
    <el-aside 
      v-if="!isMobile" 
      :width="isCollapse ? '64px' : '240px'" 
      class="sidebar"
    >
      <div class="logo">
        <el-icon size="24" color="#409eff"><TrendCharts /></el-icon>
        <span v-show="!isCollapse" class="logo-text">股票回測系統</span>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        :collapse-transition="false"
        router
        class="sidebar-menu"
        background-color="transparent"
      >
        <el-menu-item 
          v-for="item in menuItems" 
          :key="item.index" 
          :index="item.index"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <template #title>{{ item.title }}</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 手機版 Drawer 側邊欄 -->
    <el-drawer
      v-model="drawerVisible"
      direction="ltr"
      size="240px"
      :with-header="false"
      class="mobile-drawer"
    >
      <div class="logo mobile-logo">
        <el-icon size="24" color="#409eff"><TrendCharts /></el-icon>
        <span class="logo-text">股票回測系統</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        class="sidebar-menu"
      >
        <el-menu-item 
          v-for="item in menuItems" 
          :key="item.index" 
          :index="item.index"
          @click="drawerVisible = false"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-drawer>

    <!-- 主內容區 -->
    <el-container class="main-container">
      <el-header class="header">
        <div class="header-left">
          <div class="collapse-btn" @click="toggleSidebar">
            <el-icon size="20">
              <component :is="isMobile ? 'Menu' : (isCollapse ? 'Expand' : 'Fold')" />
            </el-icon>
          </div>
          <h2 class="page-title">{{ route.meta.title }}</h2>
        </div>
        
        <div class="header-right">
          <el-dropdown v-if="isAuthenticated && user" trigger="click" @command="handleLogout">
            <div class="user-info">
              <el-avatar 
                v-if="user.picture" 
                :src="user.picture" 
                :size="32"
              />
              <el-avatar v-else :size="32">
                {{ user.name?.charAt(0) || 'U' }}
              </el-avatar>
              <span class="user-name">{{ user.name }}</span>
              <el-icon><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item disabled>
                  <el-icon><User /></el-icon>
                  {{ user.email }}
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  登出
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-switch
            v-model="isDark"
            inline-prompt
            active-icon="Moon"
            inactive-icon="Sunny"
            style="margin-right: 16px"
          />
          <el-tag type="success" effect="plain" round class="status-tag">
            <el-icon><Connection /></el-icon>
            <span class="status-text">已連線</span>
          </el-tag>
        </div>
      </el-header>

      <el-main class="content-wrapper">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.app-wrapper {
  height: 100vh;
  background-color: var(--app-bg-color);
  color: var(--app-text-color);
}

.sidebar {
  background-color: var(--app-sidebar-bg);
  border-right: 1px solid var(--app-border-color);
  display: flex;
  flex-direction: column;
  transition: width 0.3s cubic-bezier(0.2, 0, 0, 1);
  z-index: 100;
}

html.dark .sidebar {
  background: linear-gradient(180deg, rgba(24, 24, 27, 0.95) 0%, rgba(15, 15, 18, 0.98) 100%);
  border-color: rgba(255, 255, 255, 0.06);
}

.logo {
  height: 68px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  border-bottom: 1px solid var(--app-border-color);
  overflow: hidden;
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.05) 0%, transparent 100%);
}

html.dark .logo {
  border-color: rgba(255, 255, 255, 0.06);
  background: linear-gradient(135deg, rgba(96, 165, 250, 0.08) 0%, transparent 100%);
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  white-space: nowrap;
  color: var(--app-text-color);
  letter-spacing: -0.3px;
}

.sidebar-menu {
  border-right: none;
  flex: 1;
  padding: 8px 0;
}

:deep(.el-menu-item) {
  height: 52px;
  margin: 4px 10px;
  border-radius: 10px;
  color: var(--app-text-color);
  transition: all 0.2s ease;
}

:deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, var(--el-color-primary) 0%, #764ba2 100%);
  color: #fff;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

html.dark :deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.5);
}

:deep(.el-menu-item:not(.is-active):hover) {
  background-color: rgba(64, 158, 255, 0.08);
}

html.dark :deep(.el-menu-item:not(.is-active):hover) {
  background-color: rgba(255, 255, 255, 0.06);
}

.header {
  height: 68px;
  background-color: var(--app-header-bg);
  border-bottom: 1px solid var(--app-border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  transition: background-color 0.25s;
}

html.dark .header {
  background: rgba(24, 24, 27, 0.8);
  backdrop-filter: blur(12px);
  border-color: rgba(255, 255, 255, 0.06);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.collapse-btn {
  cursor: pointer;
  padding: 10px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  transition: all 0.2s ease;
}

.collapse-btn:hover {
  background-color: rgba(64, 158, 255, 0.1);
  transform: scale(1.05);
}

html.dark .collapse-btn:hover {
  background-color: rgba(255, 255, 255, 0.08);
}

.page-title {
  font-size: 20px;
  font-weight: 700;
  margin: 0;
  color: var(--app-text-color);
  letter-spacing: -0.3px;
}

.status-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 20px;
}

.status-text {
  display: none;
}

@media (min-width: 640px) {
  .status-text {
    display: inline;
  }
}

.main-container {
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.content-wrapper {
  padding: 24px;
  overflow-y: auto;
  background-color: var(--app-bg-color);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

@media (max-width: 768px) {
  .content-wrapper {
    padding: 16px;
  }
  
  .page-title {
    font-size: 18px;
  }
}

.login-wrapper {
  min-height: 100vh;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: 10px;
  margin-right: 16px;
  transition: all 0.2s ease;
}

.user-info:hover {
  background-color: rgba(64, 158, 255, 0.08);
}

html.dark .user-info:hover {
  background-color: rgba(255, 255, 255, 0.06);
}

.user-name {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
  font-weight: 500;
  color: var(--app-text-color);
}

@media (max-width: 640px) {
  .user-name {
    display: none;
  }
}

.header-right {
  display: flex;
  align-items: center;
}

:deep(.el-switch) {
  --el-switch-on-color: #667eea;
}

.mobile-drawer :deep(.el-drawer__body) {
  padding: 0;
}

.mobile-logo {
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.08) 0%, transparent 100%);
}
</style>
