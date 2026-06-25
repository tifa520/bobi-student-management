import { ref, computed } from 'vue'
import { getAttendanceClasses, getClassStudents, submitAttendance, getOtherClasses, getUpcomingSchedules, transferClassStudent, getUnattendedSchedules, temporaryEnroll } from '@/api/attendance'
import { getClassDetail } from '@/api/class'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'

export function useAttendance() {
  const currentSchedule = ref(null)
  const pendingSessions = ref([])
  const completedSessions = ref([])
  const unattendedGroups = ref([])
  const studentList = ref([])
  const selectedStudents = ref([])
  const studentLoading = ref(false)
  const studentSearch = ref('')
  const currentDeductHours = ref(1)

  const leftTab = ref('pending')
  const rightTab = ref('pending')
  const showUnattendedList = ref(false)

  const otherClasses = ref([])
  const targetSchedules = ref([])

  async function loadSessions(date) {
    try {
      const res = await getAttendanceClasses(date)
      const sessions = res.data || []
      const pending = []
      const completed = []
      for (const s of sessions) {
        if (s.status === 'completed') {
          completed.push({ ...s, statusText: '已完成考勤', statusClass: 'completed' })
        } else {
          pending.push({ ...s, statusText: '待考勤', statusClass: 'pending' })
        }
      }
      pendingSessions.value = pending
      completedSessions.value = completed
      return { pending, completed }
    } catch (e) {
      console.error('加载课次失败', e)
      return { pending: [], completed: [] }
    }
  }

  async function loadUnattended() {
    try {
      const res = await getUnattendedSchedules()
      unattendedGroups.value = res.data || []
    } catch (e) {
      unattendedGroups.value = []
    }
  }

  async function selectSession(session) {
    currentSchedule.value = session
    rightTab.value = 'pending'
    try {
      const classRes = await getClassDetail(session.class_id)
      if (classRes.code === 0 && classRes.data) {
        currentDeductHours.value = classRes.data.deduct_hours || 1
      }
    } catch (e) {
      currentDeductHours.value = 1
    }
    await loadStudents()
  }

  async function loadStudents() {
    if (!currentSchedule.value) return
    studentLoading.value = true
    try {
      const res = await getClassStudents(currentSchedule.value.schedule_id)
      studentList.value = (res.data || []).map(s => {
        let displayDeductHours = null
        if (s.attendance_id && s.status !== '未考勤') {
          if (s.status === '请假' || s.status === '未到') {
            displayDeductHours = 0
          } else {
            displayDeductHours = (s.deduct_hours !== undefined && s.deduct_hours !== null)
              ? s.deduct_hours
              : currentDeductHours.value
          }
        }
        return {
          ...s,
          student_id: Number(s.student_id),
          hasAttendance: !!s.attendance_id,
          displayDeductHours
        }
      })
    } catch (e) {
      console.error('加载学员失败', e)
      studentList.value = []
    } finally {
      studentLoading.value = false
    }
  }

  const filteredStudentList = computed(() => {
    let list = studentList.value
    if (studentSearch.value) {
      const kw = studentSearch.value.toLowerCase()
      list = list.filter(s => s.name.toLowerCase().includes(kw) || (s.phone && s.phone.includes(kw)))
    }
    if (rightTab.value === 'pending') {
      list = list.filter(s => !s.attendance_id || s.status === '未考勤')
    } else if (rightTab.value === 'present') {
      list = list.filter(s => s.status === '出勤' || s.status === '迟到')
    } else if (rightTab.value === 'absent') {
      list = list.filter(s => s.status === '未到' || s.status === '请假')
    }
    return list
  })

  function handleSelectionChange(selection) {
    selectedStudents.value = selection
  }

  async function submitAttendanceDirect(status, remark = '') {
    if (selectedStudents.value.length === 0) {
      ElMessage.warning('请先选择学员')
      return false
    }
    const attendanceList = selectedStudents.value.map(s => ({
      student_id: s.student_id,
      status,
      deduct_hours: (status === '出勤' || status === '迟到') ? 1 : 0,
      leave_deduct: (status === '请假' || status === '未到') ? 1 : 0,
      hour_type: '付费',
      remark
    }))
    try {
      await submitAttendance({
        schedule_id: currentSchedule.value.schedule_id,
        attendance_list: attendanceList
      })
      ElMessage.success(`已批量设置${status}`)
      await loadStudents()
      await loadSessions(dayjs().format('YYYY-MM-DD'))
      return true
    } catch (e) {
      ElMessage.error('提交失败')
      return false
    }
  }

  async function fetchOtherClasses(classId) {
    const res = await getOtherClasses(classId)
    otherClasses.value = res.data || []
  }

  async function fetchTargetSchedules(classId) {
    const res = await getUpcomingSchedules(classId)
    targetSchedules.value = res.data || []
  }

  async function doTransferClass(studentId, fromScheduleId, toClassId, toScheduleId) {
    try {
      await transferClassStudent({
        student_id: studentId,
        from_schedule_id: fromScheduleId,
        to_class_id: toClassId,
        to_schedule_id: toScheduleId
      })
      ElMessage.success('换班成功')
      await loadStudents()
      return true
    } catch (e) {
      ElMessage.error('换班失败')
      return false
    }
  }

  async function doTemporaryEnroll(scheduleId, studentId) {
    try {
      await temporaryEnroll({ schedule_id: scheduleId, student_id: studentId })
      ElMessage.success('临时插班成功')
      await loadStudents()
      return true
    } catch (e) {
      ElMessage.error('插班失败')
      return false
    }
  }

  function reset() {
    currentSchedule.value = null
    selectedStudents.value = []
    studentList.value = []
    studentSearch.value = ''
  }

  return {
    currentSchedule,
    pendingSessions,
    completedSessions,
    unattendedGroups,
    studentList,
    selectedStudents,
    studentLoading,
    studentSearch,
    currentDeductHours,
    leftTab,
    rightTab,
    showUnattendedList,
    otherClasses,
    targetSchedules,
    filteredStudentList,
    loadSessions,
    loadUnattended,
    selectSession,
    loadStudents,
    handleSelectionChange,
    submitAttendanceDirect,
    fetchOtherClasses,
    fetchTargetSchedules,
    doTransferClass,
    doTemporaryEnroll,
    reset
  }
}