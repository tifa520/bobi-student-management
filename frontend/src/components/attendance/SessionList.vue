<!-- frontend/src/components/attendance/SessionList.vue -->
<template>
  <el-tabs v-model="localLeftTab" class="left-tabs" @tab-click="onTabClick">
    <el-tab-pane label="待考勤" name="pending" />
    <el-tab-pane label="已完成考勤" name="completed" />
  </el-tabs>
  <div class="session-list-container">
    <div v-if="localLeftTab === 'pending'">
      <div
        v-for="session in pendingSessions"
        :key="session.schedule_id"
        class="session-item"
        :class="{ active: currentSchedule?.schedule_id === session.schedule_id }"
        @click="emit('select-session', session)"
      >
        <div class="session-time">{{ formatTime(session.course_date, session.start_time) }}</div>
        <div class="session-info-row">
          <div class="session-name-teacher">
            {{ session.class_name }}（{{ session.course_name }}）- {{ session.teacher_name }} · {{ session.classroom_name || '未分配教室' }}
          </div>
          <div class="session-status-badge">
            <span :class="['status-badge', getStatusClass(session)]">{{ getStatusText(session) }}</span>
          </div>
        </div>
      </div>
      <div v-if="pendingSessions.length === 0" class="empty-tip">暂无待考勤课次</div>
    </div>
    <div v-else>
      <div
        v-for="session in completedSessions"
        :key="session.schedule_id"
        class="session-item"
        :class="{ active: currentSchedule?.schedule_id === session.schedule_id }"
        @click="emit('select-session', session)"
      >
        <div class="session-time">{{ formatTime(session.course_date, session.start_time) }}</div>
        <div class="session-info-row">
          <div class="session-name-teacher">
            {{ session.class_name }}（{{ session.course_name }}）- {{ session.teacher_name }} · {{ session.classroom_name || '未分配教室' }}
          </div>
          <div class="session-status-badge">
            <span class="status-badge status-completed">已完成考勤</span>
          </div>
        </div>
      </div>
      <div v-if="completedSessions.length === 0" class="empty-tip">暂无已完成考勤课次</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import dayjs from 'dayjs'

const props = defineProps({
  pendingSessions: { type: Array, default: () => [] },
  completedSessions: { type: Array, default: () => [] },
  leftTab: { type: String, default: 'pending' },
  currentSchedule: { type: Object, default: null }
})
const emit = defineEmits(['update:leftTab', 'select-session'])

const localLeftTab = computed({
  get: () => props.leftTab,
  set: (val) => emit('update:leftTab', val)
})

function formatTime(date, time) {
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

function getStatusText(session) {
  const now = dayjs()
  const dt = dayjs(`${session.course_date} ${session.start_time}`)
  if (session.status === 'completed') return '已完成考勤'
  return dt.isAfter(now) ? '待上课' : '请进行考勤'
}

function getStatusClass(session) {
  if (session.status === 'completed') return 'status-completed'
  const now = dayjs()
  const dt = dayjs(`${session.course_date} ${session.start_time}`)
  return dt.isAfter(now) ? 'status-waiting' : 'status-pending'
}

function onTabClick() {
  // 切换页签时可选自动选中第一个
}
</script>

<style scoped>
.left-tabs :deep(.el-tabs__header) { height: 60px; margin: 0; padding-left: var(--spacing-5); border-bottom: none; }
.left-tabs :deep(.el-tabs__item) { height: 60px; line-height: 60px; }
.session-list-container { flex: 1; overflow-y: auto; }
.session-item { padding: 0; border-bottom: 1px solid #f0f0f0; cursor: pointer; }
.session-time { font-size: 16px; font-weight: 700; color: #000; padding: var(--spacing-3) 0 var(--spacing-2) var(--spacing-3); border-bottom: 1px solid #e6edf2; }
.session-info-row { display: flex; justify-content: space-between; align-items: center; padding: var(--spacing-3); background: #fff; font-size: 14px; }
.session-info-row:hover { background: var(--gray-1); }
.status-badge { font-size: 14px; font-weight: 500; }
.status-completed { color: #67c23a; }
.status-pending { color: #e6a23c; }
.status-waiting { color: #409eff; }
.empty-tip { text-align: center; padding: 40px; color: #909399; }
</style>