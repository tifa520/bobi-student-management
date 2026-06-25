<template>
  <div class="class-manage bobi-page">
    <!-- 页面标题 -->
    <div class="bobi-page-title">
      <div>
        <h1>班级管理</h1>
        <p>查看和管理所有班级信息，进行排课与学员管理</p>
      </div>
    </div>

    <!-- 操作栏 -->
    <div class="bobi-toolbar">
      <div class="left-actions">
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>
          新建班级
        </el-button>
        <el-button>
          <el-icon><Download /></el-icon>
          导出考勤表
        </el-button>
      </div>
      <div class="right-actions">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索班级名称"
          clearable
          class="search-input"
          @input="fetchList"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select
          v-model="filters.teacherId"
          placeholder="任课教师"
          clearable
          class="filter-select"
          @change="fetchList"
        >
          <el-option v-for="t in teachers" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
        <el-select
          v-model="filters.stageId"
          placeholder="课阶筛选"
          clearable
          class="filter-select"
          @change="fetchList"
        >
          <el-option v-for="s in allStages" :key="s.id" :label="s.name" :value="s.id" />
        </el-select>
      </div>
    </div>

    <!-- 班级列表 -->
    <div class="table-section">
      <el-table :data="tableData" v-loading="loading" stripe style="width: 100%" class="class-table">
        <el-table-column prop="name" label="班级" min-width="180">
          <template #default="{ row }">
            <div class="class-cell">
              <div class="class-icon">
                <el-icon><School /></el-icon>
              </div>
              <div class="class-info">
                <el-link type="primary" class="class-name-link" @click="goToDetail(row.id)">{{ row.name }}</el-link>
                <span class="class-course">{{ row.course_name }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="课阶" min-width="120" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.stage_name" type="primary" size="small" effect="light">
              {{ row.stage_name }}
            </el-tag>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="任课教师" min-width="120" align="center">
          <template #default="{ row }">
            <div class="teacher-cell">
              <div class="teacher-avatar-sm">
                {{ row.teacher_name?.charAt(0) || '?' }}
              </div>
              <span>{{ row.teacher_name || '未分配' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="classroom_name" label="上课教室" min-width="120" align="center" />
        <el-table-column label="状态" min-width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small" effect="light">
              {{ row.status === 'active' ? '未结课' : '已结课' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="学员数" min-width="90" align="center">
          <template #default="{ row }">
            <span class="student-count">{{ row.student_count || 0 }}</span>
            <span class="count-unit">人</span>
          </template>
        </el-table-column>
        <el-table-column label="下次上课时间" min-width="220">
          <template #default="{ row }">
            <div v-if="row.next_session_time" class="next-session">
              <el-icon><Clock /></el-icon>
              <span>{{ formatNextSessionTime(row.next_session_time, row.duration) }}</span>
            </div>
            <span v-else class="text-muted">暂无排课</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button type="primary" link size="small" @click="openScheduleDrawer(row)">排课</el-button>
              <el-button type="primary" link size="small" @click="goToDetail(row.id, 'schedule')">详情</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper" v-if="total > pageSize">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="fetchList"
        />
      </div>
    </div>

    <!-- 新增班级弹窗 -->
    <el-dialog v-model="formVisible" title="新增班级" width="550px" :close-on-click-modal="false">
      <el-form :model="classForm" label-width="100px">
        <el-form-item label="所属课程">
          <el-select
            v-model="classForm.course_id"
            placeholder="选择课程"
            filterable
            style="width:100%"
            @change="onCourseChange"
          >
            <el-option v-for="c in courses" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="所属课阶">
          <el-select
            v-model="classForm.stage_id"
            placeholder="请先选择课程"
            clearable
            :disabled="!classForm.course_id"
            style="width:100%"
          >
            <el-option
              v-for="s in stageOptions"
              :key="s.id"
              :label="s.name"
              :value="s.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="班级名称">
          <el-input v-model="classForm.name" placeholder="请输入班级名称" />
        </el-form-item>
        <el-form-item label="任课教师">
          <el-select v-model="classForm.teacher_id" placeholder="选择老师" clearable style="width:100%">
            <el-option v-for="t in teachers" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="上课教室">
          <el-select v-model="classForm.classroom_id" placeholder="选择教室" clearable style="width:100%">
            <el-option v-for="r in classrooms" :key="r.id" :label="r.name" :value="r.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="classForm.remark" type="textarea" :rows="2" placeholder="选填" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" @click="saveClass" :loading="saving">确定</el-button>
      </template>
    </el-dialog>

    <!-- 排课抽屉 -->
    <el-drawer
      v-model="scheduleDrawerVisible"
      title="排课"
      direction="rtl"
      :size="drawerWidth"
      :modal="true"
      :close-on-click-modal="false"
      class="custom-drawer"
    >
      <div class="schedule-layout">
        <div class="schedule-left">
          <div class="schedule-title">已排课课表</div>
          <el-table :data="existingSchedules" border stripe style="width:100%">
            <el-table-column label="上课时间" min-width="180">
              <template #default="{ row }">{{ formatScheduleTimeWithWeekday(row.course_date, row.start_time, row.duration) }}</template>
            </el-table-column>
            <el-table-column prop="teacher_name" label="任课教师" />
            <el-table-column prop="classroom_name" label="上课教室" />
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button type="danger" link size="small" @click="handleDeleteSchedule(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div v-if="existingSchedules.length === 0" class="empty-tip">暂无排课</div>
        </div>
        <div class="schedule-right">
          <div class="schedule-form">
            <div class="form-item-row">
              <div class="form-label">班级</div>
              <div class="form-value">{{ currentScheduleClass?.name }}（{{ currentScheduleClass?.course_name }}）</div>
            </div>
            <div class="form-item-row">
              <div class="form-label">所属课阶</div>
              <div class="form-value">{{ currentScheduleClass?.stage_name || '-' }}</div>
            </div>
            <div class="form-item-row">
              <div class="form-label">单次时长</div>
              <div class="form-value">{{ courseDuration }}分钟</div>
            </div>
            <div class="form-item-vertical date-item">
              <div class="form-label">排课日期（多选）</div>
              <div class="static-calendar">
                <el-calendar v-model="calendarValue" :first-day-of-week="1">
                  <template #date-cell="{ data }">
                    <div
                      class="calendar-cell"
                      :class="{
                        'is-selected': isDateSelected(data.day),
                        'non-current': data.type === 'prev-month' || data.type === 'next-month'
                      }"
                      @click="toggleDate(data.day)"
                    >
                      {{ data.day.split('-')[2] }}
                    </div>
                  </template>
                </el-calendar>
              </div>
              <div class="date-select-info">
                <div v-if="selectedDates.length" class="selected-dates">
                  <div class="selected-label">已选日期：</div>
                  <div class="selected-list">
                    <el-tag v-for="date in selectedDates" :key="date" closable size="small" @close="removeDate(date)" style="margin-right:8px">
                      {{ formatDateDisplay(date) }}
                    </el-tag>
                  </div>
                </div>
                <div v-else class="calendar-tip">请点击日历中的日期进行多选</div>
              </div>
            </div>
            <div class="form-item-row">
              <div class="form-label">上课时间</div>
              <div class="time-input-group">
                <TimePicker v-model="startTime" placeholder="选择开始时间" />
                <span v-if="startTime && courseDuration" class="time-range">
                  {{ startTime }} ~ {{ endTimeDisplay }}
                </span>
              </div>
            </div>

            <!-- 已删除任课教师和上课教室下拉框，直接使用班级设置 -->

            <div class="form-actions">
              <el-button @click="scheduleDrawerVisible = false">取消</el-button>
              <el-button type="primary" @click="saveSchedule" :loading="scheduleSaving">确定</el-button>
            </div>
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onActivated, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Download, Search, School, Clock } from '@element-plus/icons-vue'
import TimePicker from '@/components/TimePicker.vue'
// ★ 修复：添加 createSchedule 导入
import { getClassList, createClass, getClassSchedules, deleteSchedule, createSchedule } from '@/api/class'
import { getCourseListSimple, getClassroomList, getEnabledTeachers } from '@/api/basic'
import { getCourseStages } from '@/api/course'
import dayjs from 'dayjs'

const router = useRouter()

// ========== 列表数据 ==========
const loading = ref(false)
const tableData = ref([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchKeyword = ref('')
const filters = reactive({
  teacherId: null,
  courseName: null,
  teacherName: null,
  stageName: null,
  stageId: null
})

const teachers = ref([])
const courses = ref([])
const classrooms = ref([])
const allStages = ref([])

const courseOptions = computed(() => [...new Set(tableData.value.map(c => c.course_name).filter(Boolean))])
const teacherOptions = computed(() => [...new Set(tableData.value.map(c => c.teacher_name).filter(Boolean))])
const stageOptionsFilter = computed(() => [...new Set(tableData.value.map(c => c.stage_name).filter(Boolean))])

// ========== 课阶相关 ==========
const stageOptions = ref([])

// ========== 班级表单 ==========
const formVisible = ref(false)
const saving = ref(false)
const classForm = reactive({
  name: '',
  course_id: null,
  stage_id: null,
  teacher_id: null,
  classroom_id: null,
  remark: '',
  duration: null,
  deduct_hours: null,
  unit_price: null
})

// ========== 排课抽屉 ==========
const scheduleDrawerVisible = ref(false)
const currentScheduleClass = ref(null)
const existingSchedules = ref([])
const scheduleSaving = ref(false)
const selectedDates = ref([])
const startTime = ref('')
const courseDuration = ref(0)
const calendarValue = ref(new Date())
const drawerWidth = computed(() => `calc(100% - 140px)`)

const endTimeDisplay = computed(() => {
  if (startTime.value && courseDuration.value) {
    return dayjs(`2000-01-01 ${startTime.value}`).add(courseDuration.value, 'minute').format('HH:mm')
  }
  return ''
})

// ========== 列表方法 ==========
async function fetchList() {
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value,
      search: searchKeyword.value,
      teacher_id: filters.teacherId,
      course_name: filters.courseName,
      teacher_name: filters.teacherName,
      stage_name: filters.stageName
    }
    const res = await getClassList(params)
    tableData.value = res.data?.items || res.data || []
    total.value = res.data?.total || tableData.value.length
  } catch {
    tableData.value = []
  } finally {
    loading.value = false
  }
}

function filterBy(field, value) {
  if (field === 'course_name') filters.courseName = value
  if (field === 'teacher_name') filters.teacherName = value
  if (field === 'stage_name') filters.stageName = value
  fetchList()
}

function goToDetail(id, tab = 'info') {
  router.push({ path: `/classes/${id}`, query: { tab } })
}

function formatNextSessionTime(timeStr, duration) {
  if (!timeStr) return '-'
  const d = dayjs(timeStr)
  const weekdays = ['日', '一', '二', '三', '四', '五', '六']
  return `${d.format('YYYY-MM-DD')}（周${weekdays[d.day()]}）${d.format('HH:mm')}~${d.add(duration, 'minute').format('HH:mm')}`
}

function formatScheduleTimeWithWeekday(date, time, duration) {
  if (!date || !time) return ''
  const d = dayjs(date)
  const weekdays = ['日', '一', '二', '三', '四', '五', '六']
  const end = dayjs(`2000-01-01 ${time}`).add(duration, 'minute').format('HH:mm')
  return `${date}（周${weekdays[d.day()]}）${time}~${end}`
}

function formatDateDisplay(dateStr) {
  return dayjs(dateStr).format('MM-DD')
}

function isDateSelected(dayStr) {
  return selectedDates.value.includes(dayStr)
}

function toggleDate(dayStr) {
  const idx = selectedDates.value.indexOf(dayStr)
  if (idx === -1) {
    selectedDates.value.push(dayStr)
  } else {
    selectedDates.value.splice(idx, 1)
  }
}

function removeDate(date) {
  selectedDates.value = selectedDates.value.filter(d => d !== date)
}

// ========== 新增班级 ==========
function resetClassForm() {
  Object.assign(classForm, {
    name: '',
    course_id: null,
    stage_id: null,
    teacher_id: null,
    classroom_id: null,
    remark: '',
    duration: null,
    deduct_hours: null,
    unit_price: null
  })
  stageOptions.value = []
}

function openCreateDialog() {
  resetClassForm()
  formVisible.value = true
}

async function onCourseChange(courseId) {
  classForm.stage_id = null
  stageOptions.value = []
  classForm.duration = null
  classForm.deduct_hours = null
  classForm.unit_price = null

  if (!courseId) return

  try {
    const res = await getCourseStages(courseId, { is_active: true })
    stageOptions.value = res.data || []
    if (stageOptions.value.length > 0) {
      const first = stageOptions.value[0]
      classForm.stage_id = first.id
      classForm.duration = first.duration
      classForm.deduct_hours = first.deduct_hours
      classForm.unit_price = first.unit_price
    }
  } catch (e) {
    stageOptions.value = []
  }
}

watch(() => classForm.stage_id, (newStageId) => {
  if (newStageId) {
    const stage = stageOptions.value.find(s => s.id === newStageId)
    if (stage) {
      classForm.duration = stage.duration
      classForm.deduct_hours = stage.deduct_hours
      classForm.unit_price = stage.unit_price
    }
  } else {
    classForm.duration = null
    classForm.deduct_hours = null
    classForm.unit_price = null
  }
})

async function saveClass() {
  if (!classForm.name || !classForm.course_id) {
    ElMessage.warning('请填写班级名称和所属课程')
    return
  }

  saving.value = true
  try {
    const submitData = {
      name: classForm.name,
      course_id: classForm.course_id,
      stage_id: classForm.stage_id || null,
      teacher_id: classForm.teacher_id || null,
      classroom_id: classForm.classroom_id || null,
      remark: classForm.remark || '',
      duration: classForm.duration,
      deduct_hours: classForm.deduct_hours,
      unit_price: classForm.unit_price
    }

    await createClass(submitData)
    ElMessage.success('创建成功')
    formVisible.value = false
    fetchList()
  } catch (error) {
    const msg = error.response?.data?.detail || '创建失败'
    ElMessage.error(msg)
  } finally {
    saving.value = false
  }
}

// ========== 排课 ==========
async function openScheduleDrawer(row) {
  if (!row.course_id) {
    ElMessage.error('班级数据异常：缺少课程ID')
    return
  }

  currentScheduleClass.value = row
  courseDuration.value = row.duration || 60

  selectedDates.value = []
  startTime.value = ''
  calendarValue.value = new Date()

  await loadExistingSchedules(row.id)
  scheduleDrawerVisible.value = true
}

async function loadExistingSchedules(classId) {
  try {
    const res = await getClassSchedules(classId)
    existingSchedules.value = (res.data?.upcoming || res.data || [])
  } catch {
    existingSchedules.value = []
  }
}

// ★ 修复：saveSchedule 中使用已导入的 createSchedule
async function saveSchedule() {
  if (!selectedDates.value.length) {
    ElMessage.warning('请至少选择一个上课日期')
    return
  }
  if (!startTime.value) {
    ElMessage.warning('请选择上课时间')
    return
  }

  // 直接从当前班级信息中获取教师和教室
  const teacherId = currentScheduleClass.value?.teacher_id
  const classroomId = currentScheduleClass.value?.classroom_id

  scheduleSaving.value = true
  try {
    const datesStr = selectedDates.value.join(',')
    const params = {
      dates: datesStr,
      start_time: startTime.value,
      duration: courseDuration.value,
      teacher_id: teacherId || null,
      classroom_id: classroomId || null
    }
    const res = await createSchedule(currentScheduleClass.value.id, params)
    if (res.code !== 0) {
      throw new Error(res.message || '排课失败')
    }
    ElMessage.success(`成功排课 ${selectedDates.value.length} 天`)
    scheduleDrawerVisible.value = false
    fetchList()
  } catch (error) {
    console.error('排课失败详细错误:', error)
    const msg = error.response?.data?.detail || error.message || '排课失败，请检查日期是否冲突或参数是否正确'
    ElMessage.error(msg)
  } finally {
    scheduleSaving.value = false
  }
}

async function handleDeleteSchedule(row) {
  try {
    await ElMessageBox.confirm('确认删除该排课？', '提示', { type: 'warning' })
    await deleteSchedule(row.schedule_id)
    ElMessage.success('删除成功')
    await loadExistingSchedules(currentScheduleClass.value.id)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// ========== 生命周期 ==========
onMounted(async () => {
  const [courseRes, teacherRes, classroomRes] = await Promise.all([
    getCourseListSimple(),
    getEnabledTeachers(),
    getClassroomList()
  ])
  courses.value = courseRes.data || []
  teachers.value = teacherRes.data || []
  classrooms.value = (classroomRes.data || []).filter(r => r.is_enabled !== false)

  try {
    const allCourses = courses.value
    const stagePromises = allCourses.map(c => getCourseStages(c.id, { is_active: true }))
    const results = await Promise.all(stagePromises)
    const stages = results.flatMap(r => r.data || [])
    allStages.value = stages
  } catch (e) {
    console.error('加载课阶失败', e)
  }

  fetchList()
})

onActivated(() => {
  fetchList()
})
</script>


<style scoped>
.class-manage {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.left-actions {
  display: flex;
  gap: var(--space-3);
}

.right-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.search-input {
  width: 240px;
}

.filter-select {
  width: 140px;
}

.class-table {
  border-radius: 0;
  border: none;
}

.class-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.class-icon {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--brand-300), var(--brand-500));
  color: #fff;
  font-size: 20px;
  border-radius: var(--radius-lg);
  box-shadow: 0 4px 12px rgba(30, 168, 82, 0.25);
}

.class-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.class-name-link {
  font-weight: 700;
  font-size: 14px;
}

.class-course {
  font-size: 12px;
  color: var(--text-secondary);
}

.teacher-cell {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.teacher-avatar-sm {
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--gold-300), var(--gold-500));
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  border-radius: 50%;
}

.student-count {
  font-weight: 700;
  font-size: 16px;
  color: var(--brand-600);
  font-family: var(--font-mono);
}

.count-unit {
  font-size: 12px;
  color: var(--text-secondary);
  margin-left: 2px;
}

.next-session {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-regular);
}

.next-session .el-icon {
  color: var(--brand-500);
}

.action-buttons {
  display: flex;
  gap: var(--space-1);
  justify-content: center;
  align-items: center;
}

.pagination-wrapper {
  padding: 14px 20px;
  border-top: 1px solid var(--border-light);
  background: var(--surface-soft);
  display: flex;
  justify-content: flex-end;
}

.custom-drawer :deep(.el-drawer) {
  width: calc(100% - 140px);
  left: 140px;
  right: auto;
  max-width: none;
}

.custom-drawer :deep(.el-drawer__header) {
  margin-bottom: 0;
}

.schedule-layout {
  display: flex;
  height: 100%;
}

.schedule-left {
  width: 60%;
  border-right: 1px solid var(--border-light);
  padding: 0 var(--space-5);
  overflow-y: auto;
}

.schedule-left .schedule-title {
  margin-bottom: 14px;
  font-weight: 700;
  font-size: 15px;
  font-family: var(--font-display);
}

.schedule-right {
  flex: 1;
  padding: 0 var(--space-4);
  overflow-y: auto;
}

.schedule-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.form-item-row {
  display: flex;
  gap: var(--space-4);
}

.form-item-row .el-form-item {
  flex: 1;
}

@media (max-width: 768px) {
  .schedule-layout {
    flex-direction: column;
  }
  .schedule-left {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid var(--border-light);
    padding-bottom: var(--space-4);
  }
  .search-input,
  .filter-select {
    width: 100%;
  }
  .left-actions,
  .right-actions {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
