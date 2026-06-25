<template>
  <div class="class-manage">
    <!-- 操作栏 -->
    <div class="action-bar">
      <div class="left-actions">
        <el-button type="primary" @click="openCreateDialog">+新建班级</el-button>
        <el-button>导出考勤表</el-button>
      </div>
      <div class="right-actions">
        <el-input
          v-model="searchKeyword"
          placeholder="请输入班级名称"
          clearable
          style="width:200px"
          @input="fetchList"
        />
        <el-select
          v-model="filters.teacherId"
          placeholder="老师"
          clearable
          style="width:140px; margin-left:8px"
          @change="fetchList"
        >
          <el-option v-for="t in teachers" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
        <el-select
          v-model="filters.stageId"
          placeholder="课阶"
          clearable
          style="width:140px; margin-left:8px"
          @change="fetchList"
        >
          <el-option v-for="s in allStages" :key="s.id" :label="s.name" :value="s.id" />
        </el-select>
      </div>
    </div>

    <el-table :data="tableData" v-loading="loading" border stripe style="width:100%" class="class-table">
      <el-table-column prop="name" label="班级" min-width="150">
        <template #default="{ row }">
          <el-link type="primary" class="class-name-link" @click="goToDetail(row.id)">{{ row.name }}</el-link>
        </template>
      </el-table-column>
      <el-table-column label="课程" min-width="120">
        <template #header>
          <div class="filter-header">
            <span>课程</span>
            <el-dropdown @command="(val) => filterBy('course_name', val)">
              <el-icon class="filter-icon"><ArrowDown /></el-icon>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item :command="null">全部</el-dropdown-item>
                  <el-dropdown-item v-for="c in courseOptions" :key="c" :command="c">{{ c }}</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </template>
        <template #default="{ row }">{{ row.course_name }}</template>
      </el-table-column>
      <el-table-column label="课阶" min-width="120">
        <template #header>
          <div class="filter-header">
            <span>课阶</span>
            <el-dropdown @command="(val) => filterBy('stage_name', val)">
              <el-icon class="filter-icon"><ArrowDown /></el-icon>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item :command="null">全部</el-dropdown-item>
                  <el-dropdown-item v-for="s in stageOptionsFilter" :key="s" :command="s">{{ s }}</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </template>
        <template #default="{ row }">{{ row.stage_name || '-' }}</template>
      </el-table-column>
      <el-table-column label="任课教师" min-width="120">
        <template #header>
          <div class="filter-header">
            <span>任课教师</span>
            <el-dropdown @command="(val) => filterBy('teacher_name', val)">
              <el-icon class="filter-icon"><ArrowDown /></el-icon>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item :command="null">全部</el-dropdown-item>
                  <el-dropdown-item v-for="t in teacherOptions" :key="t" :command="t">{{ t }}</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </template>
        <template #default="{ row }">{{ row.teacher_name }}</template>
      </el-table-column>
      <el-table-column prop="classroom_name" label="上课教室" min-width="120" />
      <el-table-column label="状态" min-width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
            {{ row.status === 'active' ? '未结课' : '已结课' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="student_count" label="学员数" min-width="80" />
      <el-table-column label="下次上课时间" min-width="220">
        <template #default="{ row }">{{ formatNextSessionTime(row.next_session_time, row.duration) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <div class="action-links">
            <el-button type="primary" link class="action-link" @click="openScheduleDrawer(row)">排课</el-button>
            <el-button type="primary" link class="action-link" @click="goToDetail(row.id, 'schedule')">课表</el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-box" v-if="total > pageSize">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="fetchList"
      />
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
import { ArrowDown } from '@element-plus/icons-vue'
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

.action-bar {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-3);
  padding: var(--space-4);
  background: var(--surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xs);
}

.left-actions { display: flex; gap: var(--space-3); }
.right-actions { display: flex; align-items: center; gap: var(--space-2); flex-wrap: wrap; }

.class-table {
  flex: 1;
  min-height: 0;
  overflow: auto;
  background: var(--surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xs);
}

.class-name-link { color: var(--brand-600); font-weight: 600; }
.class-name-link:hover { color: var(--brand-700); }

.filter-header { display: flex; align-items: center; gap: 4px; cursor: pointer; }
.filter-icon { font-size: 14px; color: var(--text-secondary); }

.action-links { display: flex; gap: var(--space-2); white-space: nowrap; }
.action-link { font-size: 14px; }

.pagination-box {
  flex-shrink: 0;
  display: flex;
  justify-content: flex-end;
  padding-top: var(--space-3);
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

.schedule-layout { display: flex; height: 100%; }
.schedule-left {
  width: 60%;
  border-right: 1px solid var(--border-light);
  padding: 0 var(--space-5);
  overflow-y: auto;
}
.schedule-left .schedule-title { margin-bottom: 14px; font-weight: 700; }
.schedule-right { flex: 1; padding: 0 var(--space-4); overflow-y: auto; }

.schedule-form { display: flex; flex-direction: column; gap: var(--space-4); }
.form-item-row { display: flex; gap: var(--space-4); }
.form-item-row .el-form-item { flex: 1; }

.schedule-list { margin-top: var(--space-4); }
.schedule-item { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid var(--border-light); }
.schedule-item:last-child { border-bottom: none; }
.schedule-item-left { display: flex; align-items: center; gap: var(--space-2); }
.schedule-item-right { display: flex; align-items: center; gap: var(--space-2); }

@media (max-width: 768px) {
  .schedule-layout { flex-direction: column; }
  .schedule-left { width: 100%; border-right: none; border-bottom: 1px solid var(--border-light); padding-bottom: var(--space-4); }
}
</style>
