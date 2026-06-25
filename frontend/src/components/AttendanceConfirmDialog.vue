<template>
  <el-dialog v-model="dialogVisible" title="考勤信息确认" width="900px" :close-on-click-modal="false" @close="handleClose">
    <div class="info-row"><span class="info-text">确认将以下学员考勤状态记录为 <span style="color: #f56c6c;">【{{ statusLabel }}】</span></span><template v-if="shouldDeductHours"><span>，本次考勤将扣除</span><div class="deduct-input-wrapper"><el-input-number v-model="globalDeductHours" :min="0" :step="1" size="small" :disabled="!editMode" controls-position="right" style="width:100px; margin:0 8px" /><span class="unit">课时</span><el-link type="primary" :underline="false" @click="toggleEditMode"><el-icon><Edit /></el-icon><span style="margin-left:4px;">修改</span></el-link></div></template></div>
    <div v-if="hasLeaveWarning" class="confirm-tip"><el-alert title="提示" type="warning" :closable="false" show-icon>存在学员请假/未到次数已用完，请确认</el-alert></div>
    <div class="confirm-table-wrapper"><el-table :data="confirmList" border stripe><el-table-column prop="name" label="学员姓名" width="120"><template #default="{ row }"><div class="student-info-cell"><AppImage :src="row.avatar" :size="28" class="student-avatar" /><span>{{ row.name }}</span></div></template></el-table-column><el-table-column label="课时类型" width="140" v-if="shouldDeductHours"><template #default="{ row, $index }"><el-select v-model="row.hourType" size="small" :disabled="!row.giftAvailable" style="width:100px" @change="() => recalcAfterRemaining(row)"><el-option label="付费课时" value="付费" /><el-option label="赠送课时" value="赠送" :disabled="!row.giftAvailable" /></el-select></template></el-table-column><el-table-column label="考勤后剩余课时" width="150"><template #default="{ row }"><span :class="{ 'text-danger': row.afterRemaining < 0 }">{{ row.afterRemaining }} 课时</span></template></el-table-column><el-table-column label="请假情况" width="150"><template #default="{ row }"><span :class="{ 'text-danger': row.isLeaveExhausted }">{{ row.leaveDisplay }}</span></template></el-table-column><el-table-column label="备注" min-width="200"><template #default="{ row }"><el-input v-model="row.remark" placeholder="请输入备注" size="small" /></template></el-table-column></el-table></div>
    <div v-if="hasWarning" class="confirm-tip"><el-alert title="提示" type="warning" :closable="false" show-icon>存在学员考勤后剩余课时为负数，请确认</el-alert></div>
    <template #footer><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary" @click="handleConfirm" :loading="submitting">确认考勤</el-button></template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Edit } from '@element-plus/icons-vue'
import { submitAttendance } from '@/api/attendance'
import { DEFAULT_AVATAR_SVG } from '@/utils/constants'

