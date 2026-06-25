<template>
  <div class="course-package-manage">
    <div class="action-bar">
      <el-button type="primary" size="small" @click="openAddDialog">+ 新增套餐</el-button>
    </div>
    <el-table :data="packages" v-loading="loading" border stripe>
      <el-table-column prop="name" label="套餐名称" />
      <el-table-column prop="purchase_hours" label="购买课时" width="100" />
      <el-table-column prop="gift_hours" label="赠送课时" width="100" />
      <el-table-column label="优惠" width="150">
        <template #default="{ row }">
          <span v-if="row.discount_mode === 'direct'">直减 {{ row.direct_reduction }}元</span>
          <span v-else-if="row.discount_mode === 'discount'">{{ row.discount_rate }}折</span>
          <span v-else>无</span>
        </template>
      </el-table-column>
      <el-table-column prop="validity_days" label="有效期(天)" width="100">
        <template #default="{ row }">{{ row.validity_days || '-' }}</template>
      </el-table-column>
      <el-table-column label="请假限制" width="120">
        <template #default="{ row }">
          <span v-if="row.leave_limit === '限制次数'">{{ row.leave_limit_count }}次</span>
          <span v-else>{{ row.leave_limit }}</span>
        </template>
      </el-table-column>
      <el-table-column label="默认" width="70">
        <template #default="{ row }">
          <el-tag v-if="row.is_default" type="success" size="small">是</el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link size="small" @click="openEditDialog(row)">编辑</el-button>
          <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑套餐' : '新增套餐'" width="550px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="套餐名称" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="购买课时">
              <el-input-number v-model="form.purchase_hours" :min="1" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="赠送课时">
              <el-input-number v-model="form.gift_hours" :min="0" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="优惠方式">
          <el-select v-model="form.discount_mode" style="width: 200px">
            <el-option label="无" value="none" />
            <el-option label="直减" value="direct" />
            <el-option label="折扣" value="discount" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="form.discount_mode === 'direct'" label="直减金额">
          <el-input-number v-model="form.direct_reduction" :min="0" :precision="2" controls-position="right" />
        </el-form-item>
        <el-form-item v-if="form.discount_mode === 'discount'" label="折扣率">
          <el-input-number v-model="form.discount_rate" :min="0" :max="10" :step="0.1" controls-position="right" /> 折
        </el-form-item>
        <el-form-item label="有效期天数">
          <el-input-number v-model="form.validity_days" :min="0" :controls="false" placeholder="0表示无限制" style="width: 100%" />
        </el-form-item>
        <el-form-item label="请假限制">
          <el-select v-model="form.leave_limit" style="width: 140px">
            <el-option label="不限制" value="不限制" />
            <el-option label="限制次数" value="限制次数" />
            <el-option label="不允许" value="不允许" />
          </el-select>
          <el-input-number v-if="form.leave_limit === '限制次数'" v-model="form.leave_limit_count" :min="1" style="width: 120px; margin-left: 12px" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" controls-position="right" />
        </el-form-item>
        <el-form-item label="设为默认">
          <el-switch v-model="form.is_default" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submit" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getCoursePackages, createPackage, updatePackage, deletePackage } from '@/api/basic'   // 修改导入路径

const props = defineProps({
  courseId: {
    type: Number,
    required: true
  }
})

const packages = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const editing = ref(false)
const submitting = ref(false)
const form = ref({
  name: '',
  purchase_hours: 1,
  gift_hours: 0,
  discount_mode: 'none',
  discount_rate: 0,
  direct_reduction: 0,
  validity_days: null,
  leave_limit: '不限制',
  leave_limit_count: 0,
  sort_order: 0,
  is_default: false,
  remark: ''
})

async function fetchPackages() {
  loading.value = true
  try {
    const res = await getCoursePackages(props.courseId)
    packages.value = res.data || []
  } finally {
    loading.value = false
  }
}

function resetForm() {
  form.value = {
    name: '',
    purchase_hours: 1,
    gift_hours: 0,
    discount_mode: 'none',
    discount_rate: 0,
    direct_reduction: 0,
    validity_days: null,
    leave_limit: '不限制',
    leave_limit_count: 0,
    sort_order: 0,
    is_default: false,
    remark: ''
  }
}

function openAddDialog() {
  editing.value = false
  resetForm()
  dialogVisible.value = true
}

function openEditDialog(row) {
  editing.value = true
  form.value = { ...row }
  dialogVisible.value = true
}

async function submit() {
  submitting.value = true
  try {
    if (editing.value) {
      await updatePackage(form.value.id, form.value)
      ElMessage.success('更新成功')
    } else {
      await createPackage(props.courseId, form.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    await fetchPackages()
  } catch (error) {
    ElMessage.error('操作失败')
  } finally {
    submitting.value = false
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确认删除套餐“${row.name}”？`, '提示', { type: 'warning' })
    await deletePackage(row.id)
    ElMessage.success('删除成功')
    await fetchPackages()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  fetchPackages()
})
</script>

<style scoped>
.course-package-manage {
  margin-top: 20px;
}
.action-bar {
  margin-bottom: 16px;
  text-align: right;
}
</style>