<template>
  <div class="custom-time-picker">
    <div class="time-input" @click="showPopover">
      <span :class="{ 'placeholder': !displayValue }">
        {{ displayValue || placeholder }}
      </span>
      <el-icon class="arrow-icon"><ArrowDown /></el-icon>
    </div>

    <div v-if="panelVisible" class="time-panel-overlay" @click.self="hidePopover">
      <div class="time-panel" :style="panelStyle">
        <!-- 小时列表 -->
        <div class="time-panel-left">
          <div class="panel-header">选择小时</div>
          <div class="time-list">
            <div
              v-for="hour in hours"
              :key="hour"
              class="time-item"
              :class="{ active: tempHour === hour }"
              @click="selectHour(hour)"
            >
              <span>{{ hour }}时</span>
              <el-icon class="next-icon"><ArrowRight /></el-icon>
            </div>
          </div>
        </div>

        <!-- 分钟列表（只在选择了小时后显示） -->
        <div v-if="tempHour !== null" class="time-panel-right">
          <div class="panel-header">
            <span>选择分钟</span>
            <span class="close-right-btn" @click="tempHour = null">
              <el-icon><Close /></el-icon>
            </span>
          </div>
          <div class="time-list">
            <div
              v-for="minute in minutes"
              :key="minute"
              class="time-item minute-item"
              :class="{ active: tempMinute === minute }"
              @click="selectMinute(minute)"
            >
              {{ minute }}分
            </div>
          </div>
          <!-- 底部按钮放在分钟列内部 -->
          <div class="panel-footer">
            <el-button size="small" @click="clearTime">清空</el-button>
            <el-button size="small" type="primary" @click="confirmTime">确定</el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { ArrowDown, ArrowRight, Close } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: '选择时间'
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const panelVisible = ref(false)
const tempHour = ref(null)
const tempMinute = ref(null)
const panelStyle = ref({})

const hours = computed(() => Array.from({ length: 24 }, (_, i) => String(i).padStart(2, '0')))
const minutes = computed(() => Array.from({ length: 60 }, (_, i) => String(i).padStart(2, '0')))
const displayValue = computed(() => props.modelValue || '')

function showPopover(event) {
  if (props.modelValue && props.modelValue.includes(':')) {
    const parts = props.modelValue.split(':')
    tempHour.value = parts[0]
    tempMinute.value = parts[1]
  } else {
    tempHour.value = null
    tempMinute.value = null
  }
  panelVisible.value = true

  const rect = event.currentTarget.getBoundingClientRect()
  let top = rect.bottom + 4
  let left = rect.left
  
  if (top + 320 > window.innerHeight) {
    top = rect.top - 320 - 4
  }
  panelStyle.value = {
    top: `${top}px`,
    left: `${left}px`
  }

  setTimeout(() => {
    document.addEventListener('click', handleClickOutside)
  }, 100)
}

function hidePopover() {
  panelVisible.value = false
  document.removeEventListener('click', handleClickOutside)
}

function handleClickOutside(event) {
  const panel = document.querySelector('.time-panel')
  const input = document.querySelector('.time-input')
  if (panel && !panel.contains(event.target) && input && !input.contains(event.target)) {
    hidePopover()
  }
}

function selectHour(hour) {
  tempHour.value = hour
  tempMinute.value = null
}

function selectMinute(minute) {
  tempMinute.value = minute
  const timeValue = `${tempHour.value}:${tempMinute.value}`
  emit('update:modelValue', timeValue)
  emit('change', timeValue)
  hidePopover()
}

function confirmTime() {
  if (tempHour.value !== null && tempMinute.value !== null) {
    const timeValue = `${tempHour.value}:${tempMinute.value}`
    emit('update:modelValue', timeValue)
    emit('change', timeValue)
  }
  hidePopover()
}

function clearTime() {
  tempHour.value = null
  tempMinute.value = null
  emit('update:modelValue', '')
  emit('change', '')
  hidePopover()
}

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.custom-time-picker {
  position: relative;
  display: inline-block;
}

.time-input {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  height: 36px;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  cursor: pointer;
  background-color: #fff;
  min-width: 120px;
}

.time-input:hover {
  border-color: #36b459;
}

.time-input .placeholder {
  color: #c0c4cc;
}

.arrow-icon {
  font-size: 14px;
  color: #909399;
}

.time-panel-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9998;
}

.time-panel {
  position: fixed;
  z-index: 9999;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  border: 1px solid #e4e7ed;
  width: 480px;
  display: flex;
  overflow: hidden;
}

.time-panel-left {
  width: 50%;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  max-height: 380px;
}

.time-panel-right {
  width: 50%;
  display: flex;
  flex-direction: column;
  max-height: 380px;
}

.panel-header {
  padding: 12px 16px;
  font-weight: 600;
  font-size: 14px;
  color: #303133;
  border-bottom: 1px solid #e4e7ed;
  background: #fafafa;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.close-right-btn {
  cursor: pointer;
  display: flex;
  align-items: center;
  color: #909399;
}

.close-right-btn:hover {
  color: #f56c6c;
}

.time-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.time-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  cursor: pointer;
  transition: background 0.2s;
  font-size: 14px;
  color: #606266;
}

.time-item:hover {
  background: #f5f7fa;
}

.time-item.active {
  background: #e8f5e9;
  color: #36b459;
  font-weight: 500;
}

.minute-item {
  justify-content: center;
}

.next-icon {
  font-size: 14px;
  color: #c0c4cc;
}

.panel-footer {
  padding: 12px 16px;
  border-top: 1px solid #e4e7ed;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  background: #fff;
  margin-top: auto;
}
</style>