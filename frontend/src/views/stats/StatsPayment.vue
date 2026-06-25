<!-- frontend/src/views/stats/StatsPayment.vue -->
<template>
  <div class="stats-page">
    <!-- 筛选条件栏 -->
    <el-card class="filter-card" shadow="never">
      <el-form :model="filters" inline>
        <el-form-item label="收费日期">
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
        <el-form-item label="支付方式">
          <el-select
            v-model="filters.paymentMethod"
            placeholder="全部方式"
            clearable
            style="width: 140px"
          >
            <el-option
              v-for="m in paymentMethodOptions"
              :key="m"
              :label="m"
              :value="m"
            />
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
            <span class="chart-title">每日收费趋势</span>
          </template>
          <BaseChart :options="trendChartOption" height="300px" />
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card class="chart-card" shadow="never">
          <template #header>
            <span class="chart-title">支付方式分布</span>
          </template>
          <BaseChart :options="pieChartOption" height="300px" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 明细列表 -->
    <el-card class="list-card" shadow="never">
      <template #header>
        <div class="list-header">
          <span class="list-title">收费明细</span>
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
        <el-table-column label="金额" width="110" align="right">
          <template #default="{ row }">¥{{ row.amount.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="payment_method" label="支付方式" width="100" />
        <el-table-column prop="payment_type" label="类型" width="80">
          <template #default="{ row }">
            <el-tag :type="row.payment_type === 'initial' ? 'primary' : 'success'" size="small">
              {{ row.payment_type === 'initial' ? '首付' : '补缴' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="120" />
        <el-table-column prop="occurred_at" label="收费时间" width="160" />
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
import { getPaymentMethods } from '@/api/settings'
import dayjs from 'dayjs'

const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const tableData = ref([])
const paymentMethodOptions = ref(['微信支付', '支付宝', '现金', '银行转账'])

const summaryData = ref({
  total_amount: 0,
  total_count: 0,
  avg_amount: 0,
  max_amount: 0
})
const trendData = ref([])
const distributionData = ref([])

const filters = reactive({
  dateRange: [
    dayjs().subtract(30, 'day').format('YYYY-MM-DD'),
    dayjs().format('YYYY-MM-DD')
  ],
  paymentMethod: null
})

const kpiList = computed(() => [
  { key: 'total_amount', label: '收费总金额', value: `¥${summaryData.value.total_amount.toFixed(2)}`, color: 'text-danger' },
  { key: 'total_count', label: '收费笔数', value: summaryData.value.total_count, color: '' },
  { key: 'avg_amount', label: '平均客单价', value: `¥${summaryData.value.avg_amount.toFixed(2)}`, color: 'text-primary' },
  { key: 'max_amount', label: '最大单笔', value: `¥${summaryData.value.max_amount.toFixed(2)}`, color: 'text-warning' }
])

const trendChartOption = computed(() => ({
  tooltip: { trigger: 'axis', formatter: (params) => {
    const p = params[0]
    return `${p.name}<br/>收费金额: ¥${p.value.toFixed(2)}`
  }},
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: trendData.value.map(d => d.date), boundaryGap: false },
  yAxis: { type: 'value', name: '金额(元)' },
  series: [{
    name: '收费金额',
    type: 'line',
    smooth: true,
    data: trendData.value.map(d => d.value),
    areaStyle: { color: 'rgba(54, 180, 89, 0.2)' },
    lineStyle: { color: '#36b459' },
    itemStyle: { color: '#36b459' }
  }]
}))

const pieChartOption = computed(() => ({
  tooltip: { trigger: 'item', formatter: (params) => {
    return `${params.name}<br/>¥${params.value.toFixed(2)} (${params.percent}%)`
  }},
  legend: { orient: 'vertical', left: 'left' },
  series: [{
    type: 'pie',
    radius: ['40%', '70%'],
    data: distributionData.value.map(d => ({ name: d.name, value: d.value })),
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
      payment_method: filters.paymentMethod || undefined,
      page: page.value,
      page_size: pageSize.value
    }
    const res = await request.get('/stats/payment', { params })
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

async function loadPaymentMethods() {
  try {
    const res = await getPaymentMethods()
    if (res.code === 0 && res.data) paymentMethodOptions.value = res.data
  } catch (e) { console.error(e) }
}

function resetFilters() {
  filters.dateRange = [dayjs().subtract(30, 'day').format('YYYY-MM-DD'), dayjs().format('YYYY-MM-DD')]
  filters.paymentMethod = null
  page.value = 1
  fetchData()
}

async function handleExport() {
  try {
    const params = {
      start_date: filters.dateRange?.[0],
      end_date: filters.dateRange?.[1],
      payment_method: filters.paymentMethod || undefined
    }
    const res = await request.get('/stats/payment/export', { params, responseType: 'blob' })
    const url = URL.createObjectURL(res)
    const link = document.createElement('a')
    link.href = url
    link.download = `收费统计_${dayjs().format('YYYYMMDD')}.xlsx`
    link.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败')
  }
}

onMounted(() => {
  loadPaymentMethods()
  fetchData()
})
</script>

<style scoped>
.stats-page { padding: 20px; background: var(--app-bg); min-height: 100%; }
.filter-card { margin-bottom: 20px; border-radius: 12px; }
.filter-card :deep(.el-card__body) { padding: 16px 20px; }
.kpi-row { margin-bottom: 20px; }
.kpi-card { background: var(--surface); border-radius: 12px; padding: 16px 20px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
.kpi-value { font-size: 28px; font-weight: 700; color: var(--text-primary); }
.kpi-value.text-primary { color: var(--brand-500); }
.kpi-value.text-success { color: var(--success); }
.kpi-value.text-warning { color: var(--warning); }
.kpi-value.text-danger { color: var(--danger); }
.kpi-label { font-size: 13px; color: var(--text-placeholder); margin-top: 4px; }
.chart-row { margin-bottom: 20px; }
.chart-card { border-radius: 12px; }
.chart-card :deep(.el-card__header) { padding: 12px 20px; border-bottom: 1px solid var(--border-light); }
.chart-title { font-size: 15px; font-weight: 600; color: var(--text-primary); }
.list-card { border-radius: 12px; }
.list-header { display: flex; justify-content: space-between; align-items: center; }
.list-title { font-size: 15px; font-weight: 600; color: var(--text-primary); }
.list-total { font-size: 13px; color: var(--text-placeholder); }
.pagination-box { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>