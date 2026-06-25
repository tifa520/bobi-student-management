<template>
  <el-dialog v-model="visible" title="薪酬详情" width="900px" @close="emit('update:visible', false)">
    <div v-loading="loading">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="教师姓名">{{ detail?.teacher_name }}</el-descriptions-item>
        <el-descriptions-item label="结算月份">{{ detail?.settlement_month }}</el-descriptions-item>
        <el-descriptions-item label="上课次数">{{ detail?.total_classes }} 节</el-descriptions-item>
        <el-descriptions-item label="出勤总人次">{{ detail?.total_attendance_count }} 人次</el-descriptions-item>
        <el-descriptions-item label="消耗课时数">{{ detail?.total_consumed_hours }} 课时</el-descriptions-item>
        <el-descriptions-item label="消耗课时金额">¥{{ detail?.total_consumed_amount }}</el-descriptions-item>
        <el-descriptions-item label="基本课酬">¥{{ detail?.base_amount }}</el-descriptions-item>
        <el-descriptions-item label="调整金额">¥{{ detail?.adjust_amount }}</el-descriptions-item>
        <el-descriptions-item label="应发薪酬">¥{{ detail?.final_amount }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="detail?.status === 'calculated' ? 'info' : (detail?.status === 'confirmed' ? 'success' : 'primary')">
            {{ detail?.status === 'calculated' ? '已计算' : (detail?.status === 'confirmed' ? '已确认' : '已发放') }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item v-if="detail?.paid_at" label="发放时间">{{ detail?.paid_at }}</el-descriptions-item>
        <el-descriptions-item v-if="detail?.payment_method" label="支付方式">{{ detail?.payment_method }}</el-descriptions-item>
      </el-descriptions>

      <el-tabs v-model="activeTab" style="margin-top: 20px">
        <el-tab-pane label="计算明细" name="detail">
          <el-table :data="detail?.details || []" border stripe>
            <el-table-column prop="rule_name" label="适用规则" />
            <el-table-column label="计薪标准" width="120">
              <template #default="{ row }">
                <span v-if="row.calculation_type === 'actual_attendance_amount'">实际课消金额</span>
                <span v-else-if="row.calculation_type === 'attendance_count'">出勤人次</span>
                <span v-else-if="row.calculation_type === 'consumed_hours'">消耗课时</span>
                <span v-else-if="row.calculation_type === 'consumed_amount'">消耗金额</span>
                <span v-else-if="row.calculation_type === 'class_count'">上课次数</span>
                <span v-else>{{ row.calculation_type }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="target_name" label="对象" width="150" />
            <el-table-column prop="calculated_value" label="计薪值" width="100" />
            <el-table-column label="单价" width="100">
              <template #default="{ row }">{{ row.unit_price }}{{ row.unit_price > 1 ? '' : '%' }}</template>
            </el-table-column>
            <el-table-column prop="calculated_amount" label="金额" width="120">
              <template #default="{ row }">¥{{ row.calculated_amount.toFixed(2) }}</template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="考勤明细" name="attendance">
          <el-table :data="detail?.attendance_details || []" border stripe>
            <el-table-column prop="date" label="日期" width="100" />
            <el-table-column prop="class_name" label="班级" />
            <el-table-column prop="status" label="考勤状态" width="80" />
            <el-table-column label="消耗课时" prop="deduct_hours" width="80" />
            <el-table-column label="课消金额" prop="deduct_amount" width="100" />
          </el-table>
        </el-tab-pane>
      </el-tabs>

      <el-divider v-if="detail?.status !== 'paid'">增减课酬操作</el-divider>
      <div v-if="detail?.status !== 'paid'" class="adjust-form">
        <el-form inline>
          <el-form-item label="调整金额">
            <el-input-number v-model="adjustAmount" :precision="2" />
          </el-form-item>
          <el-form-item label="原因">
            <el-input v-model="adjustReason" placeholder="请输入调整原因" style="width: 200px" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="submitAdjust" :loading="adjusting">确认调整</el-button>
          </el-form-item>
        </el-form>
      </div>

      <div v-if="detail?.adjustments?.length" class="adjust-history">
        <h4>调整历史</h4>
        <el-table :data="detail.adjustments" size="small">
          <el-table-column prop="adjust_amount" label="调整金额" width="100">
            <template #default="{ row }">¥{{ row.adjust_amount.toFixed(2) }}</template>
          </el-table-column>
          <el-table-column prop="reason" label="原因" />
          <el-table-column prop="operator_name" label="操作人" width="100" />
          <el-table-column prop="created_at" label="操作时间" width="160" />
        </el-table>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { getSalaryDetail, adjustSalary } from '@/api/salary'

const props = defineProps({
  visible: Boolean,
  salaryId: Number
})
const emit = defineEmits(['update:visible', 'refresh'])

const visible = ref(props.visible)
const detail = ref(null)
const loading = ref(false)
const activeTab = ref('detail')
const adjustAmount = ref(0)
const adjustReason = ref('')
const adjusting = ref(false)

watch(() => props.visible, async (val) => {
  visible.value = val
  if (val && props.salaryId) {
    await loadDetail()
  }
})
watch(visible, (val) => emit('update:visible', val))

async function loadDetail() {
  loading.value = true
  try {
    const res = await getSalaryDetail(props.salaryId)
    detail.value = res.data
  } catch (error) {
    ElMessage.error('加载详情失败')
  } finally {
    loading.value = false
  }
}

async function submitAdjust() {
  if (adjustAmount.value === 0) {
    ElMessage.warning('请输入调整金额')
    return
  }
  if (!adjustReason.value) {
    ElMessage.warning('请输入调整原因')
    return
  }
  adjusting.value = true
  try {
    await adjustSalary(props.salaryId, adjustAmount.value, adjustReason.value)
    ElMessage.success('调整成功')
    adjustAmount.value = 0
    adjustReason.value = ''
    await loadDetail()
    emit('refresh')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '调整失败')
  } finally {
    adjusting.value = false
  }
}
</script>

<style scoped>
.text-danger {
  color: var(--danger);
}
.adjust-form {
  margin: 16px 0;
}
.adjust-history {
  margin-top: 20px;
}
</style>