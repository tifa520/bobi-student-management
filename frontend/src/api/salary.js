import request from './request'

// 规则管理
export function getSalaryRules(params) {
  return request.get('/salary/rules', { params })
}
export function createSalaryRule(data) {
  return request.post('/salary/rules', data)
}
export function updateSalaryRule(id, data) {
  return request.put(`/salary/rules/${id}`, data)
}
export function deleteSalaryRule(id) {
  return request.delete(`/salary/rules/${id}`)
}

// 薪酬计算
export function calculateSalary(teacherId, settlementMonth) {
  return request.post('/salary/calculate', null, {
    params: { teacher_id: teacherId, settlement_month: settlementMonth }
  })
}
export function getSalaryList(params) {
  return request.get('/salary/salaries', { params })
}
export function getSalaryDetail(id) {
  return request.get(`/salary/salaries/${id}`)
}
export function adjustSalary(id, adjustAmount, reason) {
  return request.post(`/salary/salaries/${id}/adjust`, { adjust_amount: adjustAmount, reason })
}
export function confirmSalary(salaryId) {
  return request.post(`/salary/salaries/${salaryId}/confirm`)
}
export function paySalary(salaryId, paymentMethod, remark) {
  return request.post(`/salary/salaries/${salaryId}/pay`, { payment_method: paymentMethod, remark })
}
