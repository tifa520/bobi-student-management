<!-- frontend/src/views/stats/StatsItems.vue -->
<template>
  <div class="stats-page">
    <el-card class="filter-card" shadow="never">
      <el-form :model="filters" inline>
        <el-form-item label="销售日期">
          <el-date-picker v-model="filters.dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD" style="width: 280px" />
        </el-form-item>
        <el-form-item label="物品类别">
          <el-select v-model="filters.category" placeholder="全部分类" clearable style="width: 140px">
            <el-option v-for="cat in categoryOptions" :key="cat" :label="cat" :value="cat" />
          </el-select>
        </el-form-item>
        <el-form-item label="支付方式">
          <el-select v-model="filters.paymentMethod" placeholder="全部方式" clearable style="width: 140px">
            <el-option v-for="m in paymentMethodOptions" :key="m" :label="m" :value="m" />
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
          <template #header><span class="chart-title">每日销售额趋势</span></template>
          <BaseChart :options="trendChartOption" height="300px" />
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card class="chart-card" shadow="never">
          <template #header><span class="chart-title">物品销售额排行</span></template>
          <BaseChart :options="barChartOption" height="300px" />
        </el-card>
      </el-col>
    </el-row>

    <el-card class="list-card" shadow="never">
      <template #header>
        <div class="list-header">
          <span class="list-title">物品销售明细</span>
          <span class="list-total">共 {{ total }} 条记录</span>
        </div>
      </template>
      <el-table :data="tableData" v-loading="loading" border stripe>
        <el-table-column label="商品" width="60" align="center">
          <template #default="{ row }">
            <el-image v-if="row.item_image" :src="row.item_image" fit="cover" style="width:36px; height:36px; border-radius:4px; cursor:pointer;" :preview-src-list="[row.item_image]" :z-index="99999" preview-teleported />
            <div v-else style="width:36px; height:36px; background:#f5f7fa; border-radius:4px;"></div>
          </template>
        </el-table-column>
        <el-table-column prop="item_name" label="物品名称" min-width="120" />
        <el-table-column prop="category" label="类别" width="100" />
        <el-table-column prop="quantity" label="数量" width="80" align="center" />
        <el-table-column label="单价" width="100" align="right"><template #default="{ row }">¥{{ row.unit_price.toFixed(2) }}</template></el-table-column>
        <el-table-column label="销售额" width="110" align="right"><template #default="{ row }">¥{{ row.total_amount.toFixed(2) }}</template></el-table-column>
        <el-table-column label="成本" width="100" align="right"><template #default="{ row }">¥{{ row.cost.toFixed(2) }}</template></el-table-column>
        <el-table-column label="毛利" width="100" align="right">
          <template #default="{ row }">
            <span :class="row.profit >= 0 ? 'text-success' : 'text-danger'">¥{{ row.profit.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="payment_method" label="支付方式" width="100" />
        <el-table-column prop="created_at" label="销售时间" width="160" />
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
import { getPaymentMethods } from '@/api/settings'
import dayjs from 'dayjs'

const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const tableData = ref([])
const categoryOptions = ref(['教材', '教具', '礼品', '办公用品', '其他'])
const paymentMethodOptions = ref(['微信支付', '支付宝', '现金', '银行转账'])

const summaryData = ref({ total_amount: 0, total_cost: 0, total_profit: 0, total_quantity: 0 })
const trendData = ref([])
const distributionData = ref([])

const filters = reactive({
  dateRange: [dayjs().subtract(30, 'day').format('YYYY-MM-DD'), dayjs().format('YYYY-MM-DD')],
  category: null,
  paymentMethod: null
})

const kpiList = computed(() => [
  { key: 'amount', label: '销售总金额', value: `¥${summaryData.value.total_amount.toFixed(2)}`, color: 'text-danger' },
  { key: 'cost', label: '销售总成本', value: `¥${summaryData.value.total_cost.toFixed(2)}`, color: '' },
  { key: 'profit', label: '总毛利', value: `¥${summaryData.value.total_profit.toFixed(2)}`, color: 'text-primary' },
  { key: 'quantity', label: '销售总数量', value: `${summaryData.value.total_quantity} 件`, color: 'text-warning' }
])

const trendChartOption = computed(() => ({
  tooltip: { trigger: 'axis', formatter: (params) => `${params[0].name}<br/>销售额: ¥${params[0].value.toFixed(2)}` },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: trendData.value.map(d => d.date), boundaryGap: false },
  yAxis: { type: 'value', name: '金额(元)' },
  series: [{ type: 'line', smooth: true, data: trendData.value.map(d => d.value), areaStyle: { color: 'rgba(245, 108, 108, 0.2)' }, lineStyle: { color: '#f56c6c' }, itemStyle: { color: '#f56c6c' } }]
}))

const barChartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
  xAxis: { type: 'category', data: distributionData.value.map(d => d.name), axisLabel: { rotate: 20 } },
  yAxis: { type: 'value', name: '金额(元)' },
  series: [{ type: 'bar', data: distributionData.value.map(d => d.value), itemStyle: { color: '#f56c6c', borderRadius: [4, 4, 0, 0] }, barWidth: '40%' }]
}))

async function fetchData() {
  loading.value = true
  try {
    const params = {
      start_date: filters.dateRange?.[0],
      end_date: filters.dateRange?.[1],
      category: filters.category || undefined,
      payment_method: filters.paymentMethod || undefined,
      page: page.value,
      page_size: pageSize.value
    }
    const res = await request.get('/stats/items', { params })
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
    const [catRes, pmRes] = await Promise.all([
      request.get('/item-categories'),
      getPaymentMethods()
    ])
    if (catRes.code === 0 && catRes.data) categoryOptions.value = catRes.data
    if (pmRes.code === 0 && pmRes.data) paymentMethodOptions.value = pmRes.data
  } catch (e) { console.error(e) }
}

function resetFilters() {
  filters.dateRange = [dayjs().subtract(30, 'day').format('YYYY-MM-DD'), dayjs().format('YYYY-MM-DD')]
  filters.category = null
  filters.paymentMethod = null
  page.value = 1
  fetchData()
}

async function handleExport() {
  try {
    const params = {
      start_date: filters.dateRange?.[0],
      end_date: filters.dateRange?.[1],
      category: filters.category || undefined,
      payment_method: filters.paymentMethod || undefined
    }
    const res = await request.get('/stats/items/export', { params, responseType: 'blob' })
    const url = URL.createObjectURL(res)
    const link = document.createElement('a')
    link.href = url
    link.download = `物品统计_${dayjs().format('YYYYMMDD')}.xlsx`
    link.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败')
  }
}

onMounted(() => { loadOptions(); fetchData() })
</script>