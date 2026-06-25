<!-- frontend/src/views/PackageManage.vue -->
<template>
  <div class="package-manage">
    <div class="page-header">
      <el-button type="primary" @click="openCreateDialog" style="margin-left: auto;">+ 新建套餐</el-button>
    </div>

    <div v-loading="loading" class="packages-by-course">
      <div v-for="course in courses" :key="course.id" class="course-group">
        <div class="course-title">
          <span>{{ course.name }}</span>
          <span class="stage-count" v-if="course.stage_count > 0">{{ course.stage_count }}个课阶</span>
          <el-button type="primary" link size="small" @click="openCreateDialogForCourse(course)">
            + 添加套餐
          </el-button>
        </div>
        <div class="packages-grid">
          <div
            v-for="pkg in getPackagesByCourse(course.id)"
            :key="pkg.id"
            class="package-card"
            :class="{ 'default-card': pkg.is_default }"
          >
            <!-- 卡片头部 -->
            <div class="card-header">
              <div class="package-name">{{ pkg.name }}</div>
              <el-tag v-if="pkg.stage_name" size="small" type="info">{{ pkg.stage_name }}</el-tag>
              <div class="card-actions">
                <el-button type="primary" link size="small" @click="openEditDialog(pkg)">
                  <el-icon><Edit /></el-icon>
                </el-button>
                <el-button type="danger" link size="small" @click="handleDelete(pkg)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>

            <!-- 价格区 -->
            <div class="price-section">
              <div class="price-main">
                <span class="price-label">优惠后金额</span>
                <span class="price-value">¥{{ calcPayableAmount(pkg) }}</span>
              </div>
              <div class="price-saved" v-if="pkg.discount_mode !== 'none'">
                已优惠 ¥{{ calcDiscountAmount(pkg) }}
              </div>
            </div>

            <!-- 信息列表 -->
            <div class="info-list">
              <div class="info-row">
                <span class="info-label">购买课时</span>
                <span class="info-value">{{ pkg.purchase_hours }}课时</span>
              </div>
              <div class="info-row">
                <span class="info-label">赠送课时</span>
                <span class="info-value">{{ pkg.gift_hours || 0 }}课时</span>
              </div>
              <div class="info-row">
                <span class="info-label">课阶单价</span>
                <span class="info-value">¥{{ getStageUnitPrice(pkg.course_id, pkg.stage_id) }}/课时</span>
              </div>
              <div class="info-row">
                <span class="info-label">课程原价</span>
                <span class="info-value">¥{{ calcOriginalPrice(pkg) }}</span>
              </div>
              <div class="info-row" v-if="pkg.validity_days">
                <span class="info-label">有效期</span>
                <span class="info-value">{{ pkg.validity_days }}天</span>
              </div>
              <div class="info-row">
                <span class="info-label">请假限制</span>
                <span class="info-value">
                  {{ pkg.leave_limit === '限制次数' ? pkg.leave_limit_count + '次' : pkg.leave_limit }}
                </span>
              </div>
            </div>

            <!-- 底部默认标签 -->
            <div class="card-footer" v-if="pkg.is_default">
              <el-tag type="success" size="small" effect="plain">默认</el-tag>
            </div>
          </div>
          <div v-if="!getPackagesByCourse(course.id).length" class="empty-placeholder">
            <span>暂无套餐，点击「添加套餐」创建</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 新增/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editing ? '编辑套餐' : '新建套餐'"
      width="580px"
      :close-on-click-modal="false"
      class="package-dialog"
    >
      <el-form :model="form" label-width="100px" ref="formRef" :rules="rules">
        <el-form-item label="所属课程" prop="course_id" v-if="!editing">
          <el-select v-model="form.course_id" placeholder="请选择课程" filterable style="width: 100%" @change="onCourseChange">
            <el-option v-for="c in courses" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <!-- ★ 所属课阶 -->
        <el-form-item label="所属课阶">
          <el-select
            v-model="form.stage_id"
            placeholder="请选择课阶"
            clearable
            :disabled="!form.course_id"
            style="width: 100%"
          >
            <el-option
              v-for="s in stageOptions"
              :key="s.id"
              :label="`${s.name} (￥${s.unit_price}/课时)`"
              :value="s.id"
            />
          </el-select>
          <div v-if="form.stage_id && selectedStage" class="stage-info-hint">
            课阶单价：￥{{ selectedStage.unit_price }}/课时
          </div>
        </el-form-item>
        <el-form-item label="套餐名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入套餐名称" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="购买课时" prop="purchase_hours">
              <el-input v-model.number="form.purchase_hours" type="number" min="1" step="1" placeholder="请输入">
                <template #suffix><span>节</span></template>
              </el-input>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="赠送课时">
              <el-input v-model.number="form.gift_hours" type="number" min="0" step="1" placeholder="请输入">
                <template #suffix><span>节</span></template>
              </el-input>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="优惠方式">
          <el-select v-model="form.discount_mode" style="width: 100%">
            <el-option label="无" value="none" />
            <el-option label="直减" value="direct" />
            <el-option label="折扣" value="discount" />
            <el-option label="先直减再折扣" value="direct_then_discount" />
            <el-option label="先折扣再直减" value="discount_then_direct" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="['direct', 'discount_then_direct', 'direct_then_discount'].includes(form.discount_mode)" label="直减金额">
          <el-input v-model.number="form.direct_reduction" type="number" min="0" step="0.01" placeholder="请输入">
            <template #suffix><span>元</span></template>
          </el-input>
        </el-form-item>
        <el-form-item v-if="['discount', 'discount_then_direct', 'direct_then_discount'].includes(form.discount_mode)" label="折扣率">
          <el-input v-model.number="form.discount_rate" type="number" min="0" max="10" step="0.1" placeholder="请输入">
            <template #suffix><span>折</span></template>
          </el-input>
        </el-form-item>
        <el-form-item label="有效期天数">
          <el-input v-model.number="form.validity_days" type="number" min="0" step="1" placeholder="0表示无限制">
            <template #suffix><span>天</span></template>
          </el-input>
        </el-form-item>
        <el-form-item label="请假限制">
          <el-select v-model="form.leave_limit" style="width: 140px">
            <el-option label="不限制" value="不限制" />
            <el-option label="限制次数" value="限制次数" />
            <el-option label="不允许" value="不允许" />
          </el-select>
          <el-input-number
            v-if="form.leave_limit === '限制次数'"
            v-model="form.leave_limit_count"
            :min="1"
            style="width: 120px; margin-left: 12px"
            controls-position="right"
          />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" controls-position="right" style="width: 100%" />
        </el-form-item>
        <el-form-item label="设为默认">
          <el-switch v-model="form.is_default" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" rows="2" placeholder="选填" />
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
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Edit, Delete } from '@element-plus/icons-vue'
import { getCourseListSimple } from '@/api/basic'
import { getCoursePackages, createPackage, updatePackage, deletePackage } from '@/api/package'
import { getCourseStages } from '@/api/course'

