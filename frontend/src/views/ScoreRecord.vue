<template>
  <div class="score-record-container">
    <div class="filter-bar">
      <el-input v-model="filters.studentName" placeholder="学员姓名" clearable style="width:180px" @clear="fetchRecords" @keyup.enter="fetchRecords" />
      <el-select v-model="filters.recordType" placeholder="类型" clearable style="width:120px" @change="fetchRecords">
        <el-option label="全部" value="" />
        <el-option label="奖励" value="reward" />
        <el-option label="扣分" value="penalty" />
      </el-select>
      <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD" style="width:400px" @change="fetchRecords" />
      <el-button type="primary" @click="fetchRecords">查询</el-button>
    </div>

    <el-table :data="records" v-loading="loading" border stripe style="width:100%">
      <el-table-column label="学员" min-width="160">
        <template #default="{ row }">
          <div class="student-info-cell">
            <AppImage :src="row.student_avatar" :size="28" shape="circle" />
            <div class="student-name">{{ row.student_name }}</div>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="类型" min-width="100">
        <template #default="{ row }">
          <el-tag :type="row.change_amount > 0 ? 'success' : 'danger'" size="small">
            {{ row.change_amount > 0 ? '奖励' : '扣分' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="change_amount" label="积分变动" min-width="110">
        <template #default="{ row }">
          <span :class="row.change_amount > 0 ? 'text-success' : 'text-danger'">
            {{ row.change_amount > 0 ? '+' : '' }}{{ row.change_amount }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="reason" label="变动原因" min-width="200" />
      <el-table-column prop="remark" label="备注" min-width="150" />
      <el-table-column prop="created_at" label="操作时间" min-width="160" />
    </el-table>

    <div class="pagination-box" v-if="total > pageSize">
      <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total" layout="total, prev, pager, next" size="small" @current-change="fetchRecords" />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getIntegralRecords } from '@/api/score'
import { DEFAULT_AVATAR_SVG } from '@/utils/constants'

const loading = ref(false)
const records = ref([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filters = reactive({ studentName: '', recordType: '' })
const dateRange = ref(null)

async function fetchRecords() {
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value,
      student_name: filters.studentName || undefined,
      record_type: filters.recordType || undefined,
      start_date: dateRange.value?.[0] || undefined,
      end_date: dateRange.value?.[1] || undefined
    }
    const res = await getIntegralRecords(params)
    records.value = res.data?.items || []
    total.value = res.data?.total || 0
  } catch (e) { console.error(e) } finally { loading.value = false }
}

onMounted(() => { fetchRecords() })
</script>

<style scoped>
.score-record-container { margin: 16px; }
.filter-bar { display: flex; gap: 12px; align-items: center; margin-bottom: 16px; flex-wrap: wrap; }
.pagination-box { margin-top: 16px; display: flex; justify-content: flex-end; }
.text-success { color: var(--success); }
.text-danger { color: var(--danger); }
.student-info-cell { display: flex; align-items: center; gap: 10px; }
.student-name { font-weight: 500; }
.student-phone { font-size: 12px; color: var(--text-secondary); }
</style>