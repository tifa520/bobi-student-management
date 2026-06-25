<!-- frontend/src/views/stats/StatsEnroll.vue -->
<template>
  <div class="stats-page">
    <!-- 筛选条件栏 -->
    <el-card class="filter-card" shadow="never">
      <el-form :model="filters" inline>
        <el-form-item label="报名日期">
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
          <el-select
            v-model="filters.courseId"
            placeholder="全部课程"
            clearable
            filterable
            style="width: 160px"
          >
            <el-option
              v-for="c in courseOptions"
              :key="c.id"
              :label="c.name"
              :value="c.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="报名类型">
          <el-select
            v-model="filters.enrollType"
            placeholder="全部类型"
            clearable
            style="width: 140px"
          >
            <el-option label="新报" value="新报" />
            <el-option label="续报" value="续报" />
            <el-option label="扩科" value="扩科" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchData">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
          <el-button type="success" @click="handleExport">导出</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- KPI 指标卡 -->
    <el-row :gutter="16" class="kpi-row">
      <el-col :span="4" v-for="kpi in kpiList" :key="kpi.key">
        <div class="kpi-card">
          <div class="kpi-value" :class="kpi.color">{{ kpi.value }}</div>
          <div class="kpi-label">{{ kpi.label }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="16" class="chart-row">
      <el-col :span="14">
        <el-card class="chart-card" shadow="never">
          <template #header>
            <span class="chart-title">报名趋势</span>
          </template>
          <BaseChart :options="trendChartOption" height="300px" />
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card class="chart-card" shadow="never">
          <template #header>
            <span class="chart-title">报名类型分布</span>
          </template>
          <BaseChart :options="pieChartOption" height="300px" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 明细列表 -->
    <el-card class="list-card" shadow="never">
      <template #header>
        <div class="list-header">
          <span class="list-title">报名明细</span>
          <span class="list-total">共 {{ total }} 条记录</span>
        </div>
      </template>
      <el-table :data="tableData" v-loading="loading" border stripe>
        <el-table-column prop="order_no" label="订单号" width="160" />
        <el-table-column label="学员" min-width="140">
          <template #default="{ row }">
            <div style="display:flex; align-items:center; gap:8px;">
              <AppImage :src="row.student_avatar" :size="28" shape="circle" />
              <span>{{ row.student_name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="course_name" label="课程" min-width="120" />
        <el-table-column prop="enroll_type" label="报名类型" width="80">
          <template #default="{ row }">
            <el-tag :type="getEnrollTypeTag(row.enroll_type)" size="small">
              {{ row.enroll_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="金额" width="110" align="right">
          <template #default="{ row }">¥{{ row.payable_amount.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="payment_method" label="支付方式" width="100" />
        <el-table-column prop="created_at" label="报名时间" width="160" />
      </el-table>
      <div class="pagination-box" v-if="total > pageSize">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="fetchData"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import BaseChart from '@/components/BaseChart.vue'
import request from '@/api/request'
import { getCourseListSimple } from '@/api/basic'
import { DEFAULT_AVATAR_SVG } from '@/utils/constants'
import dayjs from 'dayjs'

// ========== 状态 ==========
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const tableData = ref([])
const courseOptions = ref([])
const summaryData = ref({
  total_count: 0,
  new_count: 0,
  renew_count: 0,
  expand_count: 0,
  total_amount: 0
})
const trendData = ref([])
const distributionData = ref([])

const filters = reactive({
  dateRange: [
    dayjs().subtract(30, 'day').format('YYYY-MM-DD'),
    dayjs().format('YYYY-MM-DD')
  ],
  courseId: null,
  enrollType: null
})

// ========== KPI 指标 ==========
const kpiList = computed(() => [
  { key: 'total', label: '总报名人数', value: summaryData.value.total_count, color: '' },
  { key: 'new', label: '新报', value: summaryData.value.new_count, color: 'text-primary' },
  { key: 'renew', label: '续报', value: summaryData.value.renew_count, color: 'text-success' },
  { key: 'expand', label: '扩科', value: summaryData.value.expand_count, color: 'text-warning' },
  { key: 'amount', label: '报名总金额', value: `¥${summaryData.value.total_amount.toFixed(2)}`, color: 'text-danger' }
])

// ========== 图表配置 ==========
const trendChartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['报名人数'] },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: {
    type: 'category',
    data: trendData.value.map(d => d.date),
    boundaryGap: false
  },
  yAxis: {
    type: 'value',
    name: '人数'
  },
  series: [{
    name: '报名人数',
    type: 'line',
    smooth: true,
    data: trendData.value.map(d => d.value),
    areaStyle: {
      color: 'rgba(54, 180, 89, 0.2)'
    },
    lineStyle: {
      color: '#36b459'
    },
    itemStyle: {
      color: '#36b459'
    }
  }]
}))

const pieChartOption = computed(() => ({
  tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
  legend: { orient: 'vertical', left: 'left' },
  series: [{
    type: 'pie',
    radius: ['40%', '70%'],
    avoidLabelOverlap: false,
    itemStyle: {
      borderRadius: 10,
      borderColor: '#fff',
      borderWidth: 2
    },
    label: { show: true, formatter: '{b}\n{d}%' },
    emphasis: {
      label: { show: true, fontSize: 14, fontWeight: 'bold' }
    },
    data: distributionData.value
  }]
}))

function getEnrollTypeTag(type) {
  const map = { '新报': 'primary', '续报': 'success', '扩科': 'warning' }
  return map[type] || 'info'
}

// ========== 数据获取 ==========
async function fetchData() {
  loading.value = true
  try {
    const params = {
      start_date: filters.dateRange?.[0],
      end_date: filters.dateRange?.[1],
      course_id: filters.courseId || undefined,
      enroll_type: filters.enrollType || undefined,
      page: page.value,
      page_size: pageSize.value
    }
    const res = await request.get('/stats/enroll', { params })
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

function resetFilters() {
  filters.dateRange = [
    dayjs().subtract(30, 'day').format('YYYY-MM-DD'),
    dayjs().format('YYYY-MM-DD')
  ]
  filters.courseId = null
  filters.enrollType = null
  page.value = 1
  fetchData()
}

async function handleExport() {
  try {
    const params = {
      start_date: filters.dateRange?.[0],
      end_date: filters.dateRange?.[1],
      course_id: filters.courseId || undefined,
      enroll_type: filters.enrollType || undefined
    }
    const res = await request.get('/stats/enroll/export', {
      params,
      responseType: 'blob'
    })
    const url = URL.createObjectURL(res)
    const link = document.createElement('a')
    link.href = url
    link.download = `报名统计_${dayjs().format('YYYYMMDD')}.xlsx`
    link.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败')
  }
}

async function loadCourses() {
  try {
    const res = await getCourseListSimple()
    courseOptions.value = res.data || []
  } catch (e) {
    console.error(e)
  }
}

onMounted(() => {
  loadCourses()
  fetchData()
})
</script>

<style scoped>
.stats-page {
  padding: 20px;
  background: var(--app-bg);
  min-height: 100%;
}
.filter-card {
  margin-bottom: 20px;
  border-radius: 12px;
}
.filter-card :deep(.el-card__body) {
  padding: 16px 20px;
}
.kpi-row {
  margin-bottom: 20px;
}
.kpi-card {
  background: var(--surface);
  border-radius: 12px;
  padding: 16px 20px;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.kpi-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
}
.kpi-value.text-primary { color: var(--brand-500); }
.kpi-value.text-success { color: var(--success); }
.kpi-value.text-warning { color: var(--warning); }
.kpi-value.text-danger { color: var(--danger); }
.kpi-label {
  font-size: 13px;
  color: var(--text-placeholder);
  margin-top: 4px;
}
.chart-row {
  margin-bottom: 20px;
}
.chart-card {
  border-radius: 12px;
}
.chart-card :deep(.el-card__header) {
  padding: 12px 20px;
  border-bottom: 1px solid var(--border-light);
}
.chart-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}
.list-card {
  border-radius: 12px;
}
.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.list-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}
.list-total {
  font-size: 13px;
  color: var(--text-placeholder);
}
.pagination-box {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>