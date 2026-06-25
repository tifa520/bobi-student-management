<template>
  <div class="class-detail-page">
    <!-- 头部 -->
    <div class="detail-header">
      <el-button link class="back-btn" @click="$router.back()">
        <el-icon><ArrowLeft /></el-icon><span>返回</span>
      </el-button>
      <span class="title-divider"></span>
      <span class="class-name">{{ classInfo.name }}</span>
      <div class="header-actions">
        <el-button link type="danger" @click="handleDeleteClass">删除班级</el-button>
        <el-button link type="warning" @click="handleCloseClass">班级结课</el-button>
      </div>
    </div>

    <div class="class-detail-wrapper">
      <div class="class-detail">
        <div class="vertical-tabs">
          <div
            v-for="tab in tabs"
            :key="tab.name"
            class="tab-item"
            :class="{ active: activeTab === tab.name }"
            @click="activeTab = tab.name; onTabChange(tab.name)"
          >
            {{ tab.label }}
          </div>
        </div>
        <div class="tab-content">
          <!-- 信息 Tab -->
          <div v-if="activeTab === 'info'" class="info-panel">
            <div class="info-item">
              <span class="label">班级名称：</span>
              <span v-if="!editing">{{ classInfo.name }}</span>
              <el-input v-else v-model="classInfo.name" size="small" style="width:200px" />
            </div>
            <div class="info-item">
              <span class="label">课程：</span>
              <span v-if="!editing">{{ getCourseName(classInfo.course_id) }}</span>
              <el-select v-else v-model="classInfo.course_id" placeholder="选择课程" size="small" style="width:200px" @change="onCourseChangeForEdit">
                <el-option v-for="c in courses" :key="c.id" :label="c.name" :value="c.id" />
              </el-select>
            </div>
            <div class="info-item">
              <span class="label">课阶：</span>
              <span v-if="!editing">{{ classInfo.stage_name || '未设置' }}</span>
              <el-select
                v-else
                v-model="classInfo.stage_id"
                placeholder="选择课阶"
                size="small"
                style="width:200px"
                :disabled="!classInfo.course_id"
              >
                <el-option
                  v-for="s in stageOptions"
                  :key="s.id"
                  :label="s.name"
                  :value="s.id"
                />
              </el-select>
            </div>
            <div class="info-item">
              <span class="label">单次时长：</span>
              <span v-if="!editing">{{ classInfo.duration ? classInfo.duration + '分钟' : '未设置' }}</span>
              <el-input-number v-else v-model="classInfo.duration" :min="30" :step="30" size="small" style="width:120px" :controls="false" />
            </div>
            <div class="info-item">
              <span class="label">单次课扣：</span>
              <span v-if="!editing">{{ classInfo.deduct_hours ? classInfo.deduct_hours + '课时' : '未设置' }}</span>
              <el-input-number v-else v-model="classInfo.deduct_hours" :min="1" size="small" style="width:100px" :controls="false" />
            </div>
            <div class="info-item">
              <span class="label">课时单价：</span>
              <span v-if="!editing">
                {{ classInfo.unit_price ? '¥' + classInfo.unit_price : '继承课阶价格' }}
              </span>
              <el-input-number v-else v-model="classInfo.unit_price" :min="0" :precision="2" size="small" style="width:120px" :controls="false" placeholder="留空则继承课阶" />
            </div>
            <div class="info-item">
              <span class="label">任课教师：</span>
              <span v-if="!editing">{{ getTeacherName(classInfo.teacher_id) }}</span>
              <el-select v-else v-model="classInfo.teacher_id" placeholder="选择老师" clearable size="small" style="width:200px">
                <el-option v-for="t in teachers" :key="t.id" :label="t.name" :value="t.id" />
              </el-select>
            </div>
            <div class="info-item">
              <span class="label">上课教室：</span>
              <span v-if="!editing">{{ getClassroomName(classInfo.classroom_id) }}</span>
              <el-select v-else v-model="classInfo.classroom_id" placeholder="选择教室" clearable size="small" style="width:200px">
                <el-option v-for="r in classrooms" :key="r.id" :label="r.name" :value="r.id" />
              </el-select>
            </div>
            <div class="info-item">
              <span class="label">报名人数：</span>
              <span>{{ classInfo.student_count || 0 }}</span>
            </div>
            <div class="info-item">
              <span class="label">状态：</span>
              <el-tag :type="classInfo.status === 'active' ? 'success' : 'info'" size="small">
                {{ classInfo.status === 'active' ? '未结课' : '已结课' }}
              </el-tag>
            </div>
            <div class="info-item">
              <span class="label">备注：</span>
              <span v-if="!editing">{{ classInfo.remark || '-' }}</span>
              <el-input v-else v-model="classInfo.remark" type="textarea" :rows="2" size="small" style="width:300px" />
            </div>
            <div class="form-actions">
              <el-button v-if="!editing" type="primary" size="small" @click="enableEdit">编辑</el-button>
              <template v-else>
                <el-button type="primary" size="small" class="save-btn" @click="updateInfo">保存</el-button>
                <el-button size="small" @click="cancelEdit">取消</el-button>
              </template>
            </div>
          </div>

          <!-- 学员 Tab -->
          <div v-if="activeTab === 'students'" class="students-content">
            <div class="student-list-header">
              <el-input v-model="studentSearch" placeholder="请输入学员姓名或手机号" clearable style="width:260px" />
              <el-button type="primary" @click="addStudent">添加学员</el-button>
            </div>
            <el-table :data="filteredStudents" border stripe>
              <el-table-column label="学员" min-width="160">
                <template #default="{ row }">
                  <div class="student-info-cell">
                    <AppImage :src="row.avatar" :size="32" shape="circle" class="student-avatar" />
                    <div class="student-name">{{ row.name }}</div>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="phone" label="手机号" min-width="120" />
              <el-table-column prop="birthday" label="生日" min-width="100" />
              <el-table-column label="剩余课时" min-width="100">
                <template #default="{ row }">{{ row.remaining_hours || 0 }}课时</template>
              </el-table-column>
              <el-table-column label="剩余金额" min-width="100">
                <template #default="{ row }">￥{{ row.remaining_amount || 0 }}</template>
              </el-table-column>
              <el-table-column label="有效期至" min-width="100">
                <template #default="{ row }">{{ row.validity_date || '-' }}</template>
              </el-table-column>
              <el-table-column label="请假情况" min-width="100">
                <template #default="{ row }">{{ row.used_leaves }}/{{ row.total_leaves }}</template>
              </el-table-column>
              <el-table-column label="操作" width="120">
                <template #default="{ row }">
                  <el-button type="primary" link size="small" @click="leaveStudent(row)">请假</el-button>
                  <el-button type="danger" link size="small" @click="removeStudent(row)">退班</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <!-- 课表 Tab -->
          <div v-if="activeTab === 'schedule'" class="schedule-content">
            <el-tabs v-model="scheduleSubTab" class="schedule-tabs">
              <el-tab-pane label="未上课课表" name="upcoming">
                <el-table :data="upcomingSchedules" border>
                  <el-table-column label="上课时间" width="280">
                    <template #default="{ row }">{{ formatScheduleTime(row) }}</template>
                  </el-table-column>
                  <el-table-column prop="teacher_name" label="任课教师" />
                  <el-table-column prop="classroom_name" label="上课教室" />
                  <el-table-column label="状态"><template>待上课</template></el-table-column>
                  <el-table-column label="操作" width="150">
                    <template #default="{ row }">
                      <el-button link type="primary" size="small" @click="openEditSchedule(row)">编辑</el-button>
                      <el-button link type="danger" size="small" @click="handleDeleteSchedule(row)">删除</el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </el-tab-pane>
              <el-tab-pane label="历史课表" name="history">
                <el-table :data="historySchedules" border>
                  <el-table-column label="上课时间" width="280">
                    <template #default="{ row }">{{ formatScheduleTime(row) }}</template>
                  </el-table-column>
                  <el-table-column prop="teacher_name" label="任课教师" />
                  <el-table-column prop="classroom_name" label="上课教室" />
                  <el-table-column label="状态">
                    <template #default="{ row }">出勤率 {{ row.attendance_rate }}% ({{ row.attended_count }}/{{ row.student_count }})</template>
                  </el-table-column>
                  <el-table-column label="操作" width="150">
                    <template #default="{ row }">
                      <el-button link type="primary" size="small" @click="openEditSchedule(row)">编辑</el-button>
                      <el-button link type="danger" size="small" @click="handleDeleteSchedule(row)">删除</el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </el-tab-pane>
            </el-tabs>
          </div>

          <!-- 出勤表 Tab -->
          <div v-if="activeTab === 'attendance'" class="attendance-content">
            <div class="attendance-toolbar">
              <el-date-picker v-model="attendanceMonth" type="month" placeholder="选择月份" value-format="YYYY-MM" @change="loadAttendanceData" />
              <el-button @click="exportAttendance">导出</el-button>
              <el-input v-model="attendanceSearch" placeholder="请输入学员姓名或手机号" clearable style="width:200px" />
            </div>
            <el-table :data="filteredAttendanceRecords" border>
              <el-table-column label="学员" width="140" fixed="left">
                <template #default="{ row }">
                  <div class="student-info-cell">
                    <AppImage :src="row.avatar" :size="28" shape="circle" />
                    <span class="student-name">{{ row.name }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="phone" label="手机号" width="120" />
              <el-table-column v-for="day in attendanceDays" :key="day.date" :label="day.label" width="100">
                <template #default="{ row }">
                  <div v-if="row.attendance[day.date]" class="attendance-cell">
                    <span :class="getAttendanceClass(row.attendance[day.date])">{{ getAttendanceText(row.attendance[day.date]) }}</span>
                  </div>
                  <div v-else>-</div>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </div>
    </div>

    <!-- 编辑排课弹窗 -->
    <el-dialog v-model="editScheduleDialogVisible" title="编辑排课" width="500px">
      <el-form :model="editScheduleForm" label-width="100px">
        <el-form-item label="上课日期">
          <el-date-picker v-model="editScheduleForm.course_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" style="width:100%" />
        </el-form-item>
        <el-form-item label="开始时间">
          <TimePicker v-model="editScheduleForm.start_time" placeholder="选择时间" />
        </el-form-item>
        <el-form-item label="单次时长(分钟)">
          <el-input-number v-model="editScheduleForm.duration" :min="1" :step="30" controls-position="right" style="width:100%" />
        </el-form-item>
        <el-form-item label="任课教师">
          <el-select v-model="editScheduleForm.teacher_id" placeholder="选择老师" clearable>
            <el-option v-for="t in teachers" :key="t.id" :label="t.name" :value="Number(t.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="上课教室">
          <el-select v-model="editScheduleForm.classroom_id" placeholder="选择教室" clearable>
            <el-option v-for="c in classrooms" :key="c.id" :label="c.name" :value="Number(c.id)" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editScheduleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmEditSchedule" :loading="editScheduleLoading">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'
import TimePicker from '@/components/TimePicker.vue'
import { getClassDetail, updateClass, deleteClass, closeClass, getClassStudents, getClassSchedules, getClassAttendance, updateSchedule, deleteSchedule } from '@/api/class'
import { getCourseListSimple, getEnabledTeachers, getClassroomList } from '@/api/basic'
import { getCourseStages } from '@/api/course'
import dayjs from 'dayjs'
import { DEFAULT_AVATAR_SVG } from '@/utils/constants'

const route = useRoute()
const router = useRouter()
const classId = ref(route.params.id)
const activeTab = ref(route.query.tab || 'info')
const scheduleSubTab = ref('upcoming')
const editing = ref(false)

const tabs = [
  { name: 'info', label: '信息' },
  { name: 'students', label: '学员' },
  { name: 'schedule', label: '课表' },
  { name: 'attendance', label: '出勤表' }
]

// 数据
const classInfo = reactive({
  name: '',
  course_id: null,
  stage_id: null,
  stage_name: '',
  teacher_id: null,
  classroom_id: null,
  duration: 0,
  deduct_hours: 0,
  unit_price: null,
  student_count: 0,
  remark: '',
  status: 'active'
})

const courses = ref([])
const teachers = ref([])
const classrooms = ref([])
const stageOptions = ref([])

const students = ref([])
const studentSearch = ref('')
const upcomingSchedules = ref([])
const historySchedules = ref([])
const attendanceMonth = ref(dayjs().format('YYYY-MM'))
const attendanceSearch = ref('')
const attendanceData = ref([])

// 排课编辑
const editScheduleDialogVisible = ref(false)
const editScheduleLoading = ref(false)
const currentEditSchedule = ref(null)
const editScheduleForm = reactive({
  schedule_id: null,
  course_date: '',
  start_time: '',
  duration: 60,
  teacher_id: null,
  classroom_id: null
})

// 计算属性
const filteredStudents = computed(() => {
  if (!studentSearch.value) return students.value
  return students.value.filter(s => s.name.includes(studentSearch.value) || s.phone.includes(studentSearch.value))
})

const attendanceDays = computed(() => {
  if (!attendanceMonth.value) return []
  const daysInMonth = dayjs(attendanceMonth.value).daysInMonth()
  const month = dayjs(attendanceMonth.value)
  const days = []
  for (let i = 1; i <= daysInMonth; i++) {
    days.push({
      date: month.date(i).format('YYYY-MM-DD'),
      label: month.date(i).format('MM-DD')
    })
  }
  return days
})

const filteredAttendanceRecords = computed(() => {
  if (!attendanceSearch.value) return attendanceData.value
  return attendanceData.value.filter(r => r.name.includes(attendanceSearch.value) || r.phone.includes(attendanceSearch.value))
})

// 辅助方法
function getCourseName(id) {
  const c = courses.value.find(c => c.id === id)
  return c ? c.name : ''
}

function getTeacherName(id) {
  const t = teachers.value.find(t => t.id === id)
  return t ? t.name : ''
}

function getClassroomName(id) {
  const r = classrooms.value.find(r => r.id === id)
  return r ? r.name : ''
}

function formatScheduleTime(row) {
  if (!row.course_date) return ''
  const d = dayjs(row.course_date)
  const weekday = ['日', '一', '二', '三', '四', '五', '六'][d.day()]
  return `${d.format('YYYY-MM-DD')}（周${weekday}）${row.start_time}~${row.end_time}`
}

// ★ 课程变更时加载课阶
async function onCourseChangeForEdit(courseId) {
  stageOptions.value = []
  if (!courseId) return
  try {
    const res = await getCourseStages(courseId, { is_active: true })
    stageOptions.value = res.data || []
    // 如果当前没有选中课阶，或选中课阶不在新列表中，清空
    if (classInfo.stage_id && !stageOptions.value.some(s => s.id === classInfo.stage_id)) {
      classInfo.stage_id = null
    }
  } catch (e) {
    console.error('加载课阶失败', e)
  }
}

// 加载班级信息
async function loadClassInfo() {
  try {
    const res = await getClassDetail(classId.value)
    if (res.code === 0) {
      const data = res.data
      Object.assign(classInfo, data)
      // 加载课阶选项
      if (data.course_id) {
        await onCourseChangeForEdit(data.course_id)
      }
    }
  } catch {
    ElMessage.error('加载班级信息失败')
  }
}

// 更新信息
async function updateInfo() {
  try {
    const data = {
      name: classInfo.name,
      course_id: classInfo.course_id,
      stage_id: classInfo.stage_id,
      teacher_id: classInfo.teacher_id,
      classroom_id: classInfo.classroom_id,
      duration: classInfo.duration,
      deduct_hours: classInfo.deduct_hours,
      unit_price: classInfo.unit_price,
      remark: classInfo.remark
    }
    await updateClass(classId.value, data)
    ElMessage.success('保存成功')
    editing.value = false
    await loadClassInfo()
  } catch {
    ElMessage.error('保存失败')
  }
}

function enableEdit() {
  editing.value = true
}

function cancelEdit() {
  editing.value = false
  loadClassInfo()
}

// 学员相关
async function loadStudents() {
  try {
    const res = await getClassStudents(classId.value)
    students.value = (res.data || []).map(s => ({
      ...s,
      remaining_hours: s.remaining_hours || 0,
      remaining_amount: s.remaining_amount || 0,
      validity_date: s.validity_date || '-',
      used_leaves: s.used_leaves || 0,
      total_leaves: s.total_leaves === '不限' ? 999 : (parseInt(s.total_leaves) || 0)
    }))
  } catch {
    students.value = []
  }
}

function addStudent() {
  ElMessage.info('添加学员功能开发中')
}

function leaveStudent(row) {
  ElMessage.info(`为 ${row.name} 请假`)
}

function removeStudent(row) {
  ElMessage.info(`将 ${row.name} 退班`)
}

// 课表相关
async function loadSchedules() {
  try {
    const res = await getClassSchedules(classId.value)
    if (res.code === 0) {
      upcomingSchedules.value = res.data?.upcoming || []
      historySchedules.value = res.data?.history || []
    }
  } catch {
    upcomingSchedules.value = []
    historySchedules.value = []
  }
}

async function openEditSchedule(row) {
  if (!teachers.value.length) {
    const teacherRes = await getEnabledTeachers()
    teachers.value = teacherRes.data || []
  }
  if (!classrooms.value.length) {
    const classroomRes = await getClassroomList()
    classrooms.value = (classroomRes.data || []).filter(r => r.is_enabled !== false)
  }

  currentEditSchedule.value = row
  editScheduleForm.schedule_id = row.schedule_id
  editScheduleForm.course_date = row.course_date
  editScheduleForm.start_time = row.start_time
  editScheduleForm.duration = row.duration || 60
  editScheduleForm.teacher_id = row.teacher_id ? Number(row.teacher_id) : null
  editScheduleForm.classroom_id = row.classroom_id ? Number(row.classroom_id) : null
  editScheduleDialogVisible.value = true
}

async function confirmEditSchedule() {
  if (!editScheduleForm.schedule_id) return
  editScheduleLoading.value = true
  try {
    await updateSchedule(editScheduleForm.schedule_id, {
      course_date: editScheduleForm.course_date,
      start_time: editScheduleForm.start_time,
      duration: editScheduleForm.duration,
      teacher_id: editScheduleForm.teacher_id || null,
      classroom_id: editScheduleForm.classroom_id || null
    })
    ElMessage.success('更新成功')
    editScheduleDialogVisible.value = false
    await loadSchedules()
  } catch {
    ElMessage.error('更新失败')
  } finally {
    editScheduleLoading.value = false
  }
}

async function handleDeleteSchedule(row) {
  try {
    await ElMessageBox.confirm('确认删除该排课？', '提示', { type: 'warning' })
    await deleteSchedule(row.schedule_id)
    ElMessage.success('删除成功')
    await loadSchedules()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('删除失败')
  }
}

// 出勤表相关
async function loadAttendanceData() {
  try {
    const res = await getClassAttendance(classId.value, { month: attendanceMonth.value })
    const studentsRes = await getClassStudents(classId.value)
    const avatarMap = {}
    ;(studentsRes.data || []).forEach(s => {
      avatarMap[s.student_id] = s.avatar || DEFAULT_AVATAR_SVG
    })
    attendanceData.value = (res.data || []).map(item => ({
      ...item,
      avatar: avatarMap[item.student_id] || DEFAULT_AVATAR_SVG
    }))
  } catch {
    attendanceData.value = []
  }
}

function exportAttendance() {
  if (!filteredAttendanceRecords.value.length) {
    ElMessage.warning('无数据可导出')
    return
  }
  const wsData = filteredAttendanceRecords.value.map(row => {
    const record = { '学员姓名': row.name, '手机号': row.phone }
    attendanceDays.value.forEach(day => {
      const status = row.attendance[day.date]
      let text = status === '出勤' ? '出勤\n-1课时' : (status === '请假' ? '请假\n0课时' : (status === '未到' ? '未到\n-1课时' : '-'))
      record[day.label] = text
    })
    return record
  })
  const ws = XLSX.utils.json_to_sheet(wsData)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, '出勤表')
  XLSX.writeFile(wb, `出勤表_${attendanceMonth.value}.xlsx`)
  ElMessage.success('导出成功')
}

