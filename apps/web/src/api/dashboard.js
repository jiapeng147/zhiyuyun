import request from '../utils/request'

export function getDashboardSummary(params) {
  return request({
    url: '/dashboard/summary',
    method: 'get',
    params
  })
}

export function getDashboardSalesTrend(params) {
  return request({
    url: '/dashboard/sales-trend',
    method: 'get',
    params
  })
}

// 向后兼容：旧调用名保留给数据面板和移动端统计。
export const getDashboardStats = getDashboardSummary
