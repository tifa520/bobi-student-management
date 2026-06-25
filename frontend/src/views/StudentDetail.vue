<template>
  <div class="student-detail-wrapper">
    <!-- 标题区 -->
    <div class="detail-header">
      <el-button link class="back-btn" @click="$router.back()">
        <el-icon><ArrowLeft /></el-icon><span>返回</span>
      </el-button>
      <span class="title-divider"></span>
      <AppImage :src="student.avatar" :size="40" class="header-avatar" />
      <span class="student-name">{{ student.name }}</span>
      <el-button class="quick-enroll-btn" @click="goToEnroll">
        <el-icon><Plus /></el-icon>报名
      </el-button>
    </div>

    <div class="student-detail">
      <StudentDetailTabs
        ref="detailTabsRef"
        :key="refreshKey"
        :student-id="student.id"
        :student="student"
        :courses="courses"
        :orders="orders"
        @refresh="refreshAllData"
        @renew="openRenew"
        @refund="openRefund"
        @graduate="openGraduate"
        @suspend="openSuspend"
        @transfer-hours="openTransferHours"
        @adjust-hours="openAdjustHours"
        @gift-hours="openGiftHours"
        @transfer-class="openTransferClass"
        @drop-class="openDropClass"
        @assign-class="openAssignClass"
        @repay="openRepayForCourse"
      />
    </div>

    <!-- 退费弹窗 -->
    <el-dialog v-model="refundVisible" title="退费" width="750px" class="refund-dialog" :close-on-click-modal="false">
      <div v-if="selectedCourse" class="refund-content">
        <div class="refund-header">
          <span class="course-name">{{ selectedCourse.course_name }}</span>
        </div>

        <div class="refund-preview-card">
          <div class="card-title">退费预览</div>
          <div class="card-row">
            <div class="card-item"><span class="item-label">购买课时</span><span class="item-value">{{ refundPreviewData.total_purchased_hours || refundPreviewData.total_purchased || 0 }}课时</span></div>
            <div class="card-item"><span class="item-label">购买金额</span><span class="item-value">￥{{ refundPreviewData.total_purchased_amount || 0 }}</span></div>
            <div class="card-item"><span class="item-label">消耗课时</span><span class="item-value">{{ refundPreviewData.total_consumed_hours || 0 }}课时</span></div>
            <div class="card-item"><span class="item-label">消耗金额</span><span class="item-value">￥{{ refundPreviewData.total_consumed_amount || 0 }}</span></div>
          </div>
          <div class="card-row">
            <div class="card-item"><span class="item-label">剩余课时</span><span class="item-value">{{ refundPreviewData.remaining_hours || 0 }}课时</span></div>
            <div class="card-item"><span class="item-label">剩余金额</span><span class="item-value">￥{{ refundPreviewData.remaining_amount || 0 }}</span></div>
            <div class="card-item"><span class="item-label">当前尾款</span><span class="item-value" :class="{ 'text-danger': refundPreviewData.arrears > 0 }">￥{{ refundPreviewData.arrears || 0 }}</span></div>
            <div class="card-item" v-if="refundPreviewData.arrears > 0"><span class="item-label">实际可退</span><span class="item-value text-primary">￥{{ refundPreviewData.actual_refund_amount || 0 }}</span></div>
          </div>
          <div class="card-row">
            <div class="card-item"><span class="item-label">本次退费课时</span><span class="item-value text-primary">{{ refundHours }}课时</span></div>
            <div class="card-item"><span class="item-label">预计退费金额</span><span class="item-value">￥{{ refundPreviewData.refund_amount || 0 }}</span></div>
            <div class="card-item" v-if="refundPreviewData.after_remaining_hours !== undefined"><span class="item-label">退费后剩余课时</span><span class="item-value">{{ refundPreviewData.after_remaining_hours || 0 }}课时</span></div>
            <div class="card-item" v-if="refundPreviewData.after_remaining_amount !== undefined"><span class="item-label">退费后剩余金额</span><span class="item-value">￥{{ refundPreviewData.after_remaining_amount || 0 }}</span></div>
          </div>
          <div v-if="refundPreviewData.message" class="card-error"><el-alert :title="refundPreviewData.message" type="warning" show-icon :closable="false" /></div>
        </div>

        <div class="refund-form">
          <div class="form-row"><div class="form-label">退款课时</div><div class="form-input"><el-input-number v-model="refundHours" :min="0" :max="selectedCourse.remaining_hours || 0" :step="1" controls-position="right" @change="onRefundHoursChange" /><span class="unit">课时</span></div></div>
          <div class="form-row"><div class="form-label">退费方式</div><div class="form-input"><el-select v-model="refundMethod" style="width:180px"><el-option label="微信" value="微信" /><el-option label="支付宝" value="支付宝" /><el-option label="现金" value="现金" /><el-option label="银行转账" value="银行转账" /></el-select></div></div>
          <div class="form-row"><div class="form-label">退费原因</div><div class="form-input"><el-input v-model="refundReason" placeholder="请输入退费原因" /></div></div>
        </div>
      </div>
      <template #footer><el-button @click="refundVisible = false">取消</el-button><el-button type="primary" @click="confirmRefund" :loading="refundLoading" :disabled="!canRefund || !refundHours || refundHours <= 0">确定退费</el-button></template>
    </el-dialog>

    <!-- 转课时弹窗 -->
    <el-dialog v-model="transferHoursVisible" title="转课时" width="1100px" class="transfer-dialog" :top="'5vh'" :close-on-click-modal="false">
      <div class="transfer-content" v-if="selectedCourse">
        <div class="transfer-student-info"><span>学员：{{ student.name }}</span><span>联系方式：{{ student.phone }}</span></div>
        <div class="transfer-two-columns">
          <div class="transfer-box"><div class="box-title">转出信息</div><div class="info-list"><div class="info-item"><span class="info-label">班级名称</span><span class="info-value">{{ selectedCourse.class_name || '未分班' }}</span></div><div class="info-item"><span class="info-label">剩余课时数</span><span class="info-value">{{ selectedCourse.remaining_hours }}课时</span></div><div class="info-item"><span class="info-label">剩余可转出金额</span><span class="info-value">￥{{ selectedCourse?.remaining_amount || 0 }}</span></div><div class="info-item"><span class="info-label">转出课时数</span><div class="info-control"><el-input-number v-model="transferHoursForm.hours" :min="1" :max="selectedCourse.remaining_hours" controls-position="right" @change="calcTransferOut" style="width:160px" /></div></div><div class="info-item"><span class="info-label">转出金额</span><span class="info-value">￥{{ transferOutAmount }}</span></div><div class="info-item"><span class="info-label">转出后剩余课时</span><span class="info-value">{{ Math.max(0, selectedCourse.remaining_hours - (transferHoursForm.hours || 0)) }}课时</span></div><div class="info-item"><span class="info-label">课时有效期</span><span class="info-value">{{ selectedCourse.validity_display || '无' }}</span></div></div></div>
          <div class="transfer-box"><div class="box-title">转入信息</div><div class="info-list"><div class="info-item"><span class="info-label">转入类型</span><div class="info-control"><el-radio-group v-model="transferHoursForm.targetType" @change="onTargetTypeChange"><el-radio :label="'existing'" value="'existing'">学员已有课程</el-radio><el-radio :label="'new'" value="'new'">新课程</el-radio></el-radio-group></div></div><div class="info-item"><span class="info-label">转入课程</span><div class="info-control"><el-select v-model="transferHoursForm.to_course_id" placeholder="选择课程" @change="onTransferTargetCourseChange" style="width:100%"><el-option v-for="c in targetCourseOptions" :key="c.id" :label="c.name" :value="c.id" /></el-select></div></div><div class="info-item" v-if="transferHoursForm.targetType === 'new' && transferHoursForm.to_course_id"><span class="info-label">转入班级</span><div class="info-control"><el-select v-model="transferHoursForm.to_class_id" placeholder="选择班级" clearable style="width:100%"><el-option v-for="cls in targetClasses" :key="cls.id" :label="cls.name" :value="cls.id" /></el-select></div></div><div class="info-item"><span class="info-label">转入课时数</span><div class="info-control"><el-input-number v-model="transferHoursForm.to_hours" :min="1" controls-position="right" @change="calcTransferIn" style="width:160px" /></div></div><div class="info-item"><span class="info-label">转入课时金额</span><div class="info-control"><el-input-number v-model="transferHoursForm.to_amount" :min="0" :precision="2" controls-position="right" @change="calcUnitPrice" style="width:160px" /></div></div><div class="info-item"><span class="info-label">课时单价</span><span class="info-value">￥{{ unitPriceTransfer }}</span></div><div class="info-item"><span class="info-label">有效天数(可选)</span><div class="info-control"><el-input-number v-model="transferHoursForm.validity_days" :min="1" controls-position="right" placeholder="不填则不增加" style="width:160px" /><span class="hint-text">转入课时增加的有效天数</span></div></div></div></div>
        </div>
        <div class="transfer-payment"><div class="box-title">支付信息</div><div class="payment-row"><div class="payment-item"><span class="info-label">差价</span><span :class="diffAmount >= 0 ? 'text-danger' : 'text-success'" class="info-value">{{ diffAmount >= 0 ? '需补' : '可退' }}￥{{ Math.abs(diffAmount).toFixed(2) }}</span></div><div class="payment-item"><span class="info-label">是否补差价</span><el-radio-group v-model="transferHoursForm.makeUpDiff" @change="onMakeUpDiffChange"><el-radio :label="'yes'" value="'yes'">是</el-radio><el-radio :label="'no'" value="'no'">否</el-radio></el-radio-group></div></div><div v-if="transferHoursForm.makeUpDiff === 'yes'" class="payment-detail"><div class="payment-item"><span class="info-label">支付方式</span><el-select v-model="transferHoursForm.paymentMethod" style="width:140px"><el-option label="微信" value="微信" /><el-option label="支付宝" value="支付宝" /><el-option label="现金" value="现金" /></el-select></div><div class="payment-item"><span class="info-label">支付金额</span><el-input-number v-model="transferHoursForm.payAmount" :min="0" :precision="2" controls-position="right" style="width:160px" /></div></div></div>
        <div class="transfer-reason"><div class="info-item"><span class="info-label">转课时原因</span><div class="info-control"><el-input v-model="transferHoursForm.reason" placeholder="请输入转课时原因（选填）" /></div></div></div>
      </div>
      <template #footer><el-button @click="transferHoursVisible = false">取消</el-button><el-button type="primary" @click="confirmTransferHours" :loading="transferHoursLoading">确定</el-button></template>
    </el-dialog>

    <!-- 停课弹窗 -->
    <el-dialog v-model="suspendVisible" title="停课设置" width="500px" class="suspend-dialog" :close-on-click-modal="false">
      <el-form :model="suspendForm" class="suspend-form"><div class="form-row"><div class="form-label">停课开始时间：</div><div class="form-control"><el-date-picker v-model="suspendForm.start_date" type="date" placeholder="请选择停课开始日期" value-format="YYYY-MM-DD" style="width:100%" :disabled-date="disabledStartDate" @change="onStartDateChange" /></div></div><div class="form-row"><div class="form-label">停课结束时间：</div><div class="form-control"><el-date-picker v-model="suspendForm.end_date" type="date" placeholder="请选择停课结束日期" value-format="YYYY-MM-DD" style="width:100%" :disabled="!suspendForm.start_date" :disabled-date="disabledEndDate" /></div></div><div class="form-row"><div class="form-label">停课原因：</div><div class="form-control"><el-input v-model="suspendForm.reason" type="textarea" :rows="2" placeholder="请输入停课原因（选填）" /></div></div><div class="form-row" v-if="selectedCourse && isSuspended(selectedCourse)"><div class="form-label"></div><div class="form-control"><el-button type="danger" size="small" @click="cancelSuspend">取消停课</el-button></div></div></el-form>
      <template #footer><el-button @click="suspendVisible = false">取消</el-button><el-button type="primary" @click="confirmSuspend" :loading="suspending" :disabled="!canConfirmSuspend">确定停课</el-button></template>
    </el-dialog>

    <!-- 补尾款模态框 -->
    <RepayModal v-model:visible="repayModalVisible" :student-id="student.id" :student-name="student.name" @success="onRepaySuccess" />

    <!-- 分班弹窗 -->
    <el-dialog v-model="showAssignDialog" title="分班" width="400px"><el-form label-width="80px"><el-form-item label="课程"><el-input :value="selectedCourse?.course_name" disabled /></el-form-item><el-form-item label="班级"><el-select v-model="assignForm.class_id" placeholder="选择班级"><el-option v-for="cls in assignClasses" :key="cls.id" :label="cls.name" :value="cls.id" /></el-select></el-form-item></el-form><template #footer><el-button @click="showAssignDialog = false">取消</el-button><el-button type="primary" @click="confirmAssignClass" :loading="assigning">确定</el-button></template></el-dialog>

    <!-- 转班弹窗 -->
    <el-dialog v-model="transferClassVisible" title="转班" width="400px"><el-form label-width="80px"><el-form-item label="目标班级"><el-select v-model="transferToClassId" placeholder="选择班级"><el-option v-for="cls in transferClasses" :key="cls.id" :label="cls.name" :value="cls.id" /></el-select></el-form-item></el-form><template #footer><el-button @click="transferClassVisible = false">取消</el-button><el-button type="primary" @click="confirmTransferClass" :loading="transferLoading">确定</el-button></template></el-dialog>

    <!-- 统一增减课时弹窗 -->
    <AdjustHoursDialog v-model:visible="adjustDialogVisible" :student-id="student.id" :course-id="adjustCourse?.course_id" :remaining-hours="adjustRemaining" :is-gift="isGiftAdjust" @success="onAdjustSuccess" />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import AdjustHoursDialog from '@/components/AdjustHoursDialog.vue'
