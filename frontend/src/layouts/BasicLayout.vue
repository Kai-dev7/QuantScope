<template>
  <div class="basic-layout">
    <!-- 侧边栏 -->
    <aside
      class="sidebar"
      :class="{ collapsed: appStore.sidebarCollapsed }"
      :style="{ width: appStore.actualSidebarWidth + 'px' }"
    >
      <div class="sidebar-header">
        <div class="logo">
          <img src="/logo.svg" alt="Northstar One" />
          <div v-show="!appStore.sidebarCollapsed" class="brand-meta">
            <span class="logo-text">Northstar One</span>
            <span class="logo-subtext">AI Research Terminal</span>
          </div>
        </div>
      </div>
      
      <nav class="sidebar-nav">
        <SidebarMenu />
      </nav>
      
      <div class="sidebar-footer">
        <UserProfile />
      </div>
    </aside>

    <!-- 点击蒙层：移动端展开时，点击空白处收起侧边栏 -->
    <div
      v-if="isMobile && !appStore.sidebarCollapsed"
      class="sidebar-overlay"
      @click="appStore.setSidebarCollapsed(true)"
    ></div>

    <!-- 主内容区 -->
    <div class="main-container" :style="{ marginLeft: appStore.actualSidebarWidth + 'px' }" @click="handleMainClick">
      <!-- 顶部导航栏 -->
      <header class="header">
        <div class="header-left">
          <el-button
            type="text"
            @click.stop="appStore.toggleSidebar()"
            class="sidebar-toggle"
          >
            <el-icon><Expand v-if="appStore.sidebarCollapsed" /><Fold v-else /></el-icon>
          </el-button>
          
          <div class="header-title-wrap">
            <Breadcrumb />
            <span class="header-title">{{ appStore.currentPageTitle }}</span>
          </div>
        </div>
        
        <div class="header-right">
          <div class="status-cluster">
            <span class="status-chip live">LIVE</span>
            <span class="status-chip">CN/HK/US</span>
          </div>
          <HeaderActions />
        </div>
      </header>

      <!-- 页面内容 -->
      <main class="main-content">
        <div class="content-wrapper">
          <router-view v-slot="{ Component, route }">
            <transition
              :name="route.meta.transition || 'fade'"
              mode="out-in"
              appear
            >
              <keep-alive :include="keepAliveComponents">
                <component :is="Component" :key="route.fullPath" />
              </keep-alive>
            </transition>
          </router-view>
        </div>
      </main>

      <!-- 页脚 -->
      <footer class="footer">
        <AppFooter />
      </footer>
    </div>

    <!-- 回到顶部 -->
    <el-backtop :right="40" :bottom="40" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAppStore } from '@/stores/app'
import SidebarMenu from '@/components/Layout/SidebarMenu.vue'
import UserProfile from '@/components/Layout/UserProfile.vue'
import Breadcrumb from '@/components/Layout/Breadcrumb.vue'
import HeaderActions from '@/components/Layout/HeaderActions.vue'
import AppFooter from '@/components/Layout/AppFooter.vue'
import { Expand, Fold } from '@element-plus/icons-vue'

const appStore = useAppStore()
const route = useRoute()
const { width } = useWindowSize()

// 需要缓存的组件
const keepAliveComponents = computed(() => [
  'Dashboard',
  'StockScreening',
  'AnalysisHistory',
  'QueueManagement'
])

// 移动端判断
const isMobile = computed(() => width.value < 768)

// 点击主内容时，若移动端且侧边栏已展开，则收起
const handleMainClick = () => {
  if (isMobile.value && !appStore.sidebarCollapsed) {
    appStore.setSidebarCollapsed(true)
  }
}

// 监听窗口大小变化：在小屏幕上自动折叠侧边栏
watch(width, (newWidth) => {
  if (newWidth < 768 && !appStore.sidebarCollapsed) {
    appStore.setSidebarCollapsed(true)
  }
})

