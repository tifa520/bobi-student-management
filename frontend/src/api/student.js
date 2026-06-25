import request from './request'

// 学员列表（后端分页）
export function getStudentList(params) {
  return request.get('/student/students', { params })
}

// 已结业学员列表
export function getGraduatedStudents(params) {
  return request.get('/student/graduated-students', { params })
}

// 搜索学员（用于自动补全）
export function searchStudents(keyword) {
  return request.get('/student/search', { params: { keyword } })
}

// 学员详情
export function getStudentDetail(id) {
  return request.get(`/student/student/${id}`)
}

// 学员课程账户（课时、金额等）
export function getStudentCourses(id) {
  return request.get(`/student/student/${id}/courses`)
}

// 创建学员
export function createStudent(data) {
  return request.post('/student/students', data)
}

// 更新学员信息
export function updateStudent(id, data) {
  return request.put(`/student/student/${id}`, data)
}

// 增减课时（付费课时）
export function adjustHours(studentId, params) {
  return request.post(`/student/student/${studentId}/adjust-hours`, null, { params })
}

// 分班
export function assignClass(studentId, params) {
  return request.post(`/student/student/${studentId}/assign-class`, null, { params })
}

// 转班
export function transferClass(studentId, params) {
  return request.post(`/student/student/${studentId}/transfer-class`, null, { params })
}

// 退班
export function dropClass(studentId, params) {
  return request.post(`/student/student/${studentId}/drop-class`, null, { params })
}

// 转课时
export function transferHours(studentId, data) {
  return request.post(`/student/student/${studentId}/transfer-hours`, data)
}

// 增减赠送课时
export function giftHours(studentId, params) {
  return request.post(`/student/student/${studentId}/gift-hours`, null, { params })
}

// 结业
export function graduateStudent(studentId, params) {
  return request.post(`/student/student/${studentId}/graduate`, null, { params })
}

// 退费
export function refundStudent(studentId, params) {
  return request.post(`/student/student/${studentId}/refund`, null, { params })
}

// 导出学员
export function exportStudents() {
  return request.get('/student/students/export', { responseType: 'blob' })
}

// 退费预览
export function getRefundPreview(studentId, params) {
  return request.get(`/student/student/${studentId}/refund-preview`, { params })
}

// 补缴尾款（按课程）
export function repayArrears(studentId, params) {
  return request.post(`/student/student/${studentId}/repay-arrears`, null, { params })
}

// 手动设置有效期（扩展）
export function updateCourseValidity(studentId, courseId, validityDays) {
  return request.put(`/student/student/${studentId}/course/${courseId}/validity`, null, {
    params: { validity_days: validityDays }
  })
}

// 下载导入模板
export function downloadImportTemplate() {
  return request.get('/student/students/import-template', { responseType: 'blob' })
}

// 上传头像
export function uploadAvatar(studentId, formData) {
  return request.post(`/student/student/${studentId}/avatar`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

// 删除头像
export function deleteAvatar(studentId) {
  return request.delete(`/student/student/${studentId}/avatar`)
}

// 上传卡片背景图
export function uploadCardBackground(studentId, formData) {
  return request.post(`/student/student/${studentId}/card-background`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

// 删除卡片背景图
export function deleteCardBackground(studentId) {
  return request.delete(`/student/student/${studentId}/card-background`)
}

// 计算转出金额预览
export function getTransferAmountPreview(studentId, params) {
  return request.get(`/student/student/${studentId}/transfer-preview`, { params })
}

// 手动延长有效期
export function extendValidity(studentId, courseId, extendDays, reason = '') {
  return request.post(`/student/student/${studentId}/extend-validity`, null, {
    params: { course_id: courseId, extend_days: extendDays, reason }
  })
}

// 获取聚合后的学员列表（按学员分组，支持分页和筛选）
export function getAggregatedStudents(params) {
  return request.get('/students-aggregated', { params })   // 修改此处
}