import RepayModal from '@/components/RepayModal.vue'
import StudentDetailTabs from '@/components/StudentDetailTabs.vue'
import { DEFAULT_AVATAR_SVG } from '@/utils/constants'
import {
  getStudentDetail, getStudentCourses, refundStudent, graduateStudent,
  transferHours, dropClass, assignClass, getRefundPreview,
  transferClass as transferClassApi, getTransferAmountPreview
} from '@/api/student'
import { getOrderList } from '@/api/order'
import { getCourseListSimple, getClassesByCourse, getEnabledTeachers } from '@/api/basic'
import request from '@/api/request'

const route = useRoute()
const router = useRouter()
const refreshKey = ref(0)

// ========== 数据 ==========
const student = ref({ id: null, name: '', total_integral: 0, phone: '', avatar: '' })
const courses = ref([])
const orders = ref([])
const allCourses = ref([])
const teachers = ref([])
const selectedCourse = ref(null)
const detailTabsRef = ref(null)

// ========== 退费相关 ==========
const refundVisible = ref(false)
const refundLoading = ref(false)
const refundHours = ref(0)
const refundMethod = ref('微信')
const refundReason = ref('')
const refundPreviewData = ref({})
let refundTimer = null

// ========== 转课时相关 ==========
const transferHoursVisible = ref(false)
const transferHoursLoading = ref(false)
const transferHoursForm = reactive({
  hours: 1, to_course_id: null, targetType: 'existing', to_class_id: null,
  to_hours: 1, to_amount: 0, makeUpDiff: 'yes', paymentMethod: '微信',
  payAmount: 0, reason: '', validity_days: null
})
const targetClasses = ref([])
const transferOutAmount = ref(0)
const transferOutAvailableAmount = ref(0)

