import request from './request'

export function getRefundInfo(studentId, courseId) {
  return request.get(`/refund/student/${studentId}/course/${courseId}`)
}
export function submitRefund(data) {
  return request.post('/refund/create', data)
}