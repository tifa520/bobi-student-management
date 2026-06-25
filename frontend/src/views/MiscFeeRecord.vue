<template>
  <div class="page-container">
    <div class="filter-bar">
      <el-input v-model="filters.student_name" placeholder="学员姓名" clearable style="width:160px" @change="fetchFees" />
      <el-select v-model="filters.fee_type" placeholder="费用类型" clearable style="width:140px" @change="fetchFees">
        <el-option label="物品销售" value="item_sale" />
        <el-option label="活动收费" value="activity" />
        <el-option label="退款" value="refund" />
      </el-select>
      <el-select v-model="filters.status" placeholder="缴费状态" clearable style="width:120px" @change="fetchFees">
        <el-option label="待缴费" value="pending" />
        <el-option label="部分缴纳" value="partial" />
        <el-option label="已结清" value="paid" />
        <el-option label="已退款" value="refunded" />
      </el-select>
      <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD" style="width:280px" @change="fetchFees" />
      <el-button type="primary" @click="fetchFees">查询</el-button>
    </div>

    <el-table :data="fees" v-loading="loading" border stripe>
      <el-table-column label="学员" min-width="180">
        <template #default="{ row }">
          <div class="student-info-cell">
            <AppImage :src="row.student_avatar" :size="28" />
            <div class="student-name">{{ row.student_name }}</div>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="费用类型" width="100">
        <template #default="{ row }">
          <span v-if="row.fee_type === 'refund'">退款</span>
          <span v-else-if="row.fee_type === 'item_sale'">物品销售</span>
          <span v-else-if="row.fee_type === 'activity'">活动收费</span>
          <span v-else>{{ row.fee_type }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="费用说明" min-width="200" />
      <el-table-column label="应收金额" width="100">
        <template #default="{ row }"><span :style="{ color: row.amount < 0 ? 'red' : '' }">￥{{ row.amount }}</span></template>
      </el-table-column>
      <el-table-column label="实收金额" width="100">
        <template #default="{ row }">
          <span v-if="row.points_used > 0">{{ row.points_used }}积分</span>
          <span v-else>￥{{ row.paid_amount }}</span>
        </template>
      </el-table-column>
      <el-table-column label="缴费状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'paid' ? 'success' : (row.status === 'partial' ? 'warning' : (row.status === 'refunded' ? 'danger' : 'danger'))" size="small">
            {{ row.status === 'paid' ? '已结清' : (row.status === 'partial' ? '部分缴纳' : (row.status === 'refunded' ? '已退款' : '待缴费')) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="payment_method" label="支付方式" width="100" />
      <el-table-column prop="paid_at" label="缴费时间" width="160" />
    </el-table>

    <div class="pagination-box" v-if="total > pageSize">
      <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total" layout="prev, pager, next" @current-change="fetchFees" />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import request from '@/api/request'
import { DEFAULT_AVATAR_SVG } from '@/utils/constants'

const fees = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filters = reactive({ student_name: '', fee_type: '', status: '' })
const dateRange = ref(null)

async function fetchFees() {
  loading.value = true
  const params = {
    page: page.value,
    page_size: pageSize.value,
    student_name: filters.student_name || undefined,
    fee_type: filters.fee_type || undefined,
    status: filters.status || undefined,
    start_date: dateRange.value?.[0],
    end_date: dateRange.value?.[1]
  }
  try {
    const res = await request.get('/misc-fees', { params })
    fees.value = res.data?.items || []
    total.value = res.data?.total || 0
  } finally {
    loading.value = false
  }
}

onMounted(fetchFees)
</script>

<style scoped>
.page-container { padding: 20px; }
.filter-bar { display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
.pagination-box { margin-top: 20px; display: flex; justify-content: flex-end; }
.student-info-cell { display: flex; align-items: center; gap: 10px; }
.student-name { font-weight: 500; }
.student-phone { font-size: 12px; color: var(--text-secondary); }
</style>