<template>
  <div class="attendance">
    <!-- 顶部工具栏 -->
    <div class="attendance__toolbar">
      <div class="attendance__calendar">
        <WeekCalendar
          :week-days="weekDays"
          :selected-date="selectedDate"
          @select-date="selectDate"
          @prev-week="prevWeek"
          @next-week="nextWeek"
          @go-today="goToday"
        />
        <CalendarPopover v-model="selectedDate" @change="onDatePickerChange" />
        <el-button class="attendance__unattended-btn" @click="toggleUnattendedList">未考勤课次</el-button>
      </div>
    </div>

    <div v-if="!noClassToday" class="attendance__content">
      <!-- 左侧班级列表 -->
      <div class="attendance__left-panel">
        <SessionList
          :pending-sessions="pendingSessions"
          :completed-sessions="completedSessions"
          :left-tab="leftTab"
          :current-schedule="currentSchedule"
          @update:left-tab="leftTab = $event"
          @select-session="selectSession"
        />
      </div>

      <!-- 右侧学员列表和操作区 -->
      <div v-if="currentSchedule" class="attendance__right-panel">
        <StudentTable
          :student-list="studentList"
          :student-loading="studentLoading"
          :right-tab="rightTab"
          :sub-tab-pending="subTabPending"
          :sub-tab-present="subTabPresent"
          :sub-tab-absent="subTabAbsent"
          :search-keyword="searchKeyword"
          :paginated-filtered-list="paginatedFilteredList"
          :selected-students="selectedStudents"
          @update:right-tab="rightTab = $event"
          @update:sub-tab-pending="subTabPending = $event"
          @update:sub-tab-present="subTabPresent = $event"
          @update:sub-tab-absent="subTabAbsent = $event"
          @update:search-keyword="searchKeyword = $event"
          @selection-change="handleSelectionChange"
          @edit-attendance="openEditAttendance"
        />
        <BatchActions
          :selected-students="selectedStudents"
          @open-modal="openConfirmModal"
          @remove="handleRemove"
        />
      </div>
    </div>

    <div v-else class="attendance__empty">
      <el-icon class="attendance__empty-icon"><Coffee /></el-icon>
      <p>没课的时候好好休息吧</p>
    </div>

    <!-- 临时插班抽屉 -->
    <TempEnrollDrawer
      v-model:visible="tempEnrollDrawer"
      :schedule-id="currentSchedule?.schedule_id"
      @enroll-success="onTempEnrollSuccess"
    />

    <!-- 批量考勤确认模态框 -->
    <AttendanceConfirmDialog
      v-model:visible="confirmModalVisible"
      :schedule-id="currentSchedule?.schedule_id"
      :status="confirmStatus"
      :selected-students="selectedStudents"
      :default-deduct-hours="currentDeductHours"
      @success="onConfirmSuccess"
    />

    <!-- 编辑考勤模态框 -->
    <EditAttendanceDialog
      v-model:visible="editAttendanceVisible"
      :attendance="editAttendanceData"
      @success="onEditSuccess"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Coffee } from '@element-plus/icons-vue'
import WeekCalendar from '@/components/attendance/WeekCalendar.vue'
import SessionList from '@/components/attendance/SessionList.vue'
import StudentTable from '@/components/attendance/StudentTable.vue'
import BatchActions from '@/components/attendance/BatchActions.vue'
import TempEnrollDrawer from '@/components/attendance/TempEnrollDrawer.vue'
import AttendanceConfirmDialog from '@/components/AttendanceConfirmDialog.vue'
import EditAttendanceDialog from '@/components/EditAttendanceDialog.vue'
import CalendarPopover from '@/components/CalendarPopover.vue'
import { getAttendanceClasses, getClassStudents, updateAttendance } from '@/api/attendance'
import { getClassDetail } from '@/api/class'
import { DEFAULT_AVATAR_SVG } from '@/utils/constants'
import dayjs from 'dayjs'
import isoWeek from 'dayjs/plugin/isoWeek'

// ★★★ 引入 Pinia Store ★★★
import { useStudentStore } from '@/stores/student'
import { storeToRefs } from 'pinia'

dayjs.extend(isoWeek)

const route = useRoute()

// ========== 使用 Pinia Store 获取学员数据（用于头像同步） ==========
const studentStore = useStudentStore()

// ========== 周历相关 ==========
const selectedDate = ref(dayjs().format('YYYY-MM-DD'))
const weekDays = ref([])
const currentMonday = ref(dayjs().startOf('week').add(1, 'day'))

// ========== 课次相关 ==========
const pendingSessions = ref([])
const completedSessions = ref([])
const leftTab = ref('pending')
const currentSchedule = ref(null)
const currentDeductHours = ref(1)

// ========== 学员相关 ==========
const studentList = ref([])  // 考勤页面的本地学员列表
const studentLoading = ref(false)
const selectedStudents = ref([])
const rightTab = ref('pending')
const subTabPending = ref('pending')
const subTabPresent = ref('present')
const subTabAbsent = ref('leave')
const searchKeyword = ref('')

