<template>
  <div class="course-record-container">
    <el-tabs v-model="activeTab" class="record-tabs" @tab-click="handleTabClick">
      <el-tab-pane name="attendance"><template #label><span :class="{ 'tab-active': activeTab === 'attendance' }">考勤记录</span></template></el-tab-pane>
      <el-tab-pane name="custom"><template #label><span :class="{ 'tab-active': activeTab === 'custom' }">自定义增减课时记录</span></template></el-tab-pane>
      <el-tab-pane name="gift"><template #label><span :class="{ 'tab-active': activeTab === 'gift' }">赠送课时记录</span></template></el-tab-pane>
      <el-tab-pane name="transfer"><template #label><span :class="{ 'tab-active': activeTab === 'transfer' }">转入转出记录</span></template></el-tab-pane>
    </el-tabs>

    <div class="filter-bar">
      <div class="filter-left">
        <el-select v-model="filterClassId" placeholder="选择班级" clearable filterable style="width:200px" @change="handleFilterChange"><el-option v-for="c in classes" :key="c.id" :label="c.name" :value="c.id" /></el-select>
        <el-select v-model="filterCourseId" placeholder="选择课程" clearable filterable style="width:180px" @change="handleFilterChange"><el-option v-for="c in courses" :key="c.id" :label="c.name" :value="c.id" /></el-select>
        <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD" style="width:400px" @change="handleFilterChange" />
      </div>
      <div class="filter-right"><el-button type="primary" @click="handleSearch">查询</el-button><ExportExcel :fetch-fn="handleExport" filename="课消记录.xlsx" style="margin-left:12px" /></div>
    </div>

    <!-- 考勤记录 -->
    <div v-if="activeTab === 'attendance'" class="table-wrapper">
      <el-table :data="attendanceRecords" v-loading="attendanceLoading" border stripe>
        <el-table-column label="学员" min-width="160">
          <template #default="{ row }">
            <div class="student-info-cell">
              <AppImage :src="row.student_avatar" :size="28" shape="circle" />
              <div class="student-name">{{ row.student_name }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="100"><template #default="{ row }"><el-tag :type="getTypeTag(row.type)" size="small">{{ row.type }}</el-tag></template></el-table-column>
        <el-table-column label="上课时间" width="160"><template #default="{ row }">{{ row.class_time || row.occurrence_date || '-' }}</template></el-table-column>
        <el-table-column prop="class_name" label="课消班级" min-width="140" />
        <el-table-column prop="course_name" label="所属课程" min-width="120" />
        <el-table-column label="课时类型" width="90"><template #default="{ row }"><el-tag v-if="row.hour_type === '付费'" type="primary" size="small">付费课时</el-tag><el-tag v-else-if="row.hour_type === '赠送'" type="warning" size="small">赠送课时</el-tag><el-tag v-else type="info" size="small">-</el-tag></template></el-table-column>
        <el-table-column prop="deduct_hours" label="课时变动" width="100"><template #default="{ row }"><span :class="row.deduct_hours > 0 ? 'text-success' : 'text-danger'">{{ row.deduct_hours > 0 ? '+' : '' }}{{ row.deduct_hours }}</span></template></el-table-column>
        <el-table-column prop="deduct_amount" label="金额变动" width="100"><template #default="{ row }"><span :class="row.deduct_amount > 0 ? 'text-success' : 'text-danger'">{{ row.deduct_amount > 0 ? '+' : '' }}￥{{ row.deduct_amount }}</span></template></el-table-column>
        <el-table-column prop="teacher_name" label="任课教师" width="100" />
        <el-table-column prop="attendance_status" label="考勤状态" width="100"><template #default="{ row }"><el-tag :type="getStatusTagType(row.attendance_status)" size="small">{{ row.attendance_status }}</el-tag></template></el-table-column>
        <el-table-column prop="remark" label="备注" min-width="150" />
        <el-table-column prop="created_at" label="操作时间" width="160" />
      </el-table>
      <div class="pagination-box" v-if="attendanceTotal > pageSize"><el-pagination v-model:current-page="attendancePage" :page-size="pageSize" :total="attendanceTotal" layout="total, prev, pager, next" size="small" @current-change="fetchAttendanceRecords" /></div>
    </div>

    <!-- 自定义增减课时记录 -->
    <div v-else-if="activeTab === 'custom'" class="table-wrapper">
      <el-table :data="customRecords" v-loading="customLoading" border stripe>
        <el-table-column label="学员" min-width="160">
          <template #default="{ row }">
            <div class="student-info-cell">
              <AppImage :src="row.student_avatar" :size="28" shape="circle" />
              <div class="student-name">{{ row.student_name }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="140"><template #default="{ row }"><el-tag :type="getTypeTag(row.type)" size="small">{{ row.type }}</el-tag></template></el-table-column>
        <el-table-column prop="occurrence_date" label="日期" width="100" />
        <el-table-column prop="class_name" label="课消班级" min-width="140" />
        <el-table-column prop="course_name" label="所属课程" min-width="120" />
        <el-table-column label="课时类型" width="90"><template #default="{ row }"><el-tag v-if="row.hour_type === '付费'" type="primary" size="small">付费课时</el-tag><el-tag v-else-if="row.hour_type === '赠送'" type="warning" size="small">赠送课时</el-tag><el-tag v-else type="info" size="small">-</el-tag></template></el-table-column>
        <el-table-column prop="deduct_hours" label="课时变动" width="100"><template #default="{ row }"><span :class="row.deduct_hours > 0 ? 'text-success' : 'text-danger'">{{ row.deduct_hours > 0 ? '+' : '' }}{{ row.deduct_hours }}</span></template></el-table-column>
        <el-table-column prop="deduct_amount" label="金额变动" width="100"><template #default="{ row }"><span :class="row.deduct_amount > 0 ? 'text-success' : 'text-danger'">{{ row.deduct_amount > 0 ? '+' : '' }}￥{{ row.deduct_amount }}</span></template></el-table-column>
        <el-table-column prop="teacher_name" label="任课教师" width="100" />
        <el-table-column prop="remark" label="备注" min-width="150" />
        <el-table-column prop="created_at" label="操作时间" width="160" />
      </el-table>
      <div class="pagination-box" v-if="customTotal > pageSize"><el-pagination v-model:current-page="customPage" :page-size="pageSize" :total="customTotal" layout="total, prev, pager, next" size="small" @current-change="fetchCustomRecords" /></div>
    </div>

    <!-- 赠送课时记录 -->
    <div v-else-if="activeTab === 'gift'" class="table-wrapper">
      <el-table :data="giftRecords" v-loading="giftLoading" border stripe>
        <el-table-column label="学员" min-width="160">
          <template #default="{ row }">
            <div class="student-info-cell">
              <AppImage :src="row.student_avatar" :size="28" shape="circle" />
              <div class="student-name">{{ row.student_name }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="140"><template #default="{ row }"><el-tag :type="getTypeTag(row.type)" size="small">{{ row.type }}</el-tag></template></el-table-column>
        <el-table-column prop="occurrence_date" label="日期" width="100" />
        <el-table-column prop="class_name" label="课消班级" min-width="140" />
        <el-table-column prop="course_name" label="所属课程" min-width="120" />
        <el-table-column prop="deduct_hours" label="课时变动" width="100"><template #default="{ row }"><span :class="row.deduct_hours > 0 ? 'text-success' : 'text-danger'">{{ row.deduct_hours > 0 ? '+' : '' }}{{ row.deduct_hours }}</span></template></el-table-column>
        <el-table-column prop="deduct_amount" label="金额变动" width="100"><template #default="{ row }">￥{{ row.deduct_amount }}</template></el-table-column>
        <el-table-column prop="teacher_name" label="任课教师" width="100" />
        <el-table-column prop="remark" label="备注" min-width="150" />
        <el-table-column prop="created_at" label="操作时间" width="160" />
      </el-table>
      <div class="pagination-box" v-if="giftTotal > pageSize"><el-pagination v-model:current-page="giftPage" :page-size="pageSize" :total="giftTotal" layout="total, prev, pager, next" size="small" @current-change="fetchGiftRecords" /></div>
    </div>

    <!-- 转入转出记录 -->
    <div v-else-if="activeTab === 'transfer'" class="table-wrapper">
      <el-table :data="transferRecords" v-loading="transferLoading" border stripe>
        <el-table-column label="学员" min-width="160">
          <template #default="{ row }">
            <div class="student-info-cell">
              <AppImage :src="row.student_avatar" :size="28" shape="circle" />
              <div class="student-name">{{ row.student_name }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="120"><template #default="{ row }"><el-tag :type="getTypeTag(row.type)" size="small">{{ row.type }}</el-tag></template></el-table-column>
        <el-table-column prop="occurrence_date" label="日期" width="100" />
        <el-table-column prop="class_name" label="课消班级" min-width="140" />
        <el-table-column prop="course_name" label="所属课程" min-width="120" />
        <el-table-column label="课时类型" width="90"><template #default="{ row }"><el-tag v-if="row.hour_type === '付费'" type="primary" size="small">付费课时</el-tag><el-tag v-else-if="row.hour_type === '赠送'" type="warning" size="small">赠送课时</el-tag><el-tag v-else type="info" size="small">-</el-tag></template></el-table-column>
        <el-table-column prop="deduct_hours" label="课时变动" width="100"><template #default="{ row }"><span :class="row.deduct_hours > 0 ? 'text-success' : 'text-danger'">{{ row.deduct_hours > 0 ? '+' : '' }}{{ row.deduct_hours }}</span></template></el-table-column>
        <el-table-column prop="deduct_amount" label="金额变动" width="100"><template #default="{ row }"><span :class="row.deduct_amount > 0 ? 'text-success' : 'text-danger'">{{ row.deduct_amount > 0 ? '+' : '' }}￥{{ row.deduct_amount }}</span></template></el-table-column>
        <el-table-column prop="teacher_name" label="任课教师" width="100" />
        <el-table-column prop="remark" label="备注" min-width="150" />
        <el-table-column prop="created_at" label="操作时间" width="160" />
      </el-table>
      <div class="pagination-box" v-if="transferTotal > pageSize"><el-pagination v-model:current-page="transferPage" :page-size="pageSize" :total="transferTotal" layout="total, prev, pager, next" size="small" @current-change="fetchTransferRecords" /></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import ExportExcel from '@/components/ExportExcel.vue'
import { getAttendanceRecords, getCustomRecords, getGiftRecords, getTransferRecords, exportCourseRecords } from '@/api/courseRecord'
import { getClassList } from '@/api/class'
import { getCourseListSimple } from '@/api/basic'
import { DEFAULT_AVATAR_SVG } from '@/utils/constants'

const activeTab = ref('attendance')
const filterClassId = ref(null)
const filterCourseId = ref(null)
const dateRange = ref(null)
const pageSize = ref(20)

const classes = ref([])
const courses = ref([])

const attendanceRecords = ref([])
const attendanceLoading = ref(false)
const attendancePage = ref(1)
const attendanceTotal = ref(0)

const customRecords = ref([])
const customLoading = ref(false)
const customPage = ref(1)
const customTotal = ref(0)

const giftRecords = ref([])
const giftLoading = ref(false)
const giftPage = ref(1)
const giftTotal = ref(0)

const transferRecords = ref([])
const transferLoading = ref(false)
const transferPage = ref(1)
const transferTotal = ref(0)

function getTypeTag(type) {
  if (!type) return 'info'
  if (type === '考勤') return 'primary'
  if (type.includes('增加') || type.includes('转入')) return 'success'
  if (type.includes('减少') || type.includes('转出')) return 'warning'
  if (type === '退费') return 'danger'
  return 'info'
}

function getStatusTagType(status) {
  const map = { '出勤': 'success', '迟到': 'warning', '请假': 'info', '未到': 'danger', '换班': 'primary' }
  return map[status] || 'info'
}

function getCommonParams() {
  return {
    class_id: filterClassId.value || undefined,
    course_id: filterCourseId.value || undefined,
    start_date: dateRange.value?.[0] || undefined,
    end_date: dateRange.value?.[1] || undefined,
    page_size: pageSize.value
  }
}

async function fetchAttendanceRecords() {
  attendanceLoading.value = true
  try {
    const params = { ...getCommonParams(), page: attendancePage.value }
    const res = await getAttendanceRecords(params)
    attendanceRecords.value = res.data?.records || []
    attendanceTotal.value = res.data?.total || 0
  } catch (e) { console.error(e) } finally { attendanceLoading.value = false }
}
async function fetchCustomRecords() {
  customLoading.value = true
  try {
    const params = { ...getCommonParams(), page: customPage.value }
    const res = await getCustomRecords(params)
    customRecords.value = res.data?.records || []
    customTotal.value = res.data?.total || 0
  } catch (e) { console.error(e) } finally { customLoading.value = false }
}
async function fetchGiftRecords() {
  giftLoading.value = true
  try {
    const params = { ...getCommonParams(), page: giftPage.value }
    const res = await getGiftRecords(params)
    giftRecords.value = res.data?.records || []
    giftTotal.value = res.data?.total || 0
  } catch (e) { console.error(e) } finally { giftLoading.value = false }
}
async function fetchTransferRecords() {
  transferLoading.value = true
  try {
    const params = { ...getCommonParams(), page: transferPage.value }
    const res = await getTransferRecords(params)
    transferRecords.value = res.data?.records || []
    transferTotal.value = res.data?.total || 0
  } catch (e) { console.error(e) } finally { transferLoading.value = false }
}

async function fetchAllTabsData() {
  await Promise.all([fetchAttendanceRecords(), fetchCustomRecords(), fetchGiftRecords(), fetchTransferRecords()])
}

function handleTabClick() {
  if (activeTab.value === 'attendance') { attendancePage.value = 1; fetchAttendanceRecords() }
  else if (activeTab.value === 'custom') { customPage.value = 1; fetchCustomRecords() }
  else if (activeTab.value === 'gift') { giftPage.value = 1; fetchGiftRecords() }
  else if (activeTab.value === 'transfer') { transferPage.value = 1; fetchTransferRecords() }
}

function handleFilterChange() {
  attendancePage.value = 1; customPage.value = 1; giftPage.value = 1; transferPage.value = 1
  handleTabClick()
}
function handleSearch() { handleFilterChange() }
async function handleExport() {
  const params = {
    class_id: filterClassId.value || undefined,
    course_id: filterCourseId.value || undefined,
    record_type: activeTab.value,
    start_date: dateRange.value?.[0] || undefined,
    end_date: dateRange.value?.[1] || undefined
  }
  return exportCourseRecords(params)
}
async function loadOptions() {
  try {
    const [classRes, courseRes] = await Promise.all([getClassList({ page: 1, page_size: 100 }), getCourseListSimple()])
    classes.value = classRes.data?.items || classRes.data || []
    courses.value = courseRes.data || []
  } catch (e) { console.error(e) }
}
onMounted(async () => { await loadOptions(); await fetchAllTabsData() })
</script>

<style scoped>
.course-record-container { display: flex; flex-direction: column; height: 100%; overflow: hidden; }
.record-tabs { margin-bottom: 16px; flex-shrink: 0; }
.tab-active { color: var(--brand-500); font-weight: 500; }
.filter-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-shrink: 0; gap: 16px; flex-wrap: wrap; }
.filter-left { display: flex; align-items: center; gap: 12px; }
.table-wrapper { flex: 1; overflow: auto; }
.pagination-box { margin-top: 16px; display: flex; justify-content: flex-end; }
.text-success { color: var(--success); }
.text-danger { color: var(--danger); }
.student-info-cell { display: flex; align-items: center; gap: 10px; }
.student-name { font-weight: 500; }
.student-phone { font-size: 12px; color: var(--text-secondary); }
</style>