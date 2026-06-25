<!-- frontend/src/views/Dashboard.vue -->
<template>
  <div class="dashboard-container">
    <div class="dashboard-main">
      <!-- ===== 左侧区域 70% ===== -->
      <div class="left-column">
        <!-- 1. 个人信息卡片 -->
        <div class="profile-card">
          <div class="profile-content">
            <AppImage :src="userAvatar" :size="56" shape="circle" />
            <div class="user-info">
              <div class="user-name">{{ userName }}</div>
              <div class="user-role">{{ userRole }}</div>
              <div class="welcome-text">欢迎回来！</div>
            </div>
          </div>
        </div>

        <!-- 2. 便捷入口 -->
        <div class="quick-entry-card">
          <div class="entry-row">
            <div
              v-for="item in quickEntries"
              :key="item.path"
              class="entry-item"
              @click="goToPage(item.path)"
            >
              <div class="entry-icon" :style="{ backgroundColor: item.bgColor }">
                <el-icon :size="22"><component :is="item.icon" /></el-icon>
              </div>
              <span class="entry-name">{{ item.name }}</span>
            </div>
          </div>
        </div>

        <!-- 3. 三列数据卡片（左右布局） -->
        <div class="data-cards-row">
          <!-- 3.1 学员概况 -->
          <div class="data-card" v-loading="loading.student">
            <div class="card-header">
              <span class="card-title">学员概况</span>
              <el-button type="primary" link size="small" @click="refreshStudentOverview">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
            <div class="card-body">
              <div class="card-left">
                <div class="data-item">
                  <span class="data-label">在学学员</span>
                  <span class="data-value">{{ studentOverview.active }}</span>
                  <span class="data-unit">人</span>
                </div>
              </div>
              <div class="card-right">
                <BaseChart :options="studentPieOption" height="130px" />
              </div>
            </div>
          </div>

          <!-- 3.2 收入概况 -->
          <div class="data-card" v-loading="loading.income">
            <div class="card-header">
              <span class="card-title">收入概况</span>
              <el-button type="primary" link size="small" @click="fetchIncomeOverview">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
            <div class="card-body">
              <div class="card-left">
                <div class="data-item">
                  <span class="data-label">今日报名人数</span>
                  <span class="data-value">{{ incomeData.today_count }}</span>
                  <span class="data-unit">人</span>
                </div>
                <div class="data-item">
                  <span class="data-label">今日报名收入</span>
                  <span class="data-value text-primary">¥{{ incomeData.today_amount.toFixed(0) }}</span>
                </div>
              </div>
              <div class="card-right">
                <BaseChart :options="incomePieOption" height="130px" />
              </div>
            </div>
          </div>

          <!-- 3.3 剩余课时 -->
          <div class="data-card" v-loading="loading.hours">
            <div class="card-header">
              <span class="card-title">剩余课时</span>
              <el-button type="primary" link size="small" @click="fetchHoursOverview">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
            <div class="card-body">
              <div class="card-left">
                <div class="data-item">
                  <span class="data-label">剩余总课时</span>
                  <span class="data-value">{{ hoursData.remaining_hours }}</span>
                  <span class="data-unit">课时</span>
                </div>
                <div class="data-item">
                  <span class="data-label">剩余总金额</span>
                  <span class="data-value text-primary">¥{{ hoursData.remaining_amount.toFixed(0) }}</span>
                </div>
              </div>
              <div class="card-right">
                <BaseChart :options="hoursPieOption" height="130px" />
              </div>
            </div>
          </div>
        </div>

        <!-- 4. 课程表 -->
        <div class="schedule-card">
          <div class="schedule-header">
            <span class="schedule-title">课程表</span>
            <el-button type="primary" link size="small" @click="goToAttendance">更多</el-button>
          </div>
          <div class="schedule-control">
            <el-button size="small" @click="prevTwoWeeks" :icon="ArrowLeft" />
            <span class="date-range">{{ dateRange }}</span>
            <el-button size="small" @click="nextTwoWeeks" :icon="ArrowRight" />
            <el-button size="small" @click="goToday">今天</el-button>
          </div>
          <div class="schedule-days">
            <div
              v-for="day in calendarDays"
              :key="day.date"
              class="schedule-day"
              :class="{
                'is-today': day.isToday,
                'has-schedule': day.hasSchedule
              }"
            >
              <el-tooltip
                v-if="day.hasSchedule && day.scheduleInfo && day.scheduleInfo.length"
                placement="top"
                :open-delay="300"
                :show-after="200"
              >
                <template #content>
                  <div class="tooltip-schedule-list">
                    <div
                      v-for="(session, idx) in day.scheduleInfo"
                      :key="idx"
                      class="tooltip-schedule-item"
                    >
                      <div class="tooltip-time">{{ session.start_time }} ~ {{ session.end_time }}</div>
                      <div class="tooltip-course-class">
                        {{ session.course_name || '未命名课程' }}（{{ session.class_name || '未分班' }}）
                      </div>
                      <div class="tooltip-teacher-classroom">
                        教师：{{ session.teacher_name || '-' }} | 教室：{{ session.classroom_name || '-' }}
                      </div>
                    </div>
                  </div>
                </template>
                <div class="schedule-day-content" @click="jumpToAttendance(day.date)">
                  <div class="day-week">{{ day.dayName }}</div>
                  <div class="day-date">{{ day.dayOfMonth }}</div>
                  <div class="day-dot" v-if="day.hasSchedule">
                    <span :class="day.allCompleted ? 'dot-gray' : 'dot-green'"></span>
                  </div>
                </div>
              </el-tooltip>
              <div v-else class="schedule-day-content" @click="jumpToAttendance(day.date)">
                <div class="day-week">{{ day.dayName }}</div>
                <div class="day-date">{{ day.dayOfMonth }}</div>
                <div class="day-dot" v-if="day.hasSchedule">
                  <span :class="day.allCompleted ? 'dot-gray' : 'dot-green'"></span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ===== 右侧区域 30% ===== -->
      <div class="right-column">
        <!-- 1. 近期活动 -->
        <div class="banner-card">
          <div class="card-header">
            <span class="card-title">近期活动</span>
            <el-button type="primary" link size="small" @click="goToActivities">更多</el-button>
          </div>
          <el-carousel :interval="4000" height="150px" arrow="never" indicator-position="inside">
            <el-carousel-item v-for="activity in activityList" :key="activity.id">
              <div class="carousel-item" @click="goToActivityDetail(activity.id)">
                <img
                  v-if="activity.banner_image || activity.cover_image"
                  :src="activity.banner_image || activity.cover_image"
                  class="carousel-img"
                />
                <div v-else class="carousel-content">
                  <div class="activity-name">{{ activity.name }}</div>
                  <div class="activity-date">{{ activity.start_date ? activity.start_date.split(' ')[0] : '' }}</div>
                </div>
              </div>
            </el-carousel-item>
            <el-carousel-item v-if="activityList.length === 0">
              <div class="carousel-item empty">暂无活动</div>
            </el-carousel-item>
          </el-carousel>
        </div>

        <!-- 2. 本月生日 -->
        <div class="birthday-card">
          <div class="card-header">
            <span class="card-title">本月生日</span>
            <span class="birthday-count" v-if="birthdayStudents.length > 0">
              {{ birthdayStudents.length }} 位
            </span>
            <el-button type="primary" link size="small" @click="refreshBirthdayData">
              <el-icon><Refresh /></el-icon>
            </el-button>
          </div>
          <div class="birthday-list" v-if="birthdayStudents.length > 0">
            <div
              v-for="student in birthdayStudents"
              :key="student.id"
              class="birthday-item"
            >
              <el-tooltip placement="top" :open-delay="200" :show-after="100">
                <template #content>
                  <div class="birthday-tooltip">
                    <AppImage :src="student.avatar || defaultAvatar" :size="40" shape="circle" />
                    <div class="tooltip-name">{{ student.name }}</div>
                    <div class="tooltip-birthday">🎂 {{ student.birthday || '' }}</div>
                  </div>
                </template>
                <AppImage :src="student.avatar || defaultAvatar" :size="36" shape="circle" class="birthday-avatar" />
              </el-tooltip>
              <div class="birthday-name">{{ student.name }}</div>
            </div>
          </div>
          <div v-else class="birthday-empty">暂无</div>
        </div>

        <!-- 3. 待办提醒 -->
        <div class="todo-card">
          <div class="card-header">
            <span class="card-title">待办提醒</span>
            <el-button type="primary" link size="small" @click="refreshTodos">
              <el-icon><Refresh /></el-icon>
            </el-button>
          </div>
          <div class="todo-list">
            <div v-for="(todo, idx) in todoList" :key="idx" class="todo-item">
              <div class="todo-dot" :class="todo.type"></div>
              <div class="todo-content">
                <div class="todo-title">{{ todo.title }}</div>
                <div class="todo-desc">{{ todo.description }}</div>
              </div>
              <el-button
                v-if="todo.action"
                type="primary"
                link
                size="small"
                @click="todo.action.handler"
              >
                {{ todo.action.text }}
              </el-button>
            </div>
            <div v-if="todoList.length === 0" class="empty-tip">暂无待办</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { storeToRefs } from 'pinia'
