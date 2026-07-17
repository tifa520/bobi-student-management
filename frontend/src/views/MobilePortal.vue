<template>
  <div class="mobile-container">
    <!-- ========== 登录页面 ========== -->
    <div v-if="!loggedIn" class="login-page">
      <div class="login-header">
        <div class="login-logo">BS</div>
        <h1>学员中心</h1>
        <p>使用手机号登录查看课程信息</p>
      </div>
      <div class="login-form">
        <div class="input-group">
          <label>手机号</label>
          <input v-model="loginPhone" type="tel" maxlength="11" placeholder="请输入学员手机号" />
        </div>
        <div class="input-group">
          <label>密码</label>
          <input v-model="loginPassword" type="password" placeholder="请输入密码" @keyup.enter="handleLogin" />
        </div>
        <button class="login-btn" :disabled="loginLoading" @click="handleLogin">
          {{ loginLoading ? '登录中...' : '登录' }}
        </button>
        <p class="login-tip">初始密码为手机号后6位</p>
      </div>
      <div class="login-error" v-if="loginError">{{ loginError }}</div>
    </div>

    <!-- ========== 主页面 ========== -->
    <div v-else class="main-page">
      <!-- 顶部栏 -->
      <div class="top-bar">
        <div class="bar-left">
          <div class="bar-avatar" :style="avatarStyle">{{ studentInfo.name?.charAt(0) }}</div>
          <div class="bar-info">
            <div class="bar-name">{{ studentInfo.name }}</div>
            <div class="bar-phone">{{ studentInfo.phone }}</div>
          </div>
        </div>
        <button class="logout-btn" @click="handleLogout">退出</button>
      </div>

      <!-- 内容区 -->
      <div class="content-area">
        <!-- 首页 -->
        <div v-show="activeTab === 'home'" class="tab-content">
          <div class="stats-row">
            <div class="stat-card">
              <div class="stat-num">{{ stats.total_remaining }}</div>
              <div class="stat-label">剩余课时</div>
            </div>
            <div class="stat-card">
              <div class="stat-num">{{ stats.total_gift }}</div>
              <div class="stat-label">赠送课时</div>
            </div>
            <div class="stat-card">
              <div class="stat-num">{{ stats.total_deducted }}</div>
              <div class="stat-label">已消课时</div>
            </div>
            <div class="stat-card">
              <div class="stat-num">{{ stats.total_leave }}</div>
              <div class="stat-label">已请假</div>
            </div>
          </div>

          <div class="section-title">课程概览</div>
          <div v-if="groups.length === 0" class="empty">暂无课程</div>
          <div v-for="g in groups" :key="g.class_id" class="course-group-card">
            <div class="group-header">
              <span class="group-course">{{ g.course_name }}</span>
              <span v-if="g.stage_name" class="group-stage">{{ g.stage_name }}</span>
              <span v-if="g.class_name" class="group-class">{{ g.class_name }}</span>
            </div>
            <div class="group-stats">
              <div class="group-stat">
                <span class="gs-val">{{ g.remaining_hours }}</span>
                <span class="gs-label">剩余</span>
              </div>
              <div class="group-stat">
                <span class="gs-val">{{ g.remaining_gift }}</span>
                <span class="gs-label">赠送</span>
              </div>
              <div class="group-stat">
                <span class="gs-val">{{ g.total_deducted }}</span>
                <span class="gs-label">已消</span>
              </div>
              <div class="group-stat">
                <span class="gs-val">{{ g.leave_used }}</span>
                <span class="gs-label">请假</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 课程表 -->
        <div v-show="activeTab === 'timetable'" class="tab-content">
          <div v-if="timetableGroups.length === 0" class="empty">暂无排课</div>
          <div v-for="g in timetableGroups" :key="g.class_id" class="timetable-card">
            <div class="tt-header">
              <span class="tt-course">{{ g.course_name }}</span>
              <span v-if="g.stage_name" class="tt-stage">{{ g.stage_name }}</span>
              <span v-if="g.class_name" class="tt-class">{{ g.class_name }}</span>
            </div>
            <div class="tt-list">
              <div v-for="s in g.schedules" :key="s.schedule_id" class="tt-item" :class="{ leave: s.attendance_status === '请假' }">
                <div class="tt-date">{{ formatDate(s.course_date) }}</div>
                <div class="tt-time">{{ s.start_time }} ({{ s.duration }}分钟)</div>
                <div class="tt-status" :class="statusClass(s.attendance_status)">
                  {{ s.attendance_status || '待上课' }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 作品 -->
        <div v-show="activeTab === 'works'" class="tab-content">
          <div v-if="works.length === 0" class="empty">暂无作品</div>
          <div class="works-grid">
            <div v-for="w in works" :key="w.id" class="work-card" @click="previewWork(w)">
              <div class="work-img-wrap">
                <img v-if="w.img_url" :src="w.img_url" :alt="w.name" class="work-img" @error="onImgError" />
                <div v-else class="work-img-placeholder">🖼️</div>
              </div>
              <div class="work-info">
                <div class="work-name">{{ w.name }}</div>
                <div class="work-time">{{ formatDate(w.created_at) }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 考勤 -->
        <div v-show="activeTab === 'attendance'" class="tab-content">
          <div v-if="attendanceGroups.length === 0" class="empty">暂无考勤记录</div>
          <div v-for="g in attendanceGroups" :key="g.class_id" class="att-card">
            <div class="att-header">
              <span class="att-course">{{ g.course_name }}</span>
              <span v-if="g.stage_name" class="att-stage">{{ g.stage_name }}</span>
              <span v-if="g.class_name" class="att-class">{{ g.class_name }}</span>
            </div>
            <div class="att-list">
              <div v-for="a in g.attendances" :key="a.id" class="att-item">
                <div class="att-date">{{ formatDate(a.course_date) }}</div>
                <div class="att-info">
                  <span class="att-status" :class="statusClass(a.status)">{{ a.status }}</span>
                  <span v-if="a.deduct_hours" class="att-hours">扣{{ a.deduct_hours }}课时</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 积分 -->
        <div v-show="activeTab === 'points'" class="tab-content">
          <div class="points-header">
            <div class="points-total">
              <div class="pt-num">{{ pointsData.total_integral }}</div>
              <div class="pt-label">当前积分</div>
            </div>
          </div>
          <div class="section-title">积分记录</div>
          <div v-if="pointsData.records?.length === 0" class="empty">暂无积分记录</div>
          <div class="points-list">
            <div v-for="r in pointsData.records" :key="r.id" class="point-item">
              <div class="pi-left">
                <div class="pi-reason">{{ r.reason || '积分变动' }}</div>
                <div class="pi-time">{{ formatDate(r.created_at) }}</div>
              </div>
              <div class="pi-amount" :class="r.change_amount > 0 ? 'positive' : 'negative'">
                {{ r.change_amount > 0 ? '+' : '' }}{{ r.change_amount }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部 Tab -->
      <div class="tab-bar">
        <div class="tab-item" :class="{ active: activeTab === 'home' }" @click="switchTab('home')">
          <span class="tab-icon">🏠</span><span>首页</span>
        </div>
        <div class="tab-item" :class="{ active: activeTab === 'timetable' }" @click="switchTab('timetable')">
          <span class="tab-icon">📅</span><span>课程表</span>
        </div>
        <div class="tab-item" :class="{ active: activeTab === 'works' }" @click="switchTab('works')">
          <span class="tab-icon">🖼️</span><span>作品</span>
        </div>
        <div class="tab-item" :class="{ active: activeTab === 'attendance' }" @click="switchTab('attendance')">
          <span class="tab-icon">📋</span><span>考勤</span>
        </div>
        <div class="tab-item" :class="{ active: activeTab === 'points' }" @click="switchTab('points')">
          <span class="tab-icon">⭐</span><span>积分</span>
        </div>
      </div>
    </div>

    <!-- 图片预览弹窗 -->
    <div v-if="previewImg" class="preview-overlay" @click="previewImg = null">
      <img :src="previewImg" class="preview-img" @click.stop />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const API = '/api/student-portal'

// 登录状态
const loggedIn = ref(false)
const loginPhone = ref('')
const loginPassword = ref('')
const loginLoading = ref(false)
const loginError = ref('')
const token = ref('')

// 学生信息
const studentInfo = ref({})
const stats = ref({ total_remaining: 0, total_gift: 0, total_deducted: 0, total_leave: 0 })
const groups = ref([])
const timetableGroups = ref([])
const works = ref([])
const attendanceGroups = ref([])
const pointsData = ref({ total_integral: 0, records: [] })

// UI
const activeTab = ref('home')
const previewImg = ref(null)

const avatarStyle = computed(() => {
  const colors = ['#22C55E', '#3B82F6', '#8B5CF6', '#F59E0B', '#EF4444', '#EC4899']
  const idx = studentInfo.value.id ? studentInfo.value.id % colors.length : 0
  return { background: colors[idx] }
})

function getHeaders() {
  return token.value ? { Authorization: `Bearer ${token.value}` } : {}
}

// 登录
async function handleLogin() {
  const phone = loginPhone.value.trim()
  if (!phone || phone.length < 6) {
    loginError.value = '请输入正确的手机号'
    return
  }
  loginLoading.value = true
  loginError.value = ''
  try {
    const res = await axios.post(API + '/login', { phone, password: loginPassword.value })
    if (res.data.code === 0) {
      token.value = res.data.data.access_token
      studentInfo.value = res.data.data.student
      localStorage.setItem('m_token', token.value)
      localStorage.setItem('m_student', JSON.stringify(studentInfo.value))
      loggedIn.value = true
      await loadDashboard()
    } else {
      loginError.value = res.data.message || '登录失败'
    }
  } catch (e) {
    loginError.value = e.response?.data?.detail || '登录失败，请检查手机号'
  }
  loginLoading.value = false
}

function handleLogout() {
  localStorage.removeItem('m_token')
  localStorage.removeItem('m_student')
  token.value = ''
  loggedIn.value = false
  loginPhone.value = ''
  loginPassword.value = ''
}

function switchTab(tab) {
  activeTab.value = tab
  if (tab === 'timetable') loadTimetable()
  else if (tab === 'works') loadWorks()
  else if (tab === 'attendance') loadAttendance()
  else if (tab === 'points') loadPoints()
}

// 加载仪表盘
async function loadDashboard() {
  try {
    const res = await axios.get(API + '/dashboard', { headers: getHeaders() })
    if (res.data.code === 0) {
      stats.value = res.data.data.stats
      groups.value = res.data.data.groups || []
      if (res.data.data.student) {
        studentInfo.value = { ...studentInfo.value, ...res.data.data.student }
      }
    }
  } catch (e) { console.error('加载首页失败', e) }
}

// 加载课程表
async function loadTimetable() {
  try {
    const res = await axios.get(API + '/timetable', { headers: getHeaders() })
    if (res.data.code === 0) {
      timetableGroups.value = res.data.data.groups || []
    }
  } catch (e) { console.error('加载课程表失败', e) }
}

// 加载作品
async function loadWorks() {
  try {
    const res = await axios.get(API + '/works', { headers: getHeaders() })
    if (res.data.code === 0) {
      works.value = res.data.data.list || []
    }
  } catch (e) { console.error('加载作品失败', e) }
}

// 加载考勤
async function loadAttendance() {
  try {
    const res = await axios.get(API + '/attendance', { headers: getHeaders() })
    if (res.data.code === 0) {
      attendanceGroups.value = res.data.data.groups || []
    }
  } catch (e) { console.error('加载考勤失败', e) }
}

// 加载积分
async function loadPoints() {
  try {
    const res = await axios.get(API + '/points', { headers: getHeaders() })
    if (res.data.code === 0) {
      pointsData.value = res.data.data
    }
  } catch (e) { console.error('加载积分失败', e) }
}

function formatDate(d) {
  if (!d) return ''
  return d.split('T')[0] || d.slice(0, 10)
}

function statusClass(s) {
  if (!s) return ''
  if (s === '已签到' || s === '迟到') return 'checkin'
  if (s === '请假') return 'leave'
  if (s === '缺勤') return 'absent'
  return ''
}

function previewWork(w) {
  if (w.original_url) previewImg.value = w.original_url
  else if (w.img_url) previewImg.value = w.img_url
}

function onImgError(e) {
  e.target.style.display = 'none'
  e.target.nextElementSibling?.style && (e.target.nextElementSibling.style.display = 'flex')
}

// 恢复登录状态
onMounted(() => {
  const savedToken = localStorage.getItem('m_token')
  const savedStudent = localStorage.getItem('m_student')
  if (savedToken && savedStudent) {
    token.value = savedToken
    studentInfo.value = JSON.parse(savedStudent)
    loggedIn.value = true
    loadDashboard()
  }
})
</script>

<style scoped>
/* ========== 基础 ========== */
.mobile-container {
  max-width: 480px;
  margin: 0 auto;
  min-height: 100vh;
  background: #f5f5f5;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  position: relative;
  padding-bottom: 70px;
}

/* ========== 登录页 ========== */
.login-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.login-header { text-align: center; margin-bottom: 32px; }
.login-logo {
  width: 72px; height: 72px; border-radius: 18px;
  background: rgba(255,255,255,.2); color: #fff;
  font-size: 28px; font-weight: 700; display: flex;
  align-items: center; justify-content: center; margin: 0 auto 16px;
}
.login-header h1 { color: #fff; font-size: 24px; margin: 0; }
.login-header p { color: rgba(255,255,255,.7); font-size: 14px; margin-top: 8px; }
.login-form { width: 100%; max-width: 320px; }
.input-group { margin-bottom: 16px; }
.input-group label { display: block; color: rgba(255,255,255,.8); font-size: 13px; margin-bottom: 6px; }
.input-group input {
  width: 100%; padding: 12px 16px; border: none; border-radius: 10px;
  font-size: 16px; box-sizing: border-box; outline: none;
}
.login-btn {
  width: 100%; padding: 14px; border: none; border-radius: 10px;
  background: #fff; color: #667eea; font-size: 16px; font-weight: 600;
  cursor: pointer; margin-top: 8px;
}
.login-btn:disabled { opacity: .6; }
.login-tip { color: rgba(255,255,255,.6); font-size: 12px; text-align: center; margin-top: 12px; }
.login-error {
  margin-top: 16px; padding: 10px 16px; background: rgba(255,0,0,.2);
  color: #fff; border-radius: 8px; font-size: 14px;
}

/* ========== 主页面 ========== */
.main-page { background: #f5f5f5; }

/* 顶部栏 */
.top-bar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px; background: #fff; position: sticky; top: 0; z-index: 10;
  box-shadow: 0 1px 3px rgba(0,0,0,.05);
}
.bar-left { display: flex; align-items: center; gap: 10px; }
.bar-avatar {
  width: 40px; height: 40px; border-radius: 50%;
  color: #fff; font-size: 16px; font-weight: 600;
  display: flex; align-items: center; justify-content: center;
}
.bar-name { font-size: 16px; font-weight: 600; color: #333; }
.bar-phone { font-size: 12px; color: #999; }
.logout-btn {
  padding: 6px 14px; border: 1px solid #ddd; border-radius: 6px;
  background: #fff; color: #666; font-size: 13px; cursor: pointer;
}

/* 内容区 */
.content-area { padding: 12px 16px; }
.tab-content { animation: fadeIn .2s; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

/* 统计卡片 */
.stats-row {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px;
  margin-bottom: 16px;
}
.stat-card {
  background: #fff; border-radius: 10px; padding: 12px 8px; text-align: center;
  box-shadow: 0 1px 3px rgba(0,0,0,.04);
}
.stat-num { font-size: 22px; font-weight: 700; color: #667eea; }
.stat-label { font-size: 11px; color: #999; margin-top: 4px; }

.section-title { font-size: 15px; font-weight: 600; color: #333; margin-bottom: 10px; }
.empty { text-align: center; color: #999; font-size: 14px; padding: 40px 0; }

/* 课程分组卡片 */
.course-group-card {
  background: #fff; border-radius: 10px; padding: 14px;
  margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,.04);
}
.group-header {
  display: flex; align-items: center; gap: 8px; margin-bottom: 10px;
  flex-wrap: wrap;
}
.group-course { font-size: 15px; font-weight: 600; color: #333; }
.group-stage { font-size: 12px; color: #667eea; background: #ede9fe; padding: 2px 8px; border-radius: 4px; }
.group-class { font-size: 12px; color: #059669; background: #d1fae5; padding: 2px 8px; border-radius: 4px; }
.group-stats { display: flex; gap: 16px; }
.group-stat { text-align: center; }
.gs-val { font-size: 18px; font-weight: 700; color: #333; display: block; }
.gs-label { font-size: 11px; color: #999; }

/* 课程表 */
.timetable-card {
  background: #fff; border-radius: 10px; padding: 14px;
  margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,.04);
}
.tt-header {
  display: flex; align-items: center; gap: 8px; margin-bottom: 10px;
  flex-wrap: wrap;
}
.tt-course { font-size: 15px; font-weight: 600; }
.tt-stage { font-size: 12px; color: #667eea; background: #ede9fe; padding: 2px 8px; border-radius: 4px; }
.tt-class { font-size: 12px; color: #059669; background: #d1fae5; padding: 2px 8px; border-radius: 4px; }
.tt-list { display: flex; flex-direction: column; gap: 6px; }
.tt-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 10px; background: #f8f9fa; border-radius: 6px;
}
.tt-item.leave { opacity: .5; }
.tt-date { font-size: 13px; color: #333; font-weight: 500; }
.tt-time { font-size: 12px; color: #666; }
.tt-status { font-size: 12px; padding: 2px 8px; border-radius: 4px; }
.tt-status.checkin { background: #d1fae5; color: #059669; }
.tt-status.leave { background: #fef3c7; color: #d97706; }
.tt-status.absent { background: #fee2e2; color: #dc2626; }

/* 作品 */
.works-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
.work-card {
  background: #fff; border-radius: 10px; overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,.04); cursor: pointer;
}
.work-img-wrap {
  width: 100%; padding-top: 75%; position: relative;
  background: #f0f0f0; overflow: hidden;
}
.work-img {
  position: absolute; top: 0; left: 0; width: 100%; height: 100%;
  object-fit: cover;
}
.work-img-placeholder {
  position: absolute; top: 0; left: 0; width: 100%; height: 100%;
  display: flex; align-items: center; justify-content: center;
  font-size: 32px; color: #ccc;
}
.work-info { padding: 8px 10px; }
.work-name { font-size: 13px; font-weight: 500; color: #333; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.work-time { font-size: 11px; color: #999; margin-top: 2px; }

/* 考勤 */
.att-card {
  background: #fff; border-radius: 10px; padding: 14px;
  margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,.04);
}
.att-header {
  display: flex; align-items: center; gap: 8px; margin-bottom: 10px;
  flex-wrap: wrap;
}
.att-course { font-size: 15px; font-weight: 600; }
.att-stage { font-size: 12px; color: #667eea; background: #ede9fe; padding: 2px 8px; border-radius: 4px; }
.att-class { font-size: 12px; color: #059669; background: #d1fae5; padding: 2px 8px; border-radius: 4px; }
.att-list { display: flex; flex-direction: column; gap: 6px; }
.att-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 10px; background: #f8f9fa; border-radius: 6px;
}
.att-date { font-size: 13px; color: #333; }
.att-info { display: flex; align-items: center; gap: 8px; }
.att-status { font-size: 12px; padding: 2px 8px; border-radius: 4px; }
.att-status.checkin { background: #d1fae5; color: #059669; }
.att-status.leave { background: #fef3c7; color: #d97706; }
.att-status.absent { background: #fee2e2; color: #dc2626; }
.att-hours { font-size: 12px; color: #666; }

/* 积分 */
.points-header { margin-bottom: 16px; }
.points-total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px; padding: 24px; text-align: center; color: #fff;
}
.pt-num { font-size: 36px; font-weight: 700; }
.pt-label { font-size: 14px; opacity: .8; margin-top: 4px; }
.points-list { display: flex; flex-direction: column; gap: 8px; }
.point-item {
  display: flex; align-items: center; justify-content: space-between;
  background: #fff; border-radius: 8px; padding: 12px 14px;
  box-shadow: 0 1px 3px rgba(0,0,0,.04);
}
.pi-reason { font-size: 14px; color: #333; }
.pi-time { font-size: 12px; color: #999; margin-top: 2px; }
.pi-amount { font-size: 16px; font-weight: 600; }
.pi-amount.positive { color: #059669; }
.pi-amount.negative { color: #dc2626; }

/* 底部 Tab */
.tab-bar {
  position: fixed; bottom: 0; left: 50%; transform: translateX(-50%);
  width: 100%; max-width: 480px; background: #fff;
  display: flex; justify-content: space-around;
  padding: 8px 0; padding-bottom: env(safe-area-inset-bottom, 8px);
  box-shadow: 0 -1px 3px rgba(0,0,0,.05); z-index: 100;
}
.tab-item {
  display: flex; flex-direction: column; align-items: center;
  gap: 2px; font-size: 11px; color: #999; cursor: pointer; padding: 4px 0;
}
.tab-item.active { color: #667eea; }
.tab-icon { font-size: 20px; }

/* 图片预览 */
.preview-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,.9); z-index: 200;
  display: flex; align-items: center; justify-content: center;
}
.preview-img { max-width: 90%; max-height: 90%; border-radius: 8px; }
</style>