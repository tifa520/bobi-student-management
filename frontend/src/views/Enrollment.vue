<!-- frontend/src/views/Enrollment.vue -->
<template>
  <div class="enroll-page">
    <EnrollStep
      :current-step="store.currentStep"
      :show-actions="false"
      :submitting="submitting"
      @prev="prevStep"
      @next="nextStep"
      @submit="submitEnroll"
    >
      <!-- 第一步：学员信息 -->
      <template #step1>
        <div class="step1-panel">
          <el-form :model="step1Form" label-width="90px" ref="step1FormRef">
            <el-form-item label="学员姓名" required>
              <div style="display: flex; align-items: center; gap: 10px;">
                <template v-if="store.step1Data?.student_name">
                  <el-input :value="store.step1Data.student_name" disabled style="width: 260px;" />
                  <el-button link @click="resetStudentSelection">重新选择</el-button>
                </template>
                <StudentPicker
                  v-else
                  :model-value="selectedStudentId"
                  :allow-create="true"
                  placeholder="请输入学员姓名或手机号搜索"
                  style="width: 260px;"
                  @student-selected="onStudentSelected"
                  @create-student="onStudentCreated"
                />
              </div>
            </el-form-item>
            <el-form-item label="联系方式" required>
              <el-input v-model="step1Form.phone" placeholder="请输入手机号" disabled style="width: 260px;" />
            </el-form-item>
          </el-form>
        </div>
      </template>

      <!-- 第二步：报名信息 -->
      <template #step2>
        <div class="step2-panel">
          <div class="student-summary" v-if="store.step1Data">
            学员姓名：{{ store.step1Data.student_name }} 联系方式：{{ store.step1Data.phone }}
          </div>
          <el-button type="primary" class="add-course-btn" @click="openCourseSelector">
            {{ selectedCourses.length ? '增加课程' : '选择课程' }}
          </el-button>

          <div v-for="(card, index) in selectedCourses" :key="card.courseId" class="course-card-wrapper">
            <CourseCard
              :ref="el => { if (el) courseCards[index] = el }"
              :card="card"
              :index="index"
              @remove="removeCourse(index)"
              @recalc="recalcSingle(card)"
              @stage-change="onStageChange(card)"
            />
          </div>

          <div v-if="selectedCourses.length" class="total-bar">
            应付金额合计：<strong class="text-danger">￥{{ totalPayable }}</strong>
          </div>
        </div>
      </template>

      <!-- 第三步：费用结算 -->
      <template #step3>
        <div class="step3-panel">
          <div class="student-summary" v-if="store.step1Data">
            学员姓名：{{ store.step1Data.student_name }} 联系方式：{{ store.step1Data.phone }}
          </div>

          <el-table :data="summaryCourses" border class="fixed-table">
            <el-table-column prop="courseName" label="报名课程" min-width="120" />
            <el-table-column prop="stageName" label="课阶" min-width="100" />
            <el-table-column prop="enrollType" label="购买类型" min-width="90" />
            <el-table-column prop="purchaseHours" label="购买课时" min-width="90" />
            <el-table-column label="单价" min-width="90">
              <template #default="{ row }">￥{{ row.unitPrice }}</template>
            </el-table-column>
            <el-table-column label="总金额" min-width="100">
              <template #default="{ row }">￥{{ row.originalPrice }}</template>
            </el-table-column>
            <el-table-column label="优惠金额" min-width="100">
              <template #default="{ row }">￥{{ row.discountAmount }}</template>
            </el-table-column>
            <el-table-column label="应付金额" min-width="100">
              <template #default="{ row }">￥{{ row.payableAmount }}</template>
            </el-table-column>
          </el-table>

          <el-row :gutter="20" class="step3-bottom">
            <el-col :span="12">
              <el-form :model="step3Form">
                <el-row :gutter="12">
                  <el-col :span="12">
                    <el-form-item label="支付方式" label-width="auto">
                      <el-select v-model="step3Form.paymentMethod" style="width: 150px">
                        <el-option v-for="m in paymentMethodOptions" :key="m" :label="m" :value="m" />
                      </el-select>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="业绩归属">
                      <el-select v-model="step3Form.performanceTeacherId" clearable placeholder="选择教师" style="width: 150px">
                        <el-option v-for="t in teachers" :key="t.id" :label="t.name" :value="t.id" />
                      </el-select>
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-form-item label="收款金额">
                  <el-input
                    v-model.number="step3Form.paidAmount"
                    placeholder="0"
                    inputmode="decimal"
                    class="input-with-suffix"
                    style="width: 136px"
                  >
                    <template #suffix><span class="suffix-text">元</span></template>
                  </el-input>
                  <el-button type="primary" size="small" class="tail-setting-btn" @click="openTailDialog">设置尾款</el-button>
                  <template v-if="arrears > 0">
                    <span class="arrears-tip">
                      <span class="arrears-label">尾款：</span>
                      <span class="text-danger">￥{{ arrears }}</span>
                    </span>
                  </template>
                </el-form-item>

                <template v-if="arrears > 0 && tailFormItems.length > 0 && tailFormItems.some(item => item.tailAmount > 0)">
                  <el-divider />
                  <el-table :data="tailFormItems" border size="small">
                    <el-table-column prop="courseName" label="课程" />
                    <el-table-column prop="stageName" label="课阶" />
                    <el-table-column label="应付金额">
                      <template #default="{ row }">￥{{ row.payableAmount }}</template>
                    </el-table-column>
                    <el-table-column label="尾款设置">
                      <template #default="{ row }">￥{{ row.tailAmount }}</template>
                    </el-table-column>
                    <el-table-column label="实付金额">
                      <template #default="{ row }">￥{{ row.paidAmount.toFixed(2) }}</template>
                    </el-table-column>
                  </el-table>
                </template>
              </el-form>
            </el-col>

            <el-col :span="12">
              <div class="amount-panel">
                <div class="amount-row"><span>总金额</span><span class="text-danger">￥{{ totalOriginal }}</span></div>
                <div class="amount-row"><span>优惠金额</span><span class="text-danger">￥{{ totalDiscount }}</span></div>
                <div class="amount-row"><span>应付金额</span><strong class="text-danger">￥{{ totalPayable }}</strong></div>
                <div class="amount-row"><span>实付金额</span><span class="text-danger">￥{{ step3Form.paidAmount }}</span></div>
                <div class="amount-row" v-if="arrears > 0">
                  <span>尾款</span><span class="text-danger">￥{{ arrears }}</span>
                </div>
                <div class="amount-row" v-if="totalPoints > 0">
                  <span>赠送积分</span><span class="text-primary">{{ totalPoints }} 分</span>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>
      </template>
    </EnrollStep>

    <!-- 底部固定操作栏 -->
    <div class="step-actions-fixed">
      <el-button v-if="store.currentStep > 1" @click="prevStep" class="btn-prev">上一步</el-button>
      <el-button v-if="store.currentStep < 3" type="primary" @click="nextStep" class="btn-next">下一步</el-button>
      <el-button v-if="store.currentStep === 3" type="primary" @click="submitEnroll" :loading="submitting">提交报名</el-button>
    </div>

    <!-- 课程选择弹窗 -->
    <CourseSelectorModal ref="courseSelector" @course-selected="addCourse" />

    <!-- 尾款分课程设置弹窗 -->
    <el-dialog v-model="showTailDialog" title="分课程设置尾款金额" width="700px">
      <el-table :data="tailFormItems" border size="small">
        <el-table-column prop="courseName" label="课程" min-width="120" />
        <el-table-column prop="stageName" label="课阶" min-width="100" />
        <el-table-column label="应付金额" width="120" align="right">
          <template #default="{ row }">￥{{ row.payableAmount }}</template>
        </el-table-column>
        <el-table-column label="尾款设置" width="180">
          <template #default="{ row, $index }">
            <el-input-number
              v-model="row.tailAmount"
              :min="0"
              :max="row.payableAmount"
              :precision="2"
              :step="0.01"
              :controls="false"
              size="small"
              class="tail-amount-input"
              @change="() => updatePaidAmount($index)"
            />
          </template>
        </el-table-column>
        <el-table-column label="实付金额" width="120" align="right">
          <template #default="{ row }">￥{{ row.paidAmount.toFixed(2) }}</template>
        </el-table-column>
      </el-table>
      <div class="tail-summary">
        <span>尾款合计：</span>
        <strong :class="totalTailAmount === arrears ? 'text-primary' : 'text-danger'">￥{{ totalTailAmount }}</strong>
        <span v-if="totalTailAmount !== arrears" class="error-tip">（{{ totalTailAmount > arrears ? '大于' : '小于' }}总尾款 ￥{{ arrears }}）</span>
      </div>
      <template #footer>
        <el-button @click="showTailDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmTail" :disabled="totalTailAmount !== arrears">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import EnrollStep from '@/components/EnrollStep.vue'
