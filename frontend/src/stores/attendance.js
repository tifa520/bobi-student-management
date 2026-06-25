import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getAttendanceClasses, getClassStudents } from '@/api/attendance'

export const useAttendanceStore = defineStore('attendance', () => {
  const selectedDate = ref('')
  const classList = ref([])
  const activeScheduleId = ref(null)
  const studentList = ref([])

  async function loadClasses(date) {
    selectedDate.value = date
    try {
      const res = await getAttendanceClasses(date)
      classList.value = res.data || []
    } catch {
      classList.value = []
    }
  }

  async function loadStudents(scheduleId) {
    activeScheduleId.value = scheduleId
    if (!scheduleId) {
      studentList.value = []
      return
    }
    try {
      const res = await getClassStudents(scheduleId)
      studentList.value = (res.data || []).map(s => ({
        ...s,
        isEditing: false,
        editStatus: s.status === '未考勤' ? '出勤' : s.status,
        editDeductHours: s.deduct_hours || 0,
        isAttended: s.status !== '未考勤'
      }))
    } catch {
      studentList.value = []
    }
  }

  return { selectedDate, classList, activeScheduleId, studentList, loadClasses, loadStudents }
})