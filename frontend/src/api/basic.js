import request from './request'

// 课程
export function getCourseList(params) {
  return request.get('/courses', { params })
}
export function getCourseListSimple() {
  return request.get('/courses/list')
}
export function getCourseDetail(id) {
  return request.get(`/courses/${id}`)
}
export function createCourse(params) {
  return request.post('/courses', null, { params })
}
export function updateCourse(id, params) {
  return request.put(`/courses/${id}`, null, { params })
}
export function deleteCourse(id) {
  return request.delete(`/courses/${id}`)
}

// 班级
export function getClassList(params) {
  return request.get('/classes', { params })
}
export function getClassesByCourse(courseId) {
  return request.get(`/classes/by-course/${courseId}`)
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
export function getClassAttendance(classId, params) {
  return request.get(`/classes/${classId}/attendance`, { params })
}
export function createSchedule(classId, params) {
  return request.post(`/classes/${classId}/schedules`, null, { params })
}
export function updateSchedule(scheduleId, params) {
  return request.put(`/classes/schedules/${scheduleId}`, null, { params })
}
export function deleteSchedule(scheduleId) {
  return request.delete(`/classes/schedules/${scheduleId}`)
}

// 教师
export function getTeacherList() {
  return request.get('/teachers')
}
export function createTeacher(params) {
  return request.post('/teachers', null, { params })
}
export function updateTeacher(id, params) {
  return request.put(`/teachers/${id}`, null, { params })
}
export function deleteTeacher(id) {
  return request.delete(`/teachers/${id}`)
}
export function updateTeacherStatus(id, enabled) {
  return request.put(`/teachers/${id}/status`, null, { params: { enabled } })
}
export function getEnabledTeachers() {
  return request.get('/teachers/enabled')
}

// 教室
export function getClassroomList() {
  return request.get('/classrooms')
}
export function getEnabledClassrooms() {
  return request.get('/classrooms/enabled')
}
export function updateClassroomStatus(id, enabled) {
  return request.put(`/classrooms/${id}/status`, null, { params: { enabled } })
}
export function createClassroom(params) {
  return request.post('/classrooms', null, { params })
}
export function updateClassroom(id, params) {
  return request.put(`/classrooms/${id}`, null, { params })
}
export function deleteClassroom(id) {
  return request.delete(`/classrooms/${id}`)
}

// ========== 课程套餐管理 ==========
export function getCoursePackages(courseId) {
  return request.get(`/courses/${courseId}/packages`)
}

export function createPackage(data) {
  return request.post('/packages', data)
}

export function updatePackage(packageId, data) {
  return request.put(`/packages/${packageId}`, data)
}

export function deletePackage(packageId) {
  return request.delete(`/packages/${packageId}`)
}