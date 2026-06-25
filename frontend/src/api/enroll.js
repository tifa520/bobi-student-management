// frontend/src/api/enroll.js
import request from './request'

export const enrollApi = {
  step1(data, sessionId) {
    return request.post('/step1', data, {
      headers: sessionId ? { 'enroll-session': sessionId } : {}
    })
  },
  step2(data, sessionId) {
    return request.post('/step2', data, {
      headers: { 'enroll-session': sessionId }
    })
  },
  step3Submit(data, sessionId) {
    return request.post('/step3/submit', data, {
      headers: { 'enroll-session': sessionId }
    })
  },
  getSession() {
    return request.get('/session')
  }
}

export function searchExistingStudents(keyword) {
  return request.get('/student/search', { params: { keyword } })
}

export function quickCreateStudent(data) {
  return request.post('/student/students', data)
}