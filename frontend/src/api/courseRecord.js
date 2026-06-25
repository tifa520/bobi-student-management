import request from './request'

export function getAttendanceRecords(params) {
  return request.get('/course-record/attendance-records', { params })
}
export function getCustomRecords(params) {
  return request.get('/course-record/custom-records', { params })
}
export function getGiftRecords(params) {
  return request.get('/course-record/gift-records', { params })
}
export function getTransferRecords(params) {
  return request.get('/course-record/transfer-records', { params })
}
export function exportCourseRecords(params) {
  return request.get('/course-record/export', { params, responseType: 'blob' })
}
// 兼容旧方法名
export function getCourseRecords(params) {
  return getAttendanceRecords(params)
}