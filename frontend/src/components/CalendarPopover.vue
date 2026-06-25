<template>
  <div class="calendar-popover-trigger">
    <!-- 触发器 -->
    <div class="trigger-input" @click="togglePopover">
      <el-input
        :model-value="displayDate"
        placeholder="选择日期"
        readonly
        :prefix-icon="Calendar"
      />
      <el-icon class="arrow-icon" :class="{ 'is-reverse': visible }">
        <ArrowDown />
      </el-icon>
    </div>

    <!-- 浮层日历 -->
    <teleport to="body">
      <Transition name="fade">
        <div v-if="visible" class="calendar-popover-overlay" @click.self="closePopover">
          <div class="calendar-popover-container" :style="popoverStyle" @click.stop>
            <div class="calendar-header">
              <el-button link @click="prevMonth" :disabled="loading">
                <el-icon><ArrowLeft /></el-icon>
              </el-button>
              <span class="current-month">{{ currentYearMonth }}</span>
              <el-button link @click="nextMonth" :disabled="loading">
                <el-icon><ArrowRight /></el-icon>
              </el-button>
              <el-button link @click="refreshCurrentMonth" :loading="loading" class="refresh-btn">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
            
            <div v-loading="loading" element-loading-text="加载课程数据..." class="calendar-wrapper">
              <el-calendar v-model="calendarValue" class="event-calendar" :first-day-of-week="1">
                <template #date-cell="{ data }">
                  <div 
                    class="calendar-cell" 
                    :class="{ 
                      'has-schedule': hasScheduleOnDate(data.day),
                      'has-completed': hasCompletedOnDate(data.day),
                      'is-selected': isSelectedDate(data.day),
                      'is-other-month': data.type === 'prev-month' || data.type === 'next-month'
                    }"
                    @click="selectDate(data.day)"
                  >
                    <span class="cell-date">{{ data.day.split('-')[2] }}</span>
                    <span v-if="hasScheduleOnDate(data.day) || hasCompletedOnDate(data.day)" 
                          class="event-dot" 
                          :class="{ 'dot-completed': hasCompletedOnDate(data.day) }"></span>
                  </div>
                </template>
              </el-calendar>
            </div>
          </div>
        </div>
      </Transition>
    </teleport>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { Calendar, ArrowDown, ArrowLeft, ArrowRight, Refresh } from '@element-plus/icons-vue'
import request from '@/api/request'
import dayjs from 'dayjs'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

// 状态
const visible = ref(false)
const popoverStyle = ref({})
const calendarValue = ref(new Date())
const scheduleStatusMap = ref({}) // 存储日期状态: 'scheduled' 或 'completed'
const loading = ref(false)
const currentDisplayMonth = ref('') // 当前显示的月份，用于缓存

// 当前显示的年份月份
const currentYearMonth = computed(() => {
  return dayjs(calendarValue.value).format('YYYY年MM月')
})

// 显示的日期
const displayDate = computed(() => {
  if (!props.modelValue) return ''
  return dayjs(props.modelValue).format('YYYY-MM-DD')
})

// 判断是否为选中的日期
function isSelectedDate(dateStr) {
  return dateStr === props.modelValue
}

// 判断是否有课（未完成）
function hasScheduleOnDate(dateStr) {
  return scheduleStatusMap.value[dateStr] === 'scheduled'
}

// 判断是否已完成考勤
function hasCompletedOnDate(dateStr) {
  return scheduleStatusMap.value[dateStr] === 'completed'
}