import {
  User, School, Tickets, Goods, Picture, Box, Money, Timer,
  ArrowLeft, ArrowRight, Refresh, SuccessFilled, ShoppingCart,
  Present
} from '@element-plus/icons-vue'
import request from '@/api/request'
import dayjs from 'dayjs'
import { DEFAULT_AVATAR_SVG } from '@/utils/constants'
import BaseChart from '@/components/BaseChart.vue'

const router = useRouter()
const userStore = useUserStore()
const { user } = storeToRefs(userStore)

// ===================================================================
// 1. 用户信息
// ===================================================================

const userName = computed(() => user.value.name || '管理员')
const userRole = computed(() => user.value.role || '管理员')
const userAvatar = computed(() => user.value.avatar || DEFAULT_AVATAR_SVG)
const defaultAvatar = DEFAULT_AVATAR_SVG

// ===================================================================
// 2. 便捷入口
// ===================================================================

const quickEntries = [
  { name: '报名', path: '/enroll', icon: 'User', bgColor: '#36b459' },
  { name: '考勤', path: '/attendance', icon: 'Timer', bgColor: '#e6a23c' },
  { name: '积分', path: '/scores', icon: 'Tickets', bgColor: '#f56c6c' },
  { name: '班级', path: '/classes', icon: 'School', bgColor: '#409eff' },
  { name: '课程', path: '/courses', icon: 'Goods', bgColor: '#67c23a' },
  { name: '活动', path: '/activities', icon: 'Picture', bgColor: '#909399' },
  { name: '物品', path: '/items-manage', icon: 'Box', bgColor: '#e6a23c' },
  { name: '销售', path: '/item-sale-exchange', icon: 'ShoppingCart', bgColor: '#f56c6c' },
  { name: '课酬', path: '/salary', icon: 'Money', bgColor: '#f56c6c' }
]

