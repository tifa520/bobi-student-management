/**
 * 杂费记录相关 API
 */
import request from './request'

/**
 * 获取杂费记录列表
 * @param {Object} params 查询参数
 * @returns {Promise}
 */
export function getMiscFees(params) {
  return request.get('/misc-fees', { params })
}

/**
 * 缴纳杂费
 * @param {number} feeId 费用记录ID
 * @param {number} amount 缴费金额
 * @param {string} paymentMethod 支付方式
 * @returns {Promise}
 */
export function payMiscFee(feeId, amount, paymentMethod) {
  return request.post(`/misc-fees/${feeId}/pay`, null, {
    params: { amount, payment_method: paymentMethod }
  })
}