import StudentPicker from '@/components/StudentPicker.vue'
import CourseCard from '@/components/CourseCard.vue'
import CourseSelectorModal from '@/components/CourseSelectorModal.vue'
import { useEnrollStore } from '@/stores/enroll'
import { useBaseDataStore } from '@/stores/baseData'
import { enrollApi } from '@/api/enroll'
import { getStudentDetail, getStudentCourses } from '@/api/student'
import { getCourseStages } from '@/api/course'
import request from '@/api/request'
import { getPaymentMethods } from '@/api/settings'
import dayjs from 'dayjs'

const router = useRouter()
const route = useRoute()
const store = useEnrollStore()
const baseStore = useBaseDataStore()

const step1FormRef = ref(null)
const selectedStudentId = ref(null)
const step1Form = reactive({
  student_name: '',
  phone: '',
  gender: '',
  birthDate: '',
  introducer: '',
  note: ''
})
const selectedCourses = ref([])
const courseCards = ref([])
const courseSelector = ref(null)
const step3Form = reactive({
  paymentMethod: '微信',
  paidAmount: 0,
  performanceTeacherId: null
})
const showTailDialog = ref(false)
const tailFormItems = ref([])
const submitting = ref(false)
const teachers = ref([])
const enrolledCourseIds = ref(new Set())

