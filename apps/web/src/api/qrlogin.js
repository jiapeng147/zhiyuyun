import request from '../utils/request.js'

const qrRequestOptions = {
  uiMode: 'silent',
  suppressGlobalError: true,
}

export const generateQrLogin = (data = {}) => request.post('/qrlogin/generate', data, {
  ...qrRequestOptions,
  timeout: 70000,
})
export const getQrLoginStatus = (sessionId, data = {}) => request.post(`/qrlogin/status/${encodeURIComponent(sessionId)}`, data, {
  ...qrRequestOptions,
  timeout: 20000,
})
export const cleanupQrLogin = () => request.post('/qrlogin/cleanup', {}, qrRequestOptions)
