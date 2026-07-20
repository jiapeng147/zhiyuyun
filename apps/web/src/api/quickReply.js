import request from '../utils/request.js'

// 快捷回复模板 CRUD
export function listQuickReplyTemplates(params = {}) {
  return request({ url: '/quick-reply/templates', method: 'get', params })
}

export function saveQuickReplyTemplate(data) {
  return request({
    url: '/quick-reply/templates',
    method: 'post',
    data
  })
}

export function deleteQuickReplyTemplate(id) {
  return request({ url: `/quick-reply/templates/${id}`, method: 'delete' })
}
