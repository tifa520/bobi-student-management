/**
 * 系统设置 API
 * 使用后端标准 RESTful 路径
 */

import request from './request'

// ========== 支付方式 ==========

/**
 * 获取支付方式列表
 * @returns {Promise<{code: number, data: string[]}>}
 */
export function getPaymentMethods() {
  return request.get('/payment-methods')
}

/**
 * 更新支付方式列表
 * @param {string[]} methods 支付方式数组
 * @returns {Promise}
 */
export function updatePaymentMethods(methods) {
  return request.put('/config/payment_methods', { value: methods })
}

// ========== 商品类别 ==========

/**
 * 获取商品类别列表
 * @returns {Promise<{code: number, data: string[]}>}
 */
export function getItemCategories() {
  return request.get('/item-categories')
}

/**
 * 更新商品类别列表
 * @param {string[]} categories 商品类别数组
 * @returns {Promise}
 */
export function updateItemCategories(categories) {
  return request.put('/config/item_categories', { value: categories })
}

// ========== 积分汇率 ==========

/**
 * 获取积分汇率
 * @returns {Promise<{code: number, data: number}>}
 */
export function getExchangeRate() {
  return request.get('/exchange-rate')
}

/**
 * 更新积分汇率
 * @param {number} rate 汇率值（1元 = ? 积分）
 * @returns {Promise}
 */
export function updateExchangeRate(rate) {
  return request.put('/config/exchange_rate', { value: rate })
}

// ========== 登录背景 ==========

/**
 * 获取登录页背景图
 * @returns {Promise<{code: number, data: {url: string}}>}
 */
export function getLoginBg() {
  return request.get('/upload/login-bg')
}

/**
 * 上传登录页背景图
 * @param {FormData} formData 包含图片文件的 FormData
 * @returns {Promise}
 */
export function uploadLoginBg(formData) {
  return request.post('/upload/login-bg', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}