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
