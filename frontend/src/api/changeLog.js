import request from './request'

export function getStudentChangeLogs(studentId, params) {
  return request.get(`/change-log/student/${studentId}/change-logs`, { params })
}