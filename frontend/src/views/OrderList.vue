<template>
  <div class="order-page">
    <el-tabs v-model="activeTab" @tab-click="handleTabClick">
      <!-- 报名记录页签 -->
      <el-tab-pane label="报名记录" name="enroll">
        <div class="filter-bar">
          <div class="filter-left">
            <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD" style="width:400px" @change="fetchOrders" />
            <el-input v-model="searchName" placeholder="搜索学员姓名" clearable style="width:200px" @change="fetchOrders" />
          </div>
          <ExportExcel :fetch-fn="exportOrders" filename="订单导出.xlsx" class="export-btn" />
        </div>
        <div class="table-wrapper">
          <el-table :data="orders" v-loading="loading" border stripe style="width:100%" height="100%">
            <el-table-column prop="order_no" label="订单号" width="150" fixed="left" />
            <el-table-column label="订单状态" width="90"><template #default="{ row }"><el-tag :type="row.is_invalid ? 'danger' : 'success'" size="small">{{ row.is_invalid ? '已作废' : '已生效' }}</el-tag></template></el-table-column>
            <el-table-column prop="created_at" label="报名时间" width="160"><template #default="{ row }">{{ row.created_at?.substr(0,16) }}</template></el-table-column>
            <el-table-column label="学员" min-width="160">
              <template #default="{ row }">
                <div class="student-info-cell">
                  <AppImage :src="row.student_avatar" :size="28" shape="circle" />
                  <div class="student-detail">
                    <div class="student-name">{{ row.student_name }}</div>
                  </div>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="enroll_type" label="类型" width="70" />
            <el-table-column prop="course_name" label="课程" width="120" />
            <el-table-column prop="class_name" label="班级" width="120" />
            <el-table-column prop="purchase_hours" label="购买课时" width="90" />
            <el-table-column label="原价" width="90"><template #default="{ row }">¥{{ row.total_price }}</template></el-table-column>
            <el-table-column label="优惠方式" width="150"><template #default="{ row }">{{ formatDiscountMethod(row) }}</template></el-table-column>
            <el-table-column label="优惠" width="80"><template #default="{ row }">¥{{ row.discount_amount }}</template></el-table-column>
            <el-table-column label="应付" width="90"><template #default="{ row }">¥{{ row.payable_amount }}</template></el-table-column>
            <el-table-column label="实付" width="90"><template #default="{ row }">¥{{ row.total_paid }}</template></el-table-column>
            <el-table-column label="欠款" width="90"><template #default="{ row }"><span v-if="row.arrears > 0" class="text-danger">¥{{ row.arrears }}</span><span v-else style="color:#909399">0</span></template></el-table-column>
            <el-table-column prop="payment_method" label="支付方式" width="90" />
            <el-table-column label="有效期" width="100"><template #default="{ row }">{{ formatValidity(row) }}</template></el-table-column>
            <el-table-column label="请假限制" width="110"><template #default="{ row }">{{ formatLeaveLimit(row) }}</template></el-table-column>
            <el-table-column label="赠送课时" width="90"><template #default="{ row }">{{ row.gift_hours || 0 }}课时</template></el-table-column>
            <el-table-column label="赠送说明" min-width="120"><template #default="{ row }">{{ row.gift_note || '-' }}</template></el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <div class="action-buttons">
                  <el-button type="danger" link size="small" @click="handleInvalidOrder(row)" :disabled="row.is_invalid || !row.can_invalidate" :title="row.is_invalid ? '订单已作废' : (row.invalidate_reason || '作废订单')">作废</el-button>
                  <el-button type="success" link size="small" @click="openRepayModal(row)" :disabled="row.is_invalid || row.arrears <= 0">补缴</el-button>
                  <el-button type="info" link size="small" @click="showPaymentFlow(row)">流水</el-button>
                  <el-button type="primary" link size="small" @click="printOrder(row)">打印</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
        <div class="pagination-box" v-if="total > pageSize"><el-pagination v-model:current-page="page" :page-size="pageSize" :total="total" layout="prev, pager, next" @current-change="fetchOrders" /></div>
      </el-tab-pane>

      <!-- 尾款补费页签 -->
      <el-tab-pane label="尾款补费" name="repay">
        <div class="filter-bar">
          <div class="filter-left">
            <el-date-picker v-model="repayDateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD" style="width:400px" @change="fetchRepayRecords" />
            <el-input v-model="repaySearch" placeholder="学员姓名/订单号" clearable style="width:200px" @change="fetchRepayRecords" />
          </div>
        </div>
        <div class="table-wrapper">
          <el-table :data="repayRecords" v-loading="repayLoading" border stripe style="width:100%" height="100%">
            <el-table-column label="学员" min-width="160">
              <template #default="{ row }">
                <div class="student-info-cell">
                  <AppImage :src="row.student_avatar" :size="28" shape="circle" />
                  <div class="student-name">{{ row.student_name }}</div>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="student_phone" label="联系方式" width="120" />
            <el-table-column prop="order_no" label="订单号" width="160" />
            <el-table-column prop="repay_time" label="补费时间" width="160" />
            <el-table-column prop="course_name" label="补费课程" min-width="120" />
            <el-table-column label="变更前尾款金额" width="130">
              <template #default="{ row }">¥{{ row.before_arrears.toFixed(2) }}</template>
            </el-table-column>
            <el-table-column label="补交金额" width="100">
              <template #default="{ row }">¥{{ row.repay_amount.toFixed(2) }}</template>
            </el-table-column>
            <el-table-column label="变更后尾款金额" width="130">
              <template #default="{ row }">¥{{ row.after_arrears.toFixed(2) }}</template>
            </el-table-column>
            <el-table-column prop="payment_method" label="支付方式" width="100" />
            <el-table-column label="赠送积分" width="80">
              <template #default="{ row }">{{ row.points_granted }}分</template>
            </el-table-column>
            <el-table-column prop="operator" label="经办人" width="100" />
            <el-table-column prop="operate_time" label="经办时间" width="160" />
            <el-table-column prop="remark" label="备注" min-width="150" />
            <el-table-column label="操作" width="80" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="printRepayReceipt(row)">打印小票</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
        <div class="pagination-box" v-if="repayTotal > pageSize"><el-pagination v-model:current-page="repayPage" :page-size="pageSize" :total="repayTotal" layout="prev, pager, next" @current-change="fetchRepayRecords" /></div>
      </el-tab-pane>
    </el-tabs>

    <!-- 补缴尾款模态框 -->
    <el-dialog v-model="repayDialogVisible" title="补缴尾款" width="500px">
      <el-form label-width="100px">
        <el-form-item label="订单号"><span>{{ currentOrder?.order_no }}</span></el-form-item>
        <el-form-item label="学员姓名"><span>{{ currentOrder?.student_name }}</span></el-form-item>
        <el-form-item label="报名课程"><span>{{ currentOrder?.course_name }}</span></el-form-item>
        <el-form-item label="报名时间"><span>{{ currentOrder?.created_at?.substr(0,16) }}</span></el-form-item>
        <el-form-item label="当前欠款"><span class="text-danger">¥{{ currentOrder?.arrears }}</span></el-form-item>
        <el-form-item label="补缴金额">
          <el-input-number v-model="repayAmount" :min="0.01" :max="currentOrder?.arrears" :precision="2" :step="0.01" controls-position="right" style="width:180px" />
        </el-form-item>
        <el-form-item label="支付方式">
          <el-select v-model="repayMethod" style="width:140px">
            <el-option v-for="m in paymentMethodOptions" :key="m" :label="m" :value="m" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="repayDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmRepay" :loading="repaying">确认补缴</el-button>
      </template>
    </el-dialog>

    <!-- 收款流水模态框（仅用于报名记录页签） -->
    <el-dialog v-model="flowDialogVisible" title="收款流水" width="800px">
      <div class="flow-order-summary">
        <el-descriptions :column="4" border size="small">
          <el-descriptions-item label="订单号">{{ flowOrderInfo.order_no }}</el-descriptions-item>
          <el-descriptions-item label="报名时间">{{ flowOrderInfo.created_at }}</el-descriptions-item>
          <el-descriptions-item label="学员姓名">{{ flowOrderInfo.student_name }}</el-descriptions-item>
          <el-descriptions-item label="联系方式">{{ flowOrderInfo.student_phone }}</el-descriptions-item>
          <el-descriptions-item label="剩余尾款" :span="4"><span class="text-danger">¥{{ flowOrderInfo.arrears }}</span></el-descriptions-item>
        </el-descriptions>
      </div>
      <el-table :data="paymentFlow" border stripe style="margin-top:16px;">
        <el-table-column prop="occurred_at" label="时间" width="180" />
        <el-table-column label="金额" width="100"><template #default="{ row }">¥{{ row.amount }}</template></el-table-column>
        <el-table-column prop="payment_method" label="支付方式" width="100" />
        <el-table-column label="类型" width="80"><template #default="{ row }"><el-tag :type="row.type === 'initial' ? 'primary' : 'success'" size="small">{{ row.type === 'initial' ? '首付' : '补缴' }}</el-tag></template></el-table-column>
        <el-table-column prop="remark" label="备注" min-width="200" />
      </el-table>
      <div v-if="paymentFlow.length === 0" class="empty-tip">暂无收款记录</div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import ExportExcel from '@/components/ExportExcel.vue'
