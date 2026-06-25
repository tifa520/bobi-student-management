<template>
  <div class="attendance-calendar">
    <div class="calendar-nav">
      <el-button @click="prevWeek" :icon="ArrowLeft" circle size="small" />
      <span class="week-range">{{ weekRange }}</span>
      <el-button @click="nextWeek" :icon="ArrowRight" circle size="small" />
      <el-button @click="goToday" size="small">今天</el-button>
    </div>
    <div class="calendar-grid">
      <div
        v-for="day in weekDays"
        :key="day.date"
        class="calendar-day"
        :class="{ 'is-today': day.isToday, 'is-selected': selectedDate === day.date }"
        @click="selectDate(day.date)"
      >
        <span class="day-name">{{ day.dayName }}</span>
        <span class="day-date">{{ day.dayOfMonth }}</span>
        <span v-if="day.hasSchedule" class="day-dot" :class="{ completed: day.allCompleted }"></span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import { getAttendanceClasses } from '@/api/attendance'
import dayjs from 'dayjs'

const emit = defineEmits(['date-change'])
const props = defineProps({
  scheduleStatus: { type: Object, default: () => ({}) }
})

const currentMonday = ref(dayjs().startOf('week').add(1, 'day'))
const selectedDate = ref(dayjs().format('YYYY-MM-DD'))

const weekRange = computed(() => {
  const start = currentMonday.value.format('M月D日')
  const end = currentMonday.value.add(6, 'day').format('M月D日')
  return `${start} - ${end}`
})

const weekDays = computed(() => {
  const days = []
  for (let i = 0; i < 7; i++) {
    const d = currentMonday.value.add(i, 'day')
    const dateStr = d.format('YYYY-MM-DD')
    const status = props.scheduleStatus[dateStr]
    days.push({
      date: dateStr,
      dayName: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][i],
      dayOfMonth: d.date(),
      isToday: d.isSame(dayjs(), 'day'),
      hasSchedule: !!status,
      allCompleted: status === 'completed'
    })
  }
  return days
})

async function loadWeekScheduleStatus() {
  const start = currentMonday.value
  const statusMap = {}
  for (let i = 0; i < 7; i++) {
    const date = start.add(i, 'day').format('YYYY-MM-DD')
    try {
      const res = await getAttendanceClasses(date)
      const sessions = res.data || []
      const hasClass = sessions.length > 0
      let allCompleted = true
      for (const s of sessions) if (s.status !== 'completed') { allCompleted = false; break }
      statusMap[date] = hasClass ? (allCompleted ? 'completed' : 'scheduled') : null
    } catch {
      statusMap[date] = null
    }
  }
  emit('update:scheduleStatus', statusMap)
}

function selectDate(date) {
  selectedDate.value = date
  emit('date-change', date)
}

function prevWeek() {
  currentMonday.value = currentMonday.value.subtract(7, 'day')
  loadWeekScheduleStatus()
  const newDate = currentMonday.value.add(3, 'day').format('YYYY-MM-DD')
  selectDate(newDate)
}

function nextWeek() {
  currentMonday.value = currentMonday.value.add(7, 'day')
  loadWeekScheduleStatus()
  const newDate = currentMonday.value.add(3, 'day').format('YYYY-MM-DD')
  selectDate(newDate)
}

function goToday() {
  const today = dayjs().format('YYYY-MM-DD')
  currentMonday.value = dayjs().startOf('week').add(1, 'day')
  loadWeekScheduleStatus()
  selectDate(today)
}

watch(() => currentMonday.value, () => loadWeekScheduleStatus())
loadWeekScheduleStatus()
</script>

<style scoped>
.attendance-calendar {
  background: white;
  border-radius: var(--radius-md);
  padding: 16px;
  margin-bottom: 16px;
}
.calendar-nav {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}
.week-range {
  font-size: 15px;
  font-weight: 500;
}
.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 8px;
}
.calendar-day {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px 4px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background 0.2s;
  position: relative;
}
.calendar-day:hover {
  background: var(--primary-lighter);
}
.calendar-day.is-today {
  background: var(--primary-lighter);
  font-weight: bold;
}
.calendar-day.is-selected {
  border: 2px solid var(--primary-color);
}
.day-name {
  font-size: 12px;
  color: var(--text-secondary);
}
.day-date {
  font-size: 18px;
  font-weight: 500;
  margin: 4px 0;
}
.day-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--primary-color);
}
.day-dot.completed {
  background: var(--text-secondary);
}
</style>