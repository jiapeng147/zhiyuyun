import request from '../utils/request.js'

// 超管商业管理
export const listUsers = () => request.get('/admin/users')
export const updateUser = (id, data) => request.put(`/admin/users/${id}`, data)
export const getRegistration = () => request.get('/admin/registration')
export const setRegistration = (enabled) => request.put('/admin/registration', { enabled })
export const getEmailConfig = () => request.get('/admin/email-config')
export const setEmailConfig = (data) => request.put('/admin/email-config', data)
export const getPlans = () => request.get('/auth/plans', { suppressGlobalError: true })