import { getOrderList, invalidOrder as invalidOrderApi, exportOrders as exportOrdersApi, getRepayRecords } from '@/api/order'
import request from '@/api/request'
import { getPaymentMethods } from '@/api/settings'

// ========== 报名记录相关 ==========
const orders = ref([])
const loading = ref(false)
const searchName = ref('')
const dateRange = ref(null)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const paymentMethodOptions = ref(['微信', '支付宝', '现金', '银行转账'])
const repayDialogVisible = ref(false)
const currentOrder = ref(null)
const repayAmount = ref(0)
const repayMethod = ref('微信')
const repaying = ref(false)
const flowDialogVisible = ref(false)
const paymentFlow = ref([])
const flowOrderInfo = ref({ order_no: '', created_at: '', student_name: '', student_phone: '', arrears: 0 })

// ========== 尾款补费相关 ==========
const activeTab = ref('enroll')
const repayRecords = ref([])
const repayLoading = ref(false)
const repaySearch = ref('')
const repayDateRange = ref(null)
const repayPage = ref(1)
const repayTotal = ref(0)

// ========== 方法 ==========
async function loadPaymentMethods() {
  try {
    const res = await getPaymentMethods()
    if (res.code === 0 && res.data && res.data.length) {
      paymentMethodOptions.value = res.data
      repayMethod.value = paymentMethodOptions.value[0] || '微信'
    } else {
      paymentMethodOptions.value = ['微信支付', '支付宝', '现金', '银行转账']
      repayMethod.value = '微信'
    }
  } catch (e) {
    console.error('加载支付方式失败，使用默认值', e)
    paymentMethodOptions.value = ['微信支付', '支付宝', '现金', '银行转账']
    repayMethod.value = '微信'
  }
}

