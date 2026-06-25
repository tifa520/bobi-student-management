<template>
  <div class="dashboard-container">
    <el-row :gutter="16" class="dashboard-row">
      <!-- 左侧主内容 -->
      <el-col :xl="17" :lg="16" :md="24">
        <!-- 欢迎横幅 -->
        <div class="welcome-banner">
          <div class="welcome-bg-deco">
            <div class="deco-circle deco-1"></div>
            <div class="deco-circle deco-2"></div>
            <div class="deco-circle deco-3"></div>
          </div>
          <div class="welcome-content">
            <div class="welcome-left">
              <div class="welcome-greeting">
                <span class="greeting-icon">🌿</span>
                <span class="greeting-text">{{ greetingText }}，{{ userName }}</span>
              </div>
              <h2 class="welcome-title">今日也是充满艺术灵感的一天</h2>
              <p class="welcome-desc">{{ todayDate }} · {{ weekdayText }} · 愿你的教学充满创意</p>
            </div>
            <div class="welcome-right">
              <div class="welcome-actions">
                <div class="quick-stat">
                  <span class="stat-number">{{ activeStudents }}</span>
                  <span class="stat-label">在学学员</span>
                </div>
                <div class="stat-divider"></div>
                <div class="quick-stat">
                  <span class="stat-number gold">{{ todayIncome }}</span>
                  <span class="stat-label">今日收入</span>
                </div>
                <div class="stat-divider"></div>
                <div class="quick-stat">
                  <span class="stat-number blue">{{ todayClasses }}</span>
                  <span class="stat-label">今日课程</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 数据卡片组 -->
        <div class="data-cards">
          <div
            v-for="(card, index) in statCards"
            :key="index"
            class="stat-card"
            :class="card.theme"
            @click="card.action && card.action()"
          >
            <div class="stat-card-icon">
              <el-icon :size="24"><component :is="card.icon" /></el-icon>
            </div>
            <div class="stat-card-info">
              <div class="stat-card-value">
                <span class="value-num">{{ card.value }}</span>
                <span v-if="card.unit" class="value-unit">{{ card.unit }}</span>
              </div>
              <div class="stat-card-label">{{ card.label }}</div>
            </div>
            <div class="stat-card-trend" v-if="card.trend !== undefined">
              <span :class="card.trend >= 0 ? 'trend-up' : 'trend-down'">
                <el-icon><CaretTop v-if="card.trend >= 0" /><CaretBottom v-else /></el-icon>
                {{ Math.abs(card.trend) }}%
              </span>
            </div>
            <div class="stat-card-bg-icon">
              <el-icon :size="80"><component :is="card.icon" /></el-icon>
            </div>
          </div>
        </div>

        <!-- 快捷入口 -->
        <div class="panel-card">
          <div class="panel-header">
            <div class="panel-title">
              <span class="title-bar"></span>
              <span>快捷入口</span>
            </div>
          </div>
          <div class="quick-entries">
            <div
              v-for="item in quickEntries"
              :key="item.path"
              class="entry-item"
              @click="goToPage(item.path)"
            >
              <div class="entry-icon" :style="{ background: item.gradient }">
                <el-icon :size="22"><component :is="item.icon" /></el-icon>
              </div>
              <span class="entry-name">{{ item.name }}</span>
            </div>
          </div>
        </div>

        <!-- 课程表 -->
        <div class="panel-card">
          <div class="panel-header">
            <div class="panel-title">
              <span class="title-bar"></span>
              <span>课程表</span>
              <span class="title-badge">两周</span>
            </div>
            <div class="panel-actions">
              <el-button-group size="small">
                <el-button @click="prevTwoWeeks" :icon="ArrowLeft" />
                <el-button @click="goToday">今天</el-button>
                <el-button @click="nextTwoWeeks" :icon="ArrowRight" />
              </el-button-group>
            </div>
          </div>
          <div class="schedule-days">
            <div
              v-for="day in calendarDays"
              :key="day.date"
              class="schedule-day"
              :class="{
                'is-today': day.isToday,
                'has-schedule': day.hasSchedule,
                'is-weekend': day.isWeekend
              }"
              @click="jumpToAttendance(day.date)"
            >
              <div class="day-header">
                <span class="day-week">{{ day.dayName }}</span>
                <span class="day-date">{{ day.dayOfMonth }}</span>
              </div>
              <div class="day-indicator" v-if="day.hasSchedule">
                <span v-if="day.allCompleted" class="indicator-dot done" title="全部完成"></span>
                <span v-else class="indicator-dot pending" title="进行中"></span>
              </div>
              <el-tooltip
                v-if="day.hasSchedule && day.scheduleInfo && day.scheduleInfo.length"
                placement="top"
                :open-delay="200"
              >
                <template #content>
                  <div class="tooltip-schedule">
                    <div
                      v-for="(session, idx) in day.scheduleInfo"
                      :key="idx"
                      class="tooltip-item"
                    >
                      <div class="tooltip-time">{{ session.start_time }}~{{ session.end_time }}</div>
                      <div class="tooltip-course">{{ session.course_name }}</div>
                      <div class="tooltip-meta">{{ session.class_name }} · {{ session.teacher_name }}</div>
                    </div>
                  </div>
                </template>
                <div class="day-hover-hint">
                  <el-icon><View /></el-icon>
                </div>
              </el-tooltip>
            </div>
          </div>
        </div>

        <!-- 数据分布图表 -->
        <el-row :gutter="16" class="charts-row">
          <el-col :lg="12" :md="24">
            <div class="panel-card chart-card">
              <div class="panel-header">
                <div class="panel-title">
                  <span class="title-bar"></span>
                  <span>学员分布</span>
                </div>
              </div>
              <div class="chart-container" v-loading="loading.student">
                <BaseChart :options="studentPieOption" height="240px" />
              </div>
            </div>
          </el-col>
          <el-col :lg="12" :md="24">
            <div class="panel-card chart-card">
              <div class="panel-header">
                <div class="panel-title">
                  <span class="title-bar"></span>
                  <span>收入分布</span>
                </div>
              </div>
              <div class="chart-container" v-loading="loading.income">
                <BaseChart :options="incomePieOption" height="240px" />
              </div>
            </div>
          </el-col>
        </el-row>
      </el-col>

      <!-- 右侧边栏 -->
      <el-col :xl="7" :lg="8" :md="24">
        <!-- 本月生日 -->
        <div class="panel-card sidebar-card">
          <div class="panel-header">
            <div class="panel-title">
              <span class="title-bar birthday"></span>
              <span>本月生日</span>
              <el-badge v-if="birthdayStudents.length" :value="birthdayStudents.length" class="title-badge-num" />
            </div>
            <el-button type="primary" link size="small" @click="refreshBirthdayData">
              <el-icon><Refresh /></el-icon>
            </el-button>
          </div>
          <div v-if="birthdayStudents.length" class="birthday-list">
            <div
              v-for="student in birthdayStudents.slice(0, 6)"
              :key="student.id"
              class="birthday-item"
            >
              <div class="birthday-avatar">
                <span>{{ student.name.charAt(0) }}</span>
              </div>
              <div class="birthday-info">
                <span class="birthday-name">{{ student.name }}</span>
                <span class="birthday-date">🎂 {{ student.birthday }}</span>
              </div>
            </div>
          </div>
          <div v-else class="empty-state">
            <span class="empty-icon">🎂</span>
            <span class="empty-text">本月暂无生日</span>
          </div>
        </div>

        <!-- 待办提醒 -->
        <div class="panel-card sidebar-card">
          <div class="panel-header">
            <div class="panel-title">
              <span class="title-bar"></span>
              <span>待办提醒</span>
            </div>
            <el-button type="primary" link size="small" @click="refreshTodos">
              <el-icon><Refresh /></el-icon>
            </el-button>
          </div>
          <div class="todo-list">
            <div v-for="(todo, idx) in todoList" :key="idx" class="todo-item">
              <div class="todo-icon" :class="todo.type">
                <el-icon :size="16">
                  <component :is="todo.icon || 'Bell'" />
                </el-icon>
              </div>
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
            <div v-if="todoList.length === 0" class="empty-state">
              <span class="empty-icon">✅</span>
              <span class="empty-text">暂无待办</span>
            </div>
          </div>
        </div>

        <!-- 近期活动 -->
        <div class="panel-card sidebar-card">
          <div class="panel-header">
            <div class="panel-title">
              <span class="title-bar gold"></span>
              <span>近期活动</span>
            </div>
            <el-button type="primary" link size="small" @click="goToActivities">更多</el-button>
          </div>
          <div v-if="activityList.length" class="activity-list">
            <div
              v-for="activity in activityList.slice(0, 3)"
              :key="activity.id"
              class="activity-item"
              @click="goToActivityDetail(activity.id)"
            >
              <div
                class="activity-cover"
                :style="activity.cover_image ? { backgroundImage: `url(${activity.cover_image})` } : {}"
              >
                <span v-if="!activity.cover_image" class="cover-placeholder">🎨</span>
              </div>
              <div class="activity-info">
                <div class="activity-name">{{ activity.name }}</div>
                <div class="activity-date">
                  <el-icon><Calendar /></el-icon>
                  {{ activity.start_date ? activity.start_date.split(' ')[0] : '待定' }}
                </div>
              </div>
            </div>
          </div>
          <div v-else class="empty-state">
            <span class="empty-icon">🎪</span>
            <span class="empty-text">暂无活动</span>
          </div>
        </div>
      </el-col>
    </el-row>
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
  ArrowLeft, ArrowRight, Refresh, CaretTop, CaretBottom,
  Bell, Calendar, View, UserFilled, Coin, Clock, DataLine
} from '@element-plus/icons-vue'
import request from '@/api/request'
import dayjs from 'dayjs'
import BaseChart from '@/components/BaseChart.vue'

