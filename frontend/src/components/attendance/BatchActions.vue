<!-- frontend/src/components/attendance/BatchActions.vue -->
<template>
  <div class="batch-actions-bottom">
    <el-button class="remove-btn" plain @click="emit('remove')">移除</el-button>
    <el-button class="absent-btn" plain @click="emit('open-modal', '未到')">未到</el-button>
    <el-button class="leave-btn" plain @click="emit('open-modal', '请假')">请假</el-button>
    <el-button class="late-early-btn" plain @click="emit('open-modal', '迟到')">出勤迟到</el-button>
    <el-button class="present-btn" @click="emit('open-modal', '出勤')">出勤</el-button>
  </div>
</template>

<script setup>
const emit = defineEmits(['open-modal', 'remove'])
</script>

<style scoped>
.batch-actions-bottom { display: flex; gap: var(--spacing-2); padding: var(--spacing-3) var(--spacing-4); border-top: 1px solid var(--border-color); }
.batch-actions-bottom .el-button { flex: 1; height: 35px; border-radius: var(--radius-full); background: var(--bg-white); border-color: var(--border-color); color: var(--primary); }
.batch-actions-bottom .el-button:hover { background: var(--primary); color: var(--bg-white); }
.remove-btn { border-color: #f56c6c; color: #f56c6c; }
.remove-btn:hover { background: #f56c6c; color: var(--bg-white); }
</style>