async function fetchOrders() {
  loading.value = true
  const params = {}
  if (searchName.value) params.search = searchName.value
  if (dateRange.value && dateRange.value.length === 2) {
    params.start_date = dateRange.value[0]
    params.end_date = dateRange.value[1]
  }
  try {
    const res = await getOrderList(params)
    const ordersData = res.data || []
    const enriched = await Promise.all(ordersData.map(async (order) => {
      if (order.is_invalid) return { ...order, can_invalidate: false, invalidate_reason: '订单已作废' }
      try {
        const checkRes = await request.get(`/order/orders/${order.id}/can-invalidate`)
        if (checkRes.code === 0) {
          return { ...order, can_invalidate: checkRes.data.can_invalidate, invalidate_reason: checkRes.data.reason }
        }
      } catch (e) {
        console.error(e)
      }
      return { ...order, can_invalidate: true, invalidate_reason: '' }
    }))
    orders.value = enriched
    total.value = enriched.length
  } finally {
    loading.value = false
  }
}

async function handleInvalidOrder(row) {
  if (row.is_invalid) {
    ElMessage.warning('订单已作废')
    return
  }
  if (!row.can_invalidate) {
    ElMessage.warning(row.invalidate_reason || '该订单无法作废')
    return
  }
  try {
    await ElMessageBox.confirm(`确认作废订单 ${row.order_no}？作废后不可恢复。`, '提示', { type: 'warning' })
    await invalidOrderApi(row.id)
    ElMessage.success('订单已作废')
    await fetchOrders()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(err.response?.data?.detail || '作废失败')
    }
  }
}

