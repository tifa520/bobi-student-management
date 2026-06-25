<template>
  <div class="course-card">
    <div class="card-header">
      <div class="card-title">
        <span class="course-name">{{ course.course_name }}</span>
        <el-tag v-if="course.class_name !== '未分班' && course.status !== 'refunded'" class="class-tag" size="small">{{ course.class_name }}</el-tag>
        <el-tag v-else-if="course.status === 'refunded'" type="danger" size="small" class="refunded-tag">已退费</el-tag>
        <el-tag v-else type="info" size="small" class="unassigned-tag">未分班</el-tag>
        <el-tag v-if="isSuspended(course)" type="warning" size="small" class="suspended-tag">停课中</el-tag>
        <el-button v-if="course.arrears > 0" type="danger" size="small" class="arrears-btn" @click="$emit('repay', course)">尾款：￥{{ course.arrears }}待付</el-button>
      </div>
      <div class="card-actions">
        <el-button class="action-btn" size="small" @click="$emit('renew', course)">续报</el-button>
        <el-button v-if="course.status === 'active'" class="action-btn" size="small" @click="$emit('refund', course)">退费</el-button>
        <el-button class="action-btn" size="small" @click="$emit('graduate', course)">结业</el-button>
        <el-button :class="isSuspended(course) ? 'suspend-btn-edit' : 'action-btn'" size="small" @click="$emit('suspend', course)">{{ isSuspended(course) ? '编辑停课' : '停课' }}</el-button>
        <el-button class="action-btn" size="small" @click="openExtendValidityDialog">
          <el-icon><Edit /></el-icon>修改有效期
        </el-button>
        <template v-if="course.status === 'active'">
          <el-button class="action-btn" size="small" @click="$emit('transfer-hours', course)">转课时</el-button>
          <el-button class="action-btn" size="small" @click="$emit('adjust-hours', course)">增减课时</el-button>
          <el-button class="action-btn" size="small" @click="$emit('gift-hours', course)">增减赠课</el-button>
          <el-button class="action-btn" size="small" @click="$emit('transfer-class', course)" :disabled="!course.class_id">转班</el-button>
          <el-button v-if="course.class_id" class="action-btn" size="small" type="danger" @click="$emit('drop-class', course)">退班</el-button>
          <el-button v-else class="action-btn-danger" size="small" @click="$emit('assign-class', course)">分班</el-button>
        </template>
      </div>
    </div>

    <div class="hours-table">
      <div class="table-row header-row">
        <span class="col">购买课时</span>
        <span class="col">上课消耗</span>
        <span class="col">转入转出</span>
        <span class="col">自定义增</span>
        <span class="col">自定义减</span>
        <span class="col">剩余课时</span>
        <span class="col">赠送课时</span>
        <span class="col">剩余赠送</span>
        <span class="col">有效期</span>
        <span class="col">请假次数</span>
      </div>
      <div class="table-row data-row">
        <span class="col">
          <div class="cell-line">{{ course.total_purchased }}课时</div>
          <div class="cell-line text-amount">￥{{ course.total_purchased_amount || 0 }}</div>
        </span>
        <span class="col">
          <div class="cell-line">{{ course.attendance_deducted_hours || 0 }}课时</div>
          <div class="cell-line text-amount">￥{{ course.attendance_deducted_amount || 0 }}</div>
        </span>
        <span class="col">
          <div class="cell-line">
            <template v-if="course.total_transfer_out > 0">
              <span class="text-danger">-{{ course.total_transfer_out }}课时</span>
            </template>
            <template v-else-if="course.total_transfer_in > 0">
              <span class="text-success">+{{ course.total_transfer_in }}课时</span>
            </template>
            <template v-else>0课时</template>
          </div>
          <div class="cell-line text-amount">
            <template v-if="course.transfer_out_amount > 0">
              <span class="text-danger">-￥{{ course.transfer_out_amount.toFixed(2) }}</span>
            </template>
            <template v-else-if="course.transfer_in_amount > 0">
              <span class="text-success">+￥{{ course.transfer_in_amount.toFixed(2) }}</span>
            </template>
            <template v-else>￥0</template>
          </div>
        </span>
        <span class="col">
          <div class="cell-line">{{ course.total_custom_add || 0 }}课时</div>
          <div class="cell-line text-amount">￥{{ course.custom_add_amount || 0 }}</div>
        </span>
        <span class="col">
          <div class="cell-line">{{ course.total_custom_sub > 0 ? '-' : '' }}{{ course.total_custom_sub }}课时</div>
          <div class="cell-line text-amount">{{ course.custom_sub_amount > 0 ? '-' : '' }}￥{{ Math.abs(course.custom_sub_amount) }}</div>
        </span>
        <span class="col">
          <div class="cell-line">{{ course.remaining_hours }}课时</div>
          <div class="cell-line text-amount">￥{{ course.remaining_amount }}</div>
        </span>
        <span class="col">
          <div class="cell-line">{{ course.total_gift }}课时</div>
        </span>
        <span class="col">
          <div class="cell-line">{{ course.remaining_gift }}课时</div>
        </span>
        <span class="col">
          <div class="cell-line">{{ course.validity_display || '-' }}</div>
        </span>
        <span class="col">
          <div class="cell-line">{{ course.leave_display || '-' }}</div>
        </span>
      </div>
    </div>

    <!-- 修改有效期模态框 -->
    <el-dialog 
      v-model="extendValidityDialogVisible" 
      title="修改有效期" 
      width="480px" 
      :close-on-click-modal="false"
      @close="resetExtendForm"
    >
      <div class="extend-validity-content">
        <div class="info-row">
          <span class="info-label">当前剩余有效天数：</span>
          <span class="info-value">{{ currentRemainingDays }} 天</span>
        </div>
        <div class="info-row">
          <span class="info-label">当前有效期截止日期：</span>
          <span class="info-value">{{ currentValidityEndDate || '无' }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">增加有效天数：</span>
          <div class="info-control">
            <el-input-number 
              v-model="extendDays" 
              :min="1" 
              :max="365" 
              :step="1"
              controls-position="right"
              placeholder="请输入增加天数"
              @change="calculateNewEndDate"
            />
            <span class="unit">天</span>
          </div>
        </div>
        <div class="info-row">
          <span class="info-label">修改后有效期截止日期：</span>
          <span class="info-value text-primary">{{ newValidityEndDate || '-' }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">修改原因：</span>
          <div class="info-control full-width">
            <el-input 
              v-model="extendReason" 
              type="textarea" 
              :rows="2" 
              placeholder="请输入修改原因（选填）" 
            />
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="extendValidityDialogVisible = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="confirmExtendValidity" 
          :loading="extending"
          :disabled="!extendDays || extendDays <= 0"
        >
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Edit } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { extendValidity } from '@/api/student'
import isBetween from 'dayjs/plugin/isBetween'
dayjs.extend(isBetween)

const props = defineProps({
  course: {
    type: Object,
    required: true
  },
  studentId: {
    type: Number,
    required: true
  }
})

const emit = defineEmits([
  'renew', 'refund', 'graduate', 'suspend', 'repay',
  'transfer-hours', 'adjust-hours', 'gift-hours',
  'transfer-class', 'drop-class', 'assign-class',
  'refresh'
])

// 修改有效期弹窗
const extendValidityDialogVisible = ref(false)
const extendDays = ref(1)
const extendReason = ref('')
const extending = ref(false)
const currentValidityEndDate = ref('')
const currentRemainingDays = ref(0)
const newValidityEndDate = ref('')

// 判断是否停课
const isSuspended = (course) => {
  if (!course.suspended_start || !course.suspended_end) return false
  const start = dayjs(course.suspended_start)
  const end = dayjs(course.suspended_end)
  const today = dayjs()
  return today.isBetween(start, end, 'day', '[]')
}

// 计算当前剩余有效天数
const calculateCurrentRemainingDays = () => {
  if (!props.course.validity_display || props.course.validity_display === '-') {
    currentRemainingDays.value = 0
    currentValidityEndDate.value = ''
    return
  }
  
  const endDate = dayjs(props.course.validity_display)
  const today = dayjs()
  
  if (endDate.isBefore(today)) {
    currentRemainingDays.value = 0
  } else {
    currentRemainingDays.value = endDate.diff(today, 'day')
  }
  currentValidityEndDate.value = props.course.validity_display
}

// 计算修改后的有效期截止日期
const calculateNewEndDate = () => {
  if (!extendDays.value || extendDays.value <= 0) {
    newValidityEndDate.value = currentValidityEndDate.value
    return
  }
  
  if (currentValidityEndDate.value) {
    const newDate = dayjs(currentValidityEndDate.value).add(extendDays.value, 'day')
    newValidityEndDate.value = newDate.format('YYYY-MM-DD')
  } else {
    const newDate = dayjs().add(extendDays.value, 'day')
    newValidityEndDate.value = newDate.format('YYYY-MM-DD')
  }
}

// 打开修改有效期弹窗
const openExtendValidityDialog = () => {
  calculateCurrentRemainingDays()
  extendDays.value = 1
  extendReason.value = ''
  calculateNewEndDate()
  extendValidityDialogVisible.value = true
}

// 重置表单
const resetExtendForm = () => {
  extendDays.value = 1
  extendReason.value = ''
  newValidityEndDate.value = ''
}

// 确认修改有效期
const confirmExtendValidity = async () => {
  if (!extendDays.value || extendDays.value <= 0) {
    ElMessage.warning('请输入增加的有效天数')
    return
  }
  
  extending.value = true
  try {
    await extendValidity(
      props.studentId,
      props.course.course_id,
      extendDays.value,
      extendReason.value
    )
    ElMessage.success(`已延长有效期 ${extendDays.value} 天`)
    extendValidityDialogVisible.value = false
    
    // 刷新课程数据
    emit('refresh')
  } catch (error) {
    console.error('延长有效期失败', error)
    ElMessage.error(error.response?.data?.detail || '延长有效期失败')
  } finally {
    extending.value = false
  }
}

// 监听 extendDays 变化，实时计算新有效期
watch(extendDays, () => {
  calculateNewEndDate()
})
</script>

<style scoped>
.course-card {
  background: #fff;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 20px;
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 10px;
}

.card-title {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.course-name {
  font-size: 16px;
  font-weight: 500;
}

.card-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.hours-table {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
}

.table-row {
  display: flex;
}

.header-row {
  background: var(--gray-1);
  font-weight: 500;
  color: var(--text-secondary);
  font-size: 13px;
}

.col {
  flex: 1;
  padding: 8px 6px;
  text-align: center;
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 48px;
}

.col:last-child {
  border-right: none;
}

.cell-line {
  line-height: 1.4;
}

.text-amount {
  color: var(--text-regular);
  font-size: 13px;
}

.text-danger {
  color: #f56c6c;
}

.text-success {
  color: #67c23a;
}

.action-btn {
  background: transparent;
  border: 1px solid var(--primary-color, #36b459);
  color: var(--primary-color, #36b459);
  border-radius: 20px;
  height: 32px;
  padding: 0 12px;
  font-size: 13px;
}

.action-btn:hover {
  background: var(--primary-color, #36b459);
  color: white;
}

/* 修改有效期弹窗样式 */
.extend-validity-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 16px;
}

.info-label {
  width: 140px;
  flex-shrink: 0;
  font-size: 14px;
  color: #606266;
}

.info-value {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}

.info-value.text-primary {
  color: var(--primary-color, #36b459);
}

.info-control {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.info-control.full-width {
  flex: 1;
}

.unit {
  color: #909399;
  font-size: 14px;
}
</style>