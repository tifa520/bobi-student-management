<template>
  <div class="activity-detail">
    <!-- 页面头部 -->
    <div class="page-header">
      <el-button link class="back-btn" @click="$router.push('/activities')">
        <el-icon><ArrowLeft /></el-icon> 返回
      </el-button>
      <div class="header-title">
        <span class="activity-name">{{ activity.name }}</span>
        <el-tag :type="statusTag" size="large" class="status-tag">{{ statusLabel }}</el-tag>
      </div>
      <div class="header-actions">
        <el-button v-if="isDraft" type="primary" size="default" @click="handlePublish">发布</el-button>
        <el-button v-if="isActive" type="danger" size="default" @click="handleCancel">取消活动</el-button>
        <el-button v-if="isEndedAndNotArchived" type="info" size="default" @click="handleArchive">归档</el-button>
        <el-button v-if="activity.is_archived" type="info" size="default" @click="handleUnarchive">取消归档</el-button>
        <el-button type="primary" size="default" @click="handleEdit">编辑</el-button>
      </div>
    </div>

    <!-- 标签页 -->
    <el-tabs v-model="activeTab" class="detail-tabs">
      <!-- 基本信息 -->
      <el-tab-pane label="基本信息" name="info">
        <div class="tab-content">
          <el-row :gutter="20">
            <el-col :span="16">
              <el-descriptions :column="2" border>
                <el-descriptions-item label="活动名称">{{ activity.name }}</el-descriptions-item>
                <el-descriptions-item label="活动类型">{{ activity.activity_type || '其他' }}</el-descriptions-item>
                <el-descriptions-item label="收费模式">
                  {{ activity.charge_mode === 'free' ? '免费' : activity.charge_mode === 'paid' ? '收费' : '积分兑换' }}
                </el-descriptions-item>
                <el-descriptions-item label="费用/积分">{{ activity.charge_mode === 'paid' ? '¥'+activity.fee : activity.charge_mode === 'points' ? activity.points_cost+'积分' : '-' }}</el-descriptions-item>
                <el-descriptions-item label="报名时间">{{ activity.registration_start || '未设置' }} ~ {{ activity.registration_end || '未设置' }}</el-descriptions-item>
                <el-descriptions-item label="活动时间">{{ activity.start_date || '未设置' }} ~ {{ activity.end_date || '未设置' }}</el-descriptions-item>
                <el-descriptions-item label="地点">{{ activity.location || '未设置' }}</el-descriptions-item>
                <el-descriptions-item label="人数上限">{{ activity.max_participants || '不限' }}</el-descriptions-item>
                <el-descriptions-item label="介绍" :span="2">{{ activity.content || '无' }}</el-descriptions-item>
              </el-descriptions>
            </el-col>
            <el-col :span="8">
              <div class="info-cards">
                <div class="stat-card">
                  <div class="stat-value">{{ stats.total_reg }}</div>
                  <div class="stat-label">报名人数</div>
                </div>
                <div class="stat-card">
                  <div class="stat-value">{{ stats.confirmed }}</div>
                  <div class="stat-label">确认参加</div>
                </div>
                <div class="stat-card">
                  <div class="stat-value">{{ stats.paid_count }}</div>
                  <div class="stat-label">已缴费</div>
                </div>
                <div class="stat-card">
                  <div class="stat-value">¥{{ stats.total_paid }}</div>
                  <div class="stat-label">实收金额</div>
                </div>
              </div>
              <div class="cover-preview" v-if="activity.banner_image">
                <el-image :src="activity.banner_image" fit="cover" style="width:100%; height:150px; border-radius:8px;" />
              </div>
            </el-col>
          </el-row>
        </div>
      </el-tab-pane>

      <!-- 报名管理 -->
      <el-tab-pane label="报名管理" name="registrations">
        <div class="tab-content">
          <div class="reg-actions">
            <el-button type="primary" size="default" @click="openAddRegistration">添加报名</el-button>
            <el-button size="default" @click="loadRegistrations">刷新</el-button>
            <el-button size="default" type="success" @click="batchPay(true)">批量已缴费</el-button>
            <el-button size="default" type="warning" @click="batchPay(false)">批量未缴费</el-button>
            <el-button size="default" @click="handleExportRegistrations">导出名单</el-button>
            <el-upload
              class="inline-upload"
              :action="`/api/activity/activities/${activityId}/registrations/import`"
              :headers="uploadHeaders"
              :on-success="handleImportSuccess"
              :on-error="handleImportError"
              accept=".xlsx,.xls"
              :show-file-list="false"
            >
              <el-button size="default">导入名单</el-button>
            </el-upload>
          </div>
          <el-table :data="registrations" v-loading="loadingRegs" border stripe @selection-change="handleSelectionChange">
            <el-table-column type="selection" width="45" />
            <el-table-column label="学员" min-width="180">
              <template #default="{ row }">
                <div class="student-info-cell">
                  <AppImage :src="row.student_avatar" :size="32" shape="circle" />
                  <div class="student-detail">
                    <div class="student-name">{{ row.student_name }}</div>
                    <div class="student-phone">{{ row.student_phone }}</div>
                  </div>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="是否参加" width="100">
              <template #default="{ row }">
                <el-select v-model="row.is_attending" size="default" @change="updateRegistrationRow(row)">
                  <el-option label="是" value="是" />
                  <el-option label="否" value="否" />
                  <el-option label="待定" value="待定" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="缴费状态" width="100">
              <template #default="{ row }">
                <el-switch v-model="row.is_paid" @change="updateRegistrationRow(row)" />
              </template>
            </el-table-column>
            <el-table-column label="实收" width="180">
              <template #default="{ row }">
                <div v-if="row.paid_amount > 0 && row.points_used > 0">
                  ¥{{ row.paid_amount }} + {{ row.points_used }}积分
                </div>
                <div v-else-if="row.paid_amount > 0">
                  ¥{{ row.paid_amount }}
                </div>
                <div v-else-if="row.points_used > 0">
                  {{ row.points_used }}积分
                </div>
                <div v-else>
                  -
                </div>
              </template>
            </el-table-column>
            <el-table-column label="退款" width="150">
              <template #default="{ row }">
                <div v-if="row.refund_amount > 0 && row.points_refunded > 0">
                  ¥{{ row.refund_amount }} + {{ row.points_refunded }}积分
                </div>
                <div v-else-if="row.refund_amount > 0">
                  ¥{{ row.refund_amount }}
                </div>
                <div v-else-if="row.points_refunded > 0">
                  {{ row.points_refunded }}积分
                </div>
                <div v-else>
                  -
                </div>
              </template>
            </el-table-column>
            <el-table-column label="支付方式" width="100">
              <template #default="{ row }">{{ row.cash_payment_method || '-' }}</template>
            </el-table-column>
            <el-table-column prop="created_at" label="报名时间" min-width="160" />
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <div class="action-buttons">
                  <el-button type="danger" link size="default" @click="handleCancelRegistration(row)">取消报名</el-button>
                  <el-button v-if="row.is_paid || row.points_used > 0" type="warning" link size="default" @click="openRefund(row)">退费</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <!-- 奖品管理 -->
      <el-tab-pane label="奖品管理" name="prizes">
        <div class="tab-content">
          <div class="prize-header">
            <div class="prize-left">
              <el-button type="primary" size="default" @click="openPrizeEditor">
                <el-icon><Plus /></el-icon> 设置奖项
              </el-button>
              <!-- ★★★ 已移除旧抽奖按钮 ★★★ -->
              <span class="prize-hint">点击“设置奖项”添加活动奖项</span>
            </div>
          </div>
          <!-- 奖项列表 -->
          <el-table :data="prizeList" border stripe v-if="prizeList.length">
            <el-table-column prop="name" label="奖项名称" min-width="150" />
            <el-table-column prop="level" label="等级" width="120" />
            <el-table-column prop="quantity" label="数量" width="80" />
            <el-table-column prop="remaining" label="剩余数量" width="100" />
            <el-table-column prop="cost" label="成本（元）" width="120">
              <template #default="{ row }">¥{{ row.cost || 0 }}</template>
            </el-table-column>
          </el-table>
          <div v-else class="empty-prize-tip">
            <el-empty description="暂未设置奖项，点击「设置奖项」添加" :image-size="80" />
          </div>

          <el-divider>中奖名单</el-divider>
          <div class="winner-actions">
            <el-upload
              class="inline-upload"
              :action="`/api/activity/activities/${activityId}/winners/import`"
              :headers="uploadHeaders"
              :on-success="handleImportWinnersSuccess"
              :on-error="handleImportWinnersError"
              accept=".xlsx,.xls"
              :show-file-list="false"
            >
              <el-button size="default" type="primary">
                <el-icon><Upload /></el-icon> 导入中奖名单
              </el-button>
            </el-upload>
            <el-button size="default" @click="loadWinners">刷新</el-button>
            <el-button size="default" type="success" @click="handleExportWinners">导出中奖名单</el-button>
          </div>
          <el-table :data="winners" v-loading="loadingWinners" border stripe>
            <el-table-column label="学员" min-width="160">
              <template #default="{ row }">
                <div class="student-info-cell">
                  <AppImage :src="row.student_avatar" :size="32" shape="circle" />
                  <span>{{ row.student_name }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="prize_name" label="奖品" />
            <el-table-column prop="prize_level" label="等级" width="100" />
            <el-table-column label="状态" width="120">
              <template #default="{ row }">
                <el-select v-model="row.status" size="default" @change="handleUpdateWinner(row)">
                  <el-option label="待发放" value="pending" />
                  <el-option label="已发放" value="delivered" />
                  <el-option label="已领取" value="claimed" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button type="danger" link size="default" @click="handleDeleteWinner(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <!-- 财务统计 -->
      <el-tab-pane label="财务统计" name="finance">
        <div class="tab-content">
          <!-- ★★★ 修复：缩小字体，不换行 ★★★ -->
          <el-row :gutter="16" class="finance-row">
            <el-col :span="6">
              <div class="finance-card">
                <div class="value">¥{{ finance.total_paid_amount || 0 }}</div>
                <div class="label">实收金额</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="finance-card">
                <div class="value">{{ finance.total_points_used || 0 }}</div>
                <div class="label">消耗积分</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="finance-card">
                <div class="value">¥{{ finance.total_refund_amount || 0 }}</div>
                <div class="label">退款总额</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="finance-card">
                <div class="value">¥{{ finance.total_prize_cost || 0 }}</div>
                <div class="label">奖品成本</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="finance-card">
                <div class="value">¥{{ finance.net_revenue || 0 }}</div>
                <div class="label">净收入</div>
              </div>
            </el-col>
          </el-row>
          <el-table :data="finance.payments || []" border stripe v-loading="loadingFinance">
            <el-table-column label="学员" min-width="160">
              <template #default="{ row }">
                <AppImage :src="row.student_avatar" :size="28" shape="circle" />
                <span style="margin-left:8px">{{ row.student_name }}</span>
              </template>
            </el-table-column>
            <el-table-column label="实付金额" prop="paid_amount" />
            <el-table-column label="使用积分" prop="points_used" />
            <el-table-column label="退款金额" prop="refund_amount" />
            <el-table-column label="退款积分" prop="points_refunded" />
            <el-table-column label="支付方式" prop="cash_payment_method" />
          </el-table>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 添加报名弹窗 -->
    <el-dialog v-model="addRegDialogVisible" title="添加报名" width="650px" :close-on-click-modal="false">
      <el-form :model="newReg" label-width="100px">
        <el-form-item label="学员">
          <StudentPicker v-model="newReg.student_id" placeholder="搜索学员" @student-selected="onStudentSelected" style="width:100%" />
        </el-form-item>
        <div v-if="selectedStudent" class="current-integral">当前积分：{{ studentIntegral }} 分</div>
        <el-form-item label="是否参加">
          <el-select v-model="newReg.is_attending" size="default" style="width:100%">
            <el-option label="是" value="是" />
            <el-option label="否" value="否" />
            <el-option label="待定" value="待定" />
          </el-select>
        </el-form-item>

        <template v-if="activity.charge_mode === 'paid'">
          <el-divider>支付方式</el-divider>
          <div class="payment-methods">
            <div
              v-for="(method, idx) in newReg.payments"
              :key="idx"
              class="payment-method-item"
            >
              <el-select
                v-model="method.method"
                placeholder="支付方式"
                size="default"
                class="method-select"
                @change="onPaymentMethodChange(method, idx)"
              >
                <el-option
                  v-for="opt in paymentMethodOptions"
                  :key="opt"
                  :label="opt"
                  :value="opt"
                />
              </el-select>
              <div class="method-input-wrapper">
                <template v-if="method.type === 'points'">
                  <el-input-number
                    v-model="method.points"
                    :min="0"
                    :step="10"
                    :controls="false"
                    size="default"
                    class="method-input-number"
                    @change="onPaymentValueChange(method, idx)"
                  />
                  <span class="unit">积分 (≈ ¥{{ ((method.points || 0) / exchangeRate).toFixed(2) }})</span>
                </template>
                <template v-else>
                  <el-input-number
                    v-model="method.amount"
                    :min="0"
                    :precision="2"
                    :step="0.01"
                    :controls="false"
                    size="default"
                    class="method-input-number"
                    @change="onPaymentValueChange(method, idx)"
                  />
                  <span class="unit">元</span>
                </template>
              </div>
              <el-button
                type="danger"
                link
                size="default"
                class="method-delete-btn"
                @click="removePaymentMethod(idx)"
                v-if="newReg.payments.length > 1"
              >
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
            <el-button type="primary" link size="default" @click="addPaymentMethod" class="add-payment-btn">
              <el-icon><Plus /></el-icon> 添加支付方式
            </el-button>
            <div v-if="paymentError" class="payment-error">{{ paymentError }}</div>
          </div>
        </template>
      </el-form>
      <template #footer>
        <el-button size="default" @click="addRegDialogVisible = false">取消</el-button>
        <el-button type="primary" size="default" @click="handleSubmitAddRegistration" :disabled="!canSubmit || submitting">
          {{ submitting ? '提交中...' : '确认报名' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 退费弹窗 -->
    <el-dialog v-model="refundDialogVisible" title="退费" width="450px">
      <el-form :model="refundForm" label-width="100px">
        <el-form-item label="退款金额">
          <el-input-number v-model="refundForm.amount" :min="0" :max="refundForm.maxAmount" :precision="2" controls-position="right" size="default" style="width:100%" :controls="false" />
          <span class="unit">元（可退 {{ refundForm.maxAmount }}）</span>
        </el-form-item>
        <el-form-item label="退还积分">
          <el-input-number v-model="refundForm.points" :min="0" :max="refundForm.maxPoints" controls-position="right" size="default" style="width:100%" :controls="false" />
          <span class="unit">积分（可退 {{ refundForm.maxPoints }}）</span>
        </el-form-item>
        <el-form-item label="退款方式">
          <el-select v-model="refundForm.method" size="default">
            <el-option label="原路返回" value="原路返回" />
            <el-option label="微信" value="wechat" />
            <el-option label="支付宝" value="alipay" />
            <el-option label="现金" value="cash" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button size="default" @click="refundDialogVisible = false">取消</el-button>
        <el-button type="primary" size="default" @click="handleConfirmRefund">确认退费</el-button>
      </template>
    </el-dialog>

    <!-- 设置奖项弹窗（含无奖品库） -->
    <el-dialog v-model="prizeEditorVisible" title="设置奖项" width="700px" :close-on-click-modal="false" class="prize-editor-dialog">
      <div class="prize-editor-tip">直接填写奖项信息，每个奖项包含名称、等级、数量、成本（可选），可添加多个奖项。</div>
      <el-table :data="editingPrizes" border stripe max-height="350">
        <el-table-column label="奖项名称" min-width="150">
          <template #default="{ row, $index }">
            <el-input v-model="row.name" placeholder="请输入奖项名称" size="default" />
          </template>
        </el-table-column>
        <el-table-column label="等级" width="120">
          <template #default="{ row, $index }">
            <el-select v-model="row.level" placeholder="选择等级" size="default" style="width:100%">
              <el-option label="一等奖" value="一等奖" />
              <el-option label="二等奖" value="二等奖" />
              <el-option label="三等奖" value="三等奖" />
              <el-option label="参与奖" value="参与奖" />
              <el-option label="其他" value="其他" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="数量" width="100">
          <template #default="{ row, $index }">
            <el-input-number v-model="row.quantity" :min="1" controls-position="right" size="default" style="width:100%" :controls="false" />
          </template>
        </el-table-column>
        <el-table-column label="成本（元）" width="120">
          <template #default="{ row, $index }">
            <el-input-number v-model="row.cost" :min="0" :precision="2" controls-position="right" size="default" style="width:100%" :controls="false" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80">
          <template #default="{ row, $index }">
            <el-button type="danger" link size="default" @click="removePrizeRow($index)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="add-prize-row">
        <el-button type="primary" link size="default" @click="addPrizeRow">
          <el-icon><Plus /></el-icon> 添加奖项
        </el-button>
      </div>
      <template #footer>
        <el-button size="default" @click="prizeEditorVisible = false">取消</el-button>
        <el-button type="primary" size="default" @click="savePrizes" :loading="savingPrizes">保存奖项</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Plus, Upload, Close } from '@element-plus/icons-vue'
import StudentPicker from '@/components/StudentPicker.vue'
import {
  getActivityDetail,
  getActivityRegistrations,
  updateRegistration,
  registerActivity,
  batchPayRegistrations,
  publishActivity,
  cancelActivity,
  archiveActivity,
  unarchiveActivity,
  getWinners,
  updateWinner,
  deleteWinner,
  getActivityStats,
  refundRegistration,
  cancelRegistration,
  exportRegistrations,
  importRegistrations,
  exportWinners
} from '@/api/activity'
import { getStudentScore } from '@/api/score'
import { getPaymentMethods, getExchangeRate } from '@/api/settings'
import request from '@/api/request'

const route = useRoute()
const router = useRouter()
const activityId = computed(() => Number(route.query.id))

// ========== 状态 ==========
const activeTab = ref('info')
const activity = ref({
  id: null,
  name: '',
  status: 'draft',
  charge_mode: 'free',
  fee: 0,
  is_archived: false,
  banner_image: '',
  cover_image: '',
  prizes: [],
  registration_start: '',
  registration_end: '',
  start_date: '',
  end_date: '',
  location: '',
  max_participants: 0,
  content: ''
})
const stats = ref({ total_reg: 0, confirmed: 0, paid_count: 0, total_paid: 0 })
const registrations = ref([])
const loadingRegs = ref(false)
const selectedRegIds = ref([])
const submitting = ref(false)

// 报名相关
const addRegDialogVisible = ref(false)
const newReg = reactive({
  student_id: null,
  is_attending: '是',
  payments: [
    { type: 'cash', method: '微信支付', amount: 0, points: 0 }
  ]
})
const selectedStudent = ref(null)
const studentIntegral = ref(0)

// 支付方式配置
const paymentMethodOptions = ref([])
const exchangeRate = ref(10)
const paymentError = ref('')

// 退费相关
const refundDialogVisible = ref(false)
const refundForm = reactive({
  amount: 0,
  points: 0,
  method: '原路返回',
  maxAmount: 0,
  maxPoints: 0
})
const currentRefundReg = ref(null)

// 奖项相关
const prizeEditorVisible = ref(false)
const savingPrizes = ref(false)
const editingPrizes = ref([])
const prizeList = ref([])

// 中奖名单
const winners = ref([])
const loadingWinners = ref(false)

// 财务
const loadingFinance = ref(false)
const finance = ref({
  total_paid_amount: 0,
  total_points_used: 0,
  total_refund_amount: 0,
  total_prize_cost: 0,
  net_revenue: 0,
  payments: []
})

const uploadHeaders = { Authorization: `Bearer ${localStorage.getItem('access_token')}` }

// ========== 计算属性 ==========
const isDraft = computed(() => activity.value.status === 'draft')
const isActive = computed(() => activity.value.status !== 'cancelled' && activity.value.status !== 'archived')
const isEndedAndNotArchived = computed(() => activity.value.status === 'ended' && !activity.value.is_archived)

const statusTag = computed(() => {
  const map = { draft: 'info', registering: 'success', upcoming: 'warning', ongoing: 'primary', ended: 'info', cancelled: 'danger', archived: 'info' }
  return map[activity.value.status] || 'info'
})
const statusLabel = computed(() => {
  const map = { draft: '草稿', registering: '报名中', upcoming: '待开始', ongoing: '进行中', ended: '已结束', cancelled: '已取消', archived: '已归档' }
  return map[activity.value.status] || activity.value.status
})

// 支付总额计算
const canSubmit = computed(() => {
  if (activity.value.charge_mode === 'free') return true
  const total = calcTotalPaid()
  return Math.abs(total - activity.value.fee) < 0.01 && total > 0
})

function calcTotalPaid() {
  let totalCash = 0
  let totalPoints = 0
  for (const m of newReg.payments) {
    if (m.type === 'cash') totalCash += m.amount || 0
    else if (m.type === 'points') totalPoints += m.points || 0
  }
  return totalCash + totalPoints / exchangeRate.value
}

function calcRemainingAmount() {
  const totalFee = activity.value.fee || 0
  let paidCash = 0
  let paidPoints = 0
  for (const m of newReg.payments) {
    if (m.type === 'cash') paidCash += m.amount || 0
    else if (m.type === 'points') paidPoints += m.points || 0
  }
  return totalFee - paidCash - paidPoints / exchangeRate.value
}

// ========== 支付方式管理 ==========
function validatePayments() {
  const total = calcTotalPaid()
  const fee = activity.value.fee || 0
  if (Math.abs(total - fee) < 0.01) {
    paymentError.value = ''
  } else if (total > fee) {
    paymentError.value = `支付总额 ${total.toFixed(2)} 超过应付 ${fee.toFixed(2)}`
  } else {
    paymentError.value = `支付总额 ${total.toFixed(2)} 小于应付 ${fee.toFixed(2)}`
  }
}

function autoDistributeRemaining() {
  const remaining = calcRemainingAmount()
  if (Math.abs(remaining) < 0.01) {
    for (const m of newReg.payments) {
      if (m.type === 'cash' && (m.amount === 0 || m.amount === undefined)) {
        m.amount = 0
      } else if (m.type === 'points' && (m.points === 0 || m.points === undefined)) {
        m.points = 0
      }
    }
    return
  }
  // 优先填充空现金方式
  let filled = false
  for (const m of newReg.payments) {
    if (m.type === 'cash' && (m.amount === 0 || m.amount === undefined)) {
      m.amount = Math.max(0, remaining)
      filled = true
      break
    }
  }
  if (!filled) {
    // 填充到最后一个现金方式
    for (let i = newReg.payments.length - 1; i >= 0; i--) {
      const m = newReg.payments[i]
      if (m.type === 'cash') {
        m.amount = Math.max(0, m.amount + remaining)
        filled = true
        break
      }
    }
  }
  if (!filled) {
    // 只有积分方式，折算为积分
    for (let i = newReg.payments.length - 1; i >= 0; i--) {
      const m = newReg.payments[i]
      if (m.type === 'points') {
        const points = Math.round(remaining * exchangeRate.value)
        m.points = Math.max(0, m.points + points)
        filled = true
        break
      }
    }
  }
  for (const m of newReg.payments) {
    if (m.type === 'cash' && m.amount < 0) m.amount = 0
    if (m.type === 'points' && m.points < 0) m.points = 0
  }
}

function onPaymentValueChange(method, idx) {
  paymentError.value = ''
  autoDistributeRemaining()
  validatePayments()
}

function addPaymentMethod() {
  const remaining = calcRemainingAmount()
  const defaultMethod = paymentMethodOptions.value.find(opt => opt !== '积分') || '现金'
  const newMethod = {
    type: 'cash',
    method: defaultMethod,
    amount: 0,
    points: 0
  }
  if (remaining > 0) {
    newMethod.amount = remaining
  }
  newReg.payments.push(newMethod)
  autoDistributeRemaining()
  validatePayments()
}

function removePaymentMethod(idx) {
  if (newReg.payments.length <= 1) return
  newReg.payments.splice(idx, 1)
  autoDistributeRemaining()
  validatePayments()
}

function onPaymentMethodChange(method, idx) {
  if (method.method === '积分') {
    method.type = 'points'
    method.amount = 0
    const remaining = calcRemainingAmount()
    if (remaining > 0) {
      method.points = Math.round(remaining * exchangeRate.value)
    } else {
      method.points = 0
    }
  } else {
    method.type = 'cash'
    method.points = 0
    const remaining = calcRemainingAmount()
    if (remaining > 0) {
      method.amount = remaining
    } else {
      method.amount = 0
    }
  }
  autoDistributeRemaining()
  validatePayments()
}

// ========== 数据加载 ==========
async function loadActivity() {
  if (!activityId.value) return
  try {
    const res = await getActivityDetail(activityId.value)
    activity.value = res.data.activity
    stats.value = res.data.statistics
    prizeList.value = activity.value.prizes || []
  } catch (e) { console.error(e) }
}

async function loadRegistrations() {
  if (!activityId.value) return
  loadingRegs.value = true
  try {
    const res = await getActivityRegistrations(activityId.value)
    // ★★★ 过滤 status != 'cancelled' ★★★
    registrations.value = (res.data || []).filter(r => r.status !== 'cancelled')
  } finally {
    loadingRegs.value = false
  }
}

async function loadWinners() {
  if (!activityId.value) return
  loadingWinners.value = true
  try {
    const res = await getWinners(activityId.value)
    winners.value = res.data || []
  } finally { loadingWinners.value = false }
}

async function loadFinance() {
  if (!activityId.value) return
  loadingFinance.value = true
  try {
    const res = await getActivityStats(activityId.value)
    finance.value = res.data
  } finally { loadingFinance.value = false }
}

async function loadPaymentOptions() {
  try {
    const res = await getPaymentMethods()
    if (res.code === 0) paymentMethodOptions.value = res.data
  } catch (e) { console.error(e) }
  try {
    const res = await getExchangeRate()
    if (res.code === 0) exchangeRate.value = res.data
  } catch (e) { console.error(e) }
}

function refreshAll() {
  loadActivity()
  loadRegistrations()
  loadWinners()
  loadFinance()
}

// ========== 生命周期 ==========
onMounted(() => {
  if (activityId.value) {
    refreshAll()
    loadPaymentOptions()
  }
})

// ========== 报名管理 ==========
function handleSelectionChange(selection) {
  selectedRegIds.value = selection.map(s => s.id)
}

async function updateRegistrationRow(row) {
  try {
    await updateRegistration(row.id, {
      is_attending: row.is_attending,
      is_paid: row.is_paid,
      paid_amount: row.paid_amount,
      points_used: row.points_used
    })
    ElMessage.success('更新成功')
  } catch (e) {
    ElMessage.error('更新失败')
    loadRegistrations()
  }
}

function openAddRegistration() {
  newReg.student_id = null
  newReg.is_attending = '是'
  newReg.payments = [
    { type: 'cash', method: paymentMethodOptions.value[0] || '微信支付', amount: 0, points: 0 }
  ]
  selectedStudent.value = null
  studentIntegral.value = 0
  paymentError.value = ''
  addRegDialogVisible.value = true
}

async function onStudentSelected(student) {
  selectedStudent.value = student
  newReg.student_id = student?.id || null
  if (student && activity.value.charge_mode === 'paid') {
    try {
      const res = await getStudentScore(student.id)
      studentIntegral.value = res.data?.total_integral || 0
    } catch (e) {
      studentIntegral.value = 0
    }
  }
  validatePayments()
}

async function handleSubmitAddRegistration() {
  if (!newReg.student_id) {
    ElMessage.warning('请选择学员')
    return
  }
  if (activity.value.charge_mode === 'paid') {
    const total = calcTotalPaid()
    if (Math.abs(total - activity.value.fee) > 0.01) {
      ElMessage.warning(paymentError.value || '支付总额与应付金额不匹配')
      return
    }
  }
  submitting.value = true
  try {
    const payload = {
      student_id: newReg.student_id,
      is_attending: newReg.is_attending,
      payments: newReg.payments.map(p => ({
        type: p.type,
        amount: p.type === 'cash' ? (p.amount || 0) : 0,
        points: p.type === 'points' ? (p.points || 0) : 0,
        method: p.method || '现金'
      }))
    }
    await registerActivity(activityId.value, payload)
    ElMessage.success('报名成功')
    addRegDialogVisible.value = false
    refreshAll()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '报名失败')
  } finally {
    submitting.value = false
  }
}

async function batchPay(isPaid) {
  if (!selectedRegIds.value.length) {
    ElMessage.warning('请先勾选报名记录')
    return
  }
  try {
    await batchPayRegistrations(activityId.value, selectedRegIds.value, isPaid)
    ElMessage.success('批量更新成功')
    loadRegistrations()
  } catch (e) {
    ElMessage.error('更新失败')
  }
}

async function handleCancelRegistration(row) {
  try {
    await ElMessageBox.confirm(`确认取消学员 ${row.student_name} 的报名？`, '提示', { type: 'warning' })
    await cancelRegistration(row.id, '管理员取消')
    ElMessage.success('已取消报名')
    refreshAll()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('操作失败')
  }
}

function openRefund(row) {
  currentRefundReg.value = row
  refundForm.maxAmount = row.paid_amount || 0
  refundForm.maxPoints = row.points_used - (row.points_refunded || 0)
  refundForm.amount = 0
  refundForm.points = 0
  refundForm.method = '原路返回'
  refundDialogVisible.value = true
}

async function handleConfirmRefund() {
  if (refundForm.amount <= 0 && refundForm.points <= 0) {
    ElMessage.warning('请至少输入一项退款金额或积分')
    return
  }
  try {
    await refundRegistration(currentRefundReg.value.id, {
      refund_amount: refundForm.amount,
      refund_points: refundForm.points,
      payment_method: refundForm.method
    })
    ElMessage.success('退费成功')
    refundDialogVisible.value = false
    refreshAll()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '退费失败')
  }
}