function goToPage(path) {
  router.push(path)
}

function goToAttendance() {
  router.push('/attendance')
}

function goToActivities() {
  router.push('/activities')
}

function goToActivityDetail(id) {
  router.push(`/activities/detail?id=${id}`)
}

// ===================================================================
// 3. 加载状态
// ===================================================================

const loading = reactive({
  student: true,
  income: true,
  hours: true
})

// ===================================================================
// 4. 学员概况 - 玫瑰图配置
// ===================================================================

const studentOverview = reactive({
  active: 0,
  course_distribution: []
})

/**
 * ★ 学员概况玫瑰图配置
 * 特点：玫瑰图（南丁格尔玫瑰图），渐变色，标签居中，带引导线
 */
const studentPieOption = computed(() => {
  const rawData = studentOverview.course_distribution || []
  // 如果没有数据，显示占位
  const data = rawData.length > 0 ? rawData : [{ name: '暂无数据', value: 1 }]

  // 渐变色：从橙色渐变到蓝色（与示例风格一致）
  const colors = [
    { type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [
      { offset: 0, color: '#ffd2b3' }, { offset: 1, color: '#4a90d9' }
    ]},
    { type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [
      { offset: 0, color: '#ffd2b3' }, { offset: 1, color: '#6aa3e0' }
    ]},
    { type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [
      { offset: 0, color: '#ffd2b3' }, { offset: 1, color: '#5fa0e3' }
    ]},
    { type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [
      { offset: 0, color: '#ffd2b3' }, { offset: 1, color: '#5498e6' }
    ]},
    { type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [
      { offset: 0, color: '#ffd2b3' }, { offset: 1, color: '#4a90d9' }
    ]},
    { type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [
      { offset: 0, color: '#ffd2b3' }, { offset: 1, color: '#4088d0' }
    ]},
    { type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [
      { offset: 0, color: '#ffd2b3' }, { offset: 1, color: '#3680c8' }
    ]}
  ]

  return {
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        return `<strong>${params.name}</strong><br/>人数：${params.value} 人<br/>占比：${params.percent}%`
      }
    },
    legend: { show: false },
    series: [{
      type: 'pie',
      // ★ 玫瑰图核心配置
      roseType: 'area',
      // ★ 半径范围：内圈小，外圈大，留出标签空间
      radius: ['10%', '75%'],
      center: ['50%', '50%'],
      // ★ 扇区圆角
      itemStyle: {
        borderRadius: 6
      },
      // ★ 标签：居中显示，显示名称和数值
      label: {
        show: true,
        position: 'center',
        fontSize: 10,
        fontWeight: 'bold',
        color: '#333',
        formatter: (params) => {
          // 数值为1表示暂无数据，特殊处理
          if (params.value === 1 && params.name === '暂无数据') {
            return '暂无数据'
          }
          // 名称过长时截断
          const name = params.name.length > 6 ? params.name.slice(0, 5) + '…' : params.name
          return `${name}\n${params.value}人`
        },
        lineHeight: 14
      },
      // ★ 引导线
      labelLine: {
        show: true,
        lineStyle: {
          color: '#888',
          width: 1
        },
        length: 12,
        length2: 20
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 12,
          fontWeight: 'bold'
        },
        itemStyle: {
          shadowBlur: 12,
          shadowColor: 'rgba(0,0,0,0.2)'
        }
      },
      data: data.map((item, index) => ({
        name: item.name,
        value: item.value,
        itemStyle: {
          color: colors[index % colors.length]
        }
      }))
    }]
  }
})

