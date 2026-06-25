<template>
  <div class="student-list">
    <!-- 操作栏 -->
    <div class="action-bar">
      <div class="left-actions">
        <el-button type="primary" @click="quickEnroll">新生快速报名</el-button>
        <el-button type="primary" @click="openImportDialog">学员导入</el-button>
        <el-button type="primary" @click="handleExportStudents">学员导出</el-button>
        <div class="filter-link" @click="showFilterPanel = !showFilterPanel">
          <span>筛选</span>
          <el-icon><ArrowDown /></el-icon>
        </div>
      </div>
      <div class="right-actions">
        <el-input
          v-model="filters.student_name"
          placeholder="学员姓名"
          clearable
          class="search-input"
          @input="handleFilterChange"
        />
        <el-input
          v-model="filters.student_phone"
          placeholder="手机号"
          clearable
          class="search-input"
          @input="handleFilterChange"
        />
      </div>
    </div>

    <!-- 筛选面板 -->
    <div v-show="showFilterPanel" class="filter-panel">
      <el-row :gutter="16">
        <el-col :xs="24" :sm="12" :md="8" :lg="6" :xl="6">
          <div class="filter-item">
            <label>生日月份</label>
            <el-select v-model="filters.birth_month" clearable placeholder="请选择" size="default" @change="handleFilterChange">
              <el-option v-for="m in 12" :key="m" :label="m + '月'" :value="m" />
            </el-select>
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="8" :lg="6" :xl="6">
          <div class="filter-item">
            <label>年龄范围</label>
            <div class="range-input">
              <el-input-number v-model="filters.age_min" :min="0" :max="100" placeholder="最小值" :controls="false" size="default" @change="handleFilterChange" />
              <span>~</span>
              <el-input-number v-model="filters.age_max" :min="0" :max="100" placeholder="最大值" :controls="false" size="default" @change="handleFilterChange" />
            </div>
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="8" :lg="6" :xl="6">
          <div class="filter-item">
            <label>报名课程</label>
            <el-select v-model="filters.course_name" clearable filterable placeholder="请选择" size="default" @change="handleFilterChange">
              <el-option v-for="c in courseOptions" :key="c.id" :label="c.name" :value="c.name" />
            </el-select>
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="8" :lg="6" :xl="6">
          <div class="filter-item">
            <label>报名班级</label>
            <el-select v-model="filters.class_name" clearable filterable placeholder="请选择" size="default" @change="handleFilterChange">
              <el-option v-for="c in classOptions" :key="c.name" :label="c.name" :value="c.name" />
            </el-select>
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="8" :lg="6" :xl="6">
          <div class="filter-item">
            <label>任课教师</label>
            <el-select v-model="filters.teacher_name" clearable filterable placeholder="请选择" size="default" @change="handleFilterChange">
              <el-option v-for="t in teacherOptions" :key="t.id" :label="t.name" :value="t.name" />
            </el-select>
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="8" :lg="6" :xl="6">
          <div class="filter-item">
            <label>是否停课</label>
            <el-select v-model="filters.is_suspended" clearable placeholder="请选择" size="default" @change="handleFilterChange">
              <el-option label="是" :value="true" />
              <el-option label="否" :value="false" />
            </el-select>
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="8" :lg="6" :xl="6">
          <div class="filter-item">
            <label>是否分班</label>
            <el-select v-model="filters.has_class" clearable placeholder="请选择" size="default" @change="handleFilterChange">
              <el-option label="已分班" :value="true" />
              <el-option label="未分班" :value="false" />
            </el-select>
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="8" :lg="6" :xl="6">
          <div class="filter-item">
            <label>剩余课时范围</label>
            <div class="range-input">
              <el-input-number v-model="filters.remaining_hours_min" :min="0" placeholder="最小值" :controls="false" size="default" @change="handleFilterChange" />
              <span>~</span>
              <el-input-number v-model="filters.remaining_hours_max" :min="0" placeholder="最大值" :controls="false" size="default" @change="handleFilterChange" />
            </div>
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="8" :lg="6" :xl="6">
          <div class="filter-item">
            <label>剩余有效期天数</label>
            <div class="range-input">
              <el-input-number v-model="filters.validity_days_min" :min="0" placeholder="最小值" :controls="false" size="default" @change="handleFilterChange" />
              <span>~</span>
              <el-input-number v-model="filters.validity_days_max" :min="0" placeholder="最大值" :controls="false" size="default" @change="handleFilterChange" />
            </div>
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="8" :lg="6" :xl="6">
          <div class="filter-item">
            <label>请假次数范围</label>
            <div class="range-input">
              <el-input-number v-model="filters.leave_count_min" :min="0" placeholder="最小值" :controls="false" size="default" @change="handleFilterChange" />
              <span>~</span>
              <el-input-number v-model="filters.leave_count_max" :min="0" placeholder="最大值" :controls="false" size="default" @change="handleFilterChange" />
            </div>
          </div>
        </el-col>
      </el-row>
      <div class="filter-actions">
        <el-button type="primary" @click="applyFilters" size="small">应用筛选</el-button>
        <el-button @click="resetFilters" size="small">重置</el-button>
      </div>
    </div>

    <!-- 卡片网格 -->
    <div class="cards-container" v-loading="loading">
      <div class="cards-grid">
        <div
          v-for="student in studentList"
          :key="student.id"
          class="student-card"
          @mouseenter="onCardHover(student.id, true)"
          @mouseleave="onCardHover(student.id, false)"
          @click="goToDetail(student.id)"
        >
          <!-- 背景图层（铺满整个卡片） -->
          <!-- ★★★ 内联样式，直接使用 student.card_background（后端保证完整 /media/ URL） ★★★ -->
          <div
            class="card-bg"
            :style="{
              backgroundImage: student.card_background
                ? `url(${student.card_background})`
                : (
                    student.gender === '男'
                      ? 'linear-gradient(135deg, #EAE5C9 0%, #6CC6CB 100%)'
                      : student.gender === '女'
                        ? 'linear-gradient(135deg, #CCFBFF 0%, #EF96C5 100%)'
                        : 'linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 50%, #a5d6a7 100%)'
                  ),
              backgroundSize: 'cover',
              backgroundPosition: 'center'
            }"
          ></div>

          <!-- 卡片覆盖层 -->
          <div class="card-overlay">
            <!-- 顶部信息栏 -->
            <div class="card-top">
              <span class="top-left">有效期：{{ currentCourse(student).validity_display || '无' }}</span>
              <span class="top-right">{{ currentCourse(student).course_name }}</span>
            </div>

            <!-- 中间超大剩余课时数 -->
            <div class="center-hours">
              {{ currentCourse(student).remaining_hours }}
            </div>

            <!-- ★★★ 切换按钮：卡片左右边缘中间位置 ★★★ -->
            <div v-if="student.courses.length > 1" class="course-nav-wrapper">
              <el-button
                class="nav-btn nav-btn-left"
                size="small"
                circle
                @click.stop="switchCourse(student, -1)"
              >
                <el-icon><ArrowLeft /></el-icon>
              </el-button>
              <el-button
                class="nav-btn nav-btn-right"
                size="small"
                circle
                @click.stop="switchCourse(student, 1)"
              >
                <el-icon><ArrowRight /></el-icon>
              </el-button>
            </div>

            <!-- 底部毛玻璃区域 -->
            <div class="glass-area">
              <div class="glass-content">
                <!-- 左侧：头像 + 姓名/年龄 -->
                <div class="user-info">
                  <!-- ★★★ AppImage 直接使用 student.avatar（后端保证完整 /media/ URL） ★★★ -->
                  <AppImage :src="student.avatar" :size="42" shape="circle" class="user-avatar" />
                  <div class="user-detail">
                    <span class="user-name">{{ student.name }}</span>
                    <span class="user-age">{{ student.age !== null && student.age !== undefined ? student.age + '岁' : '未知岁' }}</span>
                  </div>
                </div>
                <!-- 右侧：积分 -->
                <span class="integral-value">{{ student.total_integral }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-if="studentList.length === 0 && !loading" class="empty-state">
          <el-empty description="暂无学员数据" />
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination-box" v-if="total > pageSize">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="fetchData"
      />
    </div>

    <!-- 导入模态框 -->
    <el-dialog v-model="importDialogVisible" title="导入学员" width="540px" :close-on-click-modal="false">
      <div class="import-content">
        <div class="upload-area">
          <el-upload
            class="upload-demo"
            drag
            :action="uploadUrl"
            :headers="uploadHeaders"
            :on-success="handleImportSuccess"
            :on-error="handleImportError"
            accept=".xlsx,.xls"
            :show-file-list="false"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">上传文件</div>
            <div class="el-upload__tip">仅支持导入EXCEL文件</div>
          </el-upload>
        </div>
        <div class="import-notice">
          <p>注意：只有使用系统前机构已有的学员才有此方式进行导入</p>
          <p>新学员报名请在招生管理进行报名</p>
          <p>这里导入的学员不会增加校区报名人数和收入哦</p>
        </div>
        <div class="import-template">
          <el-button class="template-btn" @click="downloadTemplate">
            <el-icon><Download /></el-icon> 下载模板
          </el-button>
          <div class="template-tip">按照模版格式将学员信息录入EXCEL表格中</div>
        </div>
      </div>
    </el-dialog>

    <!-- 课程切换弹窗 -->
    <teleport to="body">
      <div
        v-if="activePopoverStudent"
        class="course-switch-popover"
        :style="popoverStyle"
        @click.stop
      >
        <div class="course-switch-menu">
          <div
            v-for="course in activePopoverStudent.courses"
            :key="course.course_id"
            class="course-option"
            :class="{ active: currentCourse(activePopoverStudent).course_id === course.course_id }"
            @click="switchCourse(activePopoverStudent, course)"
          >
            <div class="course-name">{{ course.course_name }}</div>
            <div class="class-name" v-if="course.class_name !== '未分班'">({{ course.class_name }})</div>
          </div>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElLoading } from 'element-plus'
