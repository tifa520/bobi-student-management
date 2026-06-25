// frontend/src/api/class.js
import request from './request'

export function getClassList(params) {
  return request.get('/classes', { params })
}

export function getClassDetail(id) {
  return request.get(`/classes/${id}`)
}

export function createClass(data) {
  return request.post('/classes', data)
}

export function updateClass(id, data) {
  return request.put(`/classes/${id}`, data)
}

export function deleteClass(id) {
  return request.delete(`/classes/${id}`)
}

export function closeClass(id) {
  return request.post(`/classes/${id}/close`)
}

export function getClassStudents(classId) {
  return request.get(`/classes/${classId}/students`)
}

export function getClassSchedules(classId) {
  return request.get(`/classes/${classId}/schedules`)
}

export function createSchedule(classId, data) {
  return request.post(`/classes/${classId}/schedules`, null, { params: data })
}

export function updateSchedule(scheduleId, params) {
  return request.put(`/schedules/${scheduleId}`, null, { params })
}

export function deleteSchedule(scheduleId) {
  return request.delete(`/schedules/${scheduleId}`)
}

export function getClassAttendance(classId, params) {
  return request.get(`/classes/${classId}/attendance`, { params })
}

// ★ 新增：按课阶筛选班级
export function getClassesByCourseAndStage(courseId, stageId) {
  return request.get(`/classes/by-course/${courseId}`, { params: { stage_id: stageId } })
}