// ★ 课阶缓存
const stageCache = ref({})

// 支付方式选项
const paymentMethodOptions = ref(['微信', '支付宝', '现金', '银行转账'])

const totalOriginal = computed(() => selectedCourses.value.reduce((s, c) => s + (c.originalPrice || 0), 0))
const totalDiscount = computed(() => selectedCourses.value.reduce((s, c) => s + (c.discountAmount || 0), 0))
const totalPayable = computed(() => selectedCourses.value.reduce((s, c) => s + (c.payableAmount || 0), 0))
const totalPoints = computed(() => {
  const paid = parseFloat(step3Form.paidAmount) || 0
  return Math.floor(paid * 10)
})
const arrears = computed(() => Math.max(0, totalPayable.value - step3Form.paidAmount))
const totalTailAmount = computed(() => tailFormItems.value.reduce((s, item) => s + (Number(item.tailAmount) || 0), 0))

const summaryCourses = computed(() => selectedCourses.value.map(c => ({
  courseName: c.courseName,
  stageName: c.stageName || '-',
  enrollType: c.enrollType,
  purchaseHours: c.purchaseHours,
  unitPrice: c.unitPrice || 0,
  originalPrice: c.originalPrice || 0,
  discountAmount: c.discountAmount || 0,
  payableAmount: c.payableAmount || 0
})))

// ★ 获取课阶选项
function getStageOptions(courseId) {
  return stageCache.value[courseId] || []
}

// ★ 加载课阶
async function loadStagesForCourse(courseId) {
  if (stageCache.value[courseId]) return stageCache.value[courseId]
  try {
    const res = await getCourseStages(courseId, { is_active: true })
    stageCache.value[courseId] = res.data || []
    return stageCache.value[courseId]
  } catch (e) {
    stageCache.value[courseId] = []
    return []
  }
}

// ★ 课阶变更时更新价格
function onStageChange(card) {
  const stages = stageCache.value[card.courseId] || []
  const stage = stages.find(s => s.id === card.stageId)
  if (stage) {
    card.stageName = stage.name
  }
  recalcSingle(card)
}

