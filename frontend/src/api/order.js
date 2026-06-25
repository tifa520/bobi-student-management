import request from './request'

export function getOrderList(params) {
  return request.get('/order/orders', { params })
}
export function invalidOrder(orderId) {
  return request.post(`/order/orders/${orderId}/invalid`)
}
export function batchRepay(data) {
  return request.post('/order/repay/batch', data)
}
export function exportOrders() {
  return request.get('/order/orders/export', { responseType: 'blob' })
}
export function getRepayRecords(params) {
  return request.get('/order/repay-records', { params })
}