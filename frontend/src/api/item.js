/**
 * 物品管理相关 API
 */
import request from './request'

// ========== 物品基础操作 ==========

/**
 * 获取物品列表
 * @param {Object} params 查询参数
 * @returns {Promise}
 */
export function getItems(params) {
  return request.get('/items', { params })
}

/**
 * 创建物品
 * @param {Object} data 物品数据
 * @returns {Promise}
 */
export function createItem(data) {
  return request.post('/items', data)
}

/**
 * 更新物品
 * @param {number} itemId 物品ID
 * @param {Object} data 更新数据
 * @returns {Promise}
 */
export function updateItem(itemId, data) {
  return request.put(`/items/${itemId}`, data)
}

/**
 * 删除物品
 * @param {number} itemId 物品ID
 * @returns {Promise}
 */
export function deleteItem(itemId) {
  return request.delete(`/items/${itemId}`)
}

// ========== 库存管理 ==========

/**
 * 物品入库
 * @param {number} itemId 物品ID
 * @param {Object} params 入库参数
 * @returns {Promise}
 */
export function stockIn(itemId, params) {
  return request.post(`/items/${itemId}/stock-in`, null, { params })
}

/**
 * 销售物品
 * @param {number} itemId 物品ID
 * @param {Object} params 销售参数
 * @returns {Promise}
 */
export function sellItem(itemId, params) {
  return request.post(`/items/${itemId}/sell`, null, { params })
}

/**
 * 兑换礼品
 * @param {number} itemId 物品ID
 * @param {Object} params 兑换参数
 * @returns {Promise}
 */
export function exchangeGift(itemId, params) {
  return request.post(`/items/${itemId}/exchange`, null, { params })
}

// ========== 批次管理 ==========

/**
 * 获取物品批次列表
 * @param {number} itemId 物品ID
 * @returns {Promise}
 */
export function getItemBatches(itemId) {
  return request.get(`/items/${itemId}/batches`)
}

/**
 * 获取库存流水记录
 * @param {Object} params 查询参数
 * @returns {Promise}
 */
export function getInventoryRecords(params) {
  return request.get('/inventory/records', { params })
}

/**
 * 销售退款
 * @param {number} saleId 销售记录ID
 * @param {Object} params 退款参数
 * @returns {Promise}
 */
export function refundItemSale(saleId, params) {
  return request.post(`/inventory/sales/${saleId}/refund`, null, { params })
}