// 加载支付方式配置
async function loadPaymentMethods() {
  try {
    const res = await getPaymentMethods()
    if (res.code === 0 && res.data && res.data.length) {
      paymentMethodOptions.value = res.data
      step3Form.paymentMethod = paymentMethodOptions.value[0] || '微信'
    } else {
      paymentMethodOptions.value = ['微信支付', '支付宝', '现金', '银行转账']
      step3Form.paymentMethod = '微信'
    }
  } catch (e) {
    console.error('加载支付方式失败，使用默认值', e)
    paymentMethodOptions.value = ['微信支付', '支付宝', '现金', '银行转账']
    step3Form.paymentMethod = '微信'
  }
}

async function loadEnrolledCourses(studentId) {
  if (!studentId) return
  try {
    const res = await getStudentCourses(studentId)
    const courses = res.data || []
    enrolledCourseIds.value = new Set(courses.map(c => c.course_id))
  } catch (e) {
    console.error('加载学员已有课程失败', e)
  }
}

function onStudentSelected(student) {
  if (student) {
    step1Form.student_name = student.name
    step1Form.phone = student.phone
    step1Form.gender = student.gender || ''
    step1Form.birthDate = student.birthday || ''
    step1Form.introducer = student.introducer || ''
    step1Form.note = student.note || ''
    selectedStudentId.value = student.id
    loadEnrolledCourses(student.id)
  }
}

function onStudentCreated(newStudent) {
  onStudentSelected(newStudent)
}

function resetStudentSelection() {
  store.step1Data = null
  step1Form.student_name = ''
  step1Form.phone = ''
  selectedStudentId.value = null
}

function updatePaidAmount(index) {
  const item = tailFormItems.value[index]
  if (item) {
    let tail = Number(item.tailAmount) || 0
    if (tail < 0) tail = 0
    if (tail > item.payableAmount) tail = item.payableAmount
    item.tailAmount = tail
    item.paidAmount = parseFloat((item.payableAmount - tail).toFixed(2))
  }
}

function openCourseSelector() {
  courseSelector.value.open()
}

async function addCourse(row) {
  const exists = selectedCourses.value.find(c => c.courseId === row.id)
  if (exists) {
    ElMessage.warning('该课程已添加')
    return
  }

  // 加载课阶
  const stages = await loadStagesForCourse(row.id)
  const defaultStage = stages.length > 0 ? stages[0] : null

  let enrollType = '新报'
  if (enrolledCourseIds.value.size > 0) {
    if (enrolledCourseIds.value.has(row.id)) {
      enrollType = '续报'
    } else {
      enrollType = '扩科'
    }
  }

  await baseStore.fetchClasses()
  const classes = baseStore.classes.filter(cls => cls.course_id === row.id)

  // 如果有课阶，按课阶筛选班级
  let filteredClasses = classes
  if (defaultStage) {
    const stageClasses = classes.filter(cls => cls.stage_id === defaultStage.id)
    if (stageClasses.length > 0) {
      filteredClasses = stageClasses
    }
  }

  const initialPrice = defaultStage?.unit_price || (baseStore.courses.find(c => c.id === row.id)?.unit_price || 0)

  selectedCourses.value.push({
    courseId: row.id,
    courseName: row.name,
    stageId: defaultStage?.id || null,
    stageName: defaultStage?.name || '',
    unitPrice: initialPrice,
    enrollType: enrollType,
    purchaseHours: null,
    validityDays: null,
    validityDisplay: '',
    originalPrice: 0,
    discountMode: 'none',
    discountRate: 0,
    directReduction: 0,
    discountRate1: null,
    discountRate2: null,
    discountAmount: 0,
    payableAmount: 0,
    classId: filteredClasses.length === 1 ? filteredClasses[0].id : null,
    classOptions: filteredClasses,
    leaveLimit: '不限制',
    leaveLimitCount: 0,
    hasGift: 'no',
    giftHours: 0,
    giftNote: '',
    paid: undefined,
    duration: defaultStage?.duration || 60,
    deduct_hours: defaultStage?.deduct_hours || 1
  })
  recalcAll()
  nextTick(() => {
    courseCards.value = new Array(selectedCourses.value.length)
  })
}

function removeCourse(index) {
  selectedCourses.value.splice(index, 1)
  courseCards.value.splice(index, 1)
  recalcAll()
}

function recalcSingle(card) {
  const hours = Number(card.purchaseHours) || 0
  const unitPrice = card.unitPrice || 0
  card.originalPrice = hours * unitPrice
  let payable = card.originalPrice
  let discount = 0
  const mode = card.discountMode
  const rate = Number(card.discountRate) || 0
  const direct = Number(card.directReduction) || 0
  const rate1 = Number(card.discountRate1) || 0
  const rate2 = Number(card.discountRate2) || 0

  if (mode === 'direct') {
    payable = card.originalPrice - direct
    discount = direct
  } else if (mode === 'discount') {
    payable = card.originalPrice * (rate / 10)
    discount = card.originalPrice - payable
  } else if (mode === 'double_discount') {
    // ★ 折上折：先打第一个折扣，再打第二个折扣
    let afterFirst = card.originalPrice * (rate1 / 10)
    payable = afterFirst * (rate2 / 10)
    discount = card.originalPrice - payable
  } else if (mode === 'discount_then_direct') {
    payable = card.originalPrice * (rate / 10) - direct
    discount = card.originalPrice - payable
  } else if (mode === 'direct_then_discount') {
    payable = (card.originalPrice - direct) * (rate / 10)
    discount = card.originalPrice - payable
  } else {
    payable = card.originalPrice
    discount = 0
  }
  payable = Math.max(0, payable)
  discount = Math.max(0, discount)
  card.discountAmount = Math.round(discount * 100) / 100
  card.payableAmount = Math.round(payable * 100) / 100
}

function recalcAll() {
  selectedCourses.value.forEach(c => recalcSingle(c))
}

async function nextStep() {
  if (store.currentStep === 1) {
    if (!step1Form.student_name || !step1Form.phone) {
      ElMessage.warning('请填写学员姓名和联系方式')
      return
    }
    try {
      const res = await enrollApi.step1({ ...step1Form }, store.sessionId)
      const sid = res.session_id || res.data?.session_id
      if (!sid) {
        ElMessage.error('创建会话失败，请联系管理员')
        return
      }
      store.setSessionId(sid)
      store.step1Data = { ...step1Form, locked_student_id: selectedStudentId.value }
    } catch (e) {
      ElMessage.error('保存第一步失败，请重试')
      return
    }
    store.currentStep = 2
  } else if (store.currentStep === 2) {
    for (let i = 0; i < courseCards.value.length; i++) {
      const card = courseCards.value[i]
      if (card && typeof card.validate === 'function' && !card.validate()) {
        ElMessage.error('请完善课程信息中的红色错误项')
        return
      }
    }
    if (!selectedCourses.value.length) {
      ElMessage.warning('请至少选择一门课程')
      return
    }
    const courses = selectedCourses.value.map(c => ({
      course_id: c.courseId,
      stage_id: c.stageId || null,
      enroll_type: c.enrollType,
      purchase_hours: c.purchaseHours,
      validity_days: c.validityDays || null,
      discount_mode: c.discountMode,
      discount_rate: c.discountRate || 0,
      direct_reduction: c.directReduction || 0,
      class_id: c.classId || null,
      leave_limit: c.leaveLimit || '不限制',
      leave_limit_count: c.leaveLimitCount || 0,
      gift_hours: c.hasGift === 'yes' ? (c.giftHours || 0) : 0,
      gift_note: c.giftNote || ''
    }))
    try {
      await store.saveStep2({ courses })
    } catch (e) {
      ElMessage.error('保存第二步失败，请重试')
      return
    }
    step3Form.paidAmount = totalPayable.value
    store.currentStep = 3
  }
}

function prevStep() {
  if (store.currentStep > 1) {
    store.currentStep--
    if (store.currentStep === 1 && store.step1Data) {
      step1Form.student_name = store.step1Data.student_name || ''
      step1Form.phone = store.step1Data.phone || ''
      step1Form.gender = store.step1Data.gender || ''
      step1Form.birthDate = store.step1Data.birthDate || ''
      step1Form.introducer = store.step1Data.introducer || ''
      step1Form.note = store.step1Data.note || ''
      selectedStudentId.value = store.step1Data.locked_student_id || null
    }
  }
}

function openTailDialog() {
  tailFormItems.value = selectedCourses.value.map(c => {
    const payableAmount = Number(c.payableAmount) || 0
    let paidAmount = (c.paid !== undefined && c.paid !== null) ? Number(c.paid) : payableAmount
    let tailAmount = payableAmount - paidAmount
    tailAmount = parseFloat(tailAmount.toFixed(2))
    paidAmount = parseFloat(paidAmount.toFixed(2))
    return {
      courseId: c.courseId,
      courseName: c.courseName,
      stageName: c.stageName || '-',
      payableAmount,
      tailAmount,
      paidAmount
    }
  })
  showTailDialog.value = true
}

function confirmTail() {
  tailFormItems.value.forEach(row => {
    const tail = Number(row.tailAmount) || 0
    row.paidAmount = parseFloat((row.payableAmount - tail).toFixed(2))
    if (row.paidAmount < 0) row.paidAmount = 0
  })
  const sumTail = tailFormItems.value.reduce((s, item) => s + (Number(item.tailAmount) || 0), 0)
  if (Math.abs(sumTail - arrears.value) > 0.01) {
    ElMessage.warning(sumTail > arrears.value ? '尾款设置总和大于总尾款' : '尾款设置总和小于总尾款')
    return
  }
  selectedCourses.value.forEach(c => {
    const item = tailFormItems.value.find(t => t.courseId === c.courseId)
    if (item) c.paid = item.paidAmount
  })
  showTailDialog.value = false
}

async function submitEnroll() {
  if (arrears.value > 0) {
    const allSet = selectedCourses.value.every(c => c.paid !== undefined && c.paid !== null)
    if (!allSet) {
      ElMessage.error('请先设置尾款分配并确认')
      return
    }
    const sumPaid = selectedCourses.value.reduce((s, c) => s + (Number(c.paid) || 0), 0)
    if (Math.abs(sumPaid - step3Form.paidAmount) > 0.01) {
      ElMessage.error('各课程实付金额总和不等于收款金额，请重新设置尾款')
      return
    }
  }
  const data = {
    payment_method: step3Form.paymentMethod,
    paid_amount: step3Form.paidAmount,
    performance_teacher_id: step3Form.performanceTeacherId || undefined,
    course_payments: selectedCourses.value.map(c => ({
      course_id: c.courseId,
      stage_id: c.stageId,
      paid: c.paid !== undefined ? c.paid : c.payableAmount
    }))
  }
  submitting.value = true
  try {
    await store.submitStep3(data)
    ElMessage.success('报名成功')
    router.push('/students')
  } catch (e) {
    ElMessage.error('报名失败')
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  await loadPaymentMethods()
  await baseStore.fetchAll()
  teachers.value = baseStore.teachers
  store.loadSessionId()

  const { student_id, course_id, step } = route.query
  if (student_id) {
    try {
      const studentRes = await getStudentDetail(student_id)
      if (studentRes.data) {
        const s = studentRes.data
        step1Form.student_name = s.name
        step1Form.phone = s.phone
        step1Form.gender = s.gender || ''
        step1Form.birthDate = s.birthday || ''
        step1Form.introducer = s.introducer || ''
        step1Form.note = s.note || ''
        selectedStudentId.value = s.id
        await store.saveStep1({ ...step1Form })
      }
    } catch (e) {
      console.error('自动填充学员信息失败', e)
    }

    if (course_id) {
      const course = baseStore.courses.find(c => c.id == course_id)
      if (course) {
        // 加载课阶
        const stages = await loadStagesForCourse(course.id)
        const defaultStage = stages.length > 0 ? stages[0] : null

        await baseStore.fetchClasses()
        let classes = baseStore.classes.filter(cls => cls.course_id === course.id)
        if (defaultStage) {
          const stageClasses = classes.filter(cls => cls.stage_id === defaultStage.id)
          if (stageClasses.length > 0) classes = stageClasses
        }

        selectedCourses.value = [{
          courseId: course.id,
          courseName: course.name,
          stageId: defaultStage?.id || null,
          stageName: defaultStage?.name || '',
          unitPrice: defaultStage?.unit_price || course.unit_price || 0,
          enrollType: '续报',
          purchaseHours: null,
          validityDays: null,
          validityDisplay: '',
          originalPrice: 0,
          discountMode: 'none',
          discountRate: 0,
          directReduction: 0,
          discountRate1: null,
          discountRate2: null,
          discountAmount: 0,
          payableAmount: 0,
          classId: classes.length === 1 ? classes[0].id : null,
          classOptions: classes,
          leaveLimit: '不限制',
          leaveLimitCount: 0,
          hasGift: 'no',
          giftHours: 0,
          giftNote: '',
          paid: undefined,
          duration: defaultStage?.duration || 60,
          deduct_hours: defaultStage?.deduct_hours || 1
        }]
        recalcAll()
        await nextTick()
        courseCards.value = new Array(selectedCourses.value.length)
      }
    }
    if (step === '2') store.currentStep = 2
    await loadEnrolledCourses(student_id)
  }
})
</script>

<style scoped>
.enroll-page {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  padding: 0 0 86px;
}

.step1-panel,
.step2-panel,
.step3-panel {
  background: var(--surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xs);
}

.step1-panel {
  width: min(420px, 100%);
  margin: 40px auto;
  padding: 28px;
}

.step2-panel,
.step3-panel {
  padding: var(--space-4);
}

.student-summary {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  margin: 0 0 var(--space-4);
  padding: 8px 14px;
  color: var(--brand-700);
  font-size: 14px;
  font-weight: 700;
  background: var(--brand-50);
  border: 1px solid rgba(54, 180, 89, 0.18);
  border-radius: var(--radius-pill);
}

.add-course-btn {
  margin-bottom: var(--space-4);
}

.course-card-wrapper {
  margin-bottom: var(--space-4);
}

.total-bar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-2);
  margin-top: var(--space-3);
  padding: 14px 18px;
  color: var(--text-regular);
  font-size: 15px;
  font-weight: 700;
  background: linear-gradient(135deg, var(--brand-50), var(--surface-soft));
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
}

.fixed-table {
  table-layout: fixed;
}

.step3-bottom {
  margin-top: var(--space-5);
}

.amount-panel {
  padding: 18px;
  background:
    radial-gradient(circle at top right, rgba(54, 180, 89, 0.12), transparent 160px),
    var(--surface-soft);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
}

.amount-row {
  display: flex;
  justify-content: space-between;
  gap: var(--space-4);
  padding: 8px 0;
  color: var(--text-regular);
  font-size: 15px;
  border-bottom: 1px dashed var(--border-light);
}

.amount-row:last-child {
  border-bottom: none;
}

.amount-row strong {
  font-size: 19px;
}

.text-danger {
  color: var(--danger);
}

.text-primary {
  color: var(--brand-600);
}

.input-with-suffix {
  width: 90px;
}

.suffix-text {
  color: var(--text-secondary);
  font-size: 14px;
  padding: 0 2px;
}

.arrears-tip {
  margin-left: 12px;
  color: var(--text-secondary);
  font-size: 14px;
}

.arrears-label {
  color: var(--text-secondary);
}

.tail-summary {
  margin-top: var(--space-4);
  text-align: right;
  font-size: 16px;
}

.error-tip {
  margin-left: var(--space-2);
  color: var(--danger);
  font-size: 13px;
}

.tail-setting-btn {
  margin-left: var(--space-3);
}

.tail-amount-input {
  width: 100%;
}

.tail-amount-input :deep(.el-input__wrapper) {
  width: 140px;
}

.step-actions-fixed {
  position: fixed;
  right: var(--space-4);
  bottom: var(--space-4);
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-3);
  padding: 10px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-pill);
  box-shadow: var(--shadow-md);
  backdrop-filter: blur(10px);
}

.step-actions-fixed .el-button + .el-button {
  margin-left: 0;
}

.enroll-page :deep(.steps-wrapper) {
  width: min(832px, 100%);
  max-width: 832px;
  margin: 0 auto var(--space-4);
}

@media (max-width: 768px) {
  .enroll-page {
    padding-bottom: 82px;
  }
  .step1-panel {
    margin: 20px auto;
    padding: 20px;
  }
  .step2-panel,
  .step3-panel {
    padding: var(--space-3);
  }
  .step-actions-fixed {
    left: var(--space-3);
    right: var(--space-3);
    justify-content: center;
    border-radius: var(--radius-lg);
  }
}
</style>