import { ArrowDown, UploadFilled, Download, Phone, ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import { getCourseListSimple, getTeacherList, getClassList } from '@/api/basic'
import { exportStudents, downloadImportTemplate } from '@/api/student'
import { useStudentStore } from '@/stores/student'
import { storeToRefs } from 'pinia'

const router = useRouter()
const route = useRoute()

// ========== 使用 Pinia Store ==========
const studentStore = useStudentStore()
const { students: studentList, total, loading } = storeToRefs(studentStore)

// ========== 本地状态 ==========
const currentPage = ref(1)
const pageSize = ref(36)
const showFilterPanel = ref(false)
const activePopoverStudent = ref(null)
const popoverStyle = ref({})

const filters = reactive({
  student_name: '',
  student_phone: '',
  birth_month: null,
  age_min: null,
  age_max: null,
  course_name: null,
  class_name: null,
  teacher_name: null,
  is_suspended: null,
  has_class: null,
  remaining_hours_min: null,
  remaining_hours_max: null,
  validity_days_min: null,
  validity_days_max: null,
  leave_count_min: null,
  leave_count_max: null
})

const courseOptions = ref([])
const teacherOptions = ref([])
const classOptions = ref([])
const importDialogVisible = ref(false)
const uploadUrl = '/api/student/students/import'
const uploadHeaders = {}

// ========== ★★★ 多课程轮播相关 ★★★ ==========
const courseIndexMap = ref({})
const timersMap = ref({})
const hoveredStudentId = ref(null)

function getCourseIndex(studentId) {
  if (!(studentId in courseIndexMap.value)) {
    courseIndexMap.value[studentId] = 0
  }
  return courseIndexMap.value[studentId]
}

function setCourseIndex(studentId, index) {
  const student = studentList.value.find(s => s.id === studentId)
  if (!student) return
  const courses = student.courses || []
  if (courses.length === 0) return
  const maxIndex = courses.length - 1
  if (index < 0) index = maxIndex
  if (index > maxIndex) index = 0
  courseIndexMap.value[studentId] = index
  resetTimer(studentId)
}

function switchCourse(student, directionOrCourse) {
  if (typeof directionOrCourse === 'number') {
    const studentId = student.id
    const currentIdx = getCourseIndex(studentId)
    const newIdx = currentIdx + directionOrCourse
    setCourseIndex(studentId, newIdx)
  } else {
    const studentId = student.id
    const courses = student.courses || []
    const idx = courses.findIndex(c => c.course_id === directionOrCourse.course_id)
    if (idx !== -1) {
      setCourseIndex(studentId, idx)
    }
  }
}

function resetTimer(studentId) {
  clearTimer(studentId)
  const student = studentList.value.find(s => s.id === studentId)
  if (!student) return
  const courses = student.courses || []
  if (courses.length <= 1) return
  const timer = setInterval(() => {
    if (hoveredStudentId.value === studentId) return
    const currentIdx = getCourseIndex(studentId)
    const nextIdx = (currentIdx + 1) % courses.length
    courseIndexMap.value[studentId] = nextIdx
  }, 5000)
  timersMap.value[studentId] = timer
}

function clearTimer(studentId) {
  if (timersMap.value[studentId]) {
    clearInterval(timersMap.value[studentId])
    delete timersMap.value[studentId]
  }
}

function clearAllTimers() {
  Object.keys(timersMap.value).forEach(id => clearTimer(Number(id)))
}

function onCardHover(studentId, isHover) {
  if (isHover) {
    hoveredStudentId.value = studentId
  } else {
    if (hoveredStudentId.value === studentId) {
      hoveredStudentId.value = null
      resetTimer(studentId)
    }
  }
}

watch(studentList, (newList) => {
  clearAllTimers()
  courseIndexMap.value = {}
  newList.forEach(student => {
    if (student.courses && student.courses.length > 1) {
      courseIndexMap.value[student.id] = 0
      resetTimer(student.id)
    }
  })
}, { deep: true, immediate: false })

onUnmounted(() => {
  clearAllTimers()
})

function initCourseCarousel() {
  clearAllTimers()
  courseIndexMap.value = {}
  studentList.value.forEach(student => {
    if (student.courses && student.courses.length > 1) {
      courseIndexMap.value[student.id] = 0
      resetTimer(student.id)
    }
  })
}

// ========== 原辅助函数 ==========

function currentCourse(student) {
  const idx = getCourseIndex(student.id)
  const courses = student.courses || []
  return courses[idx] || courses[0] || {}
}

function showCourseMenu(event, student) {
  if (student.courses.length <= 1) return
  if (activePopoverStudent.value === student) {
    closePopover()
    return
  }
  const rect = event.currentTarget.getBoundingClientRect()
  popoverStyle.value = {
    position: 'fixed',
    top: `${rect.bottom + 6}px`,
    left: `${rect.left}px`,
    zIndex: 9999,
    minWidth: `${Math.max(rect.width, 160)}px`
  }
  activePopoverStudent.value = student
}

function closePopover() {
  activePopoverStudent.value = null
}

function handleClickOutside(event) {
  if (!activePopoverStudent.value) return
  const popover = document.querySelector('.course-switch-popover')
  if (popover && !popover.contains(event.target)) {
    let isTrigger = false
    const triggers = document.querySelectorAll('.course-class')
    triggers.forEach(trigger => {
      if (trigger.contains(event.target)) isTrigger = true
    })
    if (!isTrigger) closePopover()
  }
}

// ========== 数据获取 ==========
async function fetchData() {
  const params = {
    page: currentPage.value,
    page_size: pageSize.value,
    ...filters
  }
  Object.keys(params).forEach(key => {
    if (params[key] === null || params[key] === '' || params[key] === undefined) {
      delete params[key]
    }
  })
  await studentStore.fetchStudents(params)
  // ★★★ 无需转换 avatar 和 card_background，后端保证完整 URL ★★★
  studentList.value.forEach(student => {
    if (!student.selectedCourseId && student.courses.length) {
      student.selectedCourseId = student.courses[0].course_id
    }
  })
  initCourseCarousel()
}

let debounceTimer = null
function handleFilterChange() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    currentPage.value = 1
    fetchData()
  }, 300)
}

