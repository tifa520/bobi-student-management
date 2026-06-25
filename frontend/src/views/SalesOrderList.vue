<template>
  <div class="sales-order-list bobi-page">
    <!-- 页面标题 -->
    <div class="bobi-page-title">
      <div>
        <h1>销售订单</h1>
        <p>查看和管理所有销售订单记录</p>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="bobi-toolbar">
      <div class="filters-left">
        <el-input
          v-model="filters.search"
          placeholder="搜索订单号/学员姓名"
          clearable
          class="search-input"
          @clear="fetchOrders"
          @keyup.enter="fetchOrders"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select
          v-model="filters.status"
          placeholder="订单状态"
          clearable
          class="filter-select"
          @change="fetchOrders"
        >
          <el-option label="已支付" value="paid" />
          <el-option label="已退款" value="refunded" />
        </el-select>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          class="date-picker"
          @change="fetchOrders"
        />
      </div>
      <div class="filters-right">
        <el-button type="primary" @click="fetchOrders">
          <el-icon><Search /></el-icon>
          查询
        </el-button>
      </div>
    </div>

    <!-- 表格区域 -->
    <div class="table-section">
      <el-table :data="orders" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="order_no" label="订单号" width="180">
          <template #default="{ row }">
            <span class="order-no">{{ row.order_no }}</span>
          </template>
        </el-table-column>
        <el-table-column label="学员" width="180">
          <template #default="{ row }">
            <div class="student-cell">
              <AppImage :src="row.student_avatar" :size="36" shape="circle" class="student-avatar" />
              <div class="student-info">
                <span class="student-name">{{ row.student_name }}</span>
                <span class="student-phone">{{ row.student_phone }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="应付金额" width="120" align="right">
          <template #default="{ row }">
            <span class="amount-total">¥{{ row.total_amount.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="实付现金" width="120" align="right">
          <template #default="{ row }">
            <span class="amount-paid">¥{{ row.paid_amount.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="使用积分" width="110" align="center">
          <template #default="{ row }">
            <el-tag size="small" type="warning" effect="light">{{ row.used_points || 0 }} 积分</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="支付方式" min-width="180">
          <template #default="{ row }">
            <div class="payment-list">
              <div v-for="(p, idx) in row.payment_details" :key="idx" class="payment-item">
                <span class="payment-method">{{ p.method }}</span>
                <span class="payment-amount">
                  <template v-if="p.type === 'cash'">¥{{ p.amount }}</template>
                  <template v-else-if="p.type === 'points'">{{ p.points }}积分</template>
                  <template v-else>{{ p.amount ? '¥'+p.amount : (p.points||0)+'积分' }}</template>
                </span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'paid' ? 'success' : 'danger'" size="small" effect="light">
              {{ row.status === 'paid' ? '已支付' : '已退款' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160" />
        <el-table-column label="操作" width="140" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button type="primary" link size="small" @click="viewDetail(row)">详情</el-button>
              <el-button v-if="row.status === 'paid'" type="danger" link size="small" @click="refundOrder(row)">退款</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper" v-if="total > pageSize">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="fetchOrders"
        />
      </div>
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
import { Search } from '@element-plus/icons-vue'
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
.sales-order-list {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.filters-left {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.filters-right {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.search-input {
  width: 240px;
}

.filter-select {
  width: 130px;
}

.date-picker {
  width: 280px;
}

.order-no {
  font-family: var(--font-mono);
  font-weight: 600;
  color: var(--text-primary);
  font-size: 13px;
}

.student-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.student-avatar {
  flex-shrink: 0;
  border: 2px solid var(--brand-100);
}

.student-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.student-name {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 13px;
}

.student-phone {
  font-size: 12px;
  color: var(--text-secondary);
  font-family: var(--font-mono);
}

.amount-total {
  font-family: var(--font-mono);
  font-weight: 700;
  color: var(--text-primary);
  font-size: 14px;
}

.amount-paid {
  font-family: var(--font-mono);
  font-weight: 700;
  color: var(--brand-600);
  font-size: 14px;
}

.payment-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.payment-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  font-size: 12px;
}

.payment-method {
  color: var(--text-secondary);
}

.payment-amount {
  font-weight: 600;
  color: var(--text-regular);
  font-family: var(--font-mono);
}

.action-buttons {
  display: flex;
  gap: var(--space-1);
  justify-content: center;
  align-items: center;
}

.order-detail {
  padding: 4px 0;
}

@media (max-width: 768px) {
  .search-input,
  .filter-select,
  .date-picker {
    width: 100%;
  }
  .filters-left,
  .filters-right {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>