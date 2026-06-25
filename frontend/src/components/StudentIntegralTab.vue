<template>
  <div class="integral-content">
    <el-row :gutter="20" class="integral-top">
      <el-col :span="16">
        <div class="chart-wrapper">
          <div ref="chartRef" style="width:100%;height:300px;"></div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="operation-panel">
          <div class="current-integral-display">
            <div class="integral-value">{{ currentIntegral }}</div>
            <div class="integral-label">当前可用积分</div>
          </div>
          <el-divider />
          <el-form :model="integralForm" label-width="80px">
            <el-form-item label="变动值">
              <el-input-number v-model="integralForm.changeAmount" :min="-1000" :max="1000" controls-position="right" style="width:100%" />
            </el-form-item>
            <el-form-item label="原因">
              <el-input v-model="integralForm.reason" placeholder="请输入原因" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="submitIntegralChange" :loading="submitting" style="width:100%">
                提交
              </el-button>
            </el-form-item>
          </el-form>
          <div class="history-summary">
            <span>累计获得：<strong class="text-success">{{ gainedIntegral }}</strong></span>
            <span style="margin-left:20px;">累计消耗：<strong class="text-danger">{{ consumedIntegral }}</strong></span>
          </div>
        </div>
      </el-col>
    </el-row>

    <h3 style="margin-top:20px;">积分变动记录</h3>
    <el-table :data="integralRecords" border stripe v-loading="loading" max-height="300">
      <el-table-column prop="created_at" label="时间" width="160" />
      <el-table-column prop="change_amount" label="变动值">
        <template #default="{ row }">
          <span :class="row.change_amount > 0 ? 'text-success' : 'text-danger'">
            {{ row.change_amount > 0 ? '+' : '' }}{{ row.change_amount }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="reason" label="原因" min-width="150" />
      <el-table-column prop="remark" label="备注" min-width="150" />
    </el-table>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { getStudentScore, submitScore } from '@/api/score'
import dayjs from 'dayjs'

const props = defineProps({
  studentId: {
    type: Number,
    required: true
  }
})
const emit = defineEmits(['update:success'])

const loading = ref(false)
const submitting = ref(false)
const integralRecords = ref([])
const totalIntegral = ref(0)

const integralForm = reactive({
  changeAmount: 0,
  reason: ''
})

const chartRef = ref(null)
let chartInstance = null

const currentIntegral = computed(() => totalIntegral.value)
const gainedIntegral = computed(() => {
  return integralRecords.value.reduce((sum, r) => sum + (r.change_amount > 0 ? r.change_amount : 0), 0)
})
const consumedIntegral = computed(() => {
  return Math.abs(integralRecords.value.reduce((sum, r) => sum + (r.change_amount < 0 ? r.change_amount : 0), 0))
})

async function fetchIntegralData() {
  if (!props.studentId) return
  loading.value = true
  try {
    const res = await getStudentScore(props.studentId)
    totalIntegral.value = res.data?.total_integral || 0
    integralRecords.value = res.data?.history || []
    renderChart()
  } catch (error) {
    console.error('加载积分数据失败', error)
  } finally {
    loading.value = false
  }
}

function renderChart() {
  if (!chartRef.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }
  // 按时间升序排列，取最近6个月
  const sorted = [...integralRecords.value].sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
  const months = []
  const data = []
  const now = dayjs()
  // 取最近6个月
  for (let i = 5; i >= 0; i--) {
    const month = now.subtract(i, 'month')
    const label = month.format('YYYY-MM')
    months.push(label)
    // 统计该月变动总和
    const monthRecords = sorted.filter(r => dayjs(r.created_at).format('YYYY-MM') === label)
    const total = monthRecords.reduce((sum, r) => sum + r.change_amount, 0)
    data.push(total)
  }

  const option = {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: months, boundaryGap: false },
    yAxis: { type: 'value', name: '积分' },
    series: [{
      name: '积分变动',
      type: 'line',
      smooth: true,
      data: data,
      areaStyle: { color: 'rgba(54, 180, 89, 0.2)' },
      lineStyle: { color: '#36b459' },
      itemStyle: { color: '#36b459' }
    }]
  }
  chartInstance.setOption(option)
  chartInstance.resize()
}

async function submitIntegralChange() {
  if (integralForm.changeAmount === 0) {
    ElMessage.warning('请输入变动值')
    return
  }
  if (!integralForm.reason) {
    ElMessage.warning('请输入原因')
    return
  }
  submitting.value = true
  try {
    await submitScore([{
      student_id: props.studentId,
      change_amount: integralForm.changeAmount,
      reason: integralForm.reason
    }])
    ElMessage.success('积分更新成功')
    integralForm.changeAmount = 0
    integralForm.reason = ''
    await fetchIntegralData()
    emit('update:success')
  } catch (error) {
    ElMessage.error('更新失败')
  } finally {
    submitting.value = false
  }
}

watch(() => props.studentId, () => {
  fetchIntegralData()
}, { immediate: true })

// 窗口变化时自适应图表
onMounted(() => {
  window.addEventListener('resize', () => {
    if (chartInstance) chartInstance.resize()
  })
})
</script>

<style scoped>
.integral-content {
  padding: 10px 0;
}
.integral-top {
  margin-bottom: 20px;
}
.chart-wrapper {
  background: #fafafa;
  border-radius: 8px;
  padding: 12px;
  border: 1px solid #e4e7ed;
}
.operation-panel {
  background: #fafafa;
  border-radius: 8px;
  padding: 20px;
  border: 1px solid #e4e7ed;
  height: 100%;
}
.current-integral-display {
  text-align: center;
  margin-bottom: 12px;
}
.current-integral-display .integral-value {
  font-size: 36px;
  font-weight: bold;
  color: #36b459;
}
.current-integral-display .integral-label {
  font-size: 14px;
  color: #909399;
}
.history-summary {
  margin-top: 16px;
  font-size: 14px;
  text-align: center;
}
.text-success { color: #67c23a; }
.text-danger { color: #f56c6c; }
</style>