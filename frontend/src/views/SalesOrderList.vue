<template>
  <div class="sales-order-list">
    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-input v-model="filters.search" placeholder="订单号/学员姓名" clearable style="width: 200px" @clear="fetchOrders" @keyup.enter="fetchOrders" />
      <el-select v-model="filters.status" placeholder="订单状态" clearable style="width: 120px" @change="fetchOrders">
        <el-option label="已支付" value="paid" />
        <el-option label="已退款" value="refunded" />
      </el-select>
      <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD" style="width: 260px" @change="fetchOrders" />
      <el-button type="primary" @click="fetchOrders">查询</el-button>
    </div>

    <!-- 表格（宽度100%） -->
    <el-table :data="orders" v-loading="loading" border stripe style="width: 100%">
      <el-table-column prop="order_no" label="订单号" width="180" />
      <el-table-column label="学员" width="180" fixed="left">
        <template #default="{ row }">
          <div style="display: flex; align-items: center; gap: 10px; height: 100%;">
            <AppImage :src="row.student_avatar" :size="32" shape="circle" />
            <span style="line-height: 1.4;">{{ row.student_name }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="student_phone" label="联系方式" width="130" />
      <el-table-column label="应付金额" width="110">
        <template #default="{ row }">¥{{ row.total_amount.toFixed(2) }}</template>
      </el-table-column>
      <el-table-column label="实付现金" width="110">
        <template #default="{ row }">¥{{ row.paid_amount.toFixed(2) }}</template>
      </el-table-column>
      <el-table-column label="使用积分" width="100">
        <template #default="{ row }">{{ row.used_points || 0 }}分</template>
      </el-table-column>
      <el-table-column label="支付方式" width="180">
        <template #default="{ row }">
          <div v-for="(p, idx) in row.payment_details" :key="idx" class="payment-item">
            <span>{{ p.method }}: </span>
            <span v-if="p.type === 'cash'">¥{{ p.amount }}</span>
            <span v-else-if="p.type === 'points'">{{ p.points }}积分</span>
            <span v-else>{{ p.amount ? '¥'+p.amount : (p.points||0)+'积分' }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'paid' ? 'success' : 'danger'">{{ row.status === 'paid' ? '已支付' : '已退款' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="160" />
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link size="small" @click="viewDetail(row)">详情</el-button>
          <el-button v-if="row.status === 'paid'" type="danger" link size="small" @click="refundOrder(row)">退款</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-box" v-if="total > pageSize">
      <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total" layout="prev, pager, next" @current-change="fetchOrders" />
    </div>

    <!-- 订单详情弹窗 -->
    <el-dialog v-model="detailVisible" title="订单详情" width="700px">
      <div v-if="currentOrder" class="order-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="订单号">{{ currentOrder.order_no }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="currentOrder.status === 'paid' ? 'success' : 'danger'">{{ currentOrder.status === 'paid' ? '已支付' : '已退款' }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="学员姓名">{{ currentOrder.student_name }}</el-descriptions-item>
          <el-descriptions-item label="联系方式">{{ currentOrder.student_phone }}</el-descriptions-item>
          <el-descriptions-item label="应付总额">¥{{ currentOrder.total_amount.toFixed(2) }}</el-descriptions-item>
          <el-descriptions-item label="实付现金">¥{{ currentOrder.paid_amount.toFixed(2) }}</el-descriptions-item>
          <el-descriptions-item label="使用积分">{{ currentOrder.used_points || 0 }}分</el-descriptions-item>
          <el-descriptions-item label="支付方式" :span="2">
            <div v-for="(p, idx) in currentOrder.payment_details" :key="idx">
              {{ p.method }}: {{ p.type === 'cash' ? '¥'+p.amount : (p.points||0)+'积分' }}
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ currentOrder.created_at }}</el-descriptions-item>
        </el-descriptions>
        <el-divider>商品明细</el-divider>
        <el-table :data="currentOrder.items" border stripe>
          <el-table-column prop="item_name" label="商品名称" />
          <el-table-column prop="quantity" label="数量" width="80" />
          <el-table-column label="单价" width="100"><template #default="{ row }">¥{{ row.unit_price }}</template></el-table-column>
          <el-table-column label="小计" width="100"><template #default="{ row }">¥{{ row.subtotal }}</template></el-table-column>
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/api/request'

const orders = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filters = reactive({ search: '', status: '' })
const dateRange = ref(null)

const detailVisible = ref(false)
const currentOrder = ref(null)

async function fetchOrders() {
  loading.value = true
  const params = {
    page: page.value,
    page_size: pageSize.value,
    search: filters.search || undefined,
    status: filters.status || undefined,
    start_date: dateRange.value?.[0],
    end_date: dateRange.value?.[1]
  }
  try {
    const res = await request.get('/sales/orders', { params })
    orders.value = res.data?.items || []
    total.value = res.data?.total || 0
  } catch (err) {
    ElMessage.error('加载订单列表失败')
  } finally {
    loading.value = false
  }
}

async function viewDetail(row) {
  try {
    const res = await request.get(`/sales/orders/${row.id}`)
    if (res.code === 0) {
      currentOrder.value = res.data
      detailVisible.value = true
    } else {
      ElMessage.error(res.message || '获取订单详情失败')
    }
  } catch {
    ElMessage.error('获取订单详情失败')
  }
}

async function refundOrder(row) {
  try {
    const { value: reason } = await ElMessageBox.prompt('请输入退款原因', '订单退款', {
      confirmButtonText: '确认退款',
      cancelButtonText: '取消',
      inputType: 'textarea'
    })
    await request.post(`/sales/orders/${row.id}/refund`, { reason: reason || '' })
    ElMessage.success('退款成功')
    await fetchOrders()
    if (detailVisible.value && currentOrder.value?.id === row.id) {
      detailVisible.value = false
    }
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error('退款失败')
    }
  }
}

onMounted(fetchOrders)
</script>

<style scoped>
/* 完全参考 ScoreRecord.vue 结构，但移除容器 margin/padding，使其铺满父容器 */
.sales-order-list {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--app-bg);
  /* 关键：移除所有外边距和内边距，让父容器决定 */
  margin: 0;
  padding: 0;
}

/* 筛选栏样式（与 ScoreRecord 类似，但保留内边距不影响表格宽度） */
.filter-bar {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 0;         /* 改为0，让筛选栏紧贴顶部 */
  padding: 16px 20px;       /* 保留内边距，但左右20px不影响表格宽度（表格已100%） */
  background: var(--surface);
  border-bottom: 1px solid var(--border-light);
  flex-wrap: wrap;
  flex-shrink: 0;
}

/* 表格本身已经 width:100%，无需额外设置 */
.el-table {
  flex: 1;
  width: 100%;
  margin: 0;
}

/* 分页栏 */
.pagination-box {
  margin-top: 0;
  padding: 16px 20px;
  background: var(--surface);
  border-top: 1px solid var(--border-light);
  display: flex;
  justify-content: flex-end;
  flex-shrink: 0;
}

/* 支付方式内部样式（不影响布局） */
.payment-item {
  margin: 2px 0;
  white-space: nowrap;
}

/* 确保表格内部无额外空白 */
.el-table__header-wrapper table,
.el-table__body-wrapper table {
  width: 100%;
}
</style>