// 获取指定月份的所有日期状态（批量接口）
async function fetchMonthStatus(year, month, forceRefresh = false) {
  const monthKey = `${year}-${month}`
  
  // 检查缓存（非强制刷新时）
  if (!forceRefresh && scheduleStatusMap.value[`_cached_${monthKey}`]) {
    return
  }
  
  loading.value = true
  
  try {
    // 使用批量接口，一次请求获取整个月份的状态
    const response = await request.get('/attendance/month-status', {
      params: { year, month }
    })
    
    if (response.code === 0) {
      const monthData = response.data || {}
      
      // 清除该月份的旧数据
      const keysToRemove = []
      for (const key in scheduleStatusMap.value) {
        if (key.startsWith(monthKey)) {
          keysToRemove.push(key)
        }
      }
      keysToRemove.forEach(key => {
        delete scheduleStatusMap.value[key]
      })
      
      // 存储新数据
      Object.assign(scheduleStatusMap.value, monthData)
      scheduleStatusMap.value[`_cached_${monthKey}`] = true
    }
  } catch (error) {
    console.error('获取月份课程数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 加载当前显示月份的数据
async function loadCurrentMonthData(forceRefresh = false) {
  const year = calendarValue.value.getFullYear()
  const month = calendarValue.value.getMonth() + 1
  const monthKey = `${year}-${month}`
  
  // 如果月份变化了或强制刷新，加载新月份的数据
  if (forceRefresh || currentDisplayMonth.value !== monthKey) {
    currentDisplayMonth.value = monthKey
    await fetchMonthStatus(year, month, forceRefresh)
  }
}

// 刷新当前月份数据（强制重新获取）
async function refreshCurrentMonth() {
  if (loading.value) return
  await loadCurrentMonthData(true)
}

// 选择日期
function selectDate(dateStr) {
  emit('update:modelValue', dateStr)
  emit('change', dateStr)
  closePopover()
}

// 切换月份
async function prevMonth() {
  if (loading.value) return
  const newDate = dayjs(calendarValue.value).subtract(1, 'month')
  calendarValue.value = newDate.toDate()
  await loadCurrentMonthData()
}

async function nextMonth() {
  if (loading.value) return
  const newDate = dayjs(calendarValue.value).add(1, 'month')
  calendarValue.value = newDate.toDate()
  await loadCurrentMonthData()
}

// 更新浮层位置
function updatePopoverPosition() {
  if (!visible.value) return
  
  const trigger = document.querySelector('.calendar-popover-trigger .trigger-input')
  if (trigger) {
    const rect = trigger.getBoundingClientRect()
    const viewportHeight = window.innerHeight
    const popoverHeight = 420
    let top = rect.bottom + 4
    
    if (top + popoverHeight > viewportHeight && rect.top > popoverHeight) {
      top = rect.top - popoverHeight - 4
    }
    
    popoverStyle.value = {
      top: `${top}px`,
      left: `${rect.left}px`,
      minWidth: `${Math.max(rect.width, 300)}px`,
      width: '400px',
      maxWidth: 'calc(100vw - 32px)'
    }
  }
}

// 打开浮层
async function openPopover() {
  if (visible.value) return
  
  visible.value = true
  await nextTick()
  updatePopoverPosition()
  
  window.addEventListener('scroll', updatePopoverPosition, true)
  window.addEventListener('resize', updatePopoverPosition)
  
  await loadCurrentMonthData()
}

function closePopover() {
  if (!visible.value) return
  visible.value = false
  window.removeEventListener('scroll', updatePopoverPosition, true)
  window.removeEventListener('resize', updatePopoverPosition)
}

function togglePopover() {
  if (visible.value) {
    closePopover()
  } else {
    openPopover()
  }
}

// 监听日历值变化
watch(calendarValue, async (newDate, oldDate) => {
  if (newDate && (!oldDate || 
      newDate.getMonth() !== oldDate.getMonth() || 
      newDate.getFullYear() !== oldDate.getFullYear())) {
    await loadCurrentMonthData()
  }
})

// 监听外部值变化
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    calendarValue.value = new Date(newVal)
  }
})

// 点击外部关闭
function handleClickOutside(event) {
  if (!visible.value) return
  
  const container = document.querySelector('.calendar-popover-container')
  const trigger = document.querySelector('.calendar-popover-trigger .trigger-input')
  
  if (container && !container.contains(event.target) && 
      trigger && !trigger.contains(event.target)) {
    closePopover()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  if (props.modelValue) {
    calendarValue.value = new Date(props.modelValue)
  }
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  closePopover()
})
</script>

<style scoped>
/* 样式保持不变，与之前相同 */
.calendar-popover-trigger {
  position: relative;
  display: inline-block;
}

.trigger-input {
  display: flex;
  align-items: center;
  position: relative;
  cursor: pointer;
}

.arrow-icon {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  transition: transform 0.2s;
  color: #909399;
  pointer-events: none;
}

.arrow-icon.is-reverse {
  transform: translateY(-50%) rotate(180deg);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.calendar-popover-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9998;
}

.calendar-popover-container {
  position: fixed;
  z-index: 9999;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  border: 1px solid #e4e7ed;
  padding: 16px;
  box-sizing: border-box;
}

.calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 0 8px;
}

.current-month {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.refresh-btn {
  margin-left: auto;
}

.calendar-wrapper {
  min-height: 300px;
}

.event-calendar {
  width: 100%;
}

.event-calendar :deep(.el-calendar-table) {
  table-layout: fixed;
  width: 100%;
}

.event-calendar :deep(.el-calendar-table td) {
  padding: 0;
  text-align: center;
}

.event-calendar :deep(.el-calendar-day) {
  padding: 0;
  height: auto;
  min-height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.calendar-cell {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  margin: 0 auto;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s ease;
}

.cell-date {
  font-size: 14px;
  font-weight: 500;
  color: #606266;
  line-height: 1;
}

.calendar-cell.is-other-month .cell-date {
  color: #c0c4cc;
}

.calendar-cell.is-selected {
  background-color: var(--primary, #36b459);
}

.calendar-cell.is-selected .cell-date {
  color: #fff;
}

.calendar-cell:hover:not(.is-selected) {
  background-color: var(--primary-bg, #e8f5e9);
}

.calendar-cell:hover:not(.is-selected) .cell-date {
  color: var(--primary, #36b459);
}

.event-dot {
  position: absolute;
  bottom: 0px;
  left: 50%;
  transform: translateX(-50%);
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: var(--primary, #36b459);
}

.event-dot.dot-completed {
  background-color: var(--gray-4, #c9cdd4);
}

.has-schedule .cell-date {
  font-weight: 600;
  color: var(--primary, #36b459);
}

.has-schedule.is-selected .cell-date {
  color: #fff;
}

.has-completed .cell-date {
  color: var(--text-tertiary, #86909c);
}

.has-completed.is-selected .cell-date {
  color: #fff;
}

.event-calendar :deep(.el-calendar-table thead th) {
  padding: 10px 0;
  font-size: 13px;
  font-weight: 500;
  color: #909399;
}

.event-calendar :deep(.el-calendar-table td.is-today .calendar-cell) {
  border: 1px solid var(--primary, #36b459);
}

.event-calendar :deep(.el-calendar-table td.is-today .calendar-cell.is-selected) {
  border: none;
}
</style>