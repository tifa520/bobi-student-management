import request from './request'

export function getIntegralRecords(params) {
  return request.get('/score/records', { params })
}

export function getClassStudents(classId) {
  return request.get('/score/class-students', { params: { class_id: classId } })
}

export function batchSubmitScore(data) {
  return request.post('/score/batch-submit', data)
}

// 以下为原有接口
export function getClassesWithStudents() {
  return request.get('/score/classes-with-students')
}
export function getStudentScore(studentId) {
  return request.get(`/score/student/${studentId}`)
}
export function submitScore(data) {
  return request.post('/score/submit', data)
}
export function getScoreRanking() {
  return request.get('/score/ranking')
}