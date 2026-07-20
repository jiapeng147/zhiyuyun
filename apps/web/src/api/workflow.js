import request from '../utils/request.js'

export const aiRewriteGoods = data => request.post('/ai-tools/rewrite-goods', data || {})
