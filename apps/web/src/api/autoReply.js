import request from '../utils/request'
import { pageParams } from '../utils/apiData.js'

export function getAutoReplyRules(params = {}) {
  return request({ url: '/auto-reply/rules', method: 'get', params: pageParams(params) })
}