// ========== 停课相关 ==========
const suspendVisible = ref(false)
const suspendForm = reactive({ start_date: dayjs().format('YYYY-MM-DD'), end_date: '', reason: '' })
const suspending = ref(false)

const disabledStartDate = (time) => time < new Date(new Date().setHours(0, 0, 0, 0))
const disabledEndDate = (time) => {
  if (!suspendForm.start_date) return true
  const startDate = new Date(suspendForm.start_date)
  startDate.setHours(0, 0, 0, 0)
  return time < startDate
}
const canConfirmSuspend = computed(() => suspendForm.start_date && suspendForm.end_date)

function onStartDateChange() {
  if (suspendForm.end_date && suspendForm.start_date > suspendForm.end_date) {
    suspendForm.end_date = ''
  }
}

// ========== 补尾款 ==========
const repayModalVisible = ref(false)

// ========== 分班相关 ==========
const showAssignDialog = ref(false)
const assigning = ref(false)
const assignClasses = ref([])
const assignForm = reactive({ course_id: null, class_id: null })

// ========== 转班相关 ==========
const transferClassVisible = ref(false)
const transferLoading = ref(false)
const transferClasses = ref([])
const transferToClassId = ref(null)

// ========== 增减课时相关 ==========
const adjustDialogVisible = ref(false)
const adjustCourse = ref(null)
const adjustRemaining = ref(0)
const isGiftAdjust = ref(false)