async function handleExportRegistrations() {
  try {
    const res = await exportRegistrations(activityId.value)
    const blob = new Blob([res], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `报名名单_${activity.value.name}_${new Date().toISOString().slice(0,10)}.xlsx`
    link.click()
    window.URL.revokeObjectURL(url)
  } catch (e) {
    ElMessage.error('导出失败')
  }
}

function handleImportSuccess(res) {
  if (res.code === 0) {
    ElMessage.success(`导入成功，共 ${res.data?.imported || 0} 条`)
    loadRegistrations()
  } else {
    ElMessage.error(res.message || '导入失败')
  }
}
function handleImportError() {
  ElMessage.error('导入失败')
}

// ========== 奖项管理 ==========
function openPrizeEditor() {
  editingPrizes.value = prizeList.value.map(p => ({ ...p }))
  if (editingPrizes.value.length === 0) {
    editingPrizes.value.push({ name: '', level: '其他', quantity: 1, cost: 0 })
  }
  prizeEditorVisible.value = true
}

function addPrizeRow() {
  editingPrizes.value.push({ name: '', level: '其他', quantity: 1, cost: 0 })
}

function removePrizeRow(index) {
  if (editingPrizes.value.length <= 1) {
    ElMessage.warning('至少保留一个奖项')
    return
  }
  editingPrizes.value.splice(index, 1)
}

async function savePrizes() {
  const emptyName = editingPrizes.value.some(p => !p.name.trim())
  if (emptyName) {
    ElMessage.warning('请填写所有奖项名称')
    return
  }
  const invalidQty = editingPrizes.value.some(p => p.quantity < 1)
  if (invalidQty) {
    ElMessage.warning('奖项数量必须大于0')
    return
  }
  savingPrizes.value = true
  try {
    const data = editingPrizes.value.map(p => ({
      name: p.name.trim(),
      level: p.level || '其他',
      quantity: p.quantity,
      cost: p.cost || 0,
      remaining: p.quantity
    }))
    await request.put(`/activity/activities/${activityId.value}/prizes`, data)
    ElMessage.success('奖项保存成功')
    prizeEditorVisible.value = false
    await loadActivity()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    savingPrizes.value = false
  }
}

// ========== 中奖名单 ==========
async function handleUpdateWinner(row) {
  try {
    await updateWinner(row.id, { status: row.status })
    ElMessage.success('更新成功')
  } catch (e) {
    ElMessage.error('更新失败')
  }
}

async function handleDeleteWinner(row) {
  try {
    await ElMessageBox.confirm('确认删除此中奖记录？', '提示')
    await deleteWinner(row.id)
    ElMessage.success('已删除')
    loadWinners()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

function handleImportWinnersSuccess(res) {
  if (res.code === 0) {
    ElMessage.success(`导入成功，共 ${res.data?.imported || 0} 条`)
    loadWinners()
  } else {
    ElMessage.error(res.message || '导入失败')
  }
}
function handleImportWinnersError() {
  ElMessage.error('导入失败')
}

async function handleExportWinners() {
  try {
    const res = await exportWinners(activityId.value)
    const blob = new Blob([res], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `中奖名单_${activity.value.name}_${new Date().toISOString().slice(0,10)}.xlsx`
    link.click()
    window.URL.revokeObjectURL(url)
  } catch (e) {
    ElMessage.error('导出失败')
  }
}

// ========== 活动操作 ==========
async function handlePublish() {
  try {
    await publishActivity(activityId.value)
    ElMessage.success('已发布')
    refreshAll()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '发布失败')
  }
}

async function handleCancel() {
  try {
    await ElMessageBox.confirm('确认取消活动？所有已缴费报名将自动退费', '警告', { type: 'warning' })
    await cancelActivity(activityId.value)
    ElMessage.success('已取消')
    refreshAll()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('操作失败')
  }
}

async function handleArchive() {
  try {
    await archiveActivity(activityId.value)
    ElMessage.success('已归档')
    refreshAll()
  } catch (e) {
    ElMessage.error('归档失败')
  }
}

async function handleUnarchive() {
  try {
    await unarchiveActivity(activityId.value)
    ElMessage.success('已取消归档')
    refreshAll()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

function handleEdit() {
  router.push(`/activities/edit?id=${activityId.value}`)
}
</script>

<style scoped>
.activity-detail {
  padding: 20px;
  background: var(--app-bg);
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--surface);
  padding: 16px 24px;
  border-radius: 12px;
  margin-bottom: 20px;
}
.back-btn { font-size: 14px; }
.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
}
.activity-name { font-size: 18px; font-weight: 600; }
.status-tag { font-size: 14px; }

.detail-tabs {
  background: var(--surface);
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.detail-tabs :deep(.el-tabs__header) { margin-bottom: 20px; }
.detail-tabs :deep(.el-tabs__item) { font-size: 15px; padding: 0 20px; }
.tab-content { padding: 8px 0; }

/* 信息卡片 */
.info-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 16px;
}
.stat-card {
  background: var(--surface-soft);
  border-radius: 12px;
  padding: 12px;
  text-align: center;
}
.stat-value { font-size: 24px; font-weight: 700; color: var(--brand-500); }
.stat-label { font-size: 12px; color: var(--text-secondary); }

.cover-preview {
  border-radius: 8px;
  overflow: hidden;
  margin-top: 12px;
}

/* 报名管理 */
.reg-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.student-info-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}
.student-detail {
  display: flex;
  flex-direction: column;
}
.student-name { font-weight: 500; }
.student-phone { font-size: 12px; color: var(--text-secondary); }

.action-buttons {
  display: flex;
  gap: 6px;
  flex-wrap: nowrap;
}

.current-integral {
  margin-bottom: 16px;
  padding: 8px 12px;
  background: var(--surface-green);
  border-radius: 6px;
  color: var(--brand-500);
}

.payment-hint {
  padding: 8px 12px;
  background: rgba(77, 124, 168, 0.10);
  border-radius: 6px;
  margin-bottom: 12px;
  color: var(--info);
}
.unit {
  color: var(--text-secondary);
  font-size: 13px;
  margin-left: 8px;
}

/* ★★★ 财务统计修复 ★★★ */
.finance-row {
  display: flex;
  flex-wrap: nowrap;
  margin-bottom: 16px;
}
.finance-card {
  background: var(--surface-soft);
  border-radius: 12px;
  padding: 12px 8px;
  text-align: center;
  white-space: nowrap;
}
.finance-card .value {
  font-size: 18px;
  font-weight: 700;
  color: var(--brand-500);
}
.finance-card .label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.inline-upload {
  display: inline-block;
  margin-left: 8px;
}

/* 奖品管理 */
.prize-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
  padding: 12px 16px;
  background: var(--surface-soft);
  border-radius: 8px;
}
.prize-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.prize-hint {
  font-size: 12px;
  color: var(--text-placeholder);
}
.empty-prize-tip { padding: 20px; }

.winner-actions {
  margin-bottom: 12px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.prize-editor-dialog :deep(.el-dialog__body) { padding-top: 16px; }
.prize-editor-tip {
  margin-bottom: 16px;
  padding: 8px 12px;
  background: var(--surface-green);
  border-radius: 6px;
  color: var(--brand-500);
  font-size: 14px;
}
.add-prize-row {
  margin-top: 12px;
  text-align: center;
}

/* 统一控件大小 */
:deep(.el-input__wrapper) {
  border-radius: 8px;
  height: 40px;
}
:deep(.el-select .el-input__wrapper) {
  height: 40px;
}
:deep(.el-input-number .el-input__wrapper) {
  height: 40px;
}
:deep(.el-button) {
  border-radius: 20px;
  height: 40px;
  padding: 0 20px;
}
:deep(.el-textarea .el-textarea__inner) {
  border-radius: 8px;
  border: 1px solid var(--border-color);
}
:deep(.el-textarea .el-textarea__inner:focus) {
  border-color: var(--brand-500);
}

/* ★★★ 隐藏 input number 的增减按钮 ★★★ */
:deep(.el-input-number .el-input-number__decrease),
:deep(.el-input-number .el-input-number__increase) {
  display: none;
}
:deep(.el-input-number .el-input__wrapper) {
  padding-left: 12px;
  padding-right: 12px;
}
/* 支付方式布局 - 同一行不换行 */
.payment-methods {
  margin: 12px 0;
}
.payment-method-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: nowrap; /* 强制不换行 */
}
.method-select {
  width: 140px;
  flex-shrink: 0;
}
.method-input-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0; /* 允许收缩 */
}
.method-input-number {
  width: 140px;
  flex-shrink: 0;
}
.unit {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
}
.method-delete-btn {
  flex-shrink: 0;
}
.add-payment-btn {
  margin-top: 6px;
}
.payment-error {
  color: var(--danger);
  font-size: 12px;
  margin-top: 8px;
}
</style>