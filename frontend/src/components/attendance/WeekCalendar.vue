<!-- frontend/src/components/attendance/WeekCalendar.vue -->
<template>
  <div class="week-calendar-wrapper">
    <div class="week-calendar">
      <div class="week-header">
        <div class="week-days">
          <div
            v-for="day in weekDays"
            :key="day.date"
            class="week-day"
            :class="{ 'is-today': day.isToday, 'is-selected': selectedDate === day.date, 'has-schedule': day.hasSchedule }"
            @click="emit('select-date', day.date)"
          >
            <div class="day-name">{{ day.dayName }}</div>
            <div class="day-date">{{ day.dayOfMonth }}</div>
            <div class="day-dot" v-if="day.hasSchedule">
              <span :class="{ 'dot-green': !day.allCompleted, 'dot-gray': day.allCompleted }"></span>
            </div>
          </div>
        </div>
        <div class="calendar-nav">
          <el-button @click="emit('prev-week')" :icon="ArrowLeft" circle size="small" class="nav-btn" />
          <span class="week-range">{{ weekRange }}</span>
          <el-button @click="emit('next-week')" :icon="ArrowRight" circle size="small" class="nav-btn" />
          <el-button @click="emit('go-today')" size="small" class="today-btn">今天</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import dayjs from 'dayjs'

const props = defineProps({
  weekDays: { type: Array, required: true },
  selectedDate: { type: String, required: true }
})
const emit = defineEmits(['select-date', 'prev-week', 'next-week', 'go-today'])

const weekRange = computed(() => {
  if (!props.weekDays.length) return ''
  const firstDay = props.weekDays[0]
  const lastDay = props.weekDays[6]
  return `${firstDay.dayOfMonth}日 - ${lastDay.dayOfMonth}日`
})
</script>

<style scoped>
/* 原 WeekCalendar 样式 */
.week-calendar-wrapper { flex: 1; overflow: visible; }
.week-calendar { display: flex; flex-direction: column; }
.week-header { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
.week-days { display: flex; gap: 12px; }
.week-day { width: 80px; height: 80px; border-radius: 50%; text-align: center; display: flex; flex-direction: column; justify-content: center; align-items: center; background: linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%); cursor: pointer; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05); }
.week-day:hover { background: linear-gradient(135deg, #36b459 0%, #2d9748 50%, #1a6e30 100%); transform: translateY(-4px) scale(1.05); box-shadow: 0 12px 24px rgba(54, 180, 89, 0.35); }
.week-day:hover .day-name, .week-day:hover .day-date { color: #fff; }
.week-day.is-selected { background: linear-gradient(135deg, #36b459 0%, #2d9748 50%, #1a6e30 100%); transform: translateY(-4px); box-shadow: 0 8px 20px rgba(54, 180, 89, 0.3); }
.week-day.is-selected .day-name, .week-day.is-selected .day-date { color: #fff; }
.week-day.is-today:not(.is-selected) { background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); border: 1px solid #36b459; }
.week-day.is-today:not(.is-selected) .day-name, .week-day.is-today:not(.is-selected) .day-date { color: #36b459; font-weight: 600; }
.day-name { font-size: 12px; color: var(--text-tertiary); margin-bottom: 4px; transition: color 0.2s; }
.day-date { font-size: 18px; font-weight: 600; color: var(--text-primary); transition: color 0.2s; }
.day-dot { margin-top: 4px; height: 6px; display: flex; justify-content: center; }
.dot-green { width: 6px; height: 6px; border-radius: 50%; background-color: #36b459; }
.dot-gray { width: 6px; height: 6px; border-radius: 50%; background-color: #c0c4cc; }
.calendar-nav { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.nav-btn { width: 32px; height: 32px; border-radius: 50%; padding: 0; background: var(--gray-1); border: none; }
.nav-btn:hover { background: var(--primary-bg); color: var(--primary); }
.week-range { font-size: 14px; font-weight: 500; color: var(--text-primary); }
.today-btn { background: var(--primary-bg); color: var(--primary); border: none; border-radius: var(--radius-full); height: 32px; padding: 0 12px; }
</style>