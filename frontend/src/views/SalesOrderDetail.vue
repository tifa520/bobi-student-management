<template>
  <div class="order-detail">
    <div class="detail-header">
      <el-button link @click="$router.back()"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
      <h2>订单详情</h2>
    </div>
    <div v-loading="loading">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="订单号">{{ order.order_no }}</el-descriptions-item>
        <el-descriptions-item label="订单状态"><el-tag :type="statusTag">{{ statusText }}</el-tag></el-descriptions-item>
        <el-descriptions-item label="学员姓名">{{ order.student_name }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ order.created_at }}</el-descriptions-item>
        <el-descriptions-item label="应付总额">¥{{ order.total_amount }}</el-descriptions-item>
        <el-descriptions-item label="实付现金">¥{{ order.paid_amount }}</el-descriptions-item>
        <el-descriptions-item label="使用积分">{{ order.used_points }} 分</el-descriptions-item>
        <el-descriptions-item label="支付方式详情">
          <div v-for="(p, idx) in order.payment_details" :key="idx">{{ p.method }}: {{ p.type === 'points' ? p.points + '分' : '¥' + p.amount }}</div>
        </el-descriptions-item>
      </el-descriptions>

      <h3>商品明细</h3>
      <el-table :data="order.items" border stripe>
        <el-table-column prop="item_name" label="商品名称" />
        <el-table-column prop="quantity" label="数量" width="80" />
        <el-table-column prop="unit_price" label="单价" width="100"><template #default="{ row }">¥{{ row.unit_price }}</template></el-table-column>
        <el-table-column prop="subtotal" label="小计" width="100"><template #default="{ row }">¥{{ row.subtotal }}</template></el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import request from '@/api/request'

const route = useRoute()
const orderId = route.params.id
const order = ref({})
const loading = ref(false)

const statusTag = computed(() => {
  const map = { paid: 'success', refunded: 'danger', partial_refund: 'warning' }
  return map[order.value.status] || 'info'
})
const statusText = computed(() => {
  const map = { paid: '已支付', refunded: '已退款', partial_refund: '部分退款' }
  return map[order.value.status] || order.value.status
})

async function fetchDetail() {
  loading.value = true
  try {
    const res = await request.get(`/sales/orders/${orderId}`)
    order.value = res.data || {}
  } finally { loading.value = false }
}

onMounted(fetchDetail)
</script>

<style scoped>
.order-detail { padding: 20px; }
.detail-header { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; }
</style>