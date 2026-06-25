<template>
  <div class="teacher-salary-list">
    <div class="filter-bar">
      <el-select v-model="filters.teacher_id" placeholder="选择教师" clearable filterable style="width: 180px" @change="fetchSalaries">
        <el-option v-for="t in teachers" :key="t.id" :label="t.name" :value="t.id" />
      </el-select>
      <el-date-picker v-model="filters.settlement_month" type="month" placeholder="选择结算月份" value-format="YYYY-MM" style="width: 150px" @change="fetchSalaries" />
      <el-button type="primary" @click="openCalculateDialog">开始计薪</el-button>
      <el-button @click="fetchSalaries">查询</el-button>
    </div>

    <el-table :data="salaries" v-loading="loading" border stripe>
      <el-table-column prop="teacher_name" label="教师姓名" width="120" />
      <el-table-column prop="settlement_month" label="结算月份" width="100" />
      <el-table-column label="上课次数" prop="total_classes" width="100" />
      <el-table-column label="出勤人次" prop="total_attendance_count" width="100" />
      <el-table-column label="消耗课时" prop="total_consumed_hours" width="100" />
      <el-table-column label="消耗金额" prop="total_consumed_amount" width="120">
        <template #default="{ row }">¥{{ row.total_consumed_amount.toFixed(2) }}</template>
      </el-table-column>
      <el-table-column label="基本课酬" width="120">
        <template #default="{ row }">¥{{ row.base_amount.toFixed(2) }}</template>
      </el-table-column>
      <el-table-column label="调整金额" width="120">
        <template #default="{ row }">¥{{ row.adjust_amount.toFixed(2) }}</template>
      </el-table-column>
      <el-table-column label="应发薪酬" width="120">
        <template #default="{ row }"><span class="text-danger">¥{{ row.final_amount.toFixed(2) }}</span></template>
      </el-table-column>
      <el-table-column label="发放时间" width="160">
        <template #default="{ row }">{{ row.paid_at || '-' }}</template>
      </el-table-column>
      <el-table-column label="支付方式" width="120">
        <template #default="{ row }">{{ row.payment_method || '-' }}</template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'calculated' ? 'info' : (row.status === 'confirmed' ? 'success' : 'primary')">
            {{ row.status === 'calculated' ? '已计算' : (row.status === 'confirmed' ? '已确认' : '已发放') }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link size="small" @click="viewDetail(row)">详情</el-button>
          <el-button v-if="row.status === 'calculated'" type="success" link size="small" @click="confirmSalary(row)">确认</el-button>
          <el-button v-if="row.status === 'confirmed'" type="warning" link size="small" @click="openPayDialog(row)">发放</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-box" v-if="total > pageSize">
      <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total" layout="prev, pager, next" @current-change="fetchSalaries" />
    </div>

    <!-- 计薪弹窗 -->
    <el-dialog v-model="calculateDialogVisible" title="开始计薪" width="400px">
      <el-form :model="calculateForm" label-width="100px">
        <el-form-item label="教师">
          <el-select v-model="calculateForm.teacher_id" filterable style="width: 100%">
            <el-option v-for="t in teachers" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="结算月份">
          <el-date-picker v-model="calculateForm.settlement_month" type="month" placeholder="选择月份" value-format="YYYY-MM" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="calculateDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="doCalculate" :loading="calculating">开始计薪</el-button>
      </template>
    </el-dialog>

    <!-- 发放弹窗 -->
    <el-dialog v-model="payDialogVisible" title="薪酬发放" width="400px">
      <el-form :model="payForm" label-width="100px">
        <el-form-item label="支付方式">
          <el-select v-model="payForm.payment_method" style="width: 100%">
            <el-option v-for="method in paymentMethodOptions" :key="method" :label="method" :value="method" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="payForm.remark" type="textarea" rows="2" placeholder="选填" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="payDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="doPay" :loading="paying">确认发放</el-button>
      </template>
    </el-dialog>

    <!-- 薪酬详情模态框 -->
    <TeacherSalaryDetailModal v-model:visible="detailVisible" :salary-id="currentSalaryId" @refresh="fetchSalaries" />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getTeacherList } from '@/api/basic'
