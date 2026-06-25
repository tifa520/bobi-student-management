<template>
  <el-dialog v-model="dialogVisible" title="编辑考勤" width="500px" @close="handleClose">
    <el-form :model="form" label-width="100px">
      <el-form-item label="学员姓名"><el-input :value="form.student_name" disabled /></el-form-item>
      <el-form-item label="考勤状态"><el-select v-model="form.status"><el-option label="出勤" value="出勤" /><el-option label="迟到" value="迟到" /><el-option label="请假" value="请假" /><el-option label="未到" value="未到" /></el-select></el-form-item>
      <el-form-item label="扣课时数"><el-input-number v-model="form.deduct_hours" :min="0" :step="1" /></el-form-item>
      <el-form-item label="课时类型"><el-input :value="form.hour_type" disabled /></el-form-item>
      <el-form-item label="剩余付费课时"><span>{{ form.remaining_hours }} 课时</span></el-form-item>
      <el-form-item label="剩余赠送课时"><span>{{ form.remaining_gift }} 课时</span></el-form-item>
      <el-form-item label="备注（只读）"><el-input :value="form.remark" disabled type="textarea" :rows="2" /></el-form-item>
    </el-form>
    <template #footer><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary" @click="handleSave" :loading="saving">保存</el-button></template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { updateAttendance } from '@/api/attendance'

const props = defineProps({ visible: Boolean, attendance: Object })
const emit = defineEmits(['update:visible', 'success'])
const dialogVisible = ref(false)
const saving = ref(false)
const form = ref({ attendance_id: null, student_name: '', status: '', deduct_hours: 0, hour_type: '', remaining_hours: 0, remaining_gift: 0, remark: '' })

watch(() => props.visible, (val) => { if (val && props.attendance) { form.value = { ...props.attendance }; dialogVisible.value = true } else dialogVisible.value = false })
async function handleSave() {
  saving.value = true
  try {
    await updateAttendance(form.value.attendance_id, { status: form.value.status, deduct_hours: form.value.deduct_hours, hour_type: form.value.hour_type })
    ElMessage.success('更新成功'); dialogVisible.value = false; emit('success')
  } catch { ElMessage.error('更新失败') } finally { saving.value = false }
}
function handleClose() { emit('update:visible', false) }
</script>