async function fetchStudentOverview() {
  loading.student = true
  try {
    const res = await request.get('/dashboard/student-overview')
    if (res.code === 0) {
      studentOverview.active = res.data.active || 0
      studentOverview.course_distribution = res.data.course_distribution || []
    }
  } catch (e) { console.error('获取学员概况失败', e) }
  finally { loading.student = false }
}

function refreshStudentOverview() { fetchStudentOverview(); ElMessage.success('已刷新') }

// ===================================================================
// 5. 收入概况 - 玫瑰图配置
// ===================================================================

const incomeData = reactive({
  today_count: 0,
  today_amount: 0,
  month_course_dist: []
})

/**
 * ★ 收入概况玫瑰图配置
 * 使用暖色系渐变（橙色系）
 */
const incomePieOption = computed(() => {
  const rawData = incomeData.month_course_dist || []
  const data = rawData.length > 0 ? rawData : [{ name: '暂无数据', value: 1 }]

  // 暖色系渐变（橙色到红色）
  const colors = [
    { type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [
      { offset: 0, color: '#ffd2b3' }, { offset: 1, color: '#f5a623' }
    ]},
    { type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [
      { offset: 0, color: '#ffd2b3' }, { offset: 1, color: '#f7b731' }
    ]},
    { type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [
      { offset: 0, color: '#ffd2b3' }, { offset: 1, color: '#f9c83f' }
    ]},
    { type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [
      { offset: 0, color: '#ffd2b3' }, { offset: 1, color: '#fbd54d' }
    ]},
    { type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [
      { offset: 0, color: '#ffd2b3' }, { offset: 1, color: '#f5a623' }
    ]},
    { type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [
      { offset: 0, color: '#ffd2b3' }, { offset: 1, color: '#e8961e' }
    ]},
    { type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [
      { offset: 0, color: '#ffd2b3' }, { offset: 1, color: '#dc861a' }
    ]}
  ]

  return {
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        return `<strong>${params.name}</strong><br/>金额：¥${params.value.toFixed(0)}<br/>占比：${params.percent}%`
      }
    },
    legend: { show: false },
    series: [{
      type: 'pie',
      roseType: 'area',
      radius: ['10%', '75%'],
      center: ['50%', '50%'],
      itemStyle: { borderRadius: 6 },
      label: {
        show: true,
        position: 'center',
        fontSize: 10,
        fontWeight: 'bold',
        color: '#333',
        formatter: (params) => {
          if (params.value === 1 && params.name === '暂无数据') {
            return '暂无数据'
          }
          const name = params.name.length > 6 ? params.name.slice(0, 5) + '…' : params.name
          return `${name}\n¥${params.value.toFixed(0)}`
        },
        lineHeight: 14
      },
      labelLine: {
        show: true,
        lineStyle: { color: '#888', width: 1 },
        length: 12,
        length2: 20
      },
      emphasis: {
        label: { show: true, fontSize: 12, fontWeight: 'bold' },
        itemStyle: { shadowBlur: 12, shadowColor: 'rgba(0,0,0,0.2)' }
      },
      data: data.map((item, index) => ({
        name: item.name,
        value: item.value,
        itemStyle: { color: colors[index % colors.length] }
      }))
    }]
  }
})