const courses = ref([])
const packagesMap = ref({})
const stageMap = ref({}) // 缓存课阶信息
const loading = ref(false)
const coursePriceMap = ref({})

const dialogVisible = ref(false)
const editing = ref(false)
const submitting = ref(false)
const formRef = ref(null)
const currentPackageId = ref(null)

// ★ 课阶选项
const stageOptions = ref([])
const selectedStage = computed(() => {
  return stageOptions.value.find(s => s.id === form.stage_id)
})

const form = reactive({
  course_id: null,
  stage_id: null,
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

const rules = {
  course_id: [{ required: true, message: '请选择课程', trigger: 'change' }],
  name: [{ required: true, message: '请输入套餐名称', trigger: 'blur' }],
  purchase_hours: [{ required: true, message: '请输入购买课时', trigger: 'blur' }]
}

function getPackagesByCourse(courseId) {
  return packagesMap.value[courseId] || []
}

function getCourseUnitPrice(courseId) {
  return coursePriceMap.value[courseId] || 0
}

function getStageUnitPrice(courseId, stageId) {
  if (!stageId) return getCourseUnitPrice(courseId)
  const key = `${courseId}_${stageId}`
  return stageMap.value[key]?.unit_price || getCourseUnitPrice(courseId)
}

function calcOriginalPrice(pkg) {
  const unitPrice = getStageUnitPrice(pkg.course_id, pkg.stage_id)
  return (pkg.purchase_hours * unitPrice).toFixed(2)
}

function calcPayableAmount(pkg) {
  const originalPrice = parseFloat(calcOriginalPrice(pkg))
  const mode = pkg.discount_mode
  const rate = pkg.discount_rate || 0
  const direct = pkg.direct_reduction || 0
  let payable = originalPrice
  if (mode === 'direct') {
    payable = originalPrice - direct
  } else if (mode === 'discount') {
    payable = originalPrice * (rate / 10)
  } else if (mode === 'discount_then_direct') {
    payable = originalPrice * (rate / 10) - direct
  } else if (mode === 'direct_then_discount') {
    payable = (originalPrice - direct) * (rate / 10)
  }
  return Math.max(0, payable).toFixed(2)
}

function calcDiscountAmount(pkg) {
  const original = parseFloat(calcOriginalPrice(pkg))
  const payable = parseFloat(calcPayableAmount(pkg))
  return (original - payable).toFixed(2)
}

// ★ 课程切换时加载课阶
async function onCourseChange(courseId) {
  form.stage_id = null
  stageOptions.value = []
  if (!courseId) return

  try {
    const res = await getCourseStages(courseId, { is_active: true })
    stageOptions.value = res.data || []
    // 缓存课阶价格
    stageOptions.value.forEach(s => {
      stageMap.value[`${courseId}_${s.id}`] = s
    })
    if (stageOptions.value.length === 1) {
      form.stage_id = stageOptions.value[0].id
    }
  } catch (e) {
    console.error('加载课阶失败', e)
  }
}

async function loadAllPackages() {
  loading.value = true
  try {
    const courseRes = await getCourseListSimple()
    courses.value = courseRes.data || []
    courses.value.forEach(c => {
      coursePriceMap.value[c.id] = c.unit_price || 0
    })

    // 加载所有课阶信息
    for (const course of courses.value) {
      try {
        const res = await getCourseStages(course.id, { is_active: true })
        res.data.forEach(s => {
          stageMap.value[`${course.id}_${s.id}`] = s
        })
      } catch (e) {
        console.error(`加载课阶失败 course ${course.id}`, e)
      }
    }

    const promises = courses.value.map(async (course) => {
      const res = await getCoursePackages(course.id)
      return { courseId: course.id, packages: res.data || [] }
    })
    const results = await Promise.all(promises)
    packagesMap.value = {}
    results.forEach(item => {
      packagesMap.value[item.courseId] = item.packages.map(p => {
        // 补充课阶名称
        const stage = stageMap.value[`${item.courseId}_${p.stage_id}`]
        return { ...p, stage_name: stage?.name || '' }
      })
    })
  } catch (error) {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

async function refreshCoursePackages(courseId) {
  try {
    const res = await getCoursePackages(courseId)
    packagesMap.value[courseId] = (res.data || []).map(p => {
      const stage = stageMap.value[`${courseId}_${p.stage_id}`]
      return { ...p, stage_name: stage?.name || '' }
    })
  } catch (error) {
    console.error('刷新套餐失败', error)
  }
}

function resetForm() {
  form.course_id = null
  form.stage_id = null
  form.name = ''
  form.purchase_hours = 1
  form.gift_hours = 0
  form.discount_mode = 'none'
  form.discount_rate = 0
  form.direct_reduction = 0
  form.validity_days = null
  form.leave_limit = '不限制'
  form.leave_limit_count = 0
  form.sort_order = 0
  form.is_default = false
  form.remark = ''
  stageOptions.value = []
}

function openCreateDialog() {
  editing.value = false
  currentPackageId.value = null
  resetForm()
  dialogVisible.value = true
}

function openCreateDialogForCourse(course) {
  editing.value = false
  currentPackageId.value = null
  resetForm()
  form.course_id = course.id
  onCourseChange(course.id)
  dialogVisible.value = true
}

function openEditDialog(pkg) {
  editing.value = true
  currentPackageId.value = pkg.id
  form.course_id = pkg.course_id
  form.stage_id = pkg.stage_id || null
  form.name = pkg.name
  form.purchase_hours = pkg.purchase_hours
  form.gift_hours = pkg.gift_hours
  form.discount_mode = pkg.discount_mode
  form.discount_rate = pkg.discount_rate
  form.direct_reduction = pkg.direct_reduction
  form.validity_days = pkg.validity_days
  form.leave_limit = pkg.leave_limit
  form.leave_limit_count = pkg.leave_limit_count
  form.sort_order = pkg.sort_order
  form.is_default = pkg.is_default
  form.remark = pkg.remark || ''

  // 加载课阶选项
  onCourseChange(pkg.course_id)

  dialogVisible.value = true
}

async function submit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const data = {
      course_id: form.course_id,
      stage_id: form.stage_id || null,
      name: form.name,
      purchase_hours: form.purchase_hours,
      gift_hours: form.gift_hours,
      discount_mode: form.discount_mode,
      discount_rate: form.discount_rate,
      direct_reduction: form.direct_reduction,
      validity_days: form.validity_days,
      leave_limit: form.leave_limit,
      leave_limit_count: form.leave_limit_count,
      sort_order: form.sort_order,
      is_default: form.is_default,
      remark: form.remark
    }

    if (editing.value) {
      await updatePackage(currentPackageId.value, data)
      ElMessage.success('更新成功')
      await refreshCoursePackages(form.course_id)
    } else {
      if (!form.course_id) {
        ElMessage.error('请选择所属课程')
        return
      }
      await createPackage(data)
      ElMessage.success('创建成功')
      await refreshCoursePackages(form.course_id)
    }
    dialogVisible.value = false
    await loadAllPackages()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

async function handleDelete(pkg) {
  if (!pkg || !pkg.id) {
    ElMessage.error('套餐数据无效')
    return
  }
  try {
    await ElMessageBox.confirm(`确认删除套餐"${pkg.name}"？`, '提示', {
      type: 'warning',
      confirmButtonText: '确认删除',
      cancelButtonText: '取消'
    })
    await deletePackage(pkg.id)
    ElMessage.success('删除成功')
    await refreshCoursePackages(pkg.course_id)
    await loadAllPackages()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

onMounted(() => {
  loadAllPackages()
})
</script>

<style scoped>
.package-manage {
  padding: 16px;
  background: var(--surface-soft);
  min-height: 100%;
}

.page-header {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-bottom: 24px;
}

:deep(.el-input input[type=number])::-webkit-outer-spin-button,
:deep(.el-input input[type=number])::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
:deep(.el-input input[type=number]) {
  -moz-appearance: textfield;
}

.course-group {
  margin-bottom: 32px;
}

.course-title {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-light);
}

.course-title span {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  padding-left: 12px;
  position: relative;
}

.course-title span::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 20px;
  background: var(--brand-500);
  border-radius: 2px;
}

.stage-count {
  font-size: 13px;
  font-weight: 400;
  color: var(--text-placeholder);
}

.packages-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}

.package-card {
  background: var(--surface);
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.2s ease;
  overflow: hidden;
  border: 1px solid var(--surface-soft);
  display: flex;
  flex-direction: column;
}

.package-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.06);
}

.default-card {
  border: 1.5px solid var(--brand-500);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px 6px 14px;
  flex-wrap: wrap;
  gap: 4px;
}

.package-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.card-actions {
  display: flex;
  gap: 2px;
}

.price-section {
  padding: 0 14px 6px 14px;
  border-bottom: 1px solid var(--surface-soft);
  margin-bottom: 6px;
}

.price-main {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.price-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.price-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--warning);
}

.price-saved {
  text-align: right;
  font-size: 11px;
  color: var(--text-placeholder);
}

.info-list {
  padding: 4px 14px 10px 14px;
  flex: 1;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
  font-size: 13px;
  border-bottom: 1px dashed var(--surface-soft);
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  color: var(--text-secondary);
}

.info-value {
  font-weight: 500;
  color: var(--text-primary);
}

.card-footer {
  padding: 6px 14px 10px 14px;
  text-align: right;
  border-top: 1px solid var(--surface-soft);
  background: var(--surface);
}

.empty-placeholder {
  text-align: center;
  padding: 32px;
  background: var(--surface);
  border-radius: 12px;
  color: var(--text-placeholder);
  font-size: 14px;
}

.package-dialog :deep(.el-dialog__header) {
  border-bottom: 1px solid var(--border-light);
  padding: 16px 24px;
}
.package-dialog :deep(.el-dialog__body) {
  padding: 24px;
}
.package-dialog :deep(.el-dialog__footer) {
  border-top: 1px solid var(--border-light);
  padding: 16px 24px;
}

.stage-info-hint {
  font-size: 12px;
  color: var(--text-placeholder);
  margin-top: 4px;
}
</style>