import request from '../utils/request.js'

export const amapInputTips = data => request.post('/amap/inputtips', data)
export const uploadImage = (accountId, file) => {
  const form = new FormData()
  form.append('accountId', String(accountId))
  form.append('file', file)
  return request.post('/image/upload', form)
}