function applyFilters() {
  currentPage.value = 1
  fetchData()
}

function resetFilters() {
  Object.keys(filters).forEach(key => filters[key] = null)
  currentPage.value = 1
  fetchData()
}

// ========== 加载下拉选项 ==========
async function loadOptions() {
  try {
    const [coursesRes, teachersRes, classesRes] = await Promise.all([
      getCourseListSimple(),
      getTeacherList(),
      getClassList({ page: 1, page_size: 100 })
    ])
    courseOptions.value = coursesRes.data || []
    teacherOptions.value = teachersRes.data || []
    classOptions.value = (classesRes.data?.items || classesRes.data || []).map(c => ({ name: c.name }))
  } catch (e) {
    console.error(e)
  }
}

// ========== 路由跳转 ==========
function quickEnroll() { router.push('/enroll') }
function openImportDialog() { importDialogVisible.value = true }
function goToDetail(id) { router.push(`/students/${id}`) }

// ========== 导出 / 导入 ==========
async function handleExportStudents() {
  const loadingInstance = ElLoading.service({ text: '正在导出...' })
  try {
    const params = { ...filters }
    Object.keys(params).forEach(key => {
      if (params[key] === null || params[key] === '' || params[key] === undefined) {
        delete params[key]
      }
    })
    const blob = await exportStudents(params)
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `学员列表_${new Date().toISOString().slice(0, 19)}.xlsx`
    link.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  } finally {
    loadingInstance.close()
  }
}

