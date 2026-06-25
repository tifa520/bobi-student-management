<template>
  <div class="order-timeline">
    <div v-if="orders.length === 0" class="empty">暂无订单记录</div>
    <el-timeline v-else>
      <el-timeline-item
        v-for="order in timelineData"
        :key="order.id"
        :timestamp="order.timeLabel"
        placement="top"
        :color="order.statusColor"
      >
        <el-card shadow="hover" class="timeline-order-card">
          <div class="timeline-card-header">
            <div class="timeline-order-no">
              <span class="order-no-label">订单号：</span>
              <span class="order-no-text">{{ order.order_no }}</span>
              <el-tag :type="order.enrollTypeTag" size="small" class="timeline-enroll-tag">{{ order.enroll_type }}</el-tag>
              <el-tag v-if="order.is_invalid" type="danger" size="small">已作废</el-tag>
            </div>
            <el-button type="primary" link size="small" @click="printOrder(order)">打印小票</el-button>
          </div>
          <el-divider style="margin:8px 0" />
          <div class="timeline-body">
            <div class="info-grid">
              <div class="info-item"><span class="info-label">订单号：</span>{{ order.order_no }}</div>
              <div class="info-item"><span class="info-label">报名时间：</span>{{ order.created_at }}</div>
              <div class="info-item"><span class="info-label">课程：</span>{{ order.course_name }}</div>
              <div class="info-item"><span class="info-label">班级：</span>{{ order.class_name || '-' }}</div>
              <div class="info-item"><span class="info-label">购买课时：</span>{{ order.purchase_hours }}课时</div>
              <div class="info-item"><span class="info-label">赠送课时：</span>{{ order.gift_hours }}课时</div>
              <div class="info-item"><span class="info-label">总金额：</span><span class="text-danger">¥{{ order.total_price }}</span></div>
              <div class="info-item"><span class="info-label">优惠金额：</span><span class="text-danger">¥{{ order.discount_amount || 0 }}</span></div>
              <div class="info-item"><span class="info-label">应付金额：</span><span class="text-danger">¥{{ order.payable_amount }}</span></div>
              <div class="info-item"><span class="info-label">实付金额：</span><span class="text-danger">¥{{ order.total_paid }}</span></div>
              <div class="info-item"><span class="info-label">实际课时单价：</span><span class="text-danger">¥{{ order.actual_unit_price }}/课时</span></div>
              <div v-if="order.arrears > 0" class="info-item"><span class="info-label">尾款金额：</span><span class="text-danger">¥{{ order.arrears }}</span></div>
              <div v-else-if="order.total_repay_amount > 0" class="info-item"><span class="info-label">尾款状态：</span><span class="text-success">已补交 ¥{{ order.total_repay_amount }}</span></div>
              <div class="info-item"><span class="info-label">支付方式：</span>{{ order.payment_method }}</div>
              <div class="info-item"><span class="info-label">有效期：</span>{{ order.validity_value }}天</div>
              <div class="info-item"><span class="info-label">请假限制：</span>{{ order.leave_limit === '限制次数' ? order.leave_limit_count + '次' : order.leave_limit }}</div>
            </div>
          </div>
        </el-card>
      </el-timeline-item>
    </el-timeline>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
dayjs.locale('zh-cn')

const props = defineProps({ orders: { type: Array, default: () => [] } })

const timelineData = computed(() => {
  const enrollTypeMap = { '新报': '', '续报': 'success', '扩科': 'warning', '尾款补费': 'info' }
  const statusColorMap = { '新报': '#36b459', '续报': '#409eff', '扩科': '#e6a23c', '尾款补费': '#909399' }
  return props.orders.map(order => {
    const actualUnitPrice = order.actual_unit_price || (order.payable_amount / order.purchase_hours).toFixed(2)
    return {
      ...order,
      actual_unit_price: actualUnitPrice,
      timeLabel: order.created_at ? dayjs(order.created_at).format('YYYY年MM月DD日 dddd HH:mm') : '',
      enrollTypeTag: enrollTypeMap[order.enroll_type] || '',
      statusColor: order.is_invalid ? '#f56c6c' : (statusColorMap[order.enroll_type] || '#36b459'),
      arrears: Math.max(0, (order.payable_amount || 0) - (order.total_paid || 0))
    }
  }).sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
})

function printOrder(order) {
  const content = `<html><head><title>订单小票</title><style>body{font-family:monospace;padding:20px}h2{text-align:center}table{width:100%;border-collapse:collapse}td{padding:4px 0;border-bottom:1px dashed #ccc}</style></head><body><h2>Bobi艺术·报名小票</h2><tr><td style="width:100px">订单号</td><td>${order.order_no}</td></tr><tr><td>学员</td><td>${order.student_name}</td></tr><tr><td>课程</td><td>${order.course_name}</td></tr><tr><td>班级</td><td>${order.class_name || '-'}</td></tr><tr><td>购买课时</td><td>${order.purchase_hours}</td></tr><tr><td>应付金额</td><td>¥${order.payable_amount}</td></tr><tr><td>实付金额</td><td>¥${order.total_paid}</td></tr><tr><td>支付方式</td><td>${order.payment_method}</td></tr><tr><td>时间</td><td>${order.created_at}</td></tr></table></body></html>`
  const win = window.open('', '', 'width=400,height=500')
  win.document.write(content)
  win.document.close()
  win.print()
}
</script>

<style scoped>
.order-timeline { max-width: 100%; margin: 0; }
.empty { text-align: center; padding: 40px; color: #909399; }
.timeline-order-card { border-radius: 12px; border: 1px solid #e4e7ed; margin-bottom: 8px; }
.timeline-card-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; }
.timeline-order-no { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.order-no-label { color: #909399; font-size: 14px; }
.order-no-text { font-weight: 600; font-size: 15px; color: #303133; }
.timeline-enroll-tag { margin-left: 8px; }
.timeline-body { padding: 4px 0; }
.info-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px 24px;
}
@media (max-width: 1000px) {
  .info-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 600px) {
  .info-grid { grid-template-columns: 1fr; }
}
.info-item { font-size: 14px; line-height: 1.8; }
.info-label { color: #909399; margin-right: 8px; white-space: nowrap; }
.text-success { color: #67c23a; }
.text-danger { color: #f56c6c; }
.text-primary { color: var(--primary-color); }
</style>