// ========== 弹窗控制 ==========
const confirmModalVisible = ref(false)
const confirmStatus = ref('')
const editAttendanceVisible = ref(false)
const editAttendanceData = ref(null)
const tempEnrollDrawer = ref(false)

// ========== 计算属性 ==========
const noClassToday = computed(() => pendingSessions.value.length === 0 && completedSessions.value.length === 0)

const filteredByTab = computed(() => {
  let list = studentList.value
  if (rightTab.value === 'pending') list = list.filter(s => !s.attendance_id || s.status === '未考勤')
  else if (rightTab.value === 'present') list = list.filter(s => s.status === '出勤' || s.status === '迟到')
  else if (rightTab.value === 'absent') list = list.filter(s => s.status === '未到' || s.status === '请假')
  return list
})

const filteredStudentList = computed(() => {
  let list = filteredByTab.value
  if (searchKeyword.value) {
    const kw = searchKeyword.value.toLowerCase()
    list = list.filter(s => s.name.toLowerCase().includes(kw) || (s.phone && s.phone.includes(kw)))
  }
  if (rightTab.value === 'pending' && subTabPending.value === 'pending') return list
  if (rightTab.value === 'present' && subTabPresent.value === 'present') return list.filter(s => s.status === '出勤')
  if (rightTab.value === 'present' && subTabPresent.value === 'late') return list.filter(s => s.status === '迟到')
  if (rightTab.value === 'present' && subTabPresent.value === 'temp') return list.filter(s => s.is_temporary === true)
  if (rightTab.value === 'absent' && subTabAbsent.value === 'leave') return list.filter(s => s.status === '请假')
  if (rightTab.value === 'absent' && subTabAbsent.value === 'absent') return list.filter(s => s.status === '未到')
  return []
})

const paginatedFilteredList = computed(() => filteredStudentList.value)

// ========== 核心：从 Store 同步头像 ==========
function syncAvatarFromStore(student) {
  if (!student) return student
  const storeStudent = studentStore.students.find(s => s.id === student.student_id || s.id === student.id)
  if (storeStudent && storeStudent.avatar) {
    return {
      ...student,
      avatar: storeStudent.avatar
    }
  }
  return {
    ...student,
    avatar: student.avatar || DEFAULT_AVATAR_SVG
  }
}

function syncAvatarsForList(students) {
  return students.map(s => syncAvatarFromStore(s))
}

// ========== 加载周历 ==========
async function loadWeekScheduleStatus() {
  const start = currentMonday.value
  const weekDaysTemp = []
  for (let i = 0; i < 7; i++) {
    const d = start.add(i, 'day')
    const dateStr = d.format('YYYY-MM-DD')
    let hasSchedule = false, allCompleted = true
    try {
      const res = await getAttendanceClasses(dateStr)
      const sessions = res.data || []
      hasSchedule = sessions.length > 0
      allCompleted = sessions.every(s => s.status === 'completed')
    } catch (e) { console.error(e) }
    weekDaysTemp.push({
      date: dateStr,
      dayName: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][i],
      dayOfMonth: d.date(),
      isToday: d.isSame(dayjs(), 'day'),
      hasSchedule,
      allCompleted
    })
  }
  weekDays.value = weekDaysTemp
}

// ========== 加载课次 ==========
async function loadSessions() {
  try {
    const res = await getAttendanceClasses(selectedDate.value)
    const sessions = res.data || []
    pendingSessions.value = sessions.filter(s => s.status !== 'completed')
    completedSessions.value = sessions.filter(s => s.status === 'completed')
    if (pendingSessions.value.length > 0) {
      leftTab.value = 'pending'
      rightTab.value = 'pending'
      subTabPending.value = 'pending'
      setTimeout(() => selectSession(pendingSessions.value[0]), 50)
    } else if (completedSessions.value.length > 0) {
      leftTab.value = 'completed'
      rightTab.value = 'present'
      subTabPresent.value = 'present'
      setTimeout(() => selectSession(completedSessions.value[0]), 50)
    } else {
      currentSchedule.value = null
      studentList.value = []
      studentLoading.value = false
    }
  } catch (e) {
    console.error('加载课次失败', e)
  }
}

// ========== 选择课次并加载学员 ==========
async function selectSession(session) {
  if (!session) return
  currentSchedule.value = session
  studentLoading.value = true
  try {
    const classRes = await getClassDetail(session.class_id)
    if (classRes.code === 0 && classRes.data) currentDeductHours.value = classRes.data.deduct_hours || 1

    const res = await getClassStudents(session.schedule_id)
    const rawStudents = res.data || []
    const studentsWithAvatar = rawStudents.map(s => ({
      ...s,
      student_id: Number(s.student_id),
      hasAttendance: !!s.attendance_id,
      avatar: syncAvatarFromStore(s).avatar
    }))
    studentList.value = studentsWithAvatar
  } catch (e) {
    studentList.value = []
  } finally {
    studentLoading.value = false
  }
}