async function fetchIncomeOverview() {
  loading.income = true
  try {
    const [todayRes, monthRes] = await Promise.all([
      request.get('/dashboard/income-overview', { params: { period: 'today' } }),
      request.get('/dashboard/income-overview', { params: { period: 'month' } })
    ])
    if (todayRes.code === 0) {
      incomeData.today_count = todayRes.data.new_order_count || 0
      incomeData.today_amount = todayRes.data.new_order_amount || 0
    }
    if (monthRes.code === 0) {
      incomeData.month_course_dist = monthRes.data.course_amount_distribution || []
    }
  } catch (e) { console.error('获取收入概况失败', e) }
  finally { loading.income = false }
}

// ===================================================================
// 6. 剩余课时 - 玫瑰图配置
// ===================================================================

const hoursData = reactive({
  remaining_hours: 0,
  remaining_amount: 0,
  hours_course_dist: []
})

/**
 * ★ 剩余课时玫瑰图配置
 * 使用冷色系渐变（蓝色/紫色系）
 */
const hoursPieOption = computed(() => {
  const rawData = hoursData.hours_course_dist || []
  const data = rawData.length > 0 ? rawData : [{ name: '暂无数据', value: 1 }]

  // 冷色系渐变（蓝色到紫色）
  const colors = [
    { type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [
      { offset: 0, color: '#c8d8ff' }, { offset: 1, color: '#6c8cff' }
    ]},
    { type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [
      { offset: 0, color: '#c8d8ff' }, { offset: 1, color: '#7a98ff' }
    ]},
    { type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [
      { offset: 0, color: '#c8d8ff' }, { offset: 1, color: '#88a4ff' }
    ]},
    { type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [
      { offset: 0, color: '#c8d8ff' }, { offset: 1, color: '#96b0ff' }
    ]},
    { type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [
      { offset: 0, color: '#c8d8ff' }, { offset: 1, color: '#6c8cff' }
    ]},
    { type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [
      { offset: 0, color: '#c8d8ff' }, { offset: 1, color: '#5c7cf0' }
    ]},
    { type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [
      { offset: 0, color: '#c8d8ff' }, { offset: 1, color: '#4c6ce0' }
    ]}
  ]

  return {
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        return `<strong>${params.name}</strong><br/>课时：${params.value} 课时<br/>占比：${params.percent}%`
      }
    },
    legend: { show: false },
    series: [{
      type: 'pie',
      roseType: 'area',
      radius: ['10%', '75%'],
      center: ['50%', '50%'],
      itemStyle: { borderRadius: 6 },
      label: {
        show: true,
        position: 'center',
        fontSize: 10,
        fontWeight: 'bold',
        color: '#333',
        formatter: (params) => {
          if (params.value === 1 && params.name === '暂无数据') {
            return '暂无数据'
          }
          const name = params.name.length > 6 ? params.name.slice(0, 5) + '…' : params.name
          return `${name}\n${params.value}课时`
        },
        lineHeight: 14
      },
      labelLine: {
        show: true,
        lineStyle: { color: '#888', width: 1 },
        length: 12,
        length2: 20
      },
      emphasis: {
        label: { show: true, fontSize: 12, fontWeight: 'bold' },
        itemStyle: { shadowBlur: 12, shadowColor: 'rgba(0,0,0,0.2)' }
      },
      data: data.map((item, index) => ({
        name: item.name,
        value: item.value,
        itemStyle: { color: colors[index % colors.length] }
      }))
    }]
  }
})

async function fetchHoursOverview() {
  loading.hours = true
  try {
    const res = await request.get('/dashboard/hours-overview')
    if (res.code === 0) {
      hoursData.remaining_hours = res.data.remaining_hours || 0
      hoursData.remaining_amount = res.data.remaining_amount || 0
      hoursData.hours_course_dist = res.data.hours_course_distribution || []
    }
  } catch (e) { console.error('获取剩余课时失败', e) }
  finally { loading.hours = false }
}

// ===================================================================
// 7. 课程表
// ===================================================================

const currentStartDate = ref(dayjs().startOf('week').add(1, 'day'))
const dateRange = computed(() => {
  const end = currentStartDate.value.add(13, 'day')
  return `${currentStartDate.value.format('M月D日')} - ${end.format('M月D日')}`
})
const calendarDays = ref([])

