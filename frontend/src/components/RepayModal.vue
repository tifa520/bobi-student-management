<template>
  <el-dialog
    v-model="dialogVisible"
    title="补缴尾款"
    width="500px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div v-if="loading" class="loading-tip">
      <el-icon class="is-loading"><Loading /></el-icon> 加载订单中...
    </div>
    <div v-else>
      <div class="student-info">学员：{{ studentName }}</div>

      <el-checkbox-group v-model="selectedOrderIds" @change="onSelectionChange">
        <div v-for="order in paginatedOrderList" :key="order.id" class="order-item">
          <el-checkbox :label="order.id" value="order.id">
            <span class="order-no">{{ order.order_no }}</span>
            <span class="order-course">{{ order.course_name }}</span>
            <span class="order-arrears">尾款 ¥{{ order.arrears }}</span>
          </el-checkbox>
        </div>
      </el-checkbox-group>

      <div v-if="orderList.length === 0" class="empty-tip">暂无待补缴订单</div>

      <!-- 分页 -->
      <div v-if="total > pageSize" class="pagination-box">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          size="small"
          @current-change="onPageChange"
        />
      </div>

      <el-form label-width="80px" style="margin-top: 20px">
        <el-form-item label="补缴金额">
          <el-input
            v-model.number="repayAmount"
            placeholder="0"
            link
            inputmode="decimal"
            class="repay-input"
          >
            <template #suffix><span class="suffix-text">元</span></template>
          </el-input>
        </el-form-item>
        <div v-if="repayAmount > 0" class="point-tip">
          本次补费将赠送 <strong>{{ Math.floor(repayAmount * 10) }}</strong> 积分
        </div>
      </el-form>

      <div v-if="totalArrears > 0" class="total-tip">
        所选订单总尾款：¥{{ totalArrears }}
      </div>
    </div>

    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button
        type="primary"
        @click="confirmRepay"
        :loading="submitting"
        :disabled="!canSubmit"
      >
        确认补费
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import { getOrderList, batchRepay } from '@/api/order'

const props = defineProps({
  visible: Boolean,
  studentId: Number,
  studentName: String
})

const emit = defineEmits(['update:visible', 'success'])

const dialogVisible = ref(false)
const loading = ref(false)
const submitting = ref(false)
const orderList = ref([])
const selectedOrderIds = ref([])
const repayAmount = ref(0)

// 分页相关
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

// 当前页显示的订单
const paginatedOrderList = computed(() => {
  const start = (page.value - 1) * pageSize.value
  const end = start + pageSize.value
  return orderList.value.slice(start, end)
})

// 计算所选订单总尾款
const totalArrears = computed(() => {
  return selectedOrderIds.value.reduce((sum, id) => {
    const order = orderList.value.find(o => o.id === id)
    return sum + (order?.arrears || 0)
  }, 0)
})

// 是否可以提交：有选中订单且补缴金额 > 0 且不超过总尾款
const canSubmit = computed(() => {
  return selectedOrderIds.value.length > 0 && repayAmount.value > 0 && repayAmount.value <= totalArrears.value
})

// 监听弹窗显示，加载订单数据
watch(() => props.visible, async (val) => {
  dialogVisible.value = val
  if (val && props.studentId) {
    page.value = 1
    await loadOrders()
  }
})
watch(dialogVisible, (val) => emit('update:visible', val))

async function loadOrders() {
  loading.value = true
  try {
    // 获取该学员所有订单（后端返回全量，前端分页）
    const res = await getOrderList({ search: '' })
    const allOrders = res.data || []
    // 筛选该学员下有尾款的订单（排除已作废的）
    orderList.value = allOrders
      .filter(o => o.student_id === props.studentId && o.arrears > 0 && !o.is_invalid)
      .map(o => ({
        id: o.id,
        order_no: o.order_no,
        course_name: o.course_name,
        arrears: o.arrears
      }))
    total.value = orderList.value.length
    // 默认清空选择
    selectedOrderIds.value = []
    repayAmount.value = 0
  } catch (error) {
    ElMessage.error('加载订单失败')
  } finally {
    loading.value = false
  }
}

function onSelectionChange() {
  // 自动将补缴金额设置为所选订单总尾款
  repayAmount.value = totalArrears.value
}

function onPageChange() {
  // 切换页码时清空选中项，避免跨页选中导致计算错误
  selectedOrderIds.value = []
  repayAmount.value = 0
}

async function confirmRepay() {
  if (!canSubmit.value) {
    if (selectedOrderIds.value.length === 0) {
      ElMessage.warning('请选择需要补缴的订单')
    } else if (repayAmount.value <= 0) {
      ElMessage.warning('请输入补缴金额')
    } else if (repayAmount.value > totalArrears.value) {
      ElMessage.warning('补缴金额不能超过所选订单的尾款总额')
    }
    return
  }

  // 将补缴金额按订单尾款比例分配到所选订单
  let remaining = repayAmount.value
  const items = []
  for (const id of selectedOrderIds.value) {
    const order = orderList.value.find(o => o.id === id)
    const arrears = order.arrears
    if (remaining <= 0) break
    const pay = Math.min(remaining, arrears)
    items.push({ order_id: id, amount: pay })
    remaining -= pay
  }

  submitting.value = true
  try {
    await batchRepay({ items })
    ElMessage.success('补费成功')
    dialogVisible.value = false
    emit('success')
  } catch (error) {
    ElMessage.error('补费失败')
  } finally {
    submitting.value = false
  }
}

function handleClose() {
  dialogVisible.value = false
}
</script>

<style scoped>
.loading-tip {
  text-align: center;
  padding: 30px;
  color: #909399;
}

.student-info {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e4e7ed;
}

.order-item {
  margin-bottom: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.order-no {
  font-weight: 500;
  margin-right: 12px;
  color: #303133;
}

.order-course {
  margin-right: 12px;
  color: #606266;
  font-size: 13px;
}

.order-arrears {
  color: #f56c6c;
  font-size: 13px;
}

.empty-tip {
  text-align: center;
  padding: 30px;
  color: #909399;
}

.total-tip {
  margin-top: 12px;
  text-align: right;
  font-size: 13px;
  color: #606266;
}

.repay-input {
  width: 180px;
}

/* 输入框高度 40px */
:deep(.el-input__wrapper) {
  height: 40px;
  min-height: 40px;
}

:deep(.el-input__inner) {
  line-height: 40px;
  height: 40px;
}

:deep(.el-dialog__footer) {
  padding-top: 10px;
}

.suffix-text {
  color: #909399;
  font-size: 14px;
  padding: 0 4px;
}

.point-tip {
  margin-top: 8px;
  font-size: 13px;
  color: #36b459;
  text-align: right;
}

.pagination-box {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>