import request from './request'

export function getGiftExchanges(params) {
  return request.get('/gift/exchanges', { params })
}
export function exchangeGift(data) {
  return request.post('/gift/exchange', data)
}