// 路由变化时，移动端收起侧边栏
watch(() => route.fullPath, () => {
  if (isMobile.value) {
    appStore.setSidebarCollapsed(true)
  }
})
</script>

<style lang="scss" scoped>
.basic-layout {
  min-height: 100vh;
  background:
    radial-gradient(circle at 12% 8%, rgba(27, 138, 150, 0.08), transparent 28%),
    radial-gradient(circle at 92% 4%, rgba(219, 140, 77, 0.12), transparent 26%),
    #f5f8fb;
}

.sidebar-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  z-index: 950; // 低于侧边栏(1000)，高于内容区
}

.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  background: linear-gradient(185deg, #0f2338 0%, #102943 42%, #102f3f 100%);
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  transition: width 0.3s ease;
  z-index: 1000;
  display: flex;
  flex-direction: column;

  &.collapsed {
    width: 64px !important;
  }

  .sidebar-header {
    height: 74px;
    display: flex;
    align-items: center;
    padding: 0 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);

    .logo {
      display: flex;
      align-items: center;
      gap: 12px;

      img {
        width: 32px;
        height: 32px;
      }

      .brand-meta {
        display: flex;
        flex-direction: column;
      }

      .logo-text {
        font-size: 18px;
        font-weight: 800;
        color: #f8fbff;
        white-space: nowrap;
        letter-spacing: 0.03em;
        text-transform: uppercase;
      }

      .logo-subtext {
        font-size: 11px;
        color: rgba(226, 238, 252, 0.82);
        margin-top: 2px;
        letter-spacing: 0.08em;
      }
    }
  }

  .sidebar-nav {
    flex: 1;
    overflow-y: auto;
    padding: 8px 0;
  }

  .sidebar-footer {
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    padding: 8px;
  }
}

.main-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  transition: margin-left 0.3s ease;
}

.header {
  height: 60px;
  background: var(--app-header-bg);
  border-bottom: 1px solid var(--app-header-border);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  position: sticky;
  top: 0;
  z-index: 999;

  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;

    .header-title-wrap {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .header-title {
      font-size: 12px;
      color: #6d7c90;
      padding-left: 10px;
      border-left: 1px solid #d8e3ee;
      letter-spacing: 0.02em;
    }

    .sidebar-toggle {
      padding: 8px;
      
      .el-icon {
        font-size: 18px;
      }
    }
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .status-cluster {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .status-chip {
    height: 30px;
    padding: 0 12px;
    border-radius: 999px;
    display: inline-flex;
    align-items: center;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: #2f4c5d;
    background: rgba(18, 96, 124, 0.08);
    border: 1px solid rgba(18, 96, 124, 0.16);
  }

  .status-chip.live {
    color: #0b6955;
    border-color: rgba(11, 105, 85, 0.25);
    background: rgba(24, 179, 135, 0.14);
  }
}

.main-content {
  flex: 1;
  padding: 24px;
  min-height: calc(100vh - 60px - 60px); // 减去header和footer高度

  .content-wrapper {
    max-width: 1400px;
    margin: 0 auto;
  }
}

.footer {
  height: 60px;
  background-color: var(--el-bg-color);
  border-top: 1px solid var(--el-border-color-light);
  display: flex;
  align-items: center;
  justify-content: center;
}

// 响应式设计
@media (max-width: 768px) {
  .sidebar {
    transform: translateX(-100%);
    
    &:not(.collapsed) {
      transform: translateX(0);
    }
  }

  .main-container {
    margin-left: 0 !important;
  }

  .main-content {
    padding: 16px;
  }

  .header {
    padding: 0 16px;
  }
}

// 路由过渡动画
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-left-enter-active,
.slide-left-leave-active {
  transition: all 0.3s ease;
}

.slide-left-enter-from {
  transform: translateX(30px);
  opacity: 0;
}

.slide-left-leave-to {
  transform: translateX(-30px);
  opacity: 0;
}
</style>
