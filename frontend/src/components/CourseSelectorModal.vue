<template>
  <el-dialog v-model="visible" title="选择课程" width="600px" :close-on-click-modal="false" class="course-selector-dialog">
    <div class="search-bar">
      <el-input v-model="searchKey" placeholder="搜索课程名称" clearable @input="handleSearch" />
    </div>
    <el-table :data="courseList" v-loading="loading" highlight-current-row @row-click="addCourse" max-height="400" class="course-table">
      <el-table-column label="课程名称">
        <template #default="{ row }">
          <div class="course-row">
            <span class="course-name">{{ row.name }}</span>
            <span class="class-count">（开设{{ row.class_count }}个班）</span>
          </div>
        </template>
      </el-table-column>
    </el-table>
    <div class="pagination-box">
      <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total" layout="prev, pager, next" size="small" @current-change="fetchCourses" />
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { getCourseList } from '@/api/basic'

const emit = defineEmits(['course-selected'])
const visible = ref(false)
const searchKey = ref('')
const courseList = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

async function fetchCourses() {
  loading.value = true
  try {
    const params = { search: searchKey.value || undefined, page: page.value, page_size: pageSize.value }
    const res = await getCourseList(params)
    courseList.value = res.data?.items || res.data || []
    total.value = res.data?.total || 0
  } catch { courseList.value = [] } finally { loading.value = false }
}
function handleSearch() { page.value = 1; fetchCourses() }
function addCourse(row) { if (row) { emit('course-selected', row); visible.value = false } }
watch(visible, (val) => { if (val) { searchKey.value = ''; page.value = 1; fetchCourses() } })
defineExpose({ open: () => { visible.value = true } })
</script>

<style scoped>
:deep(.el-dialog__header) { background: transparent; }
:deep(.el-dialog__title) { color: var(--primary-color, #36b459); font-size: 16px; font-weight: 500; }
.search-bar { margin: 16px 0; }
.course-table { cursor: pointer; }
.course-row { display: flex; justify-content: space-between; align-items: center; width: 100%; }
.course-name { font-weight: 500; }
.class-count { color: var(--text-secondary, #909399); font-size: 13px; }
.pagination-box { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>