function openRepayModal(row) {
  if (row.is_invalid) {
    ElMessage.warning('已作废订单不能补缴')
    return
  }
  if (row.arrears <= 0) {
    ElMessage.warning('该订单无欠款')
    return
  }
  currentOrder.value = row
  repayAmount.value = row.arrears
  repayMethod.value = paymentMethodOptions.value[0] || '微信'
  repayDialogVisible.value = true
}

async function confirmRepay() {
  if (!repayAmount.value || repayAmount.value <= 0) {
    ElMessage.warning('请输入补缴金额')
    return
  }
  if (repayAmount.value > currentOrder.value.arrears) {
    ElMessage.warning('补缴金额不能超过欠款金额')
    return
  }
  repaying.value = true
  try {
    await request.post(`/order/orders/${currentOrder.value.id}/repay`, null, {
      params: { amount: repayAmount.value, payment_method: repayMethod.value }
    })
    ElMessage.success('补缴成功')
    repayDialogVisible.value = false
    await fetchOrders()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '补缴失败')
  } finally {
    repaying.value = false
  }
}

function showPaymentFlow(row) {
  flowOrderInfo.value = {
    order_no: row.order_no,
    created_at: row.created_at?.substr(0, 16) || '',
    student_name: row.student_name,
    student_phone: row.student_phone,
    arrears: row.arrears
  }
  paymentFlow.value = row.payment_history || []
  flowDialogVisible.value = true
}

function formatDiscountMethod(order) {
  const mode = order.discount_mode
  const rate = order.discount_rate
  const direct = order.direct_reduction
  if (mode === 'direct') return `直减（${direct}元）`
  if (mode === 'discount') return `折扣（${rate}折）`
  if (mode === 'discount_then_direct') return `先折扣再直减（${rate}折，${direct}元）`
  if (mode === 'direct_then_discount') return `先直减再折扣（${direct}元，${rate}折）`
  return '无'
}

function formatValidity(order) {
  return order.validity_type === 'days' && order.validity_value ? `${order.validity_value}天` : '-'
}

function formatLeaveLimit(order) {
  if (order.leave_limit === '不限制') return '不限制'
  if (order.leave_limit === '不允许') return '不允许'
  if (order.leave_limit === '限制次数') return `限制${order.leave_limit_count}次`
  return '-'
}

function printOrder(row) {
  const win = window.open('', '', 'width=400,height=500')
  win.document.write(`
    <html>
    <head><title>订单小票</title>
    <style>body{font-family:monospace;padding:20px}h2{text-align:center}table{width:100%;border-collapse:collapse}td{padding:4px 0;border-bottom:1px dashed var(--gray-300)}</style>
    </head>
    <body>
      <h2>Bobi艺术·报名小票</h2>
      <table>
        <tr><td style="width:100px">订单号</td><td>${row.order_no}</td></tr>
        <tr><td>学员</td><td>${row.student_name}</td></tr>
        <tr><td>课程</td><td>${row.course_name}</td></tr>
        <tr><td>班级</td><td>${row.class_name || '-'}</td></tr>
        <tr><td>购买课时</td><td>${row.purchase_hours}</td></tr>
        <tr><td>应付金额</td><td>¥${row.payable_amount}</td></tr>
        <tr><td>实付金额</td><td>¥${row.total_paid}</td></tr>
        <tr><td>支付方式</td><td>${row.payment_method}</td></tr>
        <tr><td>时间</td><td>${row.created_at}</td></tr>
      </table>
    </body>
    </html>
  `)
  win.document.close()
  win.print()
}

