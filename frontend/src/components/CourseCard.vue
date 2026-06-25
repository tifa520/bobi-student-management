<template>
  <el-card class="course-card" shadow="never">
    <template #header>
      <div class="card-header">
        <span class="course-name">{{ card.courseName }}</span>
        <el-button type="danger" link @click="$emit('remove')">删除</el-button>
      </div>
    </template>

    <!-- 套餐选择器 -->
    <div class="package-section" v-if="card.courseId">
      <PackageSelector 
        :course-id="card.courseId"
        @select="onPackageSelect"
      />
    </div>

    <div class="fixed-form">
      <!-- 第一行：报名类型 -->
      <div class="form-row single-row">
        <div class="field-unit">
          <span class="field-label">报名类型:</span>
          <div class="field-control">
            <el-radio-group v-model="card.enrollType" :name="`enrollType_${index}`">
              <el-radio label="新报">新报</el-radio>
              <el-radio label="续报">续报</el-radio>
              <el-radio label="扩科">扩科</el-radio>
            </el-radio-group>
          </div>
        </div>
      </div>

      <!-- 第二行：课程 + 课阶 + 班级 -->
      <div class="form-row three-cols">
        <div class="field-unit">
          <span class="field-label">课程:</span>
          <div class="field-control">
            <span class="readonly-text">{{ card.courseName }}</span>
          </div>
        </div>
        <div class="field-unit">
          <span class="field-label">课阶:</span>
          <div class="field-control">
            <el-select
              v-model="card.stageId"
              placeholder="请选择课阶"
              clearable
              style="width: 120px"
              @change="onStageChange"
              :disabled="!card.courseId"
            >
              <el-option
                v-for="s in stageOptions"
                :key="s.id"
                :label="s.name"
                :value="s.id"
              />
            </el-select>
          </div>
        </div>
        <div class="field-unit">
          <span class="field-label">班级:</span>
          <div class="field-control">
            <div class="input-with-error">
              <el-select
                v-model="card.classId"
                placeholder="请先选择课阶"
                clearable
                style="width: 120px"
                @blur="validateClassId"
                :disabled="!card.stageId"
              >
                <el-option
                  v-for="cls in classOptions"
                  :key="cls.id"
                  :label="cls.name"
                  :value="cls.id"
                />
              </el-select>
              <div v-if="errors.classId" class="error-tip">{{ errors.classId }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 第三行：购买课时 + 有效期 + 请假限制 -->
      <div class="form-row three-cols">
        <div class="field-unit">
          <span class="field-label">购买课时:</span>
          <div class="field-control">
            <div class="input-with-error">
              <el-input
                v-model="card.purchaseHours"
                placeholder=""
                inputmode="numeric"
                style="width: 120px"
                @blur="validatePurchaseHours"
              >
                <template #suffix><span class="suffix-text">课时</span></template>
              </el-input>
              <div v-if="errors.purchaseHours" class="error-tip">{{ errors.purchaseHours }}</div>
            </div>
          </div>
        </div>
        <div class="field-unit">
          <span class="field-label">有效期:</span>
          <div class="field-control">
            <div class="validity-group">
              <div class="input-with-error">
                <el-input
                  v-model="card.validityDays"
                  placeholder=""
                  inputmode="numeric"
                  style="width: 120px"
                  @blur="validateValidityDays"
                  @input="onValidityDaysInput"
                >
                  <template #suffix><span class="suffix-text">天</span></template>
                </el-input>
                <div v-if="errors.validityDays" class="error-tip">{{ errors.validityDays }}</div>
              </div>
            </div>
          </div>
        </div>
        <div class="field-unit">
          <span class="field-label">请假限制:</span>
          <div class="field-control">
            <div class="leave-wrapper">
              <el-select v-model="card.leaveLimit" style="width: 120px" @change="handleLeaveLimitChange">
                <el-option label="不允许" value="不允许" />
                <el-option label="不限制" value="不限制" />
                <el-option label="限制次数" value="限制次数" />
              </el-select>
              <template v-if="card.leaveLimit === '限制次数'">
                <div class="input-with-error" style="margin-left: 8px;">
                  <el-input
                    v-model="card.leaveLimitCount"
                    placeholder=""
                    inputmode="numeric"
                    style="width: 120px"
                    @blur="validateLeaveLimitCount"
                  >
                    <template #suffix><span class="suffix-text">次</span></template>
                  </el-input>
                  <div v-if="errors.leaveLimitCount" class="error-tip">{{ errors.leaveLimitCount }}</div>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>

      <!-- 第四行：课程原价 + 优惠方式 -->
      <div class="form-row two-cols">
        <div class="field-unit">
          <span class="field-label">课程原价:</span>
          <div class="field-control"><span class="price-text">￥{{ card.originalPrice || 0 }}</span></div>
        </div>
        <div class="field-unit">
          <span class="field-label">优惠方式:</span>
          <div class="field-control">
            <div class="discount-wrapper">
              <el-select v-model="card.discountMode" style="width: 120px" @change="handleDiscountModeChange">
                <el-option label="无" value="none" />
                <el-option label="直减" value="direct" />
                <el-option label="折扣" value="discount" />
                <el-option label="折上折" value="double_discount" />
                <el-option label="先折扣再直减" value="discount_then_direct" />
                <el-option label="先直减再折扣" value="direct_then_discount" />
              </el-select>
              <div class="discount-inputs" v-if="showDiscountRate || showDirect || showDoubleDiscount">
                <!-- 折上折：显示两个折扣输入框 -->
                <template v-if="card.discountMode === 'double_discount'">
                  <div class="discount-item">
                    <span class="discount-label">折扣1:</span>
                    <div class="input-with-error">
                      <el-input
                        v-model="card.discountRate1"
                        placeholder=""
                        style="width: 120px"
                        @blur="validateDiscountRate1"
                      >
                        <template #suffix><span class="suffix-text">折</span></template>
                      </el-input>
                      <div v-if="errors.discountRate1" class="error-tip">{{ errors.discountRate1 }}</div>
                    </div>
                  </div>
                  <div class="discount-item">
                    <span class="discount-label">折扣2:</span>
                    <div class="input-with-error">
                      <el-input
                        v-model="card.discountRate2"
                        placeholder=""
                        style="width: 120px"
                        @blur="validateDiscountRate2"
                      >
                        <template #suffix><span class="suffix-text">折</span></template>
                      </el-input>
                      <div v-if="errors.discountRate2" class="error-tip">{{ errors.discountRate2 }}</div>
                    </div>
                  </div>
                </template>
                <!-- 原有的折扣/直减逻辑 -->
                <template v-else>
                  <div v-if="showDiscountRate" class="discount-item">
                    <span class="discount-label">折扣:</span>
                    <div class="input-with-error">
                      <el-input
                        v-model="card.discountRate"
                        placeholder=""
                        style="width: 120px"
                        @blur="validateDiscountRate"
                      >
                        <template #suffix><span class="suffix-text">折</span></template>
                      </el-input>
                      <div v-if="errors.discountRate" class="error-tip">{{ errors.discountRate }}</div>
                    </div>
                  </div>
                  <div v-if="showDirect" class="discount-item">
                    <span class="discount-label">直减:</span>
                    <div class="input-with-error">
                      <el-input
                        v-model="card.directReduction"
                        placeholder=""
                        style="width: 120px"
                        @blur="validateDirectReduction"
                      >
                        <template #suffix><span class="suffix-text">元</span></template>
                      </el-input>
                      <div v-if="errors.directReduction" class="error-tip">{{ errors.directReduction }}</div>
                    </div>
                  </div>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 第五行：赠送课时 -->
      <div class="form-row single-row">
        <div class="field-unit">
          <span class="field-label">赠送课时:</span>
          <div class="field-control">
            <div class="gift-wrapper">
              <el-select v-model="card.hasGift" style="width: 120px" @change="handleGiftTypeChange">
                <el-option label="无赠送" value="no" />
                <el-option label="赠送" value="yes" />
              </el-select>
              <template v-if="card.hasGift === 'yes'">
                <div class="input-with-error" style="margin-left: 8px;">
                  <el-input
                    v-model="card.giftHours"
                    placeholder=""
                    inputmode="numeric"
                    style="width: 120px"
                    @blur="validateGiftHours"
                  >
                    <template #suffix><span class="suffix-text">课时</span></template>
                  </el-input>
                  <div v-if="errors.giftHours" class="error-tip">{{ errors.giftHours }}</div>
                </div>
                <el-input
                  v-model="card.giftNote"
                  placeholder="赠送说明（选填）"
                  style="width: 400px; margin-left: 8px"
                />
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="card-footer">
      <span>优惠金额：<strong class="text-primary">{{ card.discountAmount }}</strong></span>
      <span class="payable">应付金额：<strong class="text-danger">{{ card.payableAmount }}</strong></span>
    </div>
  </el-card>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import PackageSelector from './PackageSelector.vue'
import { getCourseStages } from '@/api/course'
import { getClassesByCourseAndStage } from '@/api/class'
import { ElMessage } from 'element-plus'

const props = defineProps({
  card: { type: Object, required: true },
  index: { type: Number, required: true }
})
const emit = defineEmits(['remove', 'recalc', 'validate', 'stage-change']) // ★ 新增 stage-change 事件

// ========== 数据 ==========
const stageOptions = ref([])
const classOptions = ref([])

// ========== 错误状态 ==========
const errors = ref({
  purchaseHours: '',
  validityDays: '',
  classId: '',
  discountRate: '',
  discountRate1: '',
  discountRate2: '',
  directReduction: '',
  leaveLimitCount: '',
  giftHours: ''
})

// ========== 初始化 ==========
if (props.card.hasGift === undefined) {
  props.card.hasGift = 'no'
  props.card.giftHours = null
  props.card.giftNote = ''
}
if (props.card.discountRate1 === undefined) props.card.discountRate1 = null
if (props.card.discountRate2 === undefined) props.card.discountRate2 = null

// ========== 计算属性 ==========
const showDirect = computed(() => ['direct', 'discount_then_direct', 'direct_then_discount'].includes(props.card.discountMode))
const showDiscountRate = computed(() => ['discount', 'discount_then_direct', 'direct_then_discount'].includes(props.card.discountMode))
const showDoubleDiscount = computed(() => props.card.discountMode === 'double_discount')

// ========== 加载课阶 ==========
async function loadStages() {
  if (!props.card.courseId) {
    stageOptions.value = []
    return
  }
  try {
    const res = await getCourseStages(props.card.courseId, { is_active: true })
    stageOptions.value = res.data || []
    if (props.card.stageId && !stageOptions.value.some(s => s.id === props.card.stageId)) {
      props.card.stageId = null
    }
  } catch (e) {
    stageOptions.value = []
  }
}

// ========== 加载班级（根据课程+课阶） ==========
async function loadClasses() {
  if (!props.card.courseId || !props.card.stageId) {
    classOptions.value = []
    props.card.classId = null
    return
  }
  try {
    const res = await getClassesByCourseAndStage(props.card.courseId, props.card.stageId)
    classOptions.value = res.data || []
    if (classOptions.value.length === 1) {
      props.card.classId = classOptions.value[0].id
    } else {
      if (props.card.classId && !classOptions.value.some(c => c.id === props.card.classId)) {
        props.card.classId = null
      }
    }
  } catch (e) {
    classOptions.value = []
  }
}

// ========== 监听课程变化 ==========
watch(() => props.card.courseId, () => {
  loadStages()
  props.card.stageId = null
  props.card.classId = null
  classOptions.value = []
})

// ========== ★ 课阶变更（核心修复） ==========
function onStageChange() {
  loadClasses()
  const selected = stageOptions.value.find(s => s.id === props.card.stageId)
  if (selected) {
    props.card.unitPrice = selected.unit_price
    props.card.duration = selected.duration
    props.card.deduct_hours = selected.deduct_hours
    // ★ 更新 stageName，保证第三步页面能显示
    props.card.stageName = selected.name
    emit('recalc', props.card)
    emit('stage-change', props.card) // 通知父组件
  } else {
    // 如果清空课阶，清空相关字段
    props.card.stageName = ''
    emit('recalc', props.card)
    emit('stage-change', props.card)
  }
}

// ========== 套餐选择 ==========
function onPackageSelect(pkg) {
  props.card.purchaseHours = pkg.purchase_hours
  props.card.giftHours = pkg.gift_hours
  props.card.validityDays = pkg.validity_days
  props.card.leaveLimit = pkg.leave_limit
  props.card.leaveLimitCount = pkg.leave_limit_count
  props.card.discountMode = pkg.discount_mode
  props.card.discountRate = pkg.discount_rate || 0
  props.card.directReduction = pkg.direct_reduction || 0
  props.card.classId = null
  emit('recalc', props.card)
}

// ========== 校验方法 ==========
function validatePurchaseHours() {
  const val = props.card.purchaseHours
  if (!val) errors.value.purchaseHours = '请填写购买课时数'
  else { const num = Number(val); if (!Number.isInteger(num) || num <= 0) errors.value.purchaseHours = '请输入大于0的正整数'; else { errors.value.purchaseHours = ''; emit('recalc') } }
}
function validateValidityDays() {
  const val = props.card.validityDays
  if (!val) errors.value.validityDays = '请填写有效期天数'
  else { const num = Number(val); if (!Number.isInteger(num) || num <= 0) errors.value.validityDays = '请输入大于0的正整数'; else { errors.value.validityDays = ''; emit('recalc') } }
}
function onValidityDaysInput() { if (errors.value.validityDays) errors.value.validityDays = '' }
function validateClassId() {
  errors.value.classId = props.card.classId ? '' : '请选择班级'
}
function validateDiscountRate() {
  if (!['discount', 'discount_then_direct', 'direct_then_discount'].includes(props.card.discountMode)) {
    errors.value.discountRate = ''
    return
  }
  const rate = props.card.discountRate
  if (!rate) errors.value.discountRate = '请填写折扣率'
  else { const num = parseFloat(rate); if (isNaN(num) || num <= 0 || num >= 10) errors.value.discountRate = '请输入大于0且小于10的正数'; else { errors.value.discountRate = ''; emit('recalc') } }
}
function validateDiscountRate1() {
  if (props.card.discountMode !== 'double_discount') {
    errors.value.discountRate1 = ''
    return
  }
  const rate = props.card.discountRate1
  if (!rate) errors.value.discountRate1 = '请填写折扣1'
  else { const num = parseFloat(rate); if (isNaN(num) || num <= 0 || num >= 10) errors.value.discountRate1 = '请输入大于0且小于10的正数'; else { errors.value.discountRate1 = ''; emit('recalc') } }
}
function validateDiscountRate2() {
  if (props.card.discountMode !== 'double_discount') {
    errors.value.discountRate2 = ''
    return
  }
  const rate = props.card.discountRate2
  if (!rate) errors.value.discountRate2 = '请填写折扣2'
  else { const num = parseFloat(rate); if (isNaN(num) || num <= 0 || num >= 10) errors.value.discountRate2 = '请输入大于0且小于10的正数'; else { errors.value.discountRate2 = ''; emit('recalc') } }
}
function validateDirectReduction() {
  if (!['direct', 'discount_then_direct', 'direct_then_discount'].includes(props.card.discountMode)) {
    errors.value.directReduction = ''
    return
  }
  const direct = props.card.directReduction
  if (!direct) errors.value.directReduction = '请填写直减金额'
  else { const num = parseFloat(direct); if (isNaN(num) || num <= 0) errors.value.directReduction = '请输入大于0的正数'; else { errors.value.directReduction = ''; emit('recalc') } }
}
function validateLeaveLimitCount() {
  if (props.card.leaveLimit !== '限制次数') { errors.value.leaveLimitCount = ''; return }
  const val = props.card.leaveLimitCount
  if (!val) errors.value.leaveLimitCount = '请填写请假限制次数'
  else { const num = Number(val); if (!Number.isInteger(num) || num <= 0) errors.value.leaveLimitCount = '请输入大于0的正整数'; else errors.value.leaveLimitCount = '' }
}
function validateGiftHours() {
  if (props.card.hasGift !== 'yes') { errors.value.giftHours = ''; return }
  const val = props.card.giftHours
  if (!val) errors.value.giftHours = '请填写赠送课时数量'
  else { const num = Number(val); if (!Number.isInteger(num) || num <= 0) errors.value.giftHours = '请输入大于0的正整数'; else errors.value.giftHours = '' }
}

// ========== 统一校验 ==========
function validate() {
  validatePurchaseHours()
  validateValidityDays()
  validateClassId()
  validateDiscountRate()
  validateDiscountRate1()
  validateDiscountRate2()
  validateDirectReduction()
  validateLeaveLimitCount()
  validateGiftHours()
  return !Object.values(errors.value).some(e => e !== '')
}
defineExpose({ validate, errors })

// ========== 事件处理 ==========
function handleDiscountModeChange() {
  props.card.discountRate = null
  props.card.directReduction = null
  props.card.discountRate1 = null
  props.card.discountRate2 = null
  errors.value.discountRate = ''
  errors.value.discountRate1 = ''
  errors.value.discountRate2 = ''
  errors.value.directReduction = ''
  emit('recalc')
}
function handleLeaveLimitChange() {
  props.card.leaveLimitCount = null
  errors.value.leaveLimitCount = ''
}
function handleGiftTypeChange() {
  if (props.card.hasGift === 'no') {
    props.card.giftHours = null
    props.card.giftNote = ''
  } else {
    props.card.giftHours = null
  }
  errors.value.giftHours = ''
}

// ========== 组件挂载时加载数据 ==========
onMounted(() => {
  if (props.card.courseId) {
    loadStages()
    if (props.card.stageId) {
      // 如果已有 stageId，设置 stageName
      const selected = stageOptions.value.find(s => s.id === props.card.stageId)
      if (selected) {
        props.card.stageName = selected.name
      }
      loadClasses()
    }
  }
})

watch(() => props.card.stageId, (newVal, oldVal) => {
  if (newVal !== oldVal) {
    emit('recalc', props.card)
  }
})
</script>

<style scoped>
.course-card {
  margin-bottom: 20px;
  border: 1px solid #36b459;
  background: #fff;
}
.course-card :deep(.el-card__header) {
  background-color: #36b459;
  padding: 12px;
  border-bottom: none;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.course-name {
  font-weight: bold;
  font-size: 16px;
  color: white;
}
.card-header .el-button {
  color: white;
}
.fixed-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-top: 12px;
}
.form-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px 24px;
}
.single-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 24px;
}
.two-cols {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 24px;
}
.three-cols {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 24px;
}
.field-unit {
  display: flex;
  align-items: center;
  gap: 8px;
}
.field-label {
  flex-shrink: 0;
  font-size: 14px;
  color: var(--text-regular);
  line-height: 32px;
  white-space: nowrap;
}
.field-control {
  position: relative;
  display: flex;
  align-items: center;
}
.input-with-error {
  position: relative;
  display: inline-block;
}
.error-tip {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 4px;
  font-size: 12px;
  color: #f56c6c;
  white-space: nowrap;
  z-index: 10;
  background-color: #fff;
  padding: 0 4px;
  border-radius: 2px;
  pointer-events: none;
}
.price-text, .readonly-text {
  font-size: 14px;
  line-height: 32px;
}
.suffix-text {
  color: var(--text-secondary);
  font-size: 14px;
}
.validity-group {
  display: flex;
  align-items: center;
  gap: 8px;
}
.discount-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: nowrap;
}
.discount-inputs {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.discount-item {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: nowrap;
}
.discount-label {
  font-size: 13px;
  color: var(--text-regular);
  white-space: nowrap;
}
.leave-wrapper, .gift-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: nowrap;
}
.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid var(--border-color);
  margin-top: 14px;
  font-size: 14px;
}
.payable strong {
  font-size: 16px;
  color: #f56c6c;
}
.text-primary {
  color: var(--primary-color);
}
.package-section {
  margin-bottom: 12px;
  padding: 8px;
  background: #f8fafc;
  border-radius: 8px;
}
</style>