async function loadTwoWeeksCalendar() {
  const start = currentStartDate.value
  const days = []
  for (let i = 0; i < 14; i++) {
    const d = start.add(i, 'day')
    const dateStr = d.format('YYYY-MM-DD')
    let hasSchedule = false, allCompleted = true
    let scheduleInfo = []
    try {
      const res = await request.get('/attendance/classes', { params: { course_date: dateStr } })
      const sessions = res.data || []
      hasSchedule = sessions.length > 0
      allCompleted = sessions.every(s => s.status === 'completed')
      scheduleInfo = sessions.map(s => {
        let endTime = ''
        if (s.start_time && s.duration) {
          const startMinutes = parseInt(s.start_time.split(':')[0]) * 60 + parseInt(s.start_time.split(':')[1])
          const endMinutes = startMinutes + (s.duration || 60)
          const endHour = String(Math.floor(endMinutes / 60)).padStart(2, '0')
          const endMin = String(endMinutes % 60).padStart(2, '0')
          endTime = `${endHour}:${endMin}`
        }
        return {
          start_time: s.start_time || '',
          end_time: endTime,
          class_name: s.class_name || '',
          course_name: s.course_name || '',
          teacher_name: s.teacher_name || '',
          classroom_name: s.classroom_name || ''
        }
      })
    } catch (e) {}
    days.push({
      date: dateStr,
      dayName: ['一','二','三','四','五','六','日'][i % 7],
      dayOfMonth: d.date(),
      isToday: d.isSame(dayjs(), 'day'),
      hasSchedule,
      allCompleted,
      scheduleInfo
    })
  }
  calendarDays.value = days
}

function jumpToAttendance(date) {
  router.push(`/attendance?date=${date}`)
}
function prevTwoWeeks() {
  currentStartDate.value = currentStartDate.value.subtract(14, 'day')
  loadTwoWeeksCalendar()
}
function nextTwoWeeks() {
  currentStartDate.value = currentStartDate.value.add(14, 'day')
  loadTwoWeeksCalendar()
}
function goToday() {
  currentStartDate.value = dayjs().startOf('week').add(1, 'day')
  loadTwoWeeksCalendar()
}

// ===================================================================
// 8. 活动轮播
// ===================================================================

const activityList = ref([])

async function loadActivities() {
  try {
    const res = await request.get('/activity/activities')
    if (res.code === 0) {
      const allActivities = res.data?.items || res.data || []
      const withImages = allActivities.filter(a => a.banner_image || a.cover_image)
      activityList.value = withImages.length > 0 ? withImages.slice(0, 5) : allActivities.slice(0, 5)
    }
  } catch (e) {
    console.error('加载活动失败', e)
  }
}

// ===================================================================
// 9. 生日提醒
// ===================================================================

const birthdayStudents = ref([])

async function loadBirthdayData() {
  const year = dayjs().year()
  const month = dayjs().month() + 1
  try {
    const res = await request.get('/students/birthdays', { params: { year, month } })
    if (res.code === 0) {
      const data = res.data || {}
      const students = []
      Object.entries(data).forEach(([dateStr, dayStudents]) => {
        if (Array.isArray(dayStudents)) {
          dayStudents.forEach(s => {
            students.push({
              id: s.id,
              name: s.name,
              avatar: s.avatar || '',
              birthday: dateStr
            })
          })
        }
      })
      birthdayStudents.value = students
    }
  } catch (e) {
    console.error('加载生日数据失败', e)
    birthdayStudents.value = []
  }
}

async function refreshBirthdayData() {
  await loadBirthdayData()
  ElMessage.success('已刷新')
}

// ===================================================================
// 10. 待办提醒
// ===================================================================

const todoList = ref([])

async function loadTodos() {
  const todos = []
  try {
    const statsRes = await request.get('/dashboard/statistics')
    if (statsRes.code === 0) {
      const arrears = statsRes.data.arrears?.totalArrears || 0
      const arrearsCount = statsRes.data.arrears?.arrearsCount || 0
      if (arrearsCount > 0) {
        todos.push({
          title: '尾款欠费提醒',
          description: `${arrearsCount} 位学员欠费，总额 ¥${arrears.toFixed(0)}`,
          type: 'warning',
          action: { text: '查看', handler: () => router.push('/orders') }
        })
      }
    }
  } catch (e) {}
  try {
    const today = dayjs().format('YYYY-MM-DD')
    const classRes = await request.get('/attendance/classes', { params: { course_date: today } })
    const pendingCount = (classRes.data || []).filter(s => s.status !== 'completed').length
    if (pendingCount > 0) {
      todos.push({
        title: '今日待考勤',
        description: `今日有 ${pendingCount} 节课次待考勤`,
        type: 'primary',
        action: { text: '去考勤', handler: () => router.push('/attendance') }
      })
    }
  } catch (e) {}
  todoList.value = todos.length > 0
    ? todos
    : [{ title: '暂无待办', description: '所有工作已处理完毕', type: 'success' }]
}