async function exportOrders() {
  return exportOrdersApi()
}

// ========== 尾款补费相关方法 ==========
async function fetchRepayRecords() {
  repayLoading.value = true
  const params = {
    page: repayPage.value,
    page_size: pageSize.value,
    search: repaySearch.value || undefined,
    start_date: repayDateRange.value?.[0],
    end_date: repayDateRange.value?.[1]
  }
  try {
    const res = await getRepayRecords(params)
    repayRecords.value = res.data?.items || []
    repayTotal.value = res.data?.total || 0
  } catch (error) {
    ElMessage.error('加载尾款补费记录失败')
  } finally {
    repayLoading.value = false
  }
}

function printRepayReceipt(row) {
  const win = window.open('', '', 'width=400,height=600')
  win.document.write(`
    <html>
    <head><title>尾款补费小票</title>
    <style>body{font-family:monospace;padding:20px}h2{text-align:center}table{width:100%;border-collapse:collapse}td{padding:4px 0;border-bottom:1px dashed var(--gray-300)}</style>
    </head>
    <body>
      <h2>Bobi艺术·尾款补费凭证</h2>
      <table>
        <tr><td style="width:120px">订单号</td><td>${row.order_no}</td></tr>
        <tr><td>学员姓名</td><td>${row.student_name}</td></tr>
        <tr><td>补费课程</td><td>${row.course_name}</td></tr>
        <tr><td>补费时间</td><td>${row.repay_time}</td></tr>
        <tr><td>变更前尾款</td><td>¥${row.before_arrears.toFixed(2)}</td></tr>
        <tr><td>补交金额</td><td>¥${row.repay_amount.toFixed(2)}</td></tr>
        <tr><td>变更后尾款</td><td>¥${row.after_arrears.toFixed(2)}</td></tr>
        <tr><td>支付方式</td><td>${row.payment_method}</td></tr>
        <tr><td>赠送积分</td><td>${row.points_granted}分</td></tr>
        <tr><td>经办人</td><td>${row.operator}</td></tr>
        <tr><td>经办时间</td><td>${row.operate_time}</td></tr>
        <tr><td>备注</td><td>${row.remark}</td></tr>
      </table>
    </body>
    </html>
  `)
  win.document.close()
  win.print()
}

function handleTabClick() {
  if (activeTab.value === 'repay') {
    fetchRepayRecords()
  }
}

onMounted(async () => {
  await loadPaymentMethods()
  await fetchOrders()
})
</script>

<style scoped>
.order-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  padding: 16px;
}
.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  flex-shrink: 0;
}
.filter-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.table-wrapper {
  flex: 1;
  overflow: hidden;
  min-height: 0;
}
.table-wrapper :deep(.el-table) {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.table-wrapper :deep(.el-table__body-wrapper) {
  flex: 1;
  overflow-y: auto;
}
.pagination-box {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
  flex-shrink: 0;
}
.text-danger {
  color: var(--danger);
}
.empty-tip {
  text-align: center;
  padding: 20px;
  color: var(--text-secondary);
}
.action-buttons {
  display: flex;
  flex-wrap: nowrap;
  gap: 6px;
  align-items: center;
  white-space: nowrap;
}
.action-buttons .el-button {
  margin: 0;
  padding: 0 4px;
}
.flow-order-summary {
  margin-bottom: 16px;
}
.student-info-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}
.student-avatar {
  flex-shrink: 0;
}
.student-detail {
  display: flex;
  flex-direction: column;
}
.student-name {
  font-weight: 500;
}
.student-phone {
  font-size: 12px;
  color: var(--text-secondary);
}
</style>