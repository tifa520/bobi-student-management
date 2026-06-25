// frontend/src/api/course.js
import request from './request'

// ========== 课程管理 API ==========

/**
 * 获取课程列表（分页）
 */
export function getCourseList(params) {
  return request.get('/courses', { params })
}

/**
 * 获取课程列表（简单列表，用于下拉选择）
 */
export function getCourseListSimple() {
  return request.get('/courses/list')
}

/**
 * 获取课程详情
 */
export function getCourseDetail(id) {
  return request.get(`/courses/${id}`)
}

/**
 * 创建课程
 */
export function createCourse(data) {
  return request.post('/courses', data)   // data 中包含 stages
}

/**
 * 更新课程
 */
export function updateCourse(id, data) {
  return request.put(`/courses/${id}`, data)
}

/**
 * 删除课程
 */
export function deleteCourse(id) {
  return request.delete(`/courses/${id}`)
}


// ========== ★ 课阶管理 API（新增） ==========

/**
 * 获取课程下的课阶列表
 * @param {number} courseId - 课程ID
 * @param {Object} params - { is_active }
 */
export function getCourseStages(courseId, params) {
  return request.get(`/courses/${courseId}/stages`, { params })
}

/**
 * 创建课阶
 * @param {number} courseId - 课程ID
 * @param {Object} data - 课阶数据
 */
export function createStage(courseId, data) {
  return request.post(`/courses/${courseId}/stages`, data)
}

/**
 * 更新课阶
 * @param {number} courseId - 课程ID
 * @param {number} stageId - 课阶ID
 * @param {Object} data - 更新数据
 */
export function updateStage(courseId, stageId, data) {
  return request.put(`/courses/${courseId}/stages/${stageId}`, data)
}

/**
 * 删除课阶
 * @param {number} courseId - 课程ID
 * @param {number} stageId - 课阶ID
 */
export function deleteStage(courseId, stageId) {
  return request.delete(`/courses/${courseId}/stages/${stageId}`)
}


// ========== 课程套餐 API ==========

/**
 * 获取课程下的套餐列表
 */
export function getCoursePackages(courseId) {
  return request.get(`/courses/${courseId}/packages`)
}

/**
 * 创建套餐
 */
export function createPackage(data) {
  return request.post('/packages', data)
}

/**
 * 更新套餐
 */
export function updatePackage(packageId, data) {
  return request.put(`/packages/${packageId}`, data)
}

/**
 * 删除套餐
 */
export function deletePackage(packageId) {
  return request.delete(`/packages/${packageId}`)
}