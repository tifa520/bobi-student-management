<template>
  <header class="topbar">
    <div class="header-left">
      <div class="logo" @click="$router.push('/dashboard')">
        <span class="logo-mark">B</span>
        <span class="logo-text">Bobi艺术</span>
      </div>
      <div class="header-divider"></div>
      <el-breadcrumb separator="›" class="breadcrumb">
        <el-breadcrumb-item :to="{ path: '/dashboard' }">
          <span class="breadcrumb-home">首页</span>
        </el-breadcrumb-item>
        <el-breadcrumb-item
          v-for="(item, index) in breadcrumbItems"
          :key="index"
        >
          <span v-if="index === breadcrumbItems.length - 1" class="breadcrumb-current">
            {{ item.meta?.title || item.name }}
          </span>
          <router-link v-else :to="item.path" class="breadcrumb-link">
            {{ item.meta?.title || item.name }}
          </router-link>
        </el-breadcrumb-item>
      </el-breadcrumb>
    </div>
    <div class="header-right">
      <div class="header-actions">
        <div class="action-btn" title="全屏切换" @click="toggleFullscreen">
          <el-icon class="action-icon">
            <FullScreen v-if="!isFullscreen" />
            <Aim v-else />
          </el-icon>
        </div>
        <div class="action-btn" title="刷新页面" @click="refreshPage">
          <el-icon class="action-icon"><Refresh /></el-icon>
        </div>
      </div>
      <div class="header-divider vertical"></div>
      <el-dropdown trigger="click" @command="handleUserCommand">
        <div class="user-info">
          <div class="user-avatar-wrap">
            <span class="avatar-initials">{{ userName.charAt(0) }}</span>
            <span class="avatar-status"></span>
          </div>
          <div class="user-meta">
            <span class="user-name">{{ userName }}</span>
            <span class="user-role">{{ userRoleText }}</span>
          </div>
          <el-icon class="user-arrow"><ArrowDown /></el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu class="user-dropdown">
            <div class="dropdown-header">
              <span class="dropdown-avatar">{{ userName.charAt(0) }}</span>
              <div class="dropdown-user-info">
                <span class="dropdown-name">{{ userName }}</span>
                <span class="dropdown-role">{{ userRoleText }}</span>
              </div>
            </div>
            <el-dropdown-item command="profile">
              <el-icon><User /></el-icon>
              个人中心
            </el-dropdown-item>
            <el-dropdown-item command="logout" divided>
              <el-icon><SwitchButton /></el-icon>
              退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowDown,
  User,
  SwitchButton,
  FullScreen,
  Aim,
  Refresh
} from '@element-plus/icons-vue'
import { useAppStore } from '@/stores/app'
import { useUserStore } from '@/stores/user'
import { storeToRefs } from 'pinia'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const userStore = useUserStore()
const { user } = storeToRefs(userStore)

const isFullscreen = ref(false)

const userName = computed(() => user.value.name || '管理员')
const userRoleText = computed(() => {
  const role = user.value.role
  const roleMap = {
    admin: '管理员',
    teacher: '教师',
    staff: '前台'
  }
  return roleMap[role] || '管理员'
})

const breadcrumbItems = computed(() => {
  return route.matched.filter(item => item.meta?.title).slice(1)
})

function handleUserCommand(command) {
  if (command === 'profile') {
    router.push('/profile')
  } else if (command === 'logout') {
    ElMessageBox.confirm('确认退出登录？', '提示', {
      confirmButtonText: '确定退出',
      cancelButtonText: '取消',
      type: 'info',
      customClass: 'logout-confirm-dialog'
    }).then(() => {
      localStorage.clear()
      userStore.setUser({})
      router.push('/login')
      ElMessage.success('已安全退出')
    }).catch(() => {})
  }
}

function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
    isFullscreen.value = true
  } else {
    document.exitFullscreen()
    isFullscreen.value = false
  }
}

function refreshPage() {
  window.location.reload()
}

onMounted(() => {
  userStore.loadFromStorage()
})
</script>

<style scoped>
.topbar {
  height: var(--header-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background:
    radial-gradient(ellipse at 0 0, rgba(30, 168, 82, 0.08), transparent 300px),
    linear-gradient(180deg,
      rgba(255, 255, 255, 0.92),
      rgba(255, 255, 255, 0.85));
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
  z-index: 100;
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  position: relative;
}

.topbar::after {
  content: "";
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg,
    transparent,
    rgba(30, 168, 82, 0.2),
    rgba(212, 148, 26, 0.15),
    transparent);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
  min-width: 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  user-select: none;
  flex-shrink: 0;
  padding: 6px 12px 6px 6px;
  border-radius: var(--radius-pill);
  transition: all 0.25s var(--ease-soft);
}

