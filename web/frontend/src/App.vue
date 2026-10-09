<template>
  <el-container class="app-container">
    <!-- Header -->
    <el-header>
      <div class="header-left">
        <el-button @click="toggleSidebar" class="menu-toggle" :aria-label="sidebarCollapsed ? 'توسيع القائمة' : 'طي القائمة'">
          <Menu />
        </el-button>
        <div class="app-title">
          <h1 class="nados-title">نظام نادوس</h1>
          <span class="nados-subtitle">Dv1.0 - بيئة محاكاة وبحوث الدفاع الجوي</span>
        </div>
      </div>
      <div class="header-center">
        <div class="simulation-clock">
          <span class="clock-label">زمن المحاكاة:</span>
          <span class="clock-time">{{ simulationStore.formattedTime }}</span>
          <el-progress :percentage="simulationStore.progress" :stroke-width="16" color="#e94560" show-text />
        </div>
      </div>
      <div class="header-right">
        <el-dropdown trigger="click">
          <span class="user-dropdown">
            <User size="large" :src="userAvatar" alt="User" />
            <span>{{ username }}</span>
            <ArrowDown />
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item disabled>
                <div class="user-info">
                  <div class="user-name">{{ username }}</div>
                  <div class="user-role">{{ userRole }}</div>
                </div>
              </el-dropdown-item>
              <el-dropdown-item @click="goToSettings">
                <Setting /> الإعدادات
              </el-dropdown-item>
              <el-dropdown-item divided @click="logout">
                <TurnOff /> تسجيل الخروج
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>

    <!-- Main Layout -->
    <el-container>
      <!-- Sidebar -->
      <el-aside :width="sidebarCollapsed ? '64px' : '260px'" class="sidebar">
        <el-menu
          :default-active="activeMenu"
          :collapse="sidebarCollapsed"
          :unique-opened="true"
          router
          class="nav-menu"
        >
          <el-menu-item index="/">
            <HomeFilled /> <span>الرئيسية</span>
          </el-menu-item>
          <el-menu-item index="/simulation">
            <Monitor /> <span>المشهد ثنائي الأبعاد</span>
          </el-menu-item>
          <el-menu-item index="/simulation-3d">
            <Cpu /> <span>المشهد ثلاثي الأبعاد</span>
          </el-menu-item>
          <el-sub-menu index="sensors">
            <template #title>
              <Aim /> <span>المستشعرات الافتراضية</span>
            </template>
            <el-menu-item index="/sensors">
              <List /> <span>قائمة المستشعرات</span>
            </el-menu-item>
            <el-menu-item index="/sensors/config">
              <Setting /> <span>تكوين المستشعرات</span>
            </el-menu-item>
          </el-sub-menu>
          <el-sub-menu index="tracking">
            <template #title>
              <Location /> <span>تتبع الأجسام</span>
            </template>
            <el-menu-item index="/tracking">
              <List /> <span>المسارات النشطة</span>
            </el-menu-item>
            <el-menu-item index="/tracking/fusion">
              <Connection /> <span>دمج البيانات</span>
            </el-menu-item>
          </el-sub-menu>
          <el-menu-item index="/events">
            <Document /> <span>سجل الأحداث</span>
          </el-menu-item>
          <el-menu-item index="/reports">
            <DocumentCopy /> <span>التقارير</span>
          </el-menu-item>
          <el-menu-item index="/tests">
            <Checked /> <span>الاختبارات</span>
          </el-menu-item>
          <el-menu-item index="/scenario-editor">
            <Edit /> <span>محرر السيناريوهات</span>
          </el-menu-item>
          <el-menu-item index="/settings">
            <Setting /> <span>الإعدادات</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- Main Content -->
      <el-main>
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>

    <!-- Footer -->
    <el-footer>
      <div class="footer-content">
        <span class="simulation-badge">
          <Checked /> محاكاة - SIMULATION
        </span>
        <span class="version">NADOS Dv1.0 | الإصدار 1.0.0</span>
        <span class="db-status" :class="{ 'status-connected': simulationStore.isConnected, 'status-disconnected': !simulationStore.isConnected }">
          {{ simulationStore.isConnected ? 'قاعدة البيانات متصلة' : 'قاعدة البيانات غير متصلة' }}
        </span>
      </div>
    </el-footer>
  </el-container>

  <div v-if="simulationStore.isRunning" class="simulation-label">
    محاكاة - SIMULATION
  </div>
</template>

