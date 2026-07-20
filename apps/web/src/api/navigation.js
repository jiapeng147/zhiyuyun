import request from '../utils/request'

export function getNavigationNotifications(params) {
  return request({
    url: '/navigation/notifications',
    method: 'get',
    params
  })
}
