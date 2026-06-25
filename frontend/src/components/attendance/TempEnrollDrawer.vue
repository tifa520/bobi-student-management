<!-- frontend/src/components/attendance/TempEnrollDrawer.vue -->
<template>
  <el-drawer v-model="visible" title="临时插班" direction="rtl" size="600px" @close="handleClose">
    <div class="temp-enroll-drawer">
      <div class="filter-row">
        <el-select v-model="tempClassId" placeholder="所在班级" clearable filterable style="width:200px" @change="fetchTempStudents">
          <el-option v-for="cls in allClasses" :key="cls.id" :label="cls.name" :value="cls.id" />
        </el-select>
        <el-input v-model="tempSearch" placeholder="学员姓名/手机号" clearable style="width:200px" @input="fetchTempStudents" />
      </div>
      <el-table :data="tempStudents" v-loading="tempLoading" border stripe>
        <el-table-column label="学员信息" min-width="180">
          <template #default="{ row }">
            <div class="student-info-cell">
              <AppImage :src="row.avatar" :size="28" shape="circle" />
              <div class="student-name-detail">
                <div class="student-name">{{ row.name }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="class_name" label="所在班级" min-width="120" />
        <el-table-column label="剩余课时" min-width="100">
          <template #default="{ row }">{{ row.remaining_hours }}课时</template>
        </el-table-column>
        <el-table-column label="课时有效期至" min-width="120">
          <template #default="{ row }">{{ row.validity_date || '-' }}</template>
        </el-table-column>
        <el-table-column label="剩余赠送课时" min-width="100">
          <template #default="{ row }">{{ row.remaining_gift || 0 }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleTempEnroll(row)">临时插班</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-box" v-if="tempTotal > 10">
        <el-pagination v-model:current-page="tempPage" :page-size="10" :total="tempTotal" layout="prev, pager, next" @current-change="fetchTempStudents" />
      </div>
    </div>
  </el-drawer>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getClassList } from '@/api/class'
import { getStudentList } from '@/api/student'
import { temporaryEnroll } from '@/api/attendance'
import { DEFAULT_AVATAR_SVG } from '@/utils/constants'

const props = defineProps({
  visible: Boolean,
  scheduleId: Number
})
const emit = defineEmits(['update:visible', 'enroll-success'])

const visible = ref(props.visible)
const allClasses = ref([])
const tempClassId = ref(null)
const tempSearch = ref('')
const tempStudents = ref([])
const tempLoading = ref(false)
const tempPage = ref(1)
const tempTotal = ref(0)

watch(() => props.visible, (val) => {
  visible.value = val
  if (val) {
    fetchAllClasses()
    fetchTempStudents()
  }
})
watch(visible, (val) => emit('update:visible', val))

async function fetchAllClasses() {
  try {
    const res = await getClassList({ page: 1, page_size: 100 })
    allClasses.value = res.data?.items || res.data || []
  } catch (e) {
    console.error(e)
  }
}

async function fetchTempStudents() {
  tempLoading.value = true
  try {
    const params = {
      page: tempPage.value,
      page_size: 10,
      class_id: tempClassId.value || undefined,
      search: tempSearch.value || undefined
    }
    const res = await getStudentList(params)
    tempStudents.value = res.data?.items || []
    tempTotal.value = res.data?.total || 0
  } catch (e) {
    tempStudents.value = []
  } finally {
    tempLoading.value = false
  }
}

async function handleTempEnroll(student) {
  if (!props.scheduleId) {
    ElMessage.warning('请先选择课次')
    return
  }
  try {
    await temporaryEnroll({ schedule_id: props.scheduleId, student_id: student.id })
    ElMessage.success('临时插班成功')
    visible.value = false
    emit('enroll-success')
  } catch (e) {
    ElMessage.error('插班失败')
  }
}

function handleClose() {
  visible.value = false
}
</script>

<style scoped>
.temp-enroll-drawer { padding: var(--spacing-4); }
.filter-row { display: flex; gap: var(--spacing-3); margin-bottom: var(--spacing-4); }
.pagination-box { margin-top: var(--spacing-4); display: flex; justify-content: flex-end; }
.student-info-cell { display: flex; align-items: center; gap: 8px; }
</style>