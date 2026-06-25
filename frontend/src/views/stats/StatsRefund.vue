<!-- frontend/src/views/stats/StatsRefund.vue -->
<template>
  <div class="stats-page">
    <el-card class="filter-card" shadow="never">
      <el-form :model="filters" inline>
        <el-form-item label="退费日期">
          <el-date-picker v-model="filters.dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD" style="width: 280px" />
        </el-form-item>
        <el-form-item label="退费类型">
          <el-select v-model="filters.refundType" placeholder="全部类型" clearable style="width: 140px">
            <el-option label="课时退费" value="课时退费" />
            <el-option label="活动退费" value="活动退费" />
            <el-option label="物品退款" value="物品退款" />
          </el-select>
        </el-form-item>
        <el-form-item label="退款方式">
          <el-select v-model="filters.refundMethod" placeholder="全部方式" clearable style="width: 140px">
            <el-option label="微信" value="微信" />
            <el-option label="支付宝" value="支付宝" />
            <el-option label="现金" value="现金" />
            <el-option label="银行转账" value="银行转账" />
            <el-option label="原路返回" value="原路返回" />
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
          <template #header><span class="chart-title">每日退费金额趋势</span></template>
          <BaseChart :options="trendChartOption" height="300px" />
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card class="chart-card" shadow="never">
          <template #header><span class="chart-title">各课程退费排行</span></template>
          <BaseChart :options="barChartOption" height="300px" />
        </el-card>
      </el-col>
    </el-row>

    <el-card class="list-card" shadow="never">
      <template #header>
        <div class="list-header">
          <span class="list-title">退费明细</span>
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
        <el-table-column prop="refund_type" label="退费类型" width="120">
          <template #default="{ row }">
            <el-tag :type="row.refund_type === '课时退费' ? 'warning' : (row.refund_type === '活动退费' ? 'primary' : 'danger')" size="small">
              {{ row.refund_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="退费金额" width="110" align="right">
          <template #default="{ row }">¥{{ row.refund_amount.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="refund_method" label="退款方式" width="100" />
        <el-table-column prop="reason" label="退费原因" min-width="150" />
        <el-table-column prop="remark" label="备注" min-width="120" />
        <el-table-column prop="created_at" label="退费时间" width="160" />
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
import dayjs from 'dayjs'

const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const tableData = ref([])

const summaryData = ref({ total_amount: 0, total_count: 0, student_count: 0, avg_amount: 0 })
const trendData = ref([])
const distributionData = ref([])

const filters = reactive({
  dateRange: [dayjs().subtract(30, 'day').format('YYYY-MM-DD'), dayjs().format('YYYY-MM-DD')],
  refundType: null,
  refundMethod: null
})

const kpiList = computed(() => [
  { key: 'amount', label: '退费总金额', value: `¥${summaryData.value.total_amount.toFixed(2)}`, color: 'text-danger' },
  { key: 'count', label: '退费总笔数', value: summaryData.value.total_count, color: '' },
  { key: 'students', label: '涉及学员数', value: summaryData.value.student_count, color: 'text-warning' },
  { key: 'avg', label: '平均退费金额', value: `¥${summaryData.value.avg_amount.toFixed(2)}`, color: 'text-primary' }
])

const trendChartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: trendData.value.map(d => d.date), boundaryGap: false },
  yAxis: { type: 'value', name: '金额(元)' },
  series: [{
    name: '退费金额',
    type: 'line',
    smooth: true,
    data: trendData.value.map(d => d.value),
    areaStyle: { color: 'rgba(245, 108, 108, 0.2)' },
    lineStyle: { color: '#f56c6c' },
    itemStyle: { color: '#f56c6c' }
  }]
}))

const barChartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
  xAxis: { type: 'category', data: distributionData.value.map(d => d.name), axisLabel: { rotate: 15 } },
  yAxis: { type: 'value', name: '金额(元)' },
  series: [{ type: 'bar', data: distributionData.value.map(d => d.value), itemStyle: { color: '#f56c6c', borderRadius: [4, 4, 0, 0] }, barWidth: '40%' }]
}))

async function fetchData() {
  loading.value = true
  try {
    const params = {
      start_date: filters.dateRange?.[0],
      end_date: filters.dateRange?.[1],
      refund_type: filters.refundType || undefined,
      refund_method: filters.refundMethod || undefined,
      page: page.value,
      page_size: pageSize.value
    }
    const res = await request.get('/stats/refund', { params })
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
  filters.dateRange = [dayjs().subtract(30, 'day').format('YYYY-MM-DD'), dayjs().format('YYYY-MM-DD')]
  filters.refundType = null
  filters.refundMethod = null
  page.value = 1
  fetchData()
}

async function handleExport() {
  try {
    const params = {
      start_date: filters.dateRange?.[0],
      end_date: filters.dateRange?.[1],
      refund_type: filters.refundType || undefined,
      refund_method: filters.refundMethod || undefined
    }
    const res = await request.get('/stats/refund/export', { params, responseType: 'blob' })
    const url = URL.createObjectURL(res)
    const link = document.createElement('a')
    link.href = url
    link.download = `退费统计_${dayjs().format('YYYYMMDD')}.xlsx`
    link.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败')
  }
}

onMounted(fetchData)
</script>