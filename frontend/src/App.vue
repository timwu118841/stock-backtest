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

/* Sidebar Styles */
.sidebar {
  background-color: var(--app-sidebar-bg);
  border-right: 1px solid var(--app-border-color);
  display: flex;
  flex-direction: column;
  transition: width 0.3s cubic-bezier(0.2, 0, 0, 1);
  z-index: 100;
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  border-bottom: 1px solid var(--app-border-color);
  overflow: hidden;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  white-space: nowrap;
  color: var(--app-text-color);
}

.sidebar-menu {
  border-right: none;
  flex: 1;
}

:deep(.el-menu-item) {
  height: 56px;
  margin: 4px 8px;
  border-radius: 8px;
  color: var(--app-text-color);
}

:deep(.el-menu-item.is-active) {
  background-color: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  font-weight: 600;
}

html.dark :deep(.el-menu-item.is-active) {
  background-color: rgba(64, 158, 255, 0.2);
}

:deep(.el-menu-item:hover) {
  background-color: rgba(0, 0, 0, 0.05);
}

html.dark :deep(.el-menu-item:hover) {
  background-color: rgba(255, 255, 255, 0.05);
}

/* Header Styles */
.header {
  height: 64px;
  background-color: var(--app-header-bg);
  border-bottom: 1px solid var(--app-border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  transition: background-color 0.3s;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.collapse-btn {
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  transition: background-color 0.2s;
}

.collapse-btn:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

html.dark .collapse-btn:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  color: var(--app-text-color);
}

.status-tag {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-text {
  display: none;
}

@media (min-width: 640px) {
  .status-text {
    display: inline;
  }
}

/* Main Content Styles */
.main-container {
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.content-wrapper {
  padding: 20px;
  overflow-y: auto;
  background-color: var(--app-bg-color);
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Mobile Adjustments */
@media (max-width: 768px) {
  .content-wrapper {
    padding: 16px;
  }
  
  .page-title {
    font-size: 18px;
  }
}

/* User Info Styles */
.login-wrapper {
  min-height: 100vh;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 8px;
  margin-right: 12px;
}

.user-info:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

html.dark .user-info:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.user-name {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
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
</style>