async function downloadTemplate() {
  try {
    const res = await downloadImportTemplate()
    const blob = new Blob([res], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = '学员导入模板.xlsx'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    ElMessage.error('下载模板失败')
  }
}

function handleImportSuccess(res) {
  if (res.code === 0) {
    ElMessage.success('导入成功')
    importDialogVisible.value = false
    fetchData()
  } else {
    ElMessage.error(res.message || '导入失败')
  }
}
function handleImportError() { ElMessage.error('导入失败，请检查文件格式') }

// ========== 监听路由查询参数 ==========
watch(() => route.query.search, (newSearch) => {
  if (newSearch) {
    filters.student_name = newSearch
    fetchData()
  }
}, { immediate: true })

// ========== 生命周期 ==========
onMounted(() => {
  loadOptions()
  fetchData()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  clearAllTimers()
})
</script>

<style scoped>
.student-list {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  background: transparent;
}

.action-bar,
.filter-panel {
  flex-shrink: 0;
  background: var(--surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xs);
}

.action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-3);
  padding: var(--space-4);
}

.left-actions,
.right-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-3);
}

.search-input {
  width: 180px;
}

.filter-link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  cursor: pointer;
  color: var(--brand-600);
  font-size: 14px;
  font-weight: 700;
}

.filter-link:hover {
  color: var(--brand-700);
}

.filter-panel {
  padding: var(--space-4) var(--space-5);
}

.filter-item {
  margin-bottom: var(--space-3);
}

.filter-item label {
  display: block;
  margin-bottom: 5px;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 700;
}

.range-input {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.range-input .el-input-number {
  flex: 1;
}

.filter-actions {
  margin-top: var(--space-4);
  text-align: right;
}

.cards-container {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--space-4);
  padding: var(--space-1);
}

.student-card {
  position: relative;
  width: 200px;
  height: 200px;
  overflow: hidden;
  flex-shrink: 0;
  cursor: pointer;
  background: var(--surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  transition: transform 0.24s ease, box-shadow 0.24s ease, border-color 0.24s ease;
}

.student-card:hover {
  transform: translateY(-4px);
  border-color: rgba(54, 180, 89, 0.28);
  box-shadow: 0 14px 30px rgba(54, 180, 89, 0.16);
}

.card-bg {
  position: absolute;
  inset: 0;
  z-index: 1;
  background-size: cover;
  background-position: center;
  transition: transform 0.3s ease;
}

.student-card:hover .card-bg {
  transform: scale(1.03);
}

.card-overlay {
  position: absolute;
  inset: 0;
  z-index: 2;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 9px;
}

.card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  font-size: 11px;
  font-weight: 600;
}

.top-left,
.top-right {
  display: inline-block;
  min-width: auto;
  height: auto;
  padding: 0;
  color: var(--gray-800);
  font-size: 11px;
  font-weight: 600;
  line-height: normal;
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.35);
}

.center-hours {
  position: absolute;
  top: 40%;
  left: 50%;
  z-index: 3;
  transform: translate(-50%, -50%);
  color: rgba(255, 255, 255, 0.3);
  font-size: 118px;
  font-weight: 900;
  line-height: 1;
  letter-spacing: -4px;
  pointer-events: none;
  user-select: none;
}

.course-nav-wrapper {
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  z-index: 10;
  display: flex;
  justify-content: space-between;
  padding: 0 var(--space-1);
  transform: translateY(-50%);
  pointer-events: none;
}

.nav-btn {
  width: 28px;
  height: 28px;
  min-width: 28px;
  padding: 0;
  color: var(--surface);
  font-size: 14px;
  background: rgba(18, 32, 24, 0.5);
  border: none;
  opacity: 0;
  backdrop-filter: blur(4px);
  pointer-events: auto;
  transition: opacity 0.18s, background 0.18s;
}

.student-card:hover .nav-btn {
  opacity: 1;
}

.nav-btn:hover {
  color: var(--surface);
  background: rgba(18, 32, 24, 0.72);
}

.nav-btn .el-icon {
  font-size: 14px;
}

.nav-btn-left { margin-left: 2px; }
.nav-btn-right { margin-right: 2px; }

.glass-area {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 60px;
  background: rgba(255, 255, 255, 0.2);
  border-top: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 0 0 var(--radius-lg) var(--radius-lg);
  backdrop-filter: blur(14px);
  mask-image: linear-gradient(to top, black 0%, black 62%, transparent 100%);
  -webkit-mask-image: linear-gradient(to top, black 0%, black 62%, transparent 100%);
}

.glass-content {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
}

.user-info {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-avatar {
  width: 42px;
  height: 42px;
  flex-shrink: 0;
  border: 2px solid rgba(255, 255, 255, 0.74);
  border-radius: var(--radius-pill);
  box-shadow: 0 2px 8px rgba(18, 32, 24, 0.16);
}

.user-detail {
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 1px;
}

.user-name {
  overflow: hidden;
  color: var(--surface);
  font-size: 14px;
  font-weight: 800;
  line-height: 1.2;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-shadow: 0 1px 4px rgba(18, 32, 24, 0.28);
}

.user-age {
  color: rgba(255, 255, 255, 0.84);
  font-size: 11px;
  line-height: 1.2;
  text-shadow: 0 1px 4px rgba(18, 32, 24, 0.2);
}

.integral-value {
  flex-shrink: 0;
  color: var(--surface);
  font-size: 20px;
  font-weight: 900;
  line-height: 1;
  text-shadow: 0 2px 8px rgba(18, 32, 24, 0.32);
}

.empty-state {
  grid-column: 1 / -1;
  padding: 60px;
  text-align: center;
  background: var(--surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-xl);
}

.pagination-box {
  flex-shrink: 0;
  display: flex;
  justify-content: flex-end;
  padding-top: var(--space-3);
}

.import-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.upload-area :deep(.el-upload-dragger) {
  width: 100%;
  padding: 30px 20px;
  background-color: var(--surface-soft);
  border: 1px dashed var(--border-color);
  border-radius: var(--radius-lg);
}

.upload-area :deep(.el-icon--upload) {
  margin-bottom: var(--space-3);
  color: var(--text-placeholder);
  font-size: 48px;
}

.import-notice {
  margin: var(--space-4) 0;
  padding: var(--space-3);
  text-align: left;
  background-color: rgba(217, 150, 40, 0.12);
  border: 1px solid rgba(217, 150, 40, 0.28);
  border-radius: var(--radius-md);
}

.import-notice p {
  margin: 4px 0;
  color: var(--warning);
  font-size: 13px;
}

.template-btn {
  color: var(--brand-600);
  background: var(--surface);
  border: 1px solid var(--brand-500);
}

.template-btn:hover {
  background: var(--brand-50);
}

.course-switch-popover {
  overflow: hidden;
  background: var(--surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
}

.course-switch-menu {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-2);
}

.course-option {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background 0.18s, color 0.18s;
}

.course-option:hover {
  background: var(--surface-soft);
}

.course-option.active {
  color: var(--brand-700);
  background: var(--brand-50);
}

.course-option .course-name {
  font-weight: 700;
}

.course-option .class-name {
  color: var(--text-secondary);
  font-size: 12px;
}

@media (max-width: 768px) {
  .cards-grid {
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: var(--space-3);
  }
  .student-card {
    width: 180px;
    height: 180px;
  }
  .action-bar {
    align-items: stretch;
    flex-direction: column;
  }
  .left-actions,
  .right-actions {
    justify-content: center;
  }
  .search-input {
    width: 100%;
  }
  .center-hours {
    font-size: 90px;
  }
}

@media (max-width: 480px) {
  .cards-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 10px;
  }
  .student-card {
    width: 160px;
    height: 160px;
    border-radius: var(--radius-md);
  }
  .glass-area {
    height: 52px;
  }
  .user-avatar {
    width: 30px;
    height: 30px;
  }
  .user-name {
    font-size: 12px;
  }
  .user-age,
  .top-left,
  .top-right {
    font-size: 10px;
  }
  .integral-value {
    font-size: 16px;
  }
  .center-hours {
    font-size: 72px;
    letter-spacing: -2px;
  }
  .user-info {
    gap: 6px;
  }
  .nav-btn {
    width: 22px;
    height: 22px;
    min-width: 22px;
    font-size: 11px;
  }
}
</style>
