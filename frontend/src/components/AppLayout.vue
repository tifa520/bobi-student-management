<!-- frontend/src/components/AppLayout.vue -->
<template>
  <el-container class="app-layout">
    <!-- ===== 顶部通栏 ===== -->
    <el-header class="app-header" height="60px">
      <div class="header-left">
        <div class="logo" @click="goHome">
          <span class="logo-icon">🎨</span>
          <span class="logo-text">Bobi艺术</span>
        </div>
        <el-input
          v-model="searchKeyword"
          placeholder="搜索学员、课程、班级"
          prefix-icon="Search"
          clearable
          size="default"
          class="header-search"
          @keyup.enter="handleSearch"
        />
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
    </el-header>

    <el-container>
      <!-- ===== 左侧导航（手风琴模式，非折叠） ===== -->
      <el-aside class="app-sidebar" width="140px">
        <el-menu
          :default-active="activeMenu"
          router
          unique-opened
          class="sidebar-menu"
        >
          <!-- 工作台 -->
          <el-menu-item index="/dashboard">
            <el-icon><Monitor /></el-icon>
            <span>工作台</span>
          </el-menu-item>

          <!-- 教务 -->
          <el-sub-menu index="edu">
            <template #title>
              <el-icon><School /></el-icon>
              <span>教务</span>
            </template>
            <el-menu-item index="/enroll">学员报名</el-menu-item>
            <el-menu-item index="/students">在学学员</el-menu-item>
            <el-menu-item index="/history-students">历史学员</el-menu-item>
            <el-menu-item index="/attendance">学员考勤</el-menu-item>
            <el-menu-item index="/scores">积分管理</el-menu-item>
          </el-sub-menu>

          <!-- 管理 -->
          <el-sub-menu index="manage">
            <template #title>
              <el-icon><Setting /></el-icon>
              <span>管理</span>
            </template>
            <el-menu-item index="/teachers">教师管理</el-menu-item>
            <el-menu-item index="/salary">课酬提成</el-menu-item>
            <el-menu-item index="/classes">班级管理</el-menu-item>
            <el-menu-item index="/courses">课程管理</el-menu-item>
            <el-menu-item index="/packages">套餐管理</el-menu-item>
            <el-menu-item index="/classrooms">教室管理</el-menu-item>
            <el-menu-item index="/items-manage">物品管理</el-menu-item>
            <el-menu-item index="/item-sale-exchange">销售兑换</el-menu-item>
            <el-menu-item index="/activities">活动管理</el-menu-item>
          </el-sub-menu>

          <!-- 统计 -->
          <el-sub-menu index="stats">
            <template #title>
              <el-icon><DataAnalysis /></el-icon>
              <span>统计</span>
            </template>
            <el-menu-item index="/stats/enroll">报名统计</el-menu-item>
            <el-menu-item index="/stats/payment">收费统计</el-menu-item>
            <el-menu-item index="/stats/hours">课时统计</el-menu-item>
            <el-menu-item index="/stats/items">物品统计</el-menu-item>
            <el-menu-item index="/stats/fees">杂费统计</el-menu-item>
            <el-menu-item index="/stats/refund">退费统计</el-menu-item>
          </el-sub-menu>

          <!-- 记录 -->
          <el-sub-menu index="records">
            <template #title>
              <el-icon><Document /></el-icon>
              <span>记录</span>
            </template>
            <el-menu-item index="/orders">报名记录</el-menu-item>
            <el-menu-item index="/sales-orders">销售订单</el-menu-item>
            <el-menu-item index="/course-records">课消记录</el-menu-item>
            <el-menu-item index="/score-records">积分记录</el-menu-item>
            <el-menu-item index="/fees-records">杂费记录</el-menu-item>
            <el-menu-item index="/inventory-records">库存记录</el-menu-item>
          </el-sub-menu>

          <!-- 设置 -->
          <el-sub-menu index="settings">
            <template #title>
              <el-icon><Tools /></el-icon>
              <span>设置</span>
            </template>
            <el-menu-item index="/settings/payment-methods">支付方式</el-menu-item>
            <el-menu-item index="/settings/background">背景设置</el-menu-item>
            <el-menu-item index="/settings/item-categories">商品类别</el-menu-item>
            <el-menu-item index="/settings/exchange-rate">积分汇率</el-menu-item>
          </el-sub-menu>
        </el-menu>
      </el-aside>

      <!-- ===== 主内容区 ===== -->
      <el-main class="app-main">
        <div class="page-content">
          <router-view />
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Monitor,
  School,
  Setting,
  DataAnalysis,
  Document,
  Tools,
  ArrowDown
} from '@element-plus/icons-vue'
import { DEFAULT_AVATAR_SVG } from '@/utils/constants'
import AppImage from '@/components/AppImage.vue'

