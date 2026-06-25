<template>
  <div class="teacher-manage">
    <div class="action-bar">
      <div class="left-actions">
        <el-button type="primary" @click="openCreate">+ 新增教师</el-button>
      </div>
      <div class="right-actions">
        <el-input
          v-model="searchKeyword"
          placeholder="请输入教师姓名"
          clearable
          style="width: 200px"
          @input="filterList"
        />
      </div>
    </div>

    <el-table
      :data="filteredTeachers"
      v-loading="loading"
      border
      stripe
      style="width: 100%"
    >
      <el-table-column prop="name" label="姓名" min-width="120">
        <template #default="{ row }">
          <el-link type="primary" @click="openEdit(row)">{{ row.name }}</el-link>
        </template>
      </el-table-column>
      <el-table-column prop="phone" label="电话号码" min-width="150" />
      <el-table-column prop="role" label="角色" width="120">
        <template #default="{ row }">
          {{ getRoleText(row.role) }}
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-switch
            v-model="row.is_enabled"
            active-color="#36b459"
            inactive-color="#c0c4cc"
            @change="(val) => toggleStatus(row, val)"
          />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right" align="center">
        <template #default="{ row }">
          <div class="action-links">
            <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      v-model="formVisible"
      :title="editing ? '编辑教师' : '新增教师'"
      width="400px"
      :close-on-click-modal="false"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="电话" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入电话号码" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" placeholder="请选择角色" style="width: 100%">
            <el-option label="专职教师" value="full_time_teacher" />
            <el-option label="兼职教师" value="part_time_teacher" />
            <el-option label="销售" value="sales" />
            <el-option label="前台" value="reception" />
            <el-option label="财务" value="finance" />
            <el-option label="校长" value="principal" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" @click="save" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getTeacherList,
  createTeacher,
  updateTeacher,
  deleteTeacher,
  updateTeacherStatus
} from '@/api/basic'

const teachers = ref([])
const loading = ref(false)
const formVisible = ref(false)
const editing = ref(false)
const saving = ref(false)
const editId = ref(null)
const searchKeyword = ref('')
const formRef = ref(null)

const form = reactive({
  name: '',
  phone: '',
  role: 'full_time_teacher'
})

const rules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  phone: [
    { required: true, message: '请输入电话号码', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
}

const roleMap = {
  full_time_teacher: '专职教师',
  part_time_teacher: '兼职教师',
  sales: '销售',
  reception: '前台',
  finance: '财务',
  principal: '校长'
}

function getRoleText(role) {
  return roleMap[role] || role
}

const filteredTeachers = computed(() => {
  if (!searchKeyword.value) return teachers.value
  const keyword = searchKeyword.value.toLowerCase()
  return teachers.value.filter(teacher =>
    teacher.name.toLowerCase().includes(keyword) ||
    teacher.phone?.includes(keyword)
  )
})

async function fetchList() {
  loading.value = true
  try {
    const res = await getTeacherList()
    teachers.value = (res.data || []).map(t => ({
      ...t,
      is_enabled: t.is_enabled !== false
    }))
  } catch (error) {
    console.error('加载教师列表失败', error)
    ElMessage.error('加载教师列表失败')
  } finally {
    loading.value = false
  }
}

function filterList() {}

function openCreate() {
  editing.value = false
  editId.value = null
  form.name = ''
  form.phone = ''
  form.role = 'full_time_teacher'
  formVisible.value = true
  setTimeout(() => {
    formRef.value?.clearValidate()
  }, 100)
}

function openEdit(row) {
  editing.value = true
  editId.value = row.id
  form.name = row.name
  form.phone = row.phone
  form.role = row.role || 'full_time_teacher'
  formVisible.value = true
  setTimeout(() => {
    formRef.value?.clearValidate()
  }, 100)
}

async function save() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    if (editing.value) {
      await updateTeacher(editId.value, { ...form })
      ElMessage.success('更新成功')
    } else {
      await createTeacher({ ...form })
      ElMessage.success('创建成功')
    }
    formVisible.value = false
    await fetchList()
  } catch (error) {
    const msg = error.response?.data?.detail || '操作失败'
    ElMessage.error(msg)
  } finally {
    saving.value = false
  }
}

function handleDelete(row) {
  ElMessageBox.confirm(`确认删除教师"${row.name}"？`, '提示', {
    type: 'warning',
    confirmButtonText: '确认删除',
    cancelButtonText: '取消'
  })
    .then(async () => {
      try {
        await deleteTeacher(row.id)
        ElMessage.success('已删除')
        await fetchList()
      } catch (error) {
        const msg = error.response?.data?.detail || '删除失败'
        ElMessage.error(msg)
      }
    })
    .catch(() => {})
}

async function toggleStatus(row, value) {
  try {
    await updateTeacherStatus(row.id, value)
    ElMessage.success(`教师已${value ? '启用' : '禁用'}`)
  } catch (error) {
    row.is_enabled = !value
    ElMessage.error('状态更新失败')
  }
}

onMounted(() => {
  fetchList()
})
</script>

<style scoped>
.teacher-manage {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.action-bar {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-3);
  padding: var(--space-4);
  background: var(--surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xs);
}

.left-actions { display: flex; gap: var(--space-3); }
.right-actions { display: flex; align-items: center; gap: var(--space-2); }

.action-links { display: flex; gap: var(--space-2); justify-content: center; }
</style>