// ========== 刷新学员列表（保留头像同步） ==========
async function refreshStudents() {
  if (!currentSchedule.value) return
  studentLoading.value = true
  try {
    const res = await getClassStudents(currentSchedule.value.schedule_id)
    const rawStudents = res.data || []
    const studentsWithAvatar = rawStudents.map(s => ({
      ...s,
      student_id: Number(s.student_id),
      hasAttendance: !!s.attendance_id,
      avatar: syncAvatarFromStore(s).avatar
    }))
    studentList.value = studentsWithAvatar
  } catch (e) {
    studentList.value = []
  } finally {
    studentLoading.value = false
  }
}

// ========== 其他方法 ==========
function handleSelectionChange(selection) {
  selectedStudents.value = selection
}

function openConfirmModal(status) {
  if (!selectedStudents.value.length) {
    ElMessage.warning('请先选择学员')
    return
  }
  if (!currentSchedule.value) {
    ElMessage.warning('请先选择课次')
    return
  }
  confirmStatus.value = status
  confirmModalVisible.value = true
}

async function onConfirmSuccess() {
  await refreshStudents()
  await loadSessions()
}

function openEditAttendance(row) {
  editAttendanceData.value = {
    attendance_id: row.attendance_id,
    student_name: row.name,
    status: row.status,
    deduct_hours: row.deduct_hours,
    hour_type: row.gift_deduct > 0 ? '赠送' : '付费',
    remaining_hours: row.remaining_hours,
    remaining_gift: row.remaining_gift || 0,
    remark: row.remark || ''
  }
  editAttendanceVisible.value = true
}

async function onEditSuccess() {
  await refreshStudents()
  await loadSessions()
}

function handleRemove() {
  if (selectedStudents.value.length) ElMessage.info('移除功能开发中')
}

function selectDate(date) {
  selectedDate.value = date
  loadWeekScheduleStatus()
  loadSessions()
}

function onDatePickerChange(date) {
  if (date) selectDate(date)
}

function prevWeek() {
  currentMonday.value = currentMonday.value.subtract(7, 'day')
  loadWeekScheduleStatus()
  const newDate = currentMonday.value.add(3, 'day').format('YYYY-MM-DD')
  selectDate(newDate)
}

function nextWeek() {
  currentMonday.value = currentMonday.value.add(7, 'day')
  loadWeekScheduleStatus()
  const newDate = currentMonday.value.add(3, 'day').format('YYYY-MM-DD')
  selectDate(newDate)
}

function goToday() {
  currentMonday.value = dayjs().startOf('week').add(1, 'day')
  loadWeekScheduleStatus()
  selectDate(dayjs().format('YYYY-MM-DD'))
}

function toggleUnattendedList() {
  ElMessage.info('未考勤课次功能开发中')
}

function onTempEnrollSuccess() {
  refreshStudents()
  loadSessions()
}

// ========== 监听 Store 变化，自动更新头像 ==========
watch(
  () => studentStore.students,
  (newStudents) => {
    studentList.value = studentList.value.map(s => {
      const storeStudent = newStudents.find(st => st.id === s.student_id)
      if (storeStudent && storeStudent.avatar !== s.avatar) {
        return { ...s, avatar: storeStudent.avatar }
      }
      return s
    })
  },
  { deep: true }
)

// ========== 生命周期 ==========
onMounted(() => {
  const queryDate = route.query.date
  if (queryDate && dayjs(queryDate).isValid()) {
    selectedDate.value = queryDate
    loadWeekScheduleStatus()
    loadSessions()
  } else {
    selectedDate.value = dayjs().format('YYYY-MM-DD')
    loadWeekScheduleStatus()
    loadSessions()
  }
})
</script>

<style scoped>
.attendance {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.attendance__toolbar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  overflow: visible;
  padding: var(--space-4);
  background: var(--surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xs);
}

.attendance__calendar {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  flex-wrap: wrap;
  width: 100%;
  overflow: visible;
}

.attendance__unattended-btn {
  background: transparent;
  border: 1px solid var(--brand-500);
  color: var(--brand-600);
  border-radius: var(--radius-pill);
  height: var(--control-height);
  padding: 0 var(--space-4);
  cursor: pointer;
  transition: all 0.18s;
}

.attendance__unattended-btn:hover {
  background: var(--brand-500);
  color: var(--surface);
}

.attendance__content {
  flex: 1;
  display: flex;
  gap: var(--space-4);
  min-height: 0;
  overflow: hidden;
}

.attendance__left-panel,
.attendance__right-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xs);
}

.attendance__left-panel { width: 70%; }
.attendance__right-panel { width: 30%; }

.attendance__empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
  background: var(--surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xs);
}

.attendance__empty-icon {
  font-size: 48px;
  color: var(--text-placeholder);
}

@media (max-width: 960px) {
  .attendance__content { flex-direction: column; }
  .attendance__left-panel { width: 100%; height: 55%; }
  .attendance__right-panel { width: 100%; height: 45%; }
}
</style>