<script setup>
import { useRouter, useRoute } from 'vue-router'
import { useSimulationStore } from '@/stores/simulation'
import {
  Menu, Monitor, Cpu, Setting, Aim,
  Location, Connection, Document, Edit,
  ArrowDown, User, TurnOff, UserFilled, Checked
} from '@element-plus/icons-vue'
import { onMounted, onUnmounted, computed, ref } from 'vue'

const router = useRouter()
const route = useRoute()
const simulationStore = useSimulationStore()

const sidebarCollapsed = ref(false)
const username = 'مهندس محاكاة'
const userRole = 'باحث رئيسي'
const userAvatar = 'https://api.dicebear.com/7.x/avataaars/svg?seed=nad0s'

const activeMenu = computed(() => route.path)

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

const goToSettings = () => {
  router.push('/settings')
}

const logout = () => {
  ElMessageBox.confirm('هل تريد تسجيل الخروج؟', 'تأكيد', {
    confirmButtonText: 'نعم',
    cancelButtonText: 'لا',
    type: 'warning'
  }).then(() => {
    localStorage.removeItem('auth_token')
    router.push('/login')
  })
}

onMounted(() => {
  simulationStore.startPolling(1000)
})

onUnmounted(() => {
  simulationStore.stopPolling()
})
</script>

<style scoped>
.app-container {
  height: 100vh;
  overflow: hidden;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-center {
  flex: 1;
  display: flex;
  justify-content: center;
}

.header-right {
  display: flex;
  align-items: center;
}

.app-title {
  display: flex;
  flex-direction: column;
}

.nados-title {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: #e94560;
  letter-spacing: 1px;
}

.nados-subtitle {
  font-size: 12px;
  color: #aaa;
}

.simulation-clock {
  display: flex;
  align-items: center;
  gap: 16px;
}

.clock-label {
  font-size: 14px;
  color: #aaa;
  white-space: nowrap;
}

.clock-time {
  font-family: 'monospace';
  font-size: 20px;
  font-weight: 600;
  color: #e94560;
  min-width: 120px;
  text-align: center;
}

.simulation-clock :deep(.el-progress) {
  flex: 1;
  max-width: 300px;
  height: 16px !important;
}

.simulation-clock :deep(.el-progress__inner) {
  height: 16px !important;
  border-radius: 8px;
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background 0.2s;
}

.user-dropdown:hover {
  background: rgba(233, 69, 96, 0.1);
}

.user-info {
  padding: 8px 0;
}

.user-name {
  font-weight: 600;
  color: #eaeaea;
}

.user-role {
  font-size: 12px;
  color: #aaa;
}

.sidebar {
  transition: width 0.3s;
  overflow: hidden;
}

.nav-menu {
  height: 100%;
  border-right: none;
}

.nav-menu :deep(.el-menu-item) {
  padding: 12px 20px;
  transition: all 0.2s;
}

.nav-menu :deep(.el-menu-item:hover) {
  background: #0f3460 !important;
  color: #e94560 !important;
}

.nav-menu :deep(.el-menu-item.is-active) {
  background: #e94560 !important;
  color: white !important;
  border-right: 3px solid #e94560;
}

.nav-menu :deep(.el-sub-menu__title) {
  padding: 12px 20px;
}

.nav-menu :deep(.el-sub-menu__icon-arrow) {
  transition: transform 0.3s;
}

.nav-menu :deep(.el-sub-menu.is-opened .el-sub-menu__icon-arrow) {
  transform: rotate(90deg);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.simulation-label {
  position: fixed;
  top: 80px;
  left: 20px;
  background: rgba(233, 69, 96, 0.9);
  color: white;
  padding: 8px 16px;
  border-radius: 4px;
  font-weight: 700;
  font-size: 14px;
  z-index: 1000;
  box-shadow: 0 4px 12px rgba(233, 69, 96, 0.3);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.footer-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.simulation-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(233, 69, 96, 0.2);
  color: #e94560;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.version {
  color: #aaa;
  font-size: 12px;
}

.db-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 20px;
}

.db-status.status-connected {
  background: rgba(0, 255, 0, 0.1);
  color: #00ff00;
}

.db-status.status-disconnected {
  background: rgba(255, 0, 0, 0.1);
  color: #ff0000;
}

@media (max-width: 768px) {
  .nados-subtitle {
    display: none;
  }
  
  .simulation-clock {
    display: none;
  }
  
  .header-center {
    display: none;
  }
}
</style>