function getAttendanceClass(status) {
  if (status === '出勤') return 'attendance-present'
  if (status === '请假') return 'attendance-leave'
  if (status === '未到') return 'attendance-absent'
  return ''
}

function getAttendanceText(status) {
  return status === '出勤' ? '出勤\n-1课时' : (status === '请假' ? '请假\n0课时' : (status === '未到' ? '未到\n-1课时' : status))
}

// ★ 修改删除和结课方法，跳转后刷新列表
async function handleDeleteClass() {
  try {
    await ElMessageBox.confirm('确认删除该班级？', '提示', { type: 'warning' })
    await deleteClass(classId.value)
    ElMessage.success('删除成功')
    router.push('/classes')
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('删除失败')
  }
}

async function handleCloseClass() {
  try {
    await ElMessageBox.confirm('确认结课？', '提示', { type: 'warning' })
    await closeClass(classId.value)
    ElMessage.success('已结课')
    router.push('/classes')
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('结课失败')
  }
}

// Tab切换
function onTabChange(tabName) {
  if (tabName === 'students') loadStudents()
  else if (tabName === 'schedule') loadSchedules()
  else if (tabName === 'attendance') loadAttendanceData()
}

// 初始化
onMounted(async () => {
  const [courseRes, teacherRes, classroomRes] = await Promise.all([
    getCourseListSimple(),
    getEnabledTeachers(),
    getClassroomList()
  ])
  courses.value = courseRes.data || []
  teachers.value = teacherRes.data || []
  classrooms.value = (classroomRes.data || []).filter(r => r.is_enabled !== false)

  await loadClassInfo()

  if (activeTab.value === 'students') loadStudents()
  else if (activeTab.value === 'schedule') loadSchedules()
  else if (activeTab.value === 'attendance') loadAttendanceData()
})
</script>