async function refreshTodos() {
  await loadTodos()
  ElMessage.success('已刷新')
}

// ===================================================================
// 11. 生命周期
// ===================================================================

onMounted(async () => {
  userStore.loadFromStorage()
  await Promise.all([
    fetchStudentOverview(),
    fetchIncomeOverview(),
    fetchHoursOverview(),
    loadTwoWeeksCalendar(),
    loadActivities(),
    loadTodos(),
    loadBirthdayData()
  ])
})

</script>

<style scoped>
.dashboard-container {
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.dashboard-main {
  display: grid;
  grid-template-columns: minmax(0, 7fr) minmax(320px, 3fr);
  gap: var(--space-4);
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.left-column,
.right-column {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  min-height: 0;
  overflow: hidden;
}

.profile-card,
.quick-entry-card,
.data-card,
.schedule-card,
.banner-card,
.birthday-card,
.todo-card {
  background: var(--surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xs);
}

.profile-card {
  flex-shrink: 0;
  padding: 18px 20px;
  background:
    radial-gradient(circle at top right, rgba(54, 180, 89, 0.14), transparent 180px),
    var(--surface);
}

.profile-content {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  color: var(--text-primary);
  font-size: 17px;
  font-weight: 800;
}

.user-role,
.welcome-text {
  color: var(--text-secondary);
  font-size: 13px;
}

.welcome-text {
  margin-top: 2px;
}

.quick-entry-card {
  flex-shrink: 0;
  padding: 14px 16px;
}

.entry-row {
  display: grid;
  grid-template-columns: repeat(9, minmax(54px, 1fr));
  gap: var(--space-2);
}

.entry-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 7px;
  min-width: 0;
  padding: 10px 8px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background 0.18s, transform 0.18s;
}

.entry-item:hover {
  background: var(--brand-50);
  transform: translateY(-2px);
}

.entry-icon {
  width: 42px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 15px;
  color: var(--surface);
  box-shadow: 0 10px 20px rgba(18, 32, 24, 0.12);
  transition: transform 0.18s;
}

.entry-item:hover .entry-icon {
  transform: scale(1.05);
}

.entry-name {
  max-width: 100%;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 700;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.data-cards-row {
  flex-shrink: 0;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-4);
  min-height: 0;
}

.data-card {
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  min-height: 160px;
  overflow: hidden;
}

.card-header,
.schedule-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
  margin-bottom: var(--space-3);
}

.card-title,
.schedule-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 800;
}

.card-title::before,
.schedule-title::before {
  content: "";
  width: 4px;
  height: 14px;
  border-radius: var(--radius-pill);
  background: var(--brand-500);
}

.card-body {
  flex: 1;
  display: flex;
  gap: var(--space-3);
  min-height: 0;
}

.card-left {
  flex: 0 0 42%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: var(--space-2);
  min-width: 0;
}

.card-right {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.data-item {
  display: flex;
  align-items: baseline;
  gap: var(--space-1);
  flex-wrap: wrap;
}

.data-label,
.data-unit {
  color: var(--text-secondary);
  font-size: 12px;
}

.data-value {
  color: var(--text-primary);
  font-size: 20px;
  font-weight: 900;
  letter-spacing: -0.02em;
}

.data-value.text-primary,
.text-primary {
  color: var(--brand-600);
}

.schedule-card {
  flex-shrink: 0;
  padding: 14px 16px 16px;
}

.schedule-control {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: 2px 0 var(--space-2);
}

.schedule-control .date-range {
  min-width: 120px;
  color: var(--text-regular);
  font-size: 14px;
  font-weight: 700;
  text-align: center;
}

.schedule-control .el-button {
  min-width: auto;
  height: 28px;
  padding: 0 8px;
}

.schedule-days {
  display: grid;
  grid-template-columns: repeat(14, minmax(34px, 1fr));
  gap: var(--space-2);
  padding-top: var(--space-1);
}

.schedule-day {
  aspect-ratio: 1 / 1;
  min-width: 32px;
  min-height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-pill);
  cursor: pointer;
  text-align: center;
  background: var(--surface-soft);
  border: 1px solid var(--border-light);
  transition: background 0.2s, color 0.2s, transform 0.2s, box-shadow 0.2s;
}

