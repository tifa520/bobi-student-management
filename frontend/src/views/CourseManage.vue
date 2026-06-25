<template>
  <div class="course-manage bobi-page">
    <!-- 页面标题 -->
    <div class="bobi-page-title">
      <div>
        <h1>课程管理</h1>
        <p>管理课程体系与课阶定价，构建完整的教学产品矩阵</p>
      </div>
    </div>

    <!-- 操作栏 -->
    <div class="bobi-toolbar">
      <div class="left-actions">
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>
          新增课程
        </el-button>
      </div>
      <div class="right-actions">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索课程名称"
          clearable
          class="search-input"
          @input="fetchList"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
    </div>

    <!-- 课程列表 -->
    <div class="table-section">
      <el-table
        ref="tableRef"
        :data="flattenedRows"
        v-loading="loading"
        stripe
        style="width: 100%"
        :span-method="spanMethod"
        class="course-table"
      >
        <el-table-column prop="course_name" label="课程名称" min-width="160">
          <template #default="{ row }">
            <div v-if="row._stageIndex === 0 || row._isPlaceholder" class="course-cell">
              <div class="course-icon">
                <el-icon><Reading /></el-icon>
              </div>
              <el-link type="primary" class="course-name-link" @click="openEditDialog(row.course_id)">
                {{ row.course_name }}
              </el-link>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="stage_name" label="课阶名称" min-width="140">
          <template #default="{ row }">
            <div v-if="!row._isPlaceholder" class="stage-cell">
              <span class="stage-badge">{{ row.stage_name }}</span>
            </div>
            <span v-else class="text-muted">未设置</span>
          </template>
        </el-table-column>

        <el-table-column label="收费模式" width="110" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.charge_mode" :type="row.charge_mode === '课时' ? 'primary' : 'success'" size="small" effect="light">
              {{ row.charge_mode }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>

        <el-table-column label="标准单价" width="120" align="center">
          <template #default="{ row }">
            <span v-if="row.unit_price !== null && row.unit_price !== undefined" class="price-text">
              ¥{{ row.unit_price }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>

        <el-table-column label="单次时长" width="110" align="center">
          <template #default="{ row }">
            <span v-if="row.duration">{{ row.duration }} 分钟</span>
            <span v-else>-</span>
          </template>
        </el-table-column>

        <el-table-column label="扣课时数" width="100" align="center">
          <template #default="{ row }">
            <span v-if="row.deduct_hours">{{ row.deduct_hours }} 课时</span>
            <span v-else>-</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="140" align="center">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button
                v-if="row.stage_id"
                type="danger"
                link
                size="small"
                @click="handleDeleteStage(row.course_id, row.stage_id)"
              >
                删除课阶
              </el-button>
              <el-button
                v-else
                type="danger"
                link
                size="small"
                @click="handleDeleteCourse(row.course_id)"
              >
                删除课程
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper" v-if="total > pageSize">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="fetchList"
        />
      </div>
    </div>

    <!-- 新增 / 编辑 课程弹窗 -->
    <el-dialog
      v-model="formVisible"
      :title="editing ? '编辑课程' : '新增课程'"
      width="900px"
      :close-on-click-modal="false"
      class="course-dialog bobi-dialog"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <!-- 课程名称 -->
        <div class="form-section">
          <div class="form-section-title">基础信息</div>
          <el-form-item label="课程名称" prop="name">
            <el-input v-model="form.name" placeholder="请输入课程名称" style="width: 360px" />
          </el-form-item>
        </div>

        <!-- 课阶列表 -->
        <div class="form-section">
          <div class="form-section-title">
            <span>课阶设置</span>
            <el-button type="primary" link size="small" @click="addStageRow">
              <el-icon><Plus /></el-icon>
              添加课阶
            </el-button>
          </div>
          <div class="stage-table-wrapper">
            <el-table :data="form.stages" style="width: 100%">
              <el-table-column label="序号" type="index" width="60" align="center" />
              <el-table-column label="课阶名称" min-width="130">
                <template #default="{ row, $index }">
                  <el-form-item
                    :prop="`stages.${$index}.name`"
                    :rules="[{ required: true, message: '请输入名称', trigger: 'blur' }]"
                    label-width="0"
                    class="inline-form-item"
                  >
                    <el-input v-model="row.name" placeholder="如：启蒙" />
                  </el-form-item>
                </template>
              </el-table-column>
              <el-table-column label="收费模式" width="130">
                <template #default="{ row }">
                  <el-select v-model="row.charge_mode" style="width: 100%">
                    <el-option label="课时" value="课时" />
                    <el-option label="按期" value="按期" />
                  </el-select>
                </template>
              </el-table-column>
              <el-table-column label="单价(元)" width="120">
                <template #default="{ row }">
                  <el-input-number
                    v-model="row.unit_price"
                    :min="0"
                    :precision="2"
                    style="width: 100%"
                    :controls="false"
                  />
                </template>
              </el-table-column>
              <el-table-column label="时长(分)" width="110">
                <template #default="{ row }">
                  <el-input-number
                    v-model="row.duration"
                    :min="15"
                    :step="15"
                    style="width: 100%"
                    :controls="false"
                  />
                </template>
              </el-table-column>
              <el-table-column label="扣课时" width="100">
                <template #default="{ row }">
                  <el-input-number
                    v-model="row.deduct_hours"
                    :min="1"
                    style="width: 100%"
                    :controls="false"
                  />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="70" align="center">
                <template #default="{ $index }">
                  <el-button
                    type="danger"
                    link
                    size="small"
                    @click="removeStageRow($index)"
                    :disabled="form.stages.length <= 1"
                  >
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-form>

      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" @click="saveCourse" :loading="saving">
          {{ editing ? '保存修改' : '确认新增' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, Search, Reading } from '@element-plus/icons-vue'
import {
  getCourseList,
  createCourse,
  updateCourse,
  deleteCourse,
  deleteStage as deleteStageApi
} from '@/api/course'

// ========== 数据状态 ==========
const loading = ref(false)
const courses = ref([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchKeyword = ref('')
const tableRef = ref(null)

// ========== 扁平化行数据 ==========
const flattenedRows = computed(() => {
  const rows = []
  courses.value.forEach(course => {
    const stages = course.stages || []
    if (stages.length === 0) {
      rows.push({
        course_id: course.id,
        course_name: course.name,
        stage_id: null,
        stage_name: '未设置课阶',
        charge_mode: '-',
        unit_price: null,
        duration: null,
        deduct_hours: null,
        _isPlaceholder: true,
        _rowSpan: 1
      })
    } else {
      stages.forEach((stage, idx) => {
        rows.push({
          course_id: course.id,
          course_name: course.name,
          stage_id: stage.id,
          stage_name: stage.name,
          charge_mode: stage.charge_mode || '课时',
          unit_price: stage.unit_price ?? null,
          duration: stage.duration ?? null,
          deduct_hours: stage.deduct_hours ?? null,
          _isPlaceholder: false,
          _rowSpan: stages.length,
          _stageIndex: idx
        })
      })
    }
  })
  return rows
})

// ========== 行合并方法 ==========
const spanMethod = ({ row, column, rowIndex, columnIndex }) => {
  if (columnIndex === 0) {
    const rowData = flattenedRows.value[rowIndex]
    if (!rowData) return { rowspan: 1, colspan: 1 }
    if (rowData._isPlaceholder || rowData._stageIndex === 0) {
      const count = rowData._isPlaceholder ? 1 : rowData._rowSpan
      return { rowspan: count, colspan: 1 }
    } else {
      return { rowspan: 0, colspan: 0 }
    }
  }
  return { rowspan: 1, colspan: 1 }
}

// ========== 弹窗表单 ==========
const formVisible = ref(false)
const editing = ref(false)
const saving = ref(false)
const editId = ref(null)
const formRef = ref(null)

const form = reactive({
  name: '',
  stages: []
})

const rules = {
  name: [{ required: true, message: '请输入课程名称', trigger: 'blur' }]
}

// ========== 获取列表 ==========
async function fetchList() {
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value,
      search: searchKeyword.value || undefined
    }
    const res = await getCourseList(params)
    courses.value = res.data?.items || []
    total.value = res.data?.total || 0

    await nextTick()
    if (tableRef.value) {
      tableRef.value.doLayout()
    }
  } catch (error) {
    ElMessage.error('加载课程列表失败')
  } finally {
    loading.value = false
  }
}

// ========== 新增/编辑弹窗操作 ==========
function resetForm() {
  form.name = ''
  form.stages = [
    { name: '', charge_mode: '课时', unit_price: 0, duration: 60, deduct_hours: 1 }
  ]
  editId.value = null
  editing.value = false
}

function addStageRow() {
  form.stages.push({
    name: '',
    charge_mode: '课时',
    unit_price: 0,
    duration: 60,
    deduct_hours: 1
  })
}

function removeStageRow(index) {
  if (form.stages.length <= 1) {
    ElMessage.warning('至少保留一个课阶')
    return
  }
  form.stages.splice(index, 1)
}

function openCreateDialog() {
  resetForm()
  editing.value = false
  formVisible.value = true
  nextTick(() => formRef.value?.clearValidate())
}

async function openEditDialog(courseId) {
  editing.value = true
  editId.value = courseId
  const course = courses.value.find(c => c.id === courseId)
  if (!course) {
    ElMessage.error('课程数据不存在')
    return
  }
  form.name = course.name
  const stages = course.stages || []
  if (stages.length === 0) {
    form.stages = [{ name: '', charge_mode: '课时', unit_price: 0, duration: 60, deduct_hours: 1 }]
  } else {
    form.stages = stages.map(s => ({
      id: s.id,
      name: s.name,
      charge_mode: s.charge_mode || '课时',
      unit_price: s.unit_price || 0,
      duration: s.duration || 60,
      deduct_hours: s.deduct_hours || 1
    }))
  }
  formVisible.value = true
  nextTick(() => formRef.value?.clearValidate())
}

// ========== 保存课程 ==========
async function saveCourse() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  const emptyStage = form.stages.some(s => !s.name || !s.name.trim())
  if (emptyStage) {
    ElMessage.warning('请填写所有课阶名称')
    return
  }

  saving.value = true
  try {
    const payload = {
      name: form.name,
      stages: form.stages.map(s => ({
        name: s.name.trim(),
        charge_mode: s.charge_mode || '课时',
        unit_price: s.unit_price || 0,
        duration: s.duration || 60,
        deduct_hours: s.deduct_hours || 1,
        is_active: true
      }))
    }

    if (editing.value) {
      await updateCourse(editId.value, payload)
      ElMessage.success('课程更新成功')
    } else {
      await createCourse(payload)
      ElMessage.success('课程创建成功')
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

// ========== 删除单个课阶 ==========
async function handleDeleteStage(courseId, stageId) {
  if (!stageId) {
    ElMessage.warning('该课阶尚未保存，无法删除')
    return
  }
  try {
    await ElMessageBox.confirm('确认删除此课阶？', '提示', { type: 'warning' })
    await deleteStageApi(courseId, stageId)
    ElMessage.success('课阶已删除')
    await fetchList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

// ========== 删除课程 ==========
async function handleDeleteCourse(courseId) {
  const course = courses.value.find(c => c.id === courseId)
  if (!course) return
  try {
    await ElMessageBox.confirm(`确认删除课程"${course.name}"及其所有课阶？`, '提示', {
      type: 'warning',
      confirmButtonText: '确认删除',
      cancelButtonText: '取消'
    })
    await deleteCourse(courseId)
    ElMessage.success('课程已删除')
    await fetchList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

// ========== 生命周期 ==========
onMounted(() => {
  fetchList()
})
</script>

<style scoped>
.course-manage {
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

.course-table {
  border-radius: 0;
  border: none;
}

.course-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.course-icon {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--gold-200), var(--gold-400));
  color: #fff;
  font-size: 20px;
  border-radius: var(--radius-lg);
  box-shadow: 0 4px 12px rgba(212, 148, 26, 0.25);
}

.course-name-link {
  font-weight: 700;
  font-size: 14px;
}

.stage-cell {
  display: flex;
  align-items: center;
}

.stage-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  background: linear-gradient(135deg, var(--brand-50), var(--brand-100));
  color: var(--brand-700);
  font-size: 12px;
  font-weight: 600;
  border-radius: var(--radius-pill);
}

.price-text {
  font-family: var(--font-mono);
  font-weight: 700;
  color: var(--gold-600);
  font-size: 14px;
}

.action-buttons {
  display: flex;
  gap: var(--space-1);
  justify-content: center;
  align-items: center;
}

.pagination-wrapper {
  padding: 14px 20px;
  border-top: 1px solid var(--border-light);
  background: var(--surface-soft);
  display: flex;
  justify-content: flex-end;
}

.form-section {
  margin-bottom: 24px;
}

.form-section:last-child {
  margin-bottom: 0;
}

.form-section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-light);
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
  font-family: var(--font-display);
}

.form-section-title::before {
  content: "";
  display: inline-block;
  width: 4px;
  height: 16px;
  margin-right: 10px;
  border-radius: var(--radius-pill);
  background: linear-gradient(180deg, var(--brand-400), var(--brand-600));
  vertical-align: middle;
}

.stage-table-wrapper {
  width: 100%;
  overflow: hidden;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
}

.inline-form-item {
  margin-bottom: 0;
}

.inline-form-item :deep(.el-form-item__content) {
  display: flex;
  align-items: center;
  line-height: 1;
}

.stage-table-wrapper :deep(.el-table .el-table__cell) {
  padding: 6px 8px;
}

.course-dialog :deep(.el-dialog__body) {
  padding: 24px 28px;
}

.course-dialog :deep(.el-form-item) {
  margin-bottom: 18px;
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
