<!-- src/components/Sidebar/index.vue -->
<template>
  <div class="sidebar">
    <el-scrollbar>
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
  Tools
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
  padding: 12px 10px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.86), rgba(248, 250, 246, 0.76)),
    var(--surface-glass);
}

.sidebar-menu {
  border-right: none;
  height: 100%;
  background: transparent;
}

.sidebar-menu :deep(.el-menu-item) {
  height: 40px;
  line-height: 40px;
  font-size: 14px;
  color: var(--text-regular);
  border-radius: 14px;
  margin: 4px 0;
  letter-spacing: 0.01em;
  transition: background 0.18s, color 0.18s, box-shadow 0.18s, transform 0.18s;
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  position: relative;
  background: var(--surface);
  color: var(--brand-700);
  font-weight: 800;
  box-shadow: 0 12px 26px rgba(17, 31, 23, 0.08);
}

.sidebar-menu :deep(.el-menu-item.is-active::before) {
  content: "";
  position: absolute;
  left: 8px;
  top: 50%;
  width: 5px;
  height: 18px;
  border-radius: var(--radius-pill);
  background: linear-gradient(180deg, var(--brand-300), var(--brand-700));
  transform: translateY(-50%);
}

.sidebar-menu :deep(.el-menu-item.is-active .el-icon) {
  color: var(--brand-700);
}

.sidebar-menu :deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.72);
  color: var(--brand-700);
  transform: translateX(3px);
}

.sidebar-menu :deep(.el-sub-menu__title) {
  height: 40px;
  line-height: 40px;
  font-size: 14px;
  color: var(--text-regular);
  border-radius: 14px;
  margin: 4px 0;
  letter-spacing: 0.01em;
  transition: background 0.18s, color 0.18s;
}

.sidebar-menu :deep(.el-sub-menu__title:hover) {
  background: rgba(255, 255, 255, 0.72);
  color: var(--brand-700);
}

.sidebar-menu :deep(.el-sub-menu.is-opened > .el-sub-menu__title) {
  color: var(--brand-700);
  font-weight: 800;
}

.sidebar-menu :deep(.el-menu--inline .el-menu-item) {
  min-width: 0;
  margin-left: 18px;
  padding-left: 20px;
  border-left: 1px solid var(--border-light);
  border-radius: 12px;
}

.sidebar-menu :deep(.el-menu--inline .el-menu-item.is-active) {
  background: rgba(50, 168, 82, 0.1);
  color: var(--brand-700);
  box-shadow: none;
  border-left-color: var(--brand-500);
}

.sidebar-menu :deep(.el-menu-item .el-icon),
.sidebar-menu :deep(.el-sub-menu__title .el-icon) {
  font-size: 18px;
  width: 20px;
  margin-right: 8px;
  color: var(--text-secondary);
}

.sidebar-menu :deep(.el-menu--collapse .el-menu-item),
.sidebar-menu :deep(.el-menu--collapse .el-sub-menu__title) {
  justify-content: center;
}
</style>