<style scoped>
.class-detail-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 0;
  overflow: hidden;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--surface);
  padding: 12px 20px;
  box-shadow: var(--shadow-sm);
  flex-shrink: 0;
}

.back-btn {
  font-size: 14px;
  color: var(--primary-color);
  padding: 0;
}

.title-divider {
  width: 1px;
  height: 16px;
  background: var(--gray-300);
}

.class-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.header-actions {
  margin-left: auto;
  display: flex;
  gap: 12px;
}

.class-detail-wrapper {
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

.class-detail {
  display: flex;
  height: 100%;
  background: var(--surface);
  border-radius: 0;
  overflow: hidden;
}

.vertical-tabs {
  width: 90px;
  background: transparent;
  border-right: 1px solid var(--border-color);
  flex-shrink: 0;
  overflow-y: auto;
}

.tab-item {
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  cursor: pointer;
  border-bottom: 1px solid var(--border-color);
  position: relative;
  transition: all 0.2s ease;
}

.tab-item:hover {
  background-color: var(--primary-bg);
  color: var(--primary-color);
}

.tab-item.active {
  background-color: var(--primary-bg);
  color: var(--primary-color);
  font-weight: 500;
}

.tab-item.active::after {
  content: '';
  position: absolute;
  right: 0;
  top: 0;
  width: 4px;
  height: 100%;
  background-color: var(--primary-color);
}

.tab-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  min-width: 0;
}

.info-panel {
  max-width: 600px;
}

.info-item {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  min-height: 40px;
}

.info-item .label {
  width: 110px;
  font-weight: 500;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.form-actions {
  margin-top: 24px;
  margin-left: 110px;
}

.save-btn {
  background-color: var(--primary-color);
  border-color: var(--primary-color);
  color: white;
}

.student-list-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}

.student-info-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.student-avatar {
  flex-shrink: 0;
}

.student-name {
  font-weight: 500;
}

.attendance-toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.attendance-cell span {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 4px;
  white-space: pre-line;
}

.attendance-present {
  background: rgba(77, 124, 168, 0.10);
  color: var(--info);
}

.attendance-leave {
  background: rgba(217, 150, 40, 0.14);
  color: var(--warning);
}

.attendance-absent {
  background: rgba(224, 82, 82, 0.12);
  color: var(--danger);
}

.schedule-tabs {
  height: 100%;
}

.schedule-tabs :deep(.el-tabs__content) {
  height: calc(100% - 60px);
}

.schedule-content {
  height: 100%;
}
</style>