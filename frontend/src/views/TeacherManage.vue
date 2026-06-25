<template>
  <div class="teacher-manage bobi-page">
    <!-- 页面标题 -->
    <div class="bobi-page-title">
      <div>
        <h1>教师管理</h1>
        <p>管理机构的教师与工作人员信息</p>
      </div>
    </div>

    <!-- 操作栏 -->
    <div class="bobi-toolbar">
      <div class="left-actions">
        <el-button type="primary" @click="openCreate">
          <el-icon><Plus /></el-icon>
          新增教师
        </el-button>
      </div>
      <div class="right-actions">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索教师姓名或电话"
          clearable
          class="search-input"
          @input="filterList"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
    </div>

    <!-- 表格区域 -->
    <div class="table-section">
      <el-table
        :data="filteredTeachers"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="name" label="姓名" min-width="140">
          <template #default="{ row }">
            <div class="teacher-cell">
              <div class="teacher-avatar">
                {{ row.name?.charAt(0) || '?' }}
              </div>
              <div class="teacher-info">
                <span class="teacher-name">{{ row.name }}</span>
                <span class="teacher-role-tag">{{ getRoleText(row.role) }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="联系电话" min-width="160">
          <template #default="{ row }">
            <span class="phone-text">{{ row.phone || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="角色" width="140" align="center">
          <template #default="{ row }">
            <el-tag :type="getRoleTagType(row.role)" size="small" effect="light">
              {{ getRoleText(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120" align="center">
          <template #default="{ row }">
            <div class="status-cell">
              <span class="status-dot" :class="{ active: row.is_enabled }"></span>
              <span class="status-text">{{ row.is_enabled ? '在职' : '停用' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button type="primary" link size="small" @click="openEdit(row)">编辑</el-button>
              <el-button type="primary" link size="small" @click="toggleStatus(row, !row.is_enabled)">
                {{ row.is_enabled ? '停用' : '启用' }}
              </el-button>
              <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 新增/编辑弹窗 -->
    <el-dialog
      v-model="formVisible"
      :title="editing ? '编辑教师' : '新增教师'"
      width="480px"
      :close-on-click-modal="false"
      class="bobi-dialog"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="90px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" placeholder="请输入教师姓名" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入手机号码" />
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
        <el-button type="primary" @click="save" :loading="saving">
          {{ editing ? '保存修改' : '确认新增' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
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

function getRoleTagType(role) {
  const typeMap = {
    full_time_teacher: 'success',
    part_time_teacher: 'warning',
    sales: 'primary',
    reception: 'info',
    finance: '',
    principal: 'danger'
  }
  return typeMap[role] || 'info'
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

.left-actions {
  display: flex;
  gap: var(--space-3);
}

.right-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.search-input {
  width: 260px;
}

.teacher-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.teacher-avatar {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--brand-400), var(--brand-600));
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  border-radius: var(--radius-pill);
  box-shadow: 0 4px 12px rgba(30, 168, 82, 0.25);
}

.teacher-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.teacher-name {
  font-weight: 700;
  color: var(--text-primary);
  font-size: 14px;
}

.teacher-role-tag {
  font-size: 12px;
  color: var(--text-secondary);
}

.phone-text {
  font-family: var(--font-mono);
  color: var(--text-regular);
  font-size: 13px;
}

.status-cell {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--gray-300);
  box-shadow: 0 0 0 4px rgba(185, 194, 181, 0.2);
  transition: all 0.3s ease;
}

.status-dot.active {
  background: var(--success);
  box-shadow: 0 0 0 4px rgba(30, 168, 82, 0.15);
  animation: pulse-glow 2s infinite;
}

.status-text {
  font-size: 13px;
  color: var(--text-regular);
  font-weight: 500;
}

.action-buttons {
  display: flex;
  gap: var(--space-1);
  justify-content: center;
  align-items: center;
}

@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 0 4px rgba(30, 168, 82, 0.15); }
  50% { box-shadow: 0 0 0 8px rgba(30, 168, 82, 0.05); }
}

@media (max-width: 768px) {
  .search-input {
    width: 100%;
  }
  .left-actions,
  .right-actions {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