.schedule-day-content {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.schedule-day:hover,
.schedule-day.is-today {
  color: var(--surface);
  background: linear-gradient(135deg, var(--brand-500), var(--brand-700));
  border-color: transparent;
  box-shadow: 0 12px 24px rgba(54, 180, 89, 0.26);
}

.schedule-day:hover {
  transform: translateY(-3px) scale(1.03);
}

.schedule-day:hover .day-week,
.schedule-day:hover .day-date,
.schedule-day.is-today .day-week,
.schedule-day.is-today .day-date {
  color: var(--surface);
}

.day-week {
  color: var(--text-secondary);
  font-size: 10px;
  line-height: 1.2;
}

.day-date {
  color: var(--text-primary);
  font-size: 16px;
  font-weight: 800;
  line-height: 1.2;
}

.day-dot {
  display: flex;
  justify-content: center;
  margin-top: 1px;
}

.dot-green,
.dot-gray {
  width: 6px;
  height: 6px;
  display: block;
  border-radius: var(--radius-pill);
}

.dot-green { background: var(--brand-500); }
.dot-gray { background: var(--gray-300); }

.tooltip-schedule-list {
  max-width: 320px;
  padding: 4px 0;
}

.tooltip-schedule-item {
  padding: 6px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.15);
}

.tooltip-schedule-item:last-child {
  border-bottom: none;
}

.tooltip-time,
.tooltip-course-class,
.tooltip-name {
  color: var(--surface);
  font-weight: 700;
}

.tooltip-time { font-size: 14px; margin-bottom: 2px; }
.tooltip-course-class { font-size: 13px; margin-bottom: 2px; }
.tooltip-teacher-classroom,
.tooltip-birthday { color: rgba(255, 255, 255, 0.82); font-size: 12px; }

.banner-card,
.birthday-card,
.todo-card {
  padding: 14px 16px;
}

.banner-card {
  flex-shrink: 0;
}

.banner-card .el-carousel__container {
  height: 140px;
}

.carousel-item {
  width: 100%;
  height: 100%;
  overflow: hidden;
  border-radius: var(--radius-md);
  cursor: pointer;
}

.carousel-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.carousel-content,
.carousel-item.empty {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--surface);
  text-align: center;
  background: linear-gradient(135deg, var(--brand-500), var(--brand-700));
}

.activity-name {
  font-size: 15px;
  font-weight: 800;
}

.activity-date {
  font-size: 12px;
  opacity: 0.82;
}

.birthday-card {
  flex-shrink: 0;
}

.birthday-count {
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 700;
}

.birthday-list {
  display: flex;
  flex-wrap: nowrap;
  gap: var(--space-3);
  overflow-x: auto;
  padding: 4px 0 8px;
}

.birthday-item {
  width: 50px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
}

.birthday-avatar {
  border: 2px solid var(--danger);
  cursor: pointer;
  transition: transform 0.18s;
}

.birthday-avatar:hover {
  transform: scale(1.08);
}

.birthday-name {
  max-width: 50px;
  overflow: hidden;
  color: var(--text-secondary);
  font-size: 11px;
  text-align: center;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.birthday-empty,
.empty-tip {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-placeholder);
  font-size: 14px;
}

.birthday-empty {
  padding: 12px 0;
}

.birthday-tooltip {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 4px;
}

.tooltip-birthday {
  padding: 2px 10px;
  border-radius: var(--radius-pill);
  background: rgba(255, 255, 255, 0.15);
}

.todo-card {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.todo-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.todo-item {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  background: var(--surface-soft);
}

.todo-dot {
  width: 6px;
  height: 6px;
  flex-shrink: 0;
  margin-top: 7px;
  border-radius: var(--radius-pill);
}

.todo-dot.warning { background: var(--warning); }
.todo-dot.primary { background: var(--brand-500); }
.todo-dot.info { background: var(--info); }
.todo-dot.success { background: var(--success); }

.todo-content {
  flex: 1;
  min-width: 0;
}

.todo-title {
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 700;
}

.todo-desc {
  color: var(--text-secondary);
  font-size: 12px;
}

.empty-tip {
  flex: 1;
}

.text-danger { color: var(--danger); }
.text-warning { color: var(--warning); }
.text-success { color: var(--success); }

@media (max-width: 1280px) {
  .dashboard-main {
    grid-template-columns: 1fr;
    overflow: auto;
  }
  .right-column {
    min-height: 420px;
  }
}

@media (max-width: 960px) {
  .entry-row {
    grid-template-columns: repeat(5, minmax(54px, 1fr));
  }
  .data-cards-row {
    grid-template-columns: 1fr;
  }
  .schedule-days {
    grid-template-columns: repeat(7, minmax(34px, 1fr));
  }
}
</style>