const route = useRoute()
const router = useRouter()

const userName = ref('管理员')
const userAvatar = ref(DEFAULT_AVATAR_SVG)
const searchKeyword = ref('')

const activeMenu = computed(() => route.path)

function goHome() {
  router.push('/dashboard')
}

function handleSearch() {
  const keyword = searchKeyword.value.trim()
  if (keyword) {
    router.push({ path: '/students', query: { search: keyword } })
  }
}

function handleUserCommand(command) {
  if (command === 'logout') {
    ElMessageBox.confirm('确认退出登录？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info'
    }).then(() => {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      router.push('/login')
      ElMessage.success('已退出')
    }).catch(() => {})
  } else if (command === 'profile') {
    ElMessage.info('个人中心功能开发中')
  }
}

function loadUserInfo() {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    try {
      const user = JSON.parse(userStr)
      userName.value = user.name || '管理员'
      userAvatar.value = user.avatar || DEFAULT_AVATAR_SVG
    } catch (e) {
      console.error('解析用户信息失败', e)
    }
  }
}

onMounted(() => {
  loadUserInfo()
})
</script>

<style scoped>
/* ============================================================
   AppLayout 样式（手风琴模式，非折叠）
   ============================================================ */

/* -------- 顶部通栏 -------- */
.app-header {
  height: 60px;
  background: #ffffff;
  border-bottom: 1px solid var(--el-border-color-light, #e4e7ed);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  flex-shrink: 0;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
  flex: 1;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
  flex-shrink: 0;
}
.logo-icon {
  font-size: 24px;
}
.logo-text {
  font-size: 18px;
  font-weight: 700;
  color: var(--el-color-primary, #36b459);
  letter-spacing: 0.5px;
}

.header-search {
  width: 280px;
}
.header-search :deep(.el-input__wrapper) {
  border-radius: 20px;
  background: #f5f7fa;
  height: 32px;
  min-height: 32px;
}
.header-search :deep(.el-input__inner) {
  font-size: 14px;
  height: 32px;
  line-height: 32px;
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
  padding: 4px 8px;
  border-radius: 20px;
  transition: background 0.2s;
}
.user-info:hover {
  background: #f5f7fa;
}
.user-name {
  font-size: 14px;
  color: var(--el-text-color-primary, #303133);
  font-weight: 500;
}

/* -------- 左侧导航（手风琴模式，非折叠） -------- */
.app-sidebar {
  width: 140px;
  background: #ffffff;
  border-right: 1px solid var(--el-border-color-light, #e4e7ed);
  flex-shrink: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding-top: 8px;
}

.sidebar-menu {
  border-right: none;
  height: 100%;
  overflow-y: auto;
}

/* ---- 菜单项基础样式 ---- */
.sidebar-menu :deep(.el-menu-item) {
  height: 44px;
  line-height: 44px;
  font-size: 14px;
  padding: 0 12px;
  color: var(--el-text-color-regular, #606266);
  border-radius: 0 8px 8px 0;
  margin: 2px 6px 2px 0;
  transition: all 0.2s ease;
}

/* ---- 菜单项悬停 ---- */
.sidebar-menu :deep(.el-menu-item:hover) {
  background-color: var(--el-color-primary-light-9, #f0f9eb);
  color: var(--el-color-primary, #36b459);
}

/* ---- 菜单项激活（绿色背景白字） ---- */
.sidebar-menu :deep(.el-menu-item.is-active) {
  background-color: var(--el-color-primary, #36b459);
  color: #ffffff;
  font-weight: 500;
  box-shadow: 0 4px 12px rgba(54, 180, 89, 0.3);
}
.sidebar-menu :deep(.el-menu-item.is-active .el-icon) {
  color: #ffffff;
}

/* ---- 子菜单标题 ---- */
.sidebar-menu :deep(.el-sub-menu__title) {
  height: 44px;
  line-height: 44px;
  font-size: 14px;
  padding: 0 12px;
  color: var(--el-text-color-regular, #606266);
  border-radius: 0 8px 8px 0;
  margin: 2px 6px 2px 0;
  transition: all 0.2s ease;
}
.sidebar-menu :deep(.el-sub-menu__title:hover) {
  background-color: var(--el-color-primary-light-9, #f0f9eb);
  color: var(--el-color-primary, #36b459);
}

/* ---- 展开的子菜单标题（手风琴激活指示） ---- */
.sidebar-menu :deep(.el-sub-menu.is-opened > .el-sub-menu__title) {
  color: var(--el-color-primary, #36b459);
  font-weight: 500;
}

/* ---- 子菜单中的菜单项缩进 ---- */
.sidebar-menu :deep(.el-menu--inline .el-menu-item) {
  padding-left: 40px;
}

/* ---- 子菜单中的菜单项激活（浅绿背景） ---- */
.sidebar-menu :deep(.el-menu--inline .el-menu-item.is-active) {
  background-color: var(--el-color-primary-light-9, #f0f9eb);
  color: var(--el-color-primary, #36b459);
  font-weight: 500;
  box-shadow: none;
}
.sidebar-menu :deep(.el-menu--inline .el-menu-item.is-active .el-icon) {
  color: var(--el-color-primary, #36b459);
}

/* ---- 图标样式 ---- */
.sidebar-menu :deep(.el-menu-item .el-icon),
.sidebar-menu :deep(.el-sub-menu__title .el-icon) {
  font-size: 18px;
  width: 20px;
  margin-right: 8px;
}

/* ---- 手风琴箭头图标样式 ---- */
.sidebar-menu :deep(.el-sub-menu .el-sub-menu__icon-arrow) {
  color: var(--el-text-color-placeholder, #94a3b8);
  font-size: 14px;
  transition: transform 0.2s ease, color 0.2s ease;
}
.sidebar-menu :deep(.el-sub-menu.is-opened .el-sub-menu__icon-arrow) {
  color: var(--el-color-primary, #36b459);
  transform: rotate(180deg);
}

/* ---- 滚动条美化 ---- */
.app-sidebar::-webkit-scrollbar {
  width: 3px;
}
.app-sidebar::-webkit-scrollbar-thumb {
  background: #d0d5dd;
  border-radius: 2px;
}
.app-sidebar::-webkit-scrollbar-track {
  background: transparent;
}

/* -------- 主内容区 -------- */
.app-main {
  flex: 1;
  padding: 0 20px 20px 20px;
  overflow-y: auto;
  background: var(--el-bg-color-page, #f5f7fa);
  display: flex;
  flex-direction: column;
}

.page-content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

/* -------- 响应式适配 -------- */
@media (max-width: 768px) {
  .app-sidebar {
    width: 60px;
  }
  .app-sidebar .el-menu-item span,
  .app-sidebar .el-sub-menu__title span {
    display: none;
  }
  .header-search {
    width: 140px;
  }
  .logo-text {
    font-size: 16px;
  }
  .app-main {
    padding: 0 12px 12px 12px;
  }
}

@media (max-width: 480px) {
  .app-header {
    padding: 0 12px;
  }
  .header-search {
    width: 100px;
  }
  .logo-icon {
    font-size: 20px;
  }
  .logo-text {
    font-size: 14px;
  }
  .user-name {
    display: none;
  }
}
</style>