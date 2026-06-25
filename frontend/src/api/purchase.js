import request from './request'

export function getPurchaseRecords(params) {
  return request.get('/purchase/records', { params })
}
export function createPurchase(data) {
  return request.post('/purchase/create', data)
}