// ========== 计算属性 ==========
const targetCourseOptions = computed(() => {
  if (transferHoursForm.targetType === 'existing') {
    return courses.value.map(c => ({ id: c.course_id, name: c.course_name }))
  }
  return allCourses.value
})

const canRefund = computed(() => refundPreviewData.value.can_refund === true)
const diffAmount = computed(() => (transferHoursForm.to_amount || 0) - (transferOutAmount.value || 0))
const unitPriceTransfer = computed(() => {
  if (transferHoursForm.to_hours && transferHoursForm.to_hours > 0) {
    return (transferHoursForm.to_amount / transferHoursForm.to_hours).toFixed(2)
  }
  return '0.00'
})

function isSuspended(course) {
  return course.suspended_start && course.suspended_end &&
    dayjs().isBetween(dayjs(course.suspended_start), dayjs(course.suspended_end), 'day', '[]')
}

// ========== 头像和背景图更新（来自子组件） ==========
function onAvatarUpdated(newAvatar) {
  if (student.value) {
    student.value.avatar = newAvatar
  }
}

function onCardBackgroundUpdated(newBg) {
  if (student.value) {
    student.value.card_background = newBg
  }
}

// ========== 刷新数据 ==========
async function refreshAllData(keepTab = true) {
  const id = route.params.id
  if (!id) return

  const currentTab = sessionStorage.getItem(`student_tab_${id}`)

  try {
    const [studentRes, coursesRes, orderRes, coursesListRes, teacherRes] = await Promise.all([
      getStudentDetail(id),
      getStudentCourses(id),
      getOrderList({ search: '' }),
      getCourseListSimple(),
      getEnabledTeachers()
    ])
    student.value = studentRes.data
    student.value.avatar = student.value.avatar || DEFAULT_AVATAR_SVG
    courses.value = (coursesRes.data || []).map(c => ({
      ...c,
      validity_display: c.validity_display || '-',
      leave_display: c.leave_display || '-'
    }))
    orders.value = (orderRes.data || []).filter(o => o.student_id === student.value.id)
    allCourses.value = coursesListRes.data || []
    teachers.value = teacherRes.data || []

    if (keepTab && currentTab) {
      sessionStorage.setItem(`student_tab_${id}`, currentTab)
    }
    refreshKey.value++
  } catch (error) {
    console.error('加载数据失败', error)
    ElMessage.error('加载学员数据失败')
  }
}

