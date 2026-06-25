<template>
  <div class="classroom-manage">
    <div class="action-bar">
      <div class="left-actions">
        <el-button type="primary" @click="openCreate">+ 添加教室</el-button>
      </div>
      <div class="right-actions">
        <el-input
          v-model="searchKeyword"
          placeholder="请输入教室名称"
          clearable
          style="width: 200px"
          @input="filterList"
        />
      </div>
    </div>

    <el-table
      :data="filteredRooms"
      v-loading="loading"
      border
      stripe
      style="width: 100%"
    >
      <el-table-column prop="name" label="教室名称" min-width="200">
        <template #default="{ row }">
          <el-link type="primary" @click="openEdit(row)">{{ row.name }}</el-link>
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
      :title="editing ? '编辑教室' : '添加教室'"
      width="400px"
      :close-on-click-modal="false"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="教室名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入教室名称" />
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
  getClassroomList,
  createClassroom,
  updateClassroom,
  deleteClassroom,
  updateClassroomStatus
} from '@/api/basic'

const rooms = ref([])
const loading = ref(false)
const formVisible = ref(false)
const editing = ref(false)
const saving = ref(false)
const editId = ref(null)
const searchKeyword = ref('')
const formRef = ref(null)

const form = reactive({
  name: ''
})

const rules = {
  name: [{ required: true, message: '请输入教室名称', trigger: 'blur' }]
}

const filteredRooms = computed(() => {
  if (!searchKeyword.value) return rooms.value
  const keyword = searchKeyword.value.toLowerCase()
  return rooms.value.filter(room => room.name.toLowerCase().includes(keyword))
})

async function fetchList() {
  loading.value = true
  try {
    const res = await getClassroomList()
    rooms.value = (res.data || []).map(r => ({
      ...r,
      is_enabled: r.is_enabled !== false
    }))
  } catch (error) {
    console.error('加载教室列表失败', error)
    ElMessage.error('加载教室列表失败')
  } finally {
    loading.value = false
  }
}

function filterList() {}

function openCreate() {
  editing.value = false
  editId.value = null
  form.name = ''
  formVisible.value = true
  setTimeout(() => {
    formRef.value?.clearValidate()
  }, 100)
}

function openEdit(row) {
  editing.value = true
  editId.value = row.id
  form.name = row.name
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
      await updateClassroom(editId.value, { name: form.name })
      ElMessage.success('更新成功')
    } else {
      await createClassroom({ name: form.name })
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
  ElMessageBox.confirm(`确认删除教室"${row.name}"？`, '提示', {
    type: 'warning',
    confirmButtonText: '确认删除',
    cancelButtonText: '取消'
  })
    .then(async () => {
      try {
        await deleteClassroom(row.id)
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
    await updateClassroomStatus(row.id, value)
    ElMessage.success(`教室已${value ? '启用' : '禁用'}`)
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
.classroom-manage {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-shrink: 0;
}

.left-actions {
  display: flex;
  gap: 12px;
}

.right-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-links {
  display: flex;
  gap: 8px;
  justify-content: center;
}
</style>