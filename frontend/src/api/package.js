// frontend/src/api/package.js
import request from './request'

/**
 * 获取课程套餐列表
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