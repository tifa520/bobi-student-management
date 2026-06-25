<!-- frontend/src/components/Header/index.vue -->
<template>
  <header class="topbar">
    <div class="header-left">
      <div class="logo" @click="$router.push('/dashboard')">
        <span class="logo-icon">B</span>
        <span class="logo-text">Bobi艺术</span>
      </div>
      <el-icon class="collapse-icon" @click="appStore.toggleSidebar()">
        <Fold v-if="!appStore.sidebarCollapsed" />
        <Expand v-else />
      </el-icon>
      <el-breadcrumb separator="/" class="breadcrumb">
        <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
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
      <el-dropdown trigger="click" @command="handleUserCommand">
        <div class="user-info">
          <AppImage :src="userAvatar" :size="32" shape="circle" />
          <span class="user-name">{{ userName }}</span>
          <el-icon><ArrowDown /></el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">个人中心</el-dropdown-item>
            <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </header>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Fold, Expand, ArrowDown } from '@element-plus/icons-vue'
import { useAppStore } from '@/stores/app'
import { useUserStore } from '@/stores/user'
import { storeToRefs } from 'pinia'
import { DEFAULT_AVATAR_SVG } from '@/utils/constants'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const userStore = useUserStore()
const { user } = storeToRefs(userStore)

const sidebarCollapsed = computed(() => appStore.sidebarCollapsed)
const userName = computed(() => user.value.name || '管理员')
const userAvatar = computed(() => user.value.avatar || DEFAULT_AVATAR_SVG)

const breadcrumbItems = computed(() => {
  return route.matched.filter(item => item.meta?.title).slice(1)
})

function handleUserCommand(command) {
  if (command === 'profile') {
    router.push('/profile')
  } else if (command === 'logout') {
    ElMessageBox.confirm('确认退出登录？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info'
    }).then(() => {
      localStorage.clear()
      userStore.setUser({})
      router.push('/login')
      ElMessage.success('已退出')
    }).catch(() => {})
  }
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
  padding: 0 18px 0 20px;
  background:
    radial-gradient(circle at 0 50%, rgba(50, 168, 82, 0.12), transparent 260px),
    var(--surface-glass);
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
  z-index: 100;
  box-shadow: 0 1px 0 rgba(17, 31, 23, 0.03);
  backdrop-filter: blur(18px);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 18px;
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
  padding: 6px 8px 6px 6px;
  border-radius: var(--radius-pill);
  transition: background 0.18s ease;
}

.logo:hover {
  background: rgba(50, 168, 82, 0.08);
}

.logo-icon {
  width: 36px;
  height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  color: #fff;
  font-size: 18px;
  font-weight: 900;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.24), transparent 38%),
    linear-gradient(135deg, var(--brand-400), var(--brand-800));
  box-shadow: 0 12px 24px rgba(50, 168, 82, 0.22);
}

.logo-text {
  font-size: 18px;
  font-weight: 900;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.collapse-icon {
  width: 36px;
  height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-pill);
  font-size: 18px;
  cursor: pointer;
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.66);
  border: 1px solid var(--border-subtle);
  transition: color 0.18s, background 0.18s, transform 0.18s;
  flex-shrink: 0;
}

.collapse-icon:hover {
  color: var(--brand-700);
  background: var(--surface-green);
  transform: translateY(-1px);
}

.breadcrumb {
  font-size: 14px;
  flex: 1;
  min-width: 0;
}

.breadcrumb-current {
  color: var(--text-primary);
  font-weight: 800;
}

.breadcrumb-link {
  color: var(--text-secondary);
  text-decoration: none;
}

.breadcrumb-link:hover {
  color: var(--brand-600);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 6px 11px 6px 6px;
  border-radius: var(--radius-pill);
  color: var(--text-regular);
  background: rgba(255, 255, 255, 0.74);
  border: 1px solid var(--border-subtle);
  transition: background 0.18s, box-shadow 0.18s, transform 0.18s;
}

.user-info:hover {
  background: var(--surface);
  box-shadow: var(--shadow-sm);
  transform: translateY(-1px);
}

.user-name {
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 700;
}

@media (max-width: 768px) {
  .breadcrumb {
    display: none;
  }
  .logo-text {
    display: none;
  }
}
</style>