import { getSalaryList, calculateSalary, confirmSalary as confirmSalaryAPI, paySalary } from '@/api/salary'
import TeacherSalaryDetailModal from './TeacherSalaryDetailModal.vue'
import { getPaymentMethods } from '@/api/settings'

const salaries = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filters = reactive({ teacher_id: null, settlement_month: null })
const teachers = ref([])

const calculateDialogVisible = ref(false)
const calculateForm = reactive({ teacher_id: null, settlement_month: '' })
const calculating = ref(false)

const detailVisible = ref(false)
const currentSalaryId = ref(null)

const payDialogVisible = ref(false)
const currentPaySalary = ref(null)
const payForm = reactive({ payment_method: '', remark: '' })
const paying = ref(false)

const paymentMethodOptions = ref(['银行转账', '现金', '微信支付', '支付宝'])

// 在 onMounted 中确保支付方式从系统设置加载
async function loadPaymentMethods() {
  try {
    const res = await getPaymentMethods()
    if (res.code === 0 && res.data && res.data.length) {
      paymentMethodOptions.value = res.data
      payForm.payment_method = paymentMethodOptions.value[0] || '银行转账'
    }
  } catch (error) {
    console.error('加载支付方式失败', error)
  }
}

async function fetchSalaries() {
  loading.value = true
  const params = {
    page: page.value,
    page_size: pageSize.value,
    teacher_id: filters.teacher_id || undefined,
    settlement_month: filters.settlement_month || undefined
  }
  try {
    const res = await getSalaryList(params)
    salaries.value = res.data?.items || []
    total.value = res.data?.total || 0
  } catch (error) {
    ElMessage.error('加载薪酬列表失败')
  } finally {
    loading.value = false
  }
}

async function loadTeachers() {
  try {
    const res = await getTeacherList()
    teachers.value = res.data || []
  } catch (error) {
    console.error('加载教师列表失败', error)
  }
}

function openCalculateDialog() {
  calculateForm.teacher_id = null
  calculateForm.settlement_month = ''
  calculateDialogVisible.value = true
}

async function doCalculate() {
  if (!calculateForm.teacher_id || !calculateForm.settlement_month) {
    ElMessage.warning('请选择教师和结算月份')
    return
  }
  calculating.value = true
  try {
    await calculateSalary(calculateForm.teacher_id, calculateForm.settlement_month)
    ElMessage.success('计薪成功')
    calculateDialogVisible.value = false
    await fetchSalaries()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '计薪失败')
  } finally {
    calculating.value = false
  }
}

function viewDetail(row) {
  currentSalaryId.value = row.id
  detailVisible.value = true
}

async function confirmSalary(row) {
  try {
    await ElMessageBox.confirm(`确认薪酬 ${row.teacher_name} ${row.settlement_month} 的薪酬？确认后不可再修改。`, '确认', { type: 'info' })
    await confirmSalaryAPI(row.id)
    ElMessage.success('薪酬已确认')
    await fetchSalaries()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('确认失败')
    }
  }
}

// 修改 openPayDialog，每次打开时重新加载支付方式（确保最新）
async function openPayDialog(row) {
  await loadPaymentMethods()  // 确保支付方式最新
  currentPaySalary.value = row
  payForm.payment_method = paymentMethodOptions.value[0] || '银行转账'
  payForm.remark = ''
  payDialogVisible.value = true
}

async function doPay() {
  paying.value = true
  try {
    await paySalary(currentPaySalary.value.id, payForm.payment_method, payForm.remark)
    ElMessage.success('发放成功')
    payDialogVisible.value = false
    await fetchSalaries()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '发放失败')
  } finally {
    paying.value = false
  }
}

defineExpose({ fetchSalaries })

onMounted(() => {
  loadPaymentMethods()
  loadTeachers()
  fetchSalaries()
})
</script>

<style scoped>
.teacher-salary-list {
  padding: 20px;
}
.filter-bar {
  margin-bottom: 16px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.pagination-box {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
.text-danger {
  color: var(--danger);
}
</style>