<template>
  <div class="change-timeline">
    <div class="timeline-filter">
      <el-select v-model="filterCategory" placeholder="全部类型" clearable size="small" style="width: 140px" @change="handleFilter">
        <el-option label="报名相关" value="order" />
        <el-option label="课时变更" value="custom" />
        <el-option label="班级变更" value="class" />
        <el-option label="退费" value="refund" />
        <el-option label="状态变更" value="status" />
        <el-option label="缴费" value="payment" />
      </el-select>
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        value-format="YYYY-MM-DD"
        size="small"
        style="width: 260px; margin-left: 12px"
        @change="handleFilter"
      />
    </div>

    <div v-if="loading" class="timeline-loading">
      <el-icon class="is-loading"><Loading /></el-icon> 加载中...
    </div>

    <el-timeline v-else>
      <el-timeline-item
        v-for="item in filteredChanges"
        :key="item.id"
        :timestamp="formatTime(item.created_at)"
        placement="top"
        :color="item.color"
        :type="item.type"
      >
        <el-card shadow="hover" class="timeline-card">
          <div class="timeline-header">
            <div class="timeline-title">
              <el-icon :color="item.color" style="margin-right: 8px">
                <component :is="item.icon" />
              </el-icon>
              <span class="title-text">{{ item.title }}</span>
              <el-tag :type="getTagType(item.category)" size="small" style="margin-left: 12px">
                {{ getCategoryLabel(item.category) }}
              </el-tag>
            </div>
            <span class="timeline-operator">操作人：{{ item.operator || '系统' }}</span>
          </div>
          <div class="timeline-description">{{ item.description }}</div>
        </el-card>
      </el-timeline-item>
      <div v-if="filteredChanges.length === 0" class="empty-tip">
        <el-icon><Document /></el-icon>
        <span>暂无变更记录</span>
      </div>
    </el-timeline>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Loading, Document } from '@element-plus/icons-vue'
import { getStudentChangeLogs } from '@/api/changeLog'
import dayjs from 'dayjs'

const props = defineProps({ studentId: { type: Number, required: true } })
const loading = ref(false)
const changes = ref([])
const filterCategory = ref(null)
const dateRange = ref(null)

const filteredChanges = computed(() => {
  let result = changes.value
  if (filterCategory.value) result = result.filter(c => c.category === filterCategory.value)
  if (dateRange.value && dateRange.value.length === 2) {
    const [start, end] = dateRange.value
    result = result.filter(c => c.created_at.split(' ')[0] >= start && c.created_at.split(' ')[0] <= end)
  }
  return result
})

function formatTime(time) { return dayjs(time).format('YYYY-MM-DD HH:mm:ss') }
function getCategoryLabel(category) {
  const map = { order: '报名', custom: '课时', class: '班级', refund: '退费', status: '状态', validity: '有效期', payment: '缴费' }
  return map[category] || category
}
function getTagType(category) {
  const map = { order: 'success', custom: 'warning', class: 'primary', refund: 'danger', status: 'info', validity: 'warning', payment: 'info' }
  return map[category] || 'info'
}
async function fetchChanges() {
  loading.value = true
  try {
    const res = await getStudentChangeLogs(props.studentId, { limit: 100 })
    changes.value = res.data || []
  } finally { loading.value = false }
}
function handleFilter() {}
onMounted(fetchChanges)
</script>

<style scoped>
.change-timeline { padding: 0; }
.timeline-filter {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
}
.timeline-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: var(--text-secondary);
}
.timeline-card {
  border-radius: var(--radius-md);
  margin-bottom: 4px;
}
.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  flex-wrap: wrap;
  gap: 8px;
}
.timeline-title {
  display: flex;
  align-items: center;
  font-size: 15px;
  font-weight: 500;
}
.title-text { color: var(--text-primary); }
.timeline-operator {
  font-size: 12px;
  color: var(--text-secondary);
}
.timeline-description {
  font-size: 13px;
  color: var(--text-regular);
  line-height: 1.5;
}
.empty-tip {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  color: var(--text-secondary);
  gap: 12px;
}
.empty-tip .el-icon { font-size: 48px; }
</style>