.logo:hover {
  background: rgba(30, 168, 82, 0.08);
  transform: translateY(-1px);
}

.logo-mark {
  width: 38px;
  height: 38px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  color: #fff;
  font-size: 20px;
  font-weight: 900;
  font-family: var(--font-display);
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.28), transparent 45%),
    linear-gradient(135deg, var(--brand-400), var(--brand-700));
  box-shadow:
    0 4px 12px rgba(30, 168, 82, 0.28),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  letter-spacing: 1px;
}

.logo-text {
  font-size: 17px;
  font-weight: 800;
  color: var(--text-primary);
  letter-spacing: -0.01em;
  font-family: var(--font-display);
  background: linear-gradient(135deg, var(--gray-900), var(--brand-700));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-divider {
  width: 1px;
  height: 24px;
  background: linear-gradient(180deg, transparent, var(--border-light), transparent);
  flex-shrink: 0;
}

.header-divider.vertical {
  margin: 0 4px;
}

.breadcrumb {
  font-size: 14px;
  flex: 1;
  min-width: 0;
}

.breadcrumb-home {
  color: var(--text-secondary);
  font-weight: 500;
}

.breadcrumb-current {
  color: var(--text-primary);
  font-weight: 700;
}

.breadcrumb-link {
  color: var(--text-secondary);
  text-decoration: none;
  transition: color 0.2s;
}

.breadcrumb-link:hover {
  color: var(--brand-600);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.action-btn {
  width: 36px;
  height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--text-secondary);
  transition: all 0.2s var(--ease-soft);
}

.action-btn:hover {
  color: var(--brand-700);
  background: var(--surface-green);
  transform: translateY(-1px);
}

.action-icon {
  font-size: 18px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 6px 12px 6px 6px;
  border-radius: var(--radius-pill);
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid var(--border-subtle);
  transition: all 0.25s var(--ease-soft);
}

.user-info:hover {
  background: var(--surface);
  box-shadow: var(--shadow-sm);
  transform: translateY(-1px);
  border-color: rgba(30, 168, 82, 0.2);
}

.user-avatar-wrap {
  position: relative;
  width: 34px;
  height: 34px;
  flex-shrink: 0;
}

.avatar-initials {
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  font-size: 15px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, var(--brand-400), var(--brand-600));
  font-family: var(--font-display);
}

.avatar-status {
  position: absolute;
  bottom: -2px;
  right: -2px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--success-color);
  border: 2px solid #fff;
}

.user-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-name {
  font-size: 13px;
  color: var(--text-primary);
  font-weight: 600;
  line-height: 1.2;
}

.user-role {
  font-size: 11px;
  color: var(--text-placeholder);
  line-height: 1.2;
}

.user-arrow {
  font-size: 14px;
  color: var(--text-placeholder);
  margin-left: 2px;
}

.user-dropdown {
  padding: 8px 0;
  min-width: 200px;
}

.dropdown-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px 14px;
  border-bottom: 1px solid var(--border-light);
  margin-bottom: 6px;
}

.dropdown-avatar {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  font-size: 18px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, var(--brand-400), var(--brand-600));
  font-family: var(--font-display);
  flex-shrink: 0;
}

.dropdown-user-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.dropdown-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.2;
}

.dropdown-role {
  font-size: 12px;
  color: var(--text-placeholder);
  line-height: 1.2;
}

.user-dropdown :deep(.el-dropdown-menu__item) {
  padding: 10px 16px;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: all 0.18s;
}

.user-dropdown :deep(.el-dropdown-menu__item:hover) {
  background: var(--brand-50);
  color: var(--brand-700);
}

.user-dropdown :deep(.el-dropdown-menu__item .el-icon) {
  font-size: 16px;
}

.user-dropdown :deep(.el-dropdown-menu__item--divided) {
  border-top: 1px solid var(--border-light);
  margin-top: 6px;
  padding-top: 12px;
}

@media (max-width: 768px) {
  .breadcrumb {
    display: none;
  }
  .logo-text {
    display: none;
  }
  .user-meta {
    display: none;
  }
  .header-actions {
    display: none;
  }
}
</style>