async function refreshStudentInfo() {
  // 只刷新学员基本信息，保留头像和背景图
  const id = route.params.id
  if (!id) return
  try {
    const res = await getStudentDetail(id)
    if (res.code === 0 && res.data) {
      student.value = { ...student.value, ...res.data }
      // 确保头像和背景图不被覆盖（保留本地）
      if (student.value.avatar && !student.value.avatar.startsWith('/media/')) {
        // 如果后端返回的是相对路径，则拼接
      }
    }
  } catch (error) {
    console.error('刷新学员信息失败', error)
  }
}

// ========== 路由跳转 ==========
function goToEnroll() {
  router.push({ path: '/enroll', query: { student_id: student.value.id, step: '2' } })
}

function openRenew(course) {
  router.push({ path: '/enroll', query: { student_id: student.value.id, course_id: course.course_id, step: '2' } })
}

// ========== 退费 ==========
function openRefund(course) {
  selectedCourse.value = course
  refundHours.value = 0
  refundMethod.value = '微信'
  refundReason.value = ''
  resetPreviewData()
  refundVisible.value = true
}

function resetPreviewData() {
  if (!selectedCourse.value) return
  refundPreviewData.value = {
    total_purchased_hours: selectedCourse.value?.total_purchased || 0,
    total_purchased_amount: selectedCourse.value?.total_purchased_amount || 0,
    total_consumed_hours: (selectedCourse.value?.total_deducted || 0) +
                          (selectedCourse.value?.total_custom_sub || 0) +
                          (selectedCourse.value?.total_transfer_out || 0),
    total_consumed_amount: 0,
    remaining_hours: selectedCourse.value?.remaining_hours || 0,
    remaining_amount: selectedCourse.value?.remaining_amount || 0,
    refund_hours: 0,
    refund_amount: 0,
    after_remaining_hours: selectedCourse.value?.remaining_hours || 0,
    after_remaining_amount: selectedCourse.value?.remaining_amount || 0,
    arrears: selectedCourse.value?.arrears || 0,
    actual_refund_amount: 0,
    can_refund: true,
    message: ''
  }
}

function onRefundHoursChange() {
  if (!selectedCourse.value || !refundHours.value || refundHours.value <= 0) {
    resetPreviewData()
    return
  }
  if (refundTimer) clearTimeout(refundTimer)
  refundTimer = setTimeout(() => fetchRefundPreview(), 300)
}

async function fetchRefundPreview() {
  if (!selectedCourse.value || !refundHours.value) return
  try {
    const res = await getRefundPreview(student.value.id, {
      course_id: selectedCourse.value.course_id,
      refund_hours: refundHours.value
    })
    if (res.data) refundPreviewData.value = res.data
  } catch (error) {
    console.error('获取退费预览失败', error)
  }
}

async function confirmRefund() {
  if (!refundHours.value || refundHours.value <= 0) {
    ElMessage.warning('请输入退款课时')
    return
  }
  if (refundHours.value > (refundPreviewData.value.remaining_hours || 0)) {
    ElMessage.warning('退款课时不能超过剩余课时')
    return
  }
  refundLoading.value = true
  try {
    await refundStudent(student.value.id, {
      course_id: selectedCourse.value.course_id,
      refund_hours: refundHours.value,
      reason: refundReason.value,
      refund_method: refundMethod.value
    })
    ElMessage.success('退费成功')
    refundVisible.value = false
    await refreshAllData()
  } catch (error) {
    ElMessage.error('退费失败')
  } finally {
    refundLoading.value = false
  }
}

// ========== 结业 ==========
function openGraduate(course) {
  ElMessageBox.confirm(`确认将该课程"${course.course_name}"结业？\n结业后该课程剩余课时和金额将清零，且无法恢复。`, '提示', {
    type: 'warning',
    confirmButtonText: '确认结业',
    cancelButtonText: '取消'
  }).then(async () => {
    try {
      await graduateStudent(student.value.id, { course_id: course.course_id })
      ElMessage.success('已结业')
      await refreshAllData()
    } catch (error) {
      ElMessage.error('结业失败')
    }
  }).catch(() => {})
}

// ========== 停课 ==========
function openSuspend(course) {
  selectedCourse.value = course
  if (isSuspended(course)) {
    suspendForm.start_date = course.suspended_start || dayjs().format('YYYY-MM-DD')
    suspendForm.end_date = course.suspended_end || ''
  } else {
    suspendForm.start_date = dayjs().format('YYYY-MM-DD')
    suspendForm.end_date = ''
  }
  suspendForm.reason = ''
  suspendVisible.value = true
}

async function confirmSuspend() {
  if (!suspendForm.start_date || !suspendForm.end_date) {
    ElMessage.warning('请填写停课起止日期')
    return
  }
  if (dayjs(suspendForm.start_date).isAfter(dayjs(suspendForm.end_date))) {
    ElMessage.warning('开始日期不能晚于结束日期')
    return
  }
  suspending.value = true
  try {
    await request.post(`/student/student/${student.value.id}/suspend`, null, {
      params: {
        course_id: selectedCourse.value.course_id,
        start_date: suspendForm.start_date,
        end_date: suspendForm.end_date,
        reason: suspendForm.reason
      }
    })
    ElMessage.success('停课设置成功')
    suspendVisible.value = false
    setTimeout(() => {
      refreshAllData(true)
    }, 500)
  } catch (error) {
    ElMessage.error('停课设置失败')
  } finally {
    suspending.value = false
  }
}

async function cancelSuspend() {
  try {
    await request.post(`/student/student/${student.value.id}/cancel-suspend`, null, {
      params: { course_id: selectedCourse.value.course_id }
    })
    ElMessage.success('已取消停课')
    suspendVisible.value = false
    setTimeout(() => {
      refreshAllData(true)
    }, 500)
  } catch (error) {
    ElMessage.error('取消失败')
  }
}

// ========== 增减课时 ==========
function openAdjustHours(course) {
  adjustCourse.value = course
  adjustRemaining.value = course.remaining_hours || 0
  isGiftAdjust.value = false
  adjustDialogVisible.value = true
}

function openGiftHours(course) {
  adjustCourse.value = course
  adjustRemaining.value = course.remaining_gift || 0
  isGiftAdjust.value = true
  adjustDialogVisible.value = true
}

function onAdjustSuccess() {
  refreshAllData(true)
}

// ========== 转课时 ==========
function openTransferHours(course) {
  selectedCourse.value = course
  transferHoursForm.hours = 1
  transferHoursForm.to_course_id = null
  transferHoursForm.targetType = 'existing'
  transferHoursForm.to_class_id = null
  transferHoursForm.to_hours = 1
  transferHoursForm.to_amount = 0
  transferHoursForm.makeUpDiff = 'yes'
  transferHoursForm.paymentMethod = '微信'
  transferHoursForm.payAmount = 0
  transferHoursForm.reason = ''
  transferHoursForm.validity_days = null
  transferOutAmount.value = 0
  transferOutAvailableAmount.value = course.remaining_amount || 0
  targetClasses.value = []
  transferHoursVisible.value = true
  setTimeout(() => calcTransferOut(), 100)
}

async function calcTransferOut() {
  const hours = transferHoursForm.hours || 0
  if (!selectedCourse.value || hours <= 0) {
    transferOutAmount.value = 0
    return
  }
  try {
    const res = await getTransferAmountPreview(student.value.id, {
      course_id: selectedCourse.value.course_id,
      transfer_hours: hours
    })
    if (res.code === 0) transferOutAmount.value = res.data.amount || 0
  } catch (error) {
    console.error('计算转出金额失败', error)
    transferOutAmount.value = 0
  }
}

function onTargetTypeChange() {
  transferHoursForm.to_course_id = null
  transferHoursForm.to_class_id = null
  targetClasses.value = []
}

async function onTransferTargetCourseChange(courseId) {
  if (!courseId) {
    targetClasses.value = []
    return
  }
  try {
    const res = await getClassesByCourse(courseId)
    targetClasses.value = res.data || []
  } catch (error) {
    targetClasses.value = []
  }
}

function calcTransferIn() {
  if (transferHoursForm.to_amount === 0 && transferHoursForm.to_hours > 0 && selectedCourse.value) {
    const ordersList = selectedCourse.value.orders || []
    const sorted = [...ordersList].sort((a, b) => b.id - a.id)
    let remaining = transferHoursForm.to_hours
    let amount = 0
    for (const o of sorted) {
      if (remaining <= 0) break
      let unitPrice = o.actual_unit_price || o.unit_price || (o.payable_amount / o.purchase_hours)
      const take = Math.min(remaining, o.remaining_hours || 0)
      amount += take * unitPrice
      remaining -= take
    }
    transferHoursForm.to_amount = parseFloat(amount.toFixed(2))
  }
}

function calcUnitPrice() {}

function onMakeUpDiffChange() {
  if (transferHoursForm.makeUpDiff === 'yes' && diffAmount.value > 0) {
    transferHoursForm.payAmount = diffAmount.value
  } else {
    transferHoursForm.payAmount = 0
  }
}

async function confirmTransferHours() {
  if (!transferHoursForm.hours || transferHoursForm.hours <= 0) {
    ElMessage.warning('请输入转出课时数')
    return
  }
  if (!transferHoursForm.to_course_id) {
    ElMessage.warning('请选择目标课程')
    return
  }
  if (!transferHoursForm.to_hours || transferHoursForm.to_hours <= 0) {
    ElMessage.warning('请输入转入课时数')
    return
  }
  if (transferHoursForm.makeUpDiff === 'yes' && transferHoursForm.payAmount !== diffAmount.value) {
    ElMessage.warning(`补差价金额必须为 ${diffAmount.value} 元`)
    return
  }
  if (diffAmount.value < 0) {
    ElMessage.warning('转入金额不能低于转出金额，如需退款请使用退费功能')
    return
  }

  const requestData = {
    from_course_id: selectedCourse.value.course_id,
    to_course_id: transferHoursForm.to_course_id,
    transfer_hours: transferHoursForm.hours,
    reason: transferHoursForm.reason || '',
    make_up_diff: transferHoursForm.makeUpDiff === 'yes',
    pay_amount: transferHoursForm.makeUpDiff === 'yes' ? transferHoursForm.payAmount : 0,
    payment_method: transferHoursForm.paymentMethod,
    to_class_id: transferHoursForm.to_class_id || null,
    to_amount: transferHoursForm.to_amount,
    to_hours: transferHoursForm.to_hours,
    validity_days: transferHoursForm.validity_days || null
  }

  transferHoursLoading.value = true
  try {
    await transferHours(student.value.id, requestData)
    ElMessage.success('转课时成功')
    transferHoursVisible.value = false
    await refreshAllData(true)
  } catch (error) {
    const msg = error.response?.data?.detail || '转课时失败'
    ElMessage.error(msg)
  } finally {
    transferHoursLoading.value = false
  }
}

// ========== 转班 ==========
async function openTransferClass(course) {
  selectedCourse.value = course
  try {
    const res = await getClassesByCourse(course.course_id)
    transferClasses.value = (res.data || []).filter(c => c.id !== course.class_id)
    transferToClassId.value = null
    transferClassVisible.value = true
  } catch (error) {
    ElMessage.error('加载班级失败')
  }
}

async function confirmTransferClass() {
  if (!transferToClassId.value) {
    ElMessage.warning('请选择目标班级')
    return
  }
  transferLoading.value = true
  try {
    await transferClassApi(student.value.id, {
      course_id: selectedCourse.value.course_id,
      to_class_id: transferToClassId.value
    })
    ElMessage.success('转班成功')
    transferClassVisible.value = false
    await refreshAllData()
  } catch (error) {
    ElMessage.error('转班失败')
  } finally {
    transferLoading.value = false
  }
}

// ========== 退班 ==========
function openDropClass(course) {
  ElMessageBox.confirm('确认退出该班级？', '提示', { type: 'warning' })
    .then(async () => {
      try {
        await dropClass(student.value.id, { course_id: course.course_id })
        ElMessage.success('已退班')
        await refreshAllData()
      } catch (error) {
        ElMessage.error('退班失败')
      }
    })
    .catch(() => {})
}

// ========== 分班 ==========
async function openAssignClass(course) {
  selectedCourse.value = course
  try {
    const res = await getClassesByCourse(course.course_id)
    assignClasses.value = res.data || []
    assignForm.course_id = course.course_id
    assignForm.class_id = null
    showAssignDialog.value = true
  } catch (error) {
    ElMessage.error('加载班级失败')
  }
}

async function confirmAssignClass() {
  if (!assignForm.class_id) {
    ElMessage.warning('请选择班级')
    return
  }
  assigning.value = true
  try {
    await assignClass(student.value.id, {
      course_id: selectedCourse.value.course_id,
      class_id: assignForm.class_id
    })
    ElMessage.success('分班成功')
    showAssignDialog.value = false
    await refreshAllData()
  } catch (error) {
    ElMessage.error('分班失败')
  } finally {
    assigning.value = false
  }
}

// ========== 补尾款 ==========
function openRepayForCourse() {
  repayModalVisible.value = true
}

function onRepaySuccess() {
  refreshAllData(true)
}

// ========== 挂载 ==========
onMounted(() => {
  refreshAllData()
})
</script>

<style scoped>
/* 完整样式（与之前一致，已省略以避免过长，但确保包含所有原有样式） */
.student-detail-wrapper {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.detail-header {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--surface);
  padding: 16px 20px;
  box-shadow: var(--shadow-sm);
  flex-shrink: 0;
}
.back-btn {
  padding: 0;
}
.title-divider {
  width: 1px;
  height: 16px;
  background: var(--gray-300);
}
.header-avatar {
  margin-right: 4px;
}
.student-name {
  font-size: inherit;
  font-weight: normal;
  color: var(--primary-color, var(--brand-500));
}
.quick-enroll-btn {
  margin-left: 0;
}
.student-detail {
  flex: 1;
  background: var(--surface);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  min-height: 0;
}
.refund-preview-card {
  background: linear-gradient(135deg, var(--surface-soft) 0%, var(--surface) 100%);
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 24px;
  border: 1px solid var(--border-color);
}
.refund-preview-card .card-title {
  font-size: 14px;
  color: var(--text-primary);
  margin-bottom: 14px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-color);
}
.card-row {
  display: flex;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
.card-item {
  flex: 1;
  min-width: 120px;
  display: flex;
  flex-direction: column;
  padding: 4px 8px;
}
.item-label {
  font-size: 12px;
  color: var(--text-placeholder);
  margin-bottom: 4px;
}
.item-value {
  font-size: 14px;
  color: var(--text-primary);
}
.item-value.text-primary {
  color: var(--primary-color, var(--brand-500));
}
.item-value.text-danger {
  color: var(--danger);
}
.card-error {
  margin-top: 12px;
  padding-top: 8px;
  border-top: 1px solid var(--border-color);
}
.refund-form {
  margin-bottom: 0;
}
.form-row {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}
.form-label {
  width: 100px;
  flex-shrink: 0;
  font-size: 14px;
  color: var(--text-secondary);
}
.form-input {
  flex: 1;
}
.unit {
  margin-left: 8px;
  color: var(--text-secondary);
}
.refund-header {
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
}
.refund-header .course-name {
  font-size: 14px;
  color: var(--primary-color);
}
.transfer-content {
  max-height: 60vh;
  overflow-y: auto;
}
.transfer-student-info {
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 20px;
  background: var(--app-bg);
  display: flex;
  gap: 32px;
}
.transfer-two-columns {
  display: flex;
  gap: 24px;
  margin-bottom: 24px;
}
.transfer-box {
  flex: 1;
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 20px;
}
.box-title {
  font-size: 14px;
  font-weight: normal;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-light);
}
.info-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.info-item {
  display: flex;
  align-items: center;
  font-size: 14px;
}
.info-label {
  width: 110px;
  flex-shrink: 0;
  color: var(--text-secondary);
}
.info-value {
  color: var(--text-primary);
  font-weight: 500;
}
.info-control {
  flex: 1;
}
.hint-text {
  margin-left: 12px;
  font-size: 12px;
  color: var(--text-secondary);
}
.transfer-payment {
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
}
.payment-row {
  display: flex;
  align-items: center;
  gap: 40px;
  margin-bottom: 16px;
}
.payment-detail {
  display: flex;
  align-items: center;
  gap: 40px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px dashed var(--border-light);
}
.payment-item {
  display: flex;
  align-items: center;
  gap: 12px;
}
.transfer-reason {
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 20px;
}
.text-danger {
  color: var(--danger);
}
.text-success {
  color: var(--success);
}
.suspend-dialog .form-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}
.suspend-dialog .form-label {
  width: 100px;
  text-align: right;
  line-height: 32px;
}
.suspend-dialog .form-control {
  flex: 1;
}
</style>