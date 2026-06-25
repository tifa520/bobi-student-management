<template>
  <div class="sidebar">
    <div class="sidebar-brand" @click="$router.push('/dashboard')">
      <div class="brand-icon">
        <span>B</span>
      </div>
      <div v-if="!collapsed" class="brand-info">
        <span class="brand-name">Bobi艺术</span>
        <span class="brand-slogan">学员管理系统</span>
      </div>
    </div>

    <div class="sidebar-menu-wrapper">
      <el-scrollbar class="sidebar-scroll">
        <el-menu
          :default-active="activeMenu"
          router
          unique-opened
          :collapse="collapsed"
          :collapse-transition="false"
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
      </el-scrollbar>
    </div>

    <div class="sidebar-footer">
      <div
        class="collapse-toggle"
        @click="appStore.toggleSidebar()"
        :title="collapsed ? '展开侧边栏' : '收起侧边栏'"
      >
        <el-icon class="collapse-icon">
          <Back v-if="!collapsed" />
          <ArrowRight v-else />
        </el-icon>
        <span v-if="!collapsed" class="collapse-text">收起菜单</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import {
  Monitor,
  School,
  Setting,
  DataAnalysis,
  Document,
  Tools,
  Back,
  ArrowRight
} from '@element-plus/icons-vue'

const route = useRoute()
const appStore = useAppStore()

const activeMenu = computed(() => route.path)
const collapsed = computed(() => appStore.sidebarCollapsed)
</script>

<style scoped>
.sidebar {
  height: 100%;
  display: flex;
  flex-direction: column;
  background:
    linear-gradient(180deg,
      rgba(255, 255, 255, 0.92),
      rgba(248, 250, 246, 0.86));
  border-right: 1px solid var(--border-subtle);
  position: relative;
}

.sidebar::before {
  content: "";
  position: absolute;
  top: 0;
  right: 0;
  width: 1px;
  height: 120px;
  background: linear-gradient(180deg,
    rgba(30, 168, 82, 0.3),
    rgba(212, 148, 26, 0.2),
    transparent);
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 16px;
  cursor: pointer;
  border-bottom: 1px solid var(--border-subtle);
  transition: background 0.25s var(--ease-soft);
  flex-shrink: 0;
}

.sidebar-brand:hover {
  background: rgba(30, 168, 82, 0.04);
}

.brand-icon {
  width: 44px;
  height: 44px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.3), transparent 50%),
    linear-gradient(135deg, var(--brand-400), var(--brand-700));
  box-shadow:
    0 6px 16px rgba(30, 168, 82, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.25);
}

.brand-icon span {
  font-size: 22px;
  font-weight: 900;
  color: #fff;
  font-family: var(--font-display);
  letter-spacing: 1px;
}

.brand-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.brand-name {
  font-size: 18px;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1.2;
  font-family: var(--font-display);
  background: linear-gradient(135deg, var(--gray-900), var(--brand-700));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.brand-slogan {
  font-size: 12px;
  color: var(--text-placeholder);
  line-height: 1.2;
  letter-spacing: 0.05em;
}

.sidebar-menu-wrapper {
  flex: 1;
  min-height: 0;
  padding: 10px 10px;
}

.sidebar-scroll {
  height: 100%;
}

.sidebar-menu {
  border-right: none;
  height: 100%;
  background: transparent;
}

.sidebar-menu :deep(.el-menu-item) {
  height: 42px;
  line-height: 42px;
  font-size: 14px;
  color: var(--text-regular);
  border-radius: var(--radius-md);
  margin: 4px 0;
  padding: 0 14px;
  letter-spacing: 0.01em;
  font-weight: 500;
  transition: all 0.2s var(--ease-soft);
  position: relative;
  overflow: hidden;
}

.sidebar-menu :deep(.el-menu-item::before) {
  content: "";
  position: absolute;
  left: 0;
  top: 50%;
  width: 3px;
  height: 0;
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  background: linear-gradient(180deg, var(--brand-400), var(--brand-600));
  transform: translateY(-50%);
  transition: height 0.25s var(--ease-soft);
  opacity: 0;
}

.sidebar-menu :deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.8);
  color: var(--brand-700);
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg,
    rgba(30, 168, 82, 0.12),
    rgba(30, 168, 82, 0.04));
  color: var(--brand-700);
  font-weight: 700;
  box-shadow: 0 2px 8px rgba(30, 168, 82, 0.08);
}

.sidebar-menu :deep(.el-menu-item.is-active::before) {
  height: 20px;
  opacity: 1;
}

.sidebar-menu :deep(.el-menu-item.is-active .el-icon) {
  color: var(--brand-600);
}

.sidebar-menu :deep(.el-sub-menu__title) {
  height: 42px;
  line-height: 42px;
  font-size: 14px;
  color: var(--text-regular);
  border-radius: var(--radius-md);
  margin: 4px 0;
  padding: 0 14px;
  letter-spacing: 0.01em;
  font-weight: 500;
  transition: all 0.2s var(--ease-soft);
}

.sidebar-menu :deep(.el-sub-menu__title:hover) {
  background: rgba(255, 255, 255, 0.8);
  color: var(--brand-700);
}

.sidebar-menu :deep(.el-sub-menu.is-opened > .el-sub-menu__title) {
  color: var(--brand-700);
  font-weight: 700;
}

.sidebar-menu :deep(.el-sub-menu.is-opened > .el-sub-menu__title .el-icon) {
  color: var(--brand-600);
}

.sidebar-menu :deep(.el-menu--inline .el-menu-item) {
  min-width: 0;
  margin-left: 8px;
  padding-left: 28px;
  border-radius: var(--radius-md);
  height: 38px;
  line-height: 38px;
  font-size: 13.5px;
}

.sidebar-menu :deep(.el-menu--inline .el-menu-item.is-active) {
  background: rgba(30, 168, 82, 0.1);
  color: var(--brand-700);
  box-shadow: none;
  font-weight: 600;
}

.sidebar-menu :deep(.el-menu--inline .el-menu-item.is-active::before) {
  height: 16px;
}

.sidebar-menu :deep(.el-menu-item .el-icon),
.sidebar-menu :deep(.el-sub-menu__title .el-icon) {
  font-size: 18px;
  width: 20px;
  margin-right: 10px;
  color: var(--text-secondary);
  transition: color 0.2s;
}

.sidebar-menu :deep(.el-menu--collapse .el-menu-item),
.sidebar-menu :deep(.el-menu--collapse .el-sub-menu__title) {
  justify-content: center;
  padding: 0;
}

.sidebar-menu :deep(.el-menu--collapse .el-menu-item .el-icon),
.sidebar-menu :deep(.el-menu--collapse .el-sub-menu__title .el-icon) {
  margin-right: 0;
}

.sidebar-footer {
  flex-shrink: 0;
  padding: 10px 12px;
  border-top: 1px solid var(--border-subtle);
}

.collapse-toggle {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--text-secondary);
  transition: all 0.2s var(--ease-soft);
}

.collapse-toggle:hover {
  background: rgba(30, 168, 82, 0.08);
  color: var(--brand-700);
}

.collapse-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.collapse-text {
  font-size: 13px;
  font-weight: 500;
}

.sidebar-menu-wrapper :deep(.el-scrollbar__thumb) {
  background: rgba(15, 38, 25, 0.15);
  border-radius: 4px;
}

.sidebar-menu-wrapper :deep(.el-scrollbar__thumb:hover) {
  background: rgba(15, 38, 25, 0.25);
}
</style>