const router = useRouter()
const userStore = useUserStore()
const { user } = storeToRefs(userStore)

const userName = computed(() => user.value.name || '管理员')

const greetingText = computed(() => {
  const hour = dayjs().hour()
  if (hour < 6) return '夜深了'
  if (hour < 12) return '早上好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

const todayDate = computed(() => dayjs().format('YYYY年M月D日'))
const weekdayText = computed(() => {
  const days = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
  return days[dayjs().day()]
})

const quickEntries = [
  { name: '学员报名', path: '/enroll', icon: 'User', gradient: 'linear-gradient(135deg, #3fc06a, #16a34a)' },
  { name: '学员考勤', path: '/attendance', icon: 'Clock', gradient: 'linear-gradient(135deg, #e5ad2e, #d4941a)' },
  { name: '积分管理', path: '/scores', icon: 'Tickets', gradient: 'linear-gradient(135deg, #f87171, #ef4444)' },
  { name: '班级管理', path: '/classes', icon: 'School', gradient: 'linear-gradient(135deg, #60a5fa, #3b82f6)' },
  { name: '课程管理', path: '/courses', icon: 'Goods', gradient: 'linear-gradient(135deg, #4ade80, #22c55e)' },
  { name: '活动管理', path: '/activities', icon: 'Picture', gradient: 'linear-gradient(135deg, #a78bfa, #8b5cf6)' },
  { name: '物品管理', path: '/items-manage', icon: 'Box', gradient: 'linear-gradient(135deg, #fb923c, #f97316)' },
  { name: '销售兑换', path: '/item-sale-exchange', icon: 'Money', gradient: 'linear-gradient(135deg, #f472b6, #ec4899)' }
]

function goToPage(path) {
  router.push(path)
}

function goToActivities() {
  router.push('/activities')
}

function goToActivityDetail(id) {
  router.push(`/activities/detail?id=${id}`)
}

const loading = reactive({
  student: true,
  income: true,
  hours: true
})

const activeStudents = ref(0)
const todayIncome = ref(0)
const todayClasses = ref(0)

const statCards = computed(() => [
  {
    label: '在学学员',
    value: studentOverview.active,
    unit: '人',
    icon: 'UserFilled',
    theme: 'green',
    trend: 12,
    action: () => router.push('/students')
  },
  {
    label: '今日报名收入',
    value: '¥' + incomeData.today_amount.toFixed(0),
    icon: 'Coin',
    theme: 'gold',
    trend: 8,
    action: () => router.push('/orders')
  },
  {
    label: '剩余总课时',
    value: hoursData.remaining_hours,
    unit: '课时',
    icon: 'DataLine',
    theme: 'blue',
    action: () => router.push('/course-records')
  },
  {
    label: '今日课次',
    value: todayClasses.value,
    unit: '节',
    icon: 'Timer',
    theme: 'purple',
    action: () => router.push('/attendance')
  }
])

const studentOverview = reactive({
  active: 0,
  course_distribution: []
})

const studentPieOption = computed(() => {
  const rawData = studentOverview.course_distribution || []
  const data = rawData.length > 0 ? rawData : [{ name: '暂无数据', value: 1 }]

  const colors = [
    { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [
      { offset: 0, color: '#3fc06a' }, { offset: 1, color: '#16a34a' }
    ]},
    { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [
      { offset: 0, color: '#60a5fa' }, { offset: 1, color: '#3b82f6' }
    ]},
    { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [
      { offset: 0, color: '#fbbf24' }, { offset: 1, color: '#f59e0b' }
    ]},
    { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [
      { offset: 0, color: '#f87171' }, { offset: 1, color: '#ef4444' }
    ]},
    { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [
      { offset: 0, color: '#a78bfa' }, { offset: 1, color: '#8b5cf6' }
    ]},
    { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [
      { offset: 0, color: '#2dd4bf' }, { offset: 1, color: '#14b8a6' }
    ]}
  ]

  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(15, 38, 25, 0.92)',
      borderWidth: 0,
      padding: [10, 14],
      textStyle: { color: '#fff', fontSize: 12 },
      formatter: (params) => {
        return `<div style="font-weight:600;margin-bottom:4px">${params.name}</div>
                <div>人数：${params.value} 人</div>
                <div>占比：${params.percent}%</div>`
      }
    },
    legend: {
      type: 'scroll',
      orient: 'vertical',
      right: 10,
      top: 'center',
      itemWidth: 10,
      itemHeight: 10,
      itemGap: 10,
      textStyle: { color: '#52665a', fontSize: 12 },
      formatter: (name) => {
        const item = data.find(d => d.name === name)
        return item ? `${name}  ${item.value}人` : name
      }
    },
    series: [{
      type: 'pie',
      roseType: 'radius',
      radius: ['35%', '75%'],
      center: ['35%', '50%'],
      itemStyle: {
        borderRadius: 6,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: { show: false },
      labelLine: { show: false },
      emphasis: {
        itemStyle: {
          shadowBlur: 12,
          shadowColor: 'rgba(30, 168, 82, 0.3)'
        }
      },
      data: data.map((item, index) => ({
        name: item.name,
        value: item.value,
        itemStyle: { color: colors[index % colors.length] }
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
      activeStudents.value = res.data.active || 0
    }
  } catch (e) { console.error('获取学员概况失败', e) }
  finally { loading.student = false }
}

const incomeData = reactive({
  today_count: 0,
  today_amount: 0,
  month_course_dist: []
})

const incomePieOption = computed(() => {
  const rawData = incomeData.month_course_dist || []
  const data = rawData.length > 0 ? rawData : [{ name: '暂无数据', value: 1 }]

  const colors = [
    { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [
      { offset: 0, color: '#fbbf24' }, { offset: 1, color: '#f59e0b' }
    ]},
    { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [
      { offset: 0, color: '#f87171' }, { offset: 1, color: '#ef4444' }
    ]},
    { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [
      { offset: 0, color: '#fb923c' }, { offset: 1, color: '#f97316' }
    ]},
    { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [
      { offset: 0, color: '#a78bfa' }, { offset: 1, color: '#8b5cf6' }
    ]},
    { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [
      { offset: 0, color: '#34d399' }, { offset: 1, color: '#10b981' }
    ]},
    { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [
      { offset: 0, color: '#60a5fa' }, { offset: 1, color: '#3b82f6' }
    ]}
  ]

  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(15, 38, 25, 0.92)',
      borderWidth: 0,
      padding: [10, 14],
      textStyle: { color: '#fff', fontSize: 12 },
      formatter: (params) => {
        return `<div style="font-weight:600;margin-bottom:4px">${params.name}</div>
                <div>金额：¥${params.value.toFixed(0)}</div>
                <div>占比：${params.percent}%</div>`
      }
    },
    legend: {
      type: 'scroll',
      orient: 'vertical',
      right: 10,
      top: 'center',
      itemWidth: 10,
      itemHeight: 10,
      itemGap: 10,
      textStyle: { color: '#52665a', fontSize: 12 },
      formatter: (name) => {
        const item = data.find(d => d.name === name)
        return item ? `${name}  ¥${item.value.toFixed(0)}` : name
      }
    },
    series: [{
      type: 'pie',
      roseType: 'radius',
      radius: ['35%', '75%'],
      center: ['35%', '50%'],
      itemStyle: {
        borderRadius: 6,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: { show: false },
      labelLine: { show: false },
      emphasis: {
        itemStyle: {
          shadowBlur: 12,
          shadowColor: 'rgba(245, 158, 11, 0.3)'
        }
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
      todayIncome.value = '¥' + (todayRes.data.new_order_amount || 0).toFixed(0)
    }
    if (monthRes.code === 0) {
      incomeData.month_course_dist = monthRes.data.course_amount_distribution || []
    }
  } catch (e) { console.error('获取收入概况失败', e) }
  finally { loading.income = false }
}

const hoursData = reactive({
  remaining_hours: 0,
  remaining_amount: 0,
  hours_course_dist: []
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

const currentStartDate = ref(dayjs().startOf('week').add(1, 'day'))
const calendarDays = ref([])

async function loadTwoWeeksCalendar() {
  const start = currentStartDate.value
  const days = []
  const today = dayjs().format('YYYY-MM-DD')

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
      if (dateStr === today) {
        todayClasses.value = sessions.length
      }
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
    const dayOfWeek = d.day()
    days.push({
      date: dateStr,
      dayName: ['日','一','二','三','四','五','六'][dayOfWeek],
      dayOfMonth: d.date(),
      isToday: d.isSame(dayjs(), 'day'),
      isWeekend: dayOfWeek === 0 || dayOfWeek === 6,
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

const activityList = ref([])

async function loadActivities() {
  try {
    const res = await request.get('/activity/activities')
    if (res.code === 0) {
      const allActivities = res.data?.items || res.data || []
      activityList.value = allActivities.slice(0, 5)
    }
  } catch (e) {
    console.error('加载活动失败', e)
  }
}

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
          icon: 'Warning',
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
        icon: 'Clock',
        action: { text: '去考勤', handler: () => router.push('/attendance') }
      })
    }
  } catch (e) {}
  todoList.value = todos
}

async function refreshTodos() {
  await loadTodos()
  ElMessage.success('已刷新')
}

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
  padding: 20px;
  min-height: 100%;
  overflow-y: auto;
  background:
    radial-gradient(ellipse at top left, rgba(30, 168, 82, 0.04), transparent 400px),
    radial-gradient(ellipse at top right, rgba(212, 148, 26, 0.04), transparent 400px),
    var(--bg-page);
}

.dashboard-row {
  margin: 0 !important;
}

.welcome-banner {
  position: relative;
  padding: 28px 32px;
  border-radius: 20px;
  background:
    linear-gradient(135deg,
      rgba(30, 168, 82, 0.95) 0%,
      rgba(22, 163, 74, 0.95) 50%,
      rgba(21, 128, 61, 0.98) 100%);
  overflow: hidden;
  margin-bottom: 16px;
  box-shadow: 0 8px 32px rgba(22, 163, 74, 0.25);
}

.welcome-bg-deco {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.deco-circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
}

.deco-1 {
  width: 200px;
  height: 200px;
  top: -60px;
  right: 100px;
}

.deco-2 {
  width: 140px;
  height: 140px;
  bottom: -40px;
  right: 280px;
  background: rgba(255, 255, 255, 0.05);
}

.deco-3 {
  width: 80px;
  height: 80px;
  top: 50%;
  right: 40px;
  transform: translateY(-50%);
  background: rgba(229, 173, 46, 0.3);
}

.welcome-content {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

.welcome-left {
  flex: 1;
  min-width: 0;
}

.welcome-greeting {
  display: flex;
  align-items: center;
  gap: 8px;
  color: rgba(255, 255, 255, 0.9);
  font-size: 14px;
  margin-bottom: 8px;
}

.greeting-icon {
  font-size: 20px;
}

.greeting-text {
  font-weight: 500;
}

.welcome-title {
  font-size: 24px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 8px 0;
  font-family: var(--font-display);
  letter-spacing: -0.01em;
}

.welcome-desc {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.75);
  margin: 0;
}

.welcome-right {
  flex-shrink: 0;
}

.welcome-actions {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 16px 28px;
  background: rgba(255, 255, 255, 0.12);
  border-radius: 16px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.18);
}

.quick-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-width: 70px;
}

.stat-number {
  font-size: 24px;
  font-weight: 800;
  color: #fff;
  line-height: 1;
  font-family: var(--font-display);
}

.stat-number.gold {
  color: #fbbf24;
}

.stat-number.blue {
  color: #93c5fd;
}

.stat-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
}

.stat-divider {
  width: 1px;
  height: 36px;
  background: rgba(255, 255, 255, 0.2);
}

.data-cards {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.stat-card {
  position: relative;
  padding: 20px;
  border-radius: 16px;
  background: var(--surface);
  border: 1px solid var(--border-light);
  cursor: pointer;
  overflow: hidden;
  transition: all 0.3s var(--ease-soft);
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
  border-color: var(--border-color);
}

.stat-card-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  margin-bottom: 14px;
  color: #fff;
}

.stat-card.green .stat-card-icon {
  background: linear-gradient(135deg, #3fc06a, #16a34a);
  box-shadow: 0 8px 20px rgba(22, 163, 74, 0.3);
}

.stat-card.gold .stat-card-icon {
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  box-shadow: 0 8px 20px rgba(245, 158, 11, 0.3);
}

.stat-card.blue .stat-card-icon {
  background: linear-gradient(135deg, #60a5fa, #3b82f6);
  box-shadow: 0 8px 20px rgba(59, 130, 246, 0.3);
}

.stat-card.purple .stat-card-icon {
  background: linear-gradient(135deg, #a78bfa, #8b5cf6);
  box-shadow: 0 8px 20px rgba(139, 92, 246, 0.3);
}

.stat-card-info {
  margin-bottom: 8px;
}

.stat-card-value {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 4px;
}

.value-num {
  font-size: 26px;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1.2;
  font-family: var(--font-display);
  letter-spacing: -0.02em;
}

.value-unit {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}

.stat-card-label {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}

.stat-card-trend {
  font-size: 12px;
  font-weight: 600;
}

.trend-up {
  color: var(--success-color);
  display: flex;
  align-items: center;
  gap: 2px;
}

.trend-down {
  color: var(--danger-color);
  display: flex;
  align-items: center;
  gap: 2px;
}

.stat-card-bg-icon {
  position: absolute;
  right: -12px;
  bottom: -12px;
  color: var(--text-placeholder);
  opacity: 0.06;
  pointer-events: none;
}

.panel-card {
  background: var(--surface);
  border: 1px solid var(--border-light);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 16px;
  transition: box-shadow 0.3s;
}

.panel-card:hover {
  box-shadow: var(--shadow-sm);
}

.sidebar-card {
  margin-bottom: 16px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
}

.title-bar {
  width: 4px;
  height: 16px;
  border-radius: var(--radius-pill);
  background: linear-gradient(180deg, var(--brand-400), var(--brand-600));
}

.title-bar.birthday {
  background: linear-gradient(180deg, #f87171, #ef4444);
}

.title-bar.gold {
  background: linear-gradient(180deg, #fbbf24, #f59e0b);
}

.title-badge {
  font-size: 11px;
  font-weight: 500;
  color: var(--text-placeholder);
  background: var(--surface-soft);
  padding: 2px 8px;
  border-radius: var(--radius-pill);
}

.title-badge-num {
  margin-left: 4px;
}

.quick-entries {
  display: grid;
  grid-template-columns: repeat(8, minmax(0, 1fr));
  gap: 12px;
}

.entry-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 14px 8px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.25s var(--ease-soft);
}

.entry-item:hover {
  background: var(--surface-soft);
  transform: translateY(-2px);
}

.entry-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  color: #fff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  transition: transform 0.25s;
}

.entry-item:hover .entry-icon {
  transform: scale(1.08);
}

.entry-name {
  font-size: 12.5px;
  color: var(--text-secondary);
  font-weight: 500;
  white-space: nowrap;
}

.schedule-days {
  display: grid;
  grid-template-columns: repeat(14, minmax(0, 1fr));
  gap: 6px;
}

.schedule-day {
  aspect-ratio: 3 / 4;
  min-height: 60px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: var(--surface-soft);
  border: 1px solid var(--border-light);
  cursor: pointer;
  transition: all 0.25s var(--ease-soft);
  position: relative;
  gap: 4px;
}

.schedule-day:hover {
  background: var(--surface);
  border-color: var(--brand-300);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.06);
}

.schedule-day.is-today {
  background: linear-gradient(135deg, rgba(30, 168, 82, 0.1), rgba(30, 168, 82, 0.04));
  border-color: var(--brand-400);
  box-shadow: 0 4px 12px rgba(22, 163, 74, 0.15);
}

.schedule-day.is-today .day-week,
.schedule-day.is-today .day-date {
  color: var(--brand-700);
}

.schedule-day.is-weekend .day-week {
  color: var(--danger-color);
}

.day-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.day-week {
  font-size: 11px;
  color: var(--text-placeholder);
  font-weight: 500;
}

.day-date {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
}

.day-indicator {
  position: absolute;
  bottom: 6px;
}

.indicator-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  display: block;
}

.indicator-dot.pending {
  background: var(--brand-500);
  box-shadow: 0 0 0 2px rgba(22, 163, 74, 0.15);
}

.indicator-dot.done {
  background: var(--gray-400);
}

.day-hover-hint {
  position: absolute;
  top: 4px;
  right: 4px;
  font-size: 12px;
  color: var(--text-placeholder);
  opacity: 0;
  transition: opacity 0.2s;
}

.schedule-day:hover .day-hover-hint {
  opacity: 1;
}

.tooltip-schedule {
  max-width: 260px;
}

.tooltip-item {
  padding: 6px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
}

.tooltip-item:last-child {
  border-bottom: none;
}

.tooltip-time {
  font-size: 13px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 2px;
}

.tooltip-course {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 2px;
}

.tooltip-meta {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.65);
}

.charts-row {
  margin: 0 -8px !important;
}

.chart-card {
  margin-bottom: 0;
}

.chart-container {
  width: 100%;
}

.birthday-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.birthday-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 10px;
  border-radius: 10px;
  transition: background 0.2s;
}

.birthday-item:hover {
  background: var(--surface-soft);
}

.birthday-avatar {
  width: 38px;
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: linear-gradient(135deg, #f87171, #ef4444);
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  flex-shrink: 0;
  font-family: var(--font-display);
}

.birthday-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.birthday-name {
  font-size: 13.5px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.birthday-date {
  font-size: 12px;
  color: var(--text-placeholder);
}

.todo-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.todo-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  background: var(--surface-soft);
  border: 1px solid var(--border-light);
}

.todo-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  flex-shrink: 0;
  color: #fff;
}

.todo-icon.primary {
  background: linear-gradient(135deg, #3fc06a, #16a34a);
}

.todo-icon.warning {
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
}

.todo-icon.info {
  background: linear-gradient(135deg, #60a5fa, #3b82f6);
}

.todo-icon.success {
  background: linear-gradient(135deg, #34d399, #10b981);
}

.todo-content {
  flex: 1;
  min-width: 0;
}

.todo-title {
  font-size: 13.5px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 2px;
}

.todo-desc {
  font-size: 12px;
  color: var(--text-secondary);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px 12px;
  color: var(--text-placeholder);
}

.empty-icon {
  font-size: 32px;
  opacity: 0.7;
}

.empty-text {
  font-size: 13px;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.activity-item {
  display: flex;
  gap: 12px;
  padding: 8px;
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.2s;
}

.activity-item:hover {
  background: var(--surface-soft);
}

.activity-cover {
  width: 60px;
  height: 60px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--gold-200), var(--gold-400));
  flex-shrink: 0;
  background-size: cover;
  background-position: center;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cover-placeholder {
  font-size: 24px;
}

.activity-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 4px;
}

.activity-name {
  font-size: 13.5px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.activity-date {
  font-size: 12px;
  color: var(--text-placeholder);
  display: flex;
  align-items: center;
  gap: 4px;
}

.activity-date .el-icon {
  font-size: 13px;
}

@media (max-width: 1400px) {
  .quick-entries {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

@media (max-width: 1200px) {
  .data-cards {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .schedule-days {
    grid-template-columns: repeat(7, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .dashboard-container {
    padding: 12px;
  }

  .welcome-banner {
    padding: 20px;
  }

  .welcome-content {
    flex-direction: column;
    align-items: flex-start;
  }

  .welcome-actions {
    width: 100%;
    justify-content: space-around;
  }

  .data-cards {
    grid-template-columns: 1fr;
  }

  .quick-entries {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}
</style>