const props = defineProps({ visible: Boolean, scheduleId: Number, status: String, selectedStudents: Array, defaultDeductHours: { type: Number, default: 1 } })
const emit = defineEmits(['update:visible', 'success'])
const dialogVisible = ref(false)
const submitting = ref(false)
const confirmList = ref([])
const globalDeductHours = ref(props.defaultDeductHours)
const editMode = ref(false)
const shouldDeductHours = computed(() => props.status === '出勤' || props.status === '迟到')
const isLeaveOrAbsent = computed(() => props.status === '请假' || props.status === '未到')
const statusLabel = computed(() => ({ '未到': '未到', '请假': '请假', '迟到': '迟到', '出勤': '出勤' }[props.status] || ''))
function toggleEditMode() { editMode.value = !editMode.value }
function recalcAfterRemaining(row) {
  if (isLeaveOrAbsent.value) row.afterRemaining = row.remaining_hours
  else { const deduct = globalDeductHours.value; row.afterRemaining = row.hourType === '赠送' ? row.remaining_gift - deduct : row.remaining_hours - deduct }
}
function isGiftAvailable(remaining_gift, deduct) { return remaining_gift >= deduct }
function checkLeaveAvailable(row) {
  const parts = row.leaveDisplay.split(' / '); const used = parseInt(parts[0]) || 0; const total = parseInt(parts[1]) || 0
  if (total === 0 && isLeaveOrAbsent.value) { row.isLeaveExhausted = true; return false }
  if (total > 0 && used >= total && isLeaveOrAbsent.value) { row.isLeaveExhausted = true; return false }
  row.isLeaveExhausted = false; return true
}
function buildConfirmList() {
  const deduct = globalDeductHours.value
  return props.selectedStudents.map(s => {
    const remaining_paid = s.remaining_hours || 0; const remaining_gift = s.remaining_gift || 0
    let defaultHourType = '付费', giftAvailable = false
    if (!isLeaveOrAbsent.value) { giftAvailable = isGiftAvailable(remaining_gift, deduct); if (giftAvailable) defaultHourType = '赠送' }
    let afterRemaining = isLeaveOrAbsent.value ? remaining_paid : (defaultHourType === '赠送' ? remaining_gift - deduct : remaining_paid - deduct)
    const totalLeaveQuota = s.total_leave_quota ?? 0; const usedLeave = s.used_leave ?? 0; const remainingLeaves = Math.max(0, totalLeaveQuota - usedLeave)
    let leaveDisplay = '', isLeaveExhausted = false
    if (totalLeaveQuota === 0) { leaveDisplay = '不允许'; isLeaveExhausted = isLeaveOrAbsent.value }
    else if (totalLeaveQuota === 999) { leaveDisplay = '不限制'; isLeaveExhausted = false }
    else { leaveDisplay = `${usedLeave} / ${totalLeaveQuota}`; isLeaveExhausted = isLeaveOrAbsent.value && remainingLeaves <= 0 }
    return { student_id: s.student_id, name: s.name, avatar: s.avatar, remaining_hours: remaining_paid, remaining_gift, hourType: defaultHourType, afterRemaining, giftAvailable, leaveDisplay, isLeaveExhausted, remark: '', total_leave_quota: totalLeaveQuota, used_leave: usedLeave }
  })
}
watch(globalDeductHours, () => { if (isLeaveOrAbsent.value) return; confirmList.value.forEach(row => { recalcAfterRemaining(row); row.giftAvailable = isGiftAvailable(row.remaining_gift, globalDeductHours.value); if (!row.giftAvailable && row.hourType === '赠送') { row.hourType = '付费'; recalcAfterRemaining(row) } }) })
const hasLeaveWarning = computed(() => confirmList.value.some(item => item.isLeaveExhausted && isLeaveOrAbsent.value))
const hasWarning = computed(() => confirmList.value.some(item => item.afterRemaining < 0))
async function handleConfirm() {
  if (isLeaveOrAbsent.value) { for (const item of confirmList.value) if (item.isLeaveExhausted) { ElMessage.warning(`学员 ${item.name} 的请假/未到次数已用完，无法继续`); return } }
  submitting.value = true
  try {
    const attendanceList = confirmList.value.map(item => ({ student_id: item.student_id, status: props.status, deduct_hours: isLeaveOrAbsent.value ? 0 : globalDeductHours.value, leave_deduct: isLeaveOrAbsent.value ? 1 : 0, hour_type: isLeaveOrAbsent.value ? '付费' : item.hourType, remark: item.remark }))
    await submitAttendance({ schedule_id: props.scheduleId, attendance_list: attendanceList })
    ElMessage.success(`已批量设置${statusLabel.value}`)
    dialogVisible.value = false
    emit('success')
  } catch (error) { ElMessage.error('提交失败') } finally { submitting.value = false }
}
function handleClose() { emit('update:visible', false) }
watch(() => props.visible, (val) => { if (val && props.selectedStudents?.length) { globalDeductHours.value = props.defaultDeductHours; editMode.value = false; confirmList.value = buildConfirmList(); dialogVisible.value = true } else { dialogVisible.value = false } })
watch(() => dialogVisible, (val) => { if (!val) emit('update:visible', false) })
</script>

<style scoped>
.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.dialog-title {
  font-size: 16px;
  font-weight: bold;
}
.info-row {
  margin-bottom: 16px;
  padding: 8px 0;
  display: flex;
  align-items: center;
  font-size: 14px;
  flex-wrap: wrap;
}
.info-text {
  line-height: 32px;
}
.deduct-input-wrapper {
  display: inline-flex;
  align-items: center;
}
.unit {
  margin-right: 8px;
  color: #606266;
}
.confirm-table-wrapper {
  max-height: 400px;
  overflow-y: auto;
  margin-bottom: 16px;
}
.confirm-tip {
  margin-top: 12px;
}
.text-danger {
  color: #f56c6c;
}
.student-info-cell { display: flex; align-items: center; gap: 8px; }
.student-avatar { flex-shrink: 0; }
</style>