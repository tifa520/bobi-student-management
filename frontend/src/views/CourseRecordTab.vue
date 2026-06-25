<template>
  <div class="course-record-tab">
    <div v-if="courses.length > 1" class="course-switch">
      <el-button v-for="c in courses" :key="c.course_id" :class="['course-btn', { active: selectedCourseId === c.course_id }]" size="small" @click="selectCourse(c.course_id)">
        {{ c.course_name }}
      </el-button>
    </div>
    <el-table :data="records" v-loading="loading" border stripe>
      <el-table-column prop="type" label="类型" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.type === '考勤'" type="primary">考勤</el-tag>
          <el-tag v-else-if="row.type === '自定义增加课时'" type="success">自定义增加课时</el-tag>
          <el-tag v-else-if="row.type === '自定义减少课时'" type="warning">自定义减少课时</el-tag>
          <el-tag v-else-if="row.type === '增加赠送课时'" type="success">增加赠送课时</el-tag>
          <el-tag v-else-if="row.type === '减少赠送课时'" type="danger">减少赠送课时</el-tag>
          <el-tag v-else-if="row.type === '转出课时'" type="info">转出课时</el-tag>
          <el-tag v-else-if="row.type === '转入课时'" type="success">转入课时</el-tag>
          <el-tag v-else type="info">{{ row.type }}</el-tag>
        </template>
      </el-table-column>
      <!-- 考勤状态列 -->
      <el-table-column label="考勤状态" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.type === '考勤' && row.attendance_status" :type="getAttendanceTagType(row.attendance_status)" size="small">
            {{ row.attendance_status }}
          </el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="上课时间" width="150">
        <template #default="{ row }">{{ formatDateTime(row) }}</template>
      </el-table-column>
      <el-table-column prop="class_name" label="课消班级" width="140" />
      <el-table-column prop="course_name" label="所属课程" width="120" />
      <el-table-column label="课时类型" width="90">
        <template #default="{ row }">
          <el-tag v-if="row.hour_type === '付费'" type="primary" size="small">付费课时</el-tag>
          <el-tag v-else-if="row.hour_type === '赠送'" type="warning" size="small">赠送课时</el-tag>
          <el-tag v-else type="info" size="small">-</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="deduct_hours" label="课时变动" width="100">
        <template #default="{ row }">
          <span :class="row.deduct_hours > 0 ? 'text-success' : (row.deduct_hours < 0 ? 'text-danger' : '')">
            {{ row.deduct_hours > 0 ? '+' : '' }}{{ row.deduct_hours }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="deduct_amount" label="金额变动" width="100">
        <template #default="{ row }">
          <span :class="row.deduct_amount > 0 ? 'text-success' : (row.deduct_amount < 0 ? 'text-danger' : '')">
            {{ row.deduct_amount > 0 ? '+' : '' }}￥{{ row.deduct_amount }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="teacher_name" label="任课教师" width="100" />
      <el-table-column prop="remark" label="备注" min-width="150" />
      <el-table-column prop="created_at" label="操作时间" width="160" />
    </el-table>
    <div class="pagination-box" v-if="total > pageSize">
      <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total" layout="total, prev, pager, next" size="small" @current-change="fetchRecords" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { getStudentCourses } from '@/api/student'
import { getAttendanceRecords, getCustomRecords, getGiftRecords, getTransferRecords } from '@/api/courseRecord'
import dayjs from 'dayjs'

const props = defineProps({
  studentId: { type: Number, required: true },
  type: { type: String, default: 'attendance' }
})

const records = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const courses = ref([])
const selectedCourseId = ref(null)

const apiMap = {
  attendance: getAttendanceRecords,
  custom: getCustomRecords,
  gift: getGiftRecords,
  transfer: getTransferRecords
}

function formatDateTime(row) {
  if (row.class_time) return row.class_time
  if (row.occurrence_date && row.start_time) return `${row.occurrence_date} ${row.start_time}`
  if (row.occurrence_date) return row.occurrence_date
  if (row.created_at) return row.created_at.substring(0, 16)
  return '-'
}

function getAttendanceTagType(status) {
  const map = {
    '出勤': 'success',
    '迟到': 'warning',
    '请假': 'info',
    '未到': 'danger',
    '换班': 'primary'
  }
  return map[status] || 'info'
}

async function loadCourses() {
  if (!props.studentId) return
  try {
    const res = await getStudentCourses(props.studentId)
    courses.value = res.data || []
    if (courses.value.length > 0) {
      selectedCourseId.value = courses.value[0].course_id
      await fetchRecords()
    }
  } catch (e) { console.error(e) }
}

function selectCourse(courseId) {
  selectedCourseId.value = courseId
  page.value = 1
  fetchRecords()
}

async function fetchRecords() {
  if (!selectedCourseId.value) return
  loading.value = true
  try {
    const apiFn = apiMap[props.type]
    if (!apiFn) return
    const params = {
      student_id: props.studentId,
      course_id: selectedCourseId.value,
      page: page.value,
      page_size: pageSize.value
    }
    const res = await apiFn(params)
    records.value = res.data?.records || []
    total.value = res.data?.total || 0
  } catch (e) {
    console.error(e)
    ElMessage.error('加载记录失败')
  } finally {
    loading.value = false
  }
}

watch(() => props.type, () => {
  page.value = 1
  fetchRecords()
})

onMounted(() => {
  loadCourses()
})
</script>

<style scoped>
.course-record-tab { padding: 0; }
.course-switch { margin-bottom: 16px; display: flex; gap: 8px; flex-wrap: wrap; }
.course-btn { background-color: var(--app-bg); color: var(--text-secondary); border: 1px solid var(--border-light); border-radius: 4px; padding: 6px 16px; font-size: 14px; cursor: pointer; }
.course-btn.active { background-color: var(--brand-500); color: white; border-color: var(--brand-500); }
.pagination-box { margin-top: 16px; display: flex; justify-content: flex-end; }
.text-success { color: var(--success); }
.text-danger { color: var(--danger); }
</style>