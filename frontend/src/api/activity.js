import request from './request'

// ==================== 活动 CRUD ====================

/**
 * 获取活动列表（支持分页、筛选）
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码
 * @param {number} params.page_size - 每页数量
 * @param {string} params.keyword - 搜索关键词
 * @param {string} params.status - 活动状态
 * @param {string} params.activity_type - 活动类型
 * @param {boolean} params.is_featured - 是否推荐
 * @param {boolean} params.is_archived - 是否归档
 */
export function getActivityList(params) {
  return request.get('/activity/activities', { params })
}

/**
 * 获取活动详情
 * @param {number} id - 活动ID
 */
export function getActivityDetail(id) {
  return request.get(`/activity/activities/${id}`)
}

/**
 * 创建活动
 * @param {Object} data - 活动数据
 */
export function createActivity(data) {
  return request.post('/activity/activities', data)
}

/**
 * 更新活动
 * @param {number} id - 活动ID
 * @param {Object} data - 更新数据
 */
export function updateActivity(id, data) {
  return request.put(`/activity/activities/${id}`, data)
}

/**
 * 删除活动
 * @param {number} id - 活动ID
 */
export function deleteActivity(id) {
  return request.delete(`/activity/activities/${id}`)
}

// ==================== 活动状态操作 ====================

/**
 * 发布活动（草稿 -> 报名中）
 * @param {number} id - 活动ID
 */
export function publishActivity(id) {
  return request.post(`/activity/activities/${id}/publish`)
}

/**
 * 取消活动（自动退费）
 * @param {number} id - 活动ID
 */
export function cancelActivity(id) {
  return request.post(`/activity/activities/${id}/cancel`)
}

/**
 * 归档活动
 * @param {number} id - 活动ID
 */
export function archiveActivity(id) {
  return request.post(`/activity/activities/${id}/archive`)
}

/**
 * 取消归档
 * @param {number} id - 活动ID
 */
export function unarchiveActivity(id) {
  return request.post(`/activity/activities/${id}/unarchive`)
}

// ==================== 活动报名管理 ====================

/**
 * 获取活动报名列表
 * @param {number} activityId - 活动ID
 */
export function getActivityRegistrations(activityId) {
  return request.get(`/activity/activities/${activityId}/registrations`)
}

/**
 * 学员报名
 * @param {number} activityId - 活动ID
 * @param {Object} data - 报名数据 { student_id, is_attending, payment_type, cash_payment_method }
 */
export function registerActivity(activityId, data) {
  return request.post(`/activity/activities/${activityId}/register`, data)
}

/**
 * 更新报名信息
 * @param {number} registrationId - 报名ID
 * @param {Object} data - 更新数据
 */
export function updateRegistration(registrationId, data) {
  return request.put(`/activity/registrations/${registrationId}`, data)
}

/**
 * 删除报名记录（仅限未缴费）
 * @param {number} registrationId - 报名ID
 */
export function deleteRegistration(registrationId) {
  return request.delete(`/activity/registrations/${registrationId}`)
}

/**
 * 取消报名（退费）
 * @param {number} registrationId - 报名ID
 * @param {string} reason - 取消原因
 */
export function cancelRegistration(registrationId, reason = '') {
  return request.post(`/activity/registrations/${registrationId}/cancel`, null, { params: { reason } })
}

/**
 * 批量更新报名缴费状态
 * @param {number} activityId - 活动ID
 * @param {number[]} registrationIds - 报名ID列表
 * @param {boolean} isPaid - 是否已缴费
 */
export function batchPayRegistrations(activityId, registrationIds, isPaid) {
  return request.put(`/activity/activities/${activityId}/batch-pay`, registrationIds, { params: { is_paid: isPaid } })
}

/**
 * 批量报名
 * @param {number} activityId - 活动ID
 * @param {number[]} studentIds - 学员ID列表
 * @param {Object} options - 报名选项
 */
export function batchRegister(activityId, studentIds, options = {}) {
  return request.post(`/activity/activities/${activityId}/batch-register`, studentIds, {
    params: {
      is_attending: options.is_attending || '是',
      payment_type: options.payment_type || 'cash',
      cash_payment_method: options.cash_payment_method || 'wechat'
    }
  })
}

// ==================== 退费管理 ====================

/**
 * 退费（单个报名）
 * @param {number} registrationId - 报名ID
 * @param {Object} params - { refund_amount, refund_points, payment_method }
 */
export function refundRegistration(registrationId, params) {
  return request.post(`/activity/registrations/${registrationId}/refund`, null, { params })
}

// ==================== 奖品管理 ====================

/**
 * 获取奖品库列表
 * @param {Object} params - { keyword }
 */
export function getPrizes(params) {
  return request.get('/activity/prizes', { params })
}

/**
 * 创建奖品
 * @param {Object} data - 奖品数据
 */
export function createPrize(data) {
  return request.post('/activity/prizes', data)
}

/**
 * 更新奖品
 * @param {number} id - 奖品ID
 * @param {Object} data - 更新数据
 */
export function updatePrize(id, data) {
  return request.put(`/activity/prizes/${id}`, data)
}

/**
 * 删除奖品
 * @param {number} id - 奖品ID
 */
export function deletePrize(id) {
  return request.delete(`/activity/prizes/${id}`)
}

/**
 * 设置活动奖项
 * @param {number} activityId - 活动ID
 * @param {Array} prizes - 奖项列表 [{ prize_id, quantity }]
 */
export function setActivityPrizes(activityId, prizes) {
  return request.put(`/activity/activities/${activityId}/prizes`, prizes)
}

/**
 * 执行抽奖
 * @param {number} activityId - 活动ID
 */
export function doLottery(activityId) {
  return request.post(`/activity/activities/${activityId}/lottery`)
}

/**
 * 获取中奖名单
 * @param {number} activityId - 活动ID
 */
export function getWinners(activityId) {
  return request.get(`/activity/activities/${activityId}/winners`)
}

/**
 * 更新中奖记录
 * @param {number} winnerId - 中奖记录ID
 * @param {Object} data - { status, delivery_method, delivery_info }
 */
export function updateWinner(winnerId, data) {
  return request.put(`/activity/winners/${winnerId}`, data)
}

/**
 * 删除中奖记录
 * @param {number} winnerId - 中奖记录ID
 */
export function deleteWinner(winnerId) {
  return request.delete(`/activity/winners/${winnerId}`)
}

// ==================== 导入导出 ====================

/**
 * 导出报名名单（Excel）
 * @param {number} activityId - 活动ID
 * @returns {Promise<Blob>}
 */
export function exportRegistrations(activityId) {
  return request.get(`/activity/activities/${activityId}/registrations/export`, { responseType: 'blob' })
}

/**
 * 导入报名名单（Excel）
 * @param {number} activityId - 活动ID
 * @param {FormData} formData - 包含文件的 FormData
 */
export function importRegistrations(activityId, formData) {
  return request.post(`/activity/activities/${activityId}/registrations/import`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

/**
 * 导出中奖名单（Excel）
 * @param {number} activityId - 活动ID
 */
export function exportWinners(activityId) {
  return request.get(`/activity/activities/${activityId}/winners/export`, { responseType: 'blob' })
}

// ==================== 数据统计 ====================

/**
 * 获取活动统计（单个活动）
 * @param {number} activityId - 活动ID
 */
export function getActivityStats(activityId) {
  return request.get(`/activity/activities/${activityId}/stats`)
}

/**
 * 获取整体活动统计概览
 * @param {Object} params - { start_date, end_date }
 */
export function getActivitiesOverview(params) {
  return request.get('/activity/stats/overview', { params })
}

// ==================== 活动图片上传 ====================

/**
 * 上传活动图片
 * @param {FormData} formData - 包含图片文件的 FormData
 */
export function uploadActivityImage(formData) {
  return request.post('/activity/upload-image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}