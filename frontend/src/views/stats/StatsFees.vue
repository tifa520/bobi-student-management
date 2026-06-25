<!-- frontend/src/views/stats/StatsFees.vue -->
<template>
  <div class="stats-page">
    <el-card class="filter-card" shadow="never">
      <el-form :model="filters" inline>
        <el-form-item label="日期范围">
          <el-date-picker v-model="filters.dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD" style="width: 280px" />
        </el-form-item>
        <el-form-item label="费用类型">
          <el-select v-model="filters.feeType" placeholder="全部类型" clearable style="width: 140px">
            <el-option label="物品销售" value="item_sale" />
            <el-option label="活动收费" value="activity" />
            <el-option label="退款" value="refund" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部状态" clearable style="width: 120px">
            <el-option label="待缴费" value="pending" />
            <el-option label="部分缴纳" value="partial" />
            <el-option label="已结清" value="paid" />
            <el-option label="已退款" value="refunded" />
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
          <template #header><span class="chart-title">每日杂费收支趋势</span></template>
          <BaseChart :options="trendChartOption" height="300px" />
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card class="chart-card" shadow="never">
          <template #header><span class="chart-title">费用类型分布</span></template>
          <BaseChart :options="pieChartOption" height="300px" />
        </el-card>
      </el-col>
    </el-row>

    <el-card class="list-card" shadow="never">
      <template #header>
        <div class="list-header">
          <span class="list-title">杂费明细</span>
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
        <el-table-column prop="fee_type" label="费用类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.fee_type_key === 'refund' ? 'danger' : (row.fee_type_key === 'activity' ? 'warning' : 'primary')" size="small">
              {{ row.fee_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="说明" min-width="150" />
        <el-table-column label="金额" width="100" align="right">
          <template #default="{ row }">
            <span :class="row.amount < 0 ? 'text-danger' : 'text-success'">¥{{ row.amount.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="实收" width="100" align="right">
          <template #default="{ row }">¥{{ row.paid_amount.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="积分" width="80" align="center">
          <template #default="{ row }">{{ row.points_used || 0 }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === '已结清' ? 'success' : (row.status === '已退款' ? 'danger' : 'warning')" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="payment_method" label="支付方式" width="100" />
        <el-table-column prop="created_at" label="时间" width="160" />
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

const summaryData = ref({ total_income: 0, total_expense: 0, net_income: 0, record_count: 0 })
const trendData = ref([])
const distributionData = ref([])

const filters = reactive({
  dateRange: [dayjs().subtract(30, 'day').format('YYYY-MM-DD'), dayjs().format('YYYY-MM-DD')],
  feeType: null,
  status: null
})

const kpiList = computed(() => [
  { key: 'income', label: '杂费总收入', value: `¥${summaryData.value.total_income.toFixed(2)}`, color: 'text-success' },
  { key: 'expense', label: '杂费总支出', value: `¥${summaryData.value.total_expense.toFixed(2)}`, color: 'text-danger' },
  { key: 'net', label: '净收入', value: `¥${summaryData.value.net_income.toFixed(2)}`, color: 'text-primary' },
  { key: 'count', label: '记录数', value: summaryData.value.record_count, color: '' }
])

const trendChartOption = computed(() => {
  const dates = trendData.value.map(d => d.date)
  const values = trendData.value.map(d => d.value)
  return {
    tooltip: { trigger: 'axis', formatter: (params) => {
      let html = `${params[0].name}<br/>`
      params.forEach(p => { html += `${p.marker} ${p.seriesName}: ¥${p.value.toFixed(2)}<br/>` })
      return html
    }},
    legend: { data: ['收入', '支出'] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: dates, boundaryGap: false },
    yAxis: { type: 'value', name: '金额(元)' },
    series: [
      { name: '收入', type: 'line', smooth: true, data: values.map(v => v >= 0 ? v : 0), lineStyle: { color: '#67c23a' }, itemStyle: { color: '#67c23a' } },
      { name: '支出', type: 'line', smooth: true, data: values.map(v => v < 0 ? Math.abs(v) : 0), lineStyle: { color: '#f56c6c' }, itemStyle: { color: '#f56c6c' } }
    ]
  }
})

const pieChartOption = computed(() => ({
  tooltip: { trigger: 'item', formatter: (params) => `${params.name}<br/>¥${params.value.toFixed(2)} (${params.percent}%)` },
  legend: { orient: 'vertical', left: 'left' },
  series: [{
    type: 'pie',
    radius: ['40%', '70%'],
    data: distributionData.value,
    itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
    label: { formatter: '{b}\n¥{c}' }
  }]
}))

async function fetchData() {
  loading.value = true
  try {
    const params = {
      start_date: filters.dateRange?.[0],
      end_date: filters.dateRange?.[1],
      fee_type: filters.feeType || undefined,
      status: filters.status || undefined,
      page: page.value,
      page_size: pageSize.value
    }
    const res = await request.get('/stats/fees', { params })
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
  filters.feeType = null
  filters.status = null
  page.value = 1
  fetchData()
}

async function handleExport() {
  try {
    const params = {
      start_date: filters.dateRange?.[0],
      end_date: filters.dateRange?.[1],
      fee_type: filters.feeType || undefined,
      status: filters.status || undefined
    }
    const res = await request.get('/stats/fees/export', { params, responseType: 'blob' })
    const url = URL.createObjectURL(res)
    const link = document.createElement('a')
    link.href = url
    link.download = `杂费统计_${dayjs().format('YYYYMMDD')}.xlsx`
    link.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败')
  }
}

onMounted(fetchData)
</script>