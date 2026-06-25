// frontend/src/api/auth.js
import request from './request'

export function login(data) {
  return request.post('/auth/login', data)
}

export function logout() {
  return request.post('/auth/logout')
}

export function refreshToken(data) {
  return request.post('/auth/refresh', data)
}

export function getCurrentUser() {
  return request.get('/auth/me')
}

export function changePassword(data) {
  return request.post('/auth/change-password', data)
}

// ★ 新增：管理员账号相关接口 ★

/**
 * 检查系统中是否已存在管理员
 */
export function hasAdmin() {
  return request.get('/auth/has-admin')
}

/**
 * 创建管理员账号
 * @param {Object} data - { username, password, name, email, phone }
 */
export function createAdmin(data) {
  return request.post('/auth/create-admin', data)
}