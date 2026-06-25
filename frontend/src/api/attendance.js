import request from './request'

export function getAttendanceClasses(date) {
  return request.get('/attendance/classes', { params: { course_date: date } })
}

export function getClassStudents(scheduleId) {
  return request.get('/attendance/students', { params: { schedule_id: scheduleId } })
}

export function submitAttendance(data) {
  return request.post('/attendance/submit', data)
}

export function getOtherClasses(classId) {
  return request.get('/attendance/other-classes', { params: { class_id: classId } })
}

export function getUpcomingSchedules(classId) {
  return request.get('/attendance/upcoming-schedules', { params: { class_id: classId } })
}

export function transferClassStudent(data) {
  return request.post('/attendance/transfer', data)
}

export function getUnattendedSchedules() {
  return request.get('/attendance/unattended')
}

export function temporaryEnroll(data) {
  return request.post('/attendance/temporary-enroll', data)
}

export function updateAttendance(attendanceId, data) {
  return request.put(`/attendance/record/${attendanceId}`, null, { params: data })
}