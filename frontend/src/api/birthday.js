/**
 * 生日提醒相关 API
 */
import request from './request'

/**
 * 获取指定月份的生日学员
 * @param {number} year 年份
 * @param {number} month 月份
 * @returns {Promise}
 */
export function getBirthdaysByMonth(year, month) {
  return request.get('/students/birthdays', {
    params: { year, month }
  })
}