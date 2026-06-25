<!-- frontend/src/views/stats/StatsHours.vue -->
<template>
  <div class="stats-page">
    <el-card class="filter-card" shadow="never">
      <el-form :model="filters" inline>
        <el-form-item label="上课日期">
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 280px"
          />
        </el-form-item>
        <el-form-item label="课程">
          <el-select v-model="filters.courseId" placeholder="全部课程" clearable filterable style="width: 160px">
            <el-option v-for="c in courseOptions" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="班级">
          <el-select v-model="filters.classId" placeholder="全部班级" clearable filterable style="width: 160px">
            <el-option v-for="c in classOptions" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchData">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
          <el-button type="success" @click="handleExport">导出</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-row :gutter="16" class="kpi-row">
      <el-col :span="6" v-for="kpi in kpiList" :key="kpi.key">
        <div class="kpi-card">
          <div class="kpi-value" :class="kpi.color">{{ kpi.value }}</div>
          <div class="kpi-label">{{ kpi.label }}</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="chart-row">
      <el-col :span="14">
        <el-card class="chart-card" shadow="never">
          <template #header><span class="chart-title">每日课时消耗趋势</span></template>
          <BaseChart :options="trendChartOption" height="300px" />
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card class="chart-card" shadow="never">
          <template #header><span class="chart-title">各课程课时消耗排行</span></template>
          <BaseChart :options="barChartOption" height="300px" />
        </el-card>
      </el-col>
    </el-row>

    <el-card class="list-card" shadow="never">
      <template #header>
        <div class="list-header">
          <span class="list-title">课时消耗明细</span>
          <span class="list-total">共 {{ total }} 条记录</span>
        </div>
      </template>
      <el-table :data="tableData" v-loading="loading" border stripe>
        <el-table-column label="学员" min-width="140">
          <template #default="{ row }">
            <div style="display:flex; align-items:center; gap:8px;">
              <AppImage :src="row.student_avatar" :size="28" shape="circle" />
              <span>{{ row.student_name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="course_name" label="课程" min-width="120" />
        <el-table-column prop="class_name" label="班级" min-width="120" />
        <el-table-column label="消耗课时" width="100" align="center">
          <template #default="{ row }">{{ row.hours }} 课时</template>
        </el-table-column>
        <el-table-column label="消耗金额" width="110" align="right">
          <template #default="{ row }">¥{{ row.amount.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="occurred_at" label="上课时间" width="160" />
      </el-table>
      <div class="pagination-box" v-if="total > pageSize">
        <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total" layout="total, prev, pager, next" @current-change="fetchData" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import BaseChart from '@/components/BaseChart.vue'
import request from '@/api/request'
import { getCourseListSimple, getClassList } from '@/api/basic'
import dayjs from 'dayjs'

const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const tableData = ref([])
const courseOptions = ref([])
const classOptions = ref([])

const summaryData = ref({ total_hours: 0, total_amount: 0, attendance_count: 0, avg_price: 0 })
const trendData = ref([])
const distributionData = ref([])

const filters = reactive({
  dateRange: [dayjs().subtract(30, 'day').format('YYYY-MM-DD'), dayjs().format('YYYY-MM-DD')],
  courseId: null,
  classId: null
})

const kpiList = computed(() => [
  { key: 'hours', label: '总消耗课时', value: `${summaryData.value.total_hours} 课时`, color: '' },
  { key: 'amount', label: '总消耗金额', value: `¥${summaryData.value.total_amount.toFixed(2)}`, color: 'text-danger' },
  { key: 'count', label: '出勤人次', value: summaryData.value.attendance_count, color: 'text-primary' },
  { key: 'avg', label: '平均课时单价', value: `¥${summaryData.value.avg_price.toFixed(2)}`, color: 'text-warning' }
])

const trendChartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: trendData.value.map(d => d.date), boundaryGap: false },
  yAxis: { type: 'value', name: '课时' },
  series: [{
    name: '消耗课时',
    type: 'line',
    smooth: true,
    data: trendData.value.map(d => d.value),
    areaStyle: { color: 'rgba(54, 180, 89, 0.2)' },
    lineStyle: { color: '#36b459' },
    itemStyle: { color: '#36b459' }
  }]
}))

const barChartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: distributionData.value.map(d => d.name) },
  yAxis: { type: 'value', name: '课时' },
  series: [{
    type: 'bar',
    data: distributionData.value.map(d => d.value),
    itemStyle: { color: '#36b459', borderRadius: [4, 4, 0, 0] },
    barWidth: '40%'
  }]
}))

async function fetchData() {
  loading.value = true
  try {
    const params = {
      start_date: filters.dateRange?.[0],
      end_date: filters.dateRange?.[1],
      course_id: filters.courseId || undefined,
      class_id: filters.classId || undefined,
      page: page.value,
      page_size: pageSize.value
    }
    const res = await request.get('/stats/hours', { params })
    if (res.code === 0) {
      const data = res.data
      summaryData.value = data.summary || {}
      trendData.value = data.trend || []
      distributionData.value = data.distribution || []
      tableData.value = data.list || []
      total.value = data.total || 0
    }
  } catch (e) {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

async function loadOptions() {
  try {
    const [coursesRes, classesRes] = await Promise.all([
      getCourseListSimple(),
      getClassList({ page: 1, page_size: 100 })
    ])
    courseOptions.value = coursesRes.data || []
    classOptions.value = (classesRes.data?.items || classesRes.data || [])
  } catch (e) { console.error(e) }
}

function resetFilters() {
  filters.dateRange = [dayjs().subtract(30, 'day').format('YYYY-MM-DD'), dayjs().format('YYYY-MM-DD')]
  filters.courseId = null
  filters.classId = null
  page.value = 1
  fetchData()
}

async function handleExport() {
  try {
    const params = {
      start_date: filters.dateRange?.[0],
      end_date: filters.dateRange?.[1],
      course_id: filters.courseId || undefined,
      class_id: filters.classId || undefined
    }
    const res = await request.get('/stats/hours/export', { params, responseType: 'blob' })
    const url = URL.createObjectURL(res)
    const link = document.createElement('a')
    link.href = url
    link.download = `课时统计_${dayjs().format('YYYYMMDD')}.xlsx`
    link.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败')
  }
}

onMounted(() => { loadOptions(); fetchData() })
</script>

<style scoped>
/* 与 StatsPayment.vue 样式相同，略 */
</style>