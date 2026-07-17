import request from '../utils/request.js'

// === 用户管理 ===
export const listUsers = () => request.get('/admin/users')
export const updateUser = (id, data) => request.put(`/admin/users/${id}`, data)
export const createUser = (data) => request.post('/admin/users', data)
export const resetPassword = (id, newPassword) =>
  request.post(`/admin/users/${id}/reset-password`, { newPassword })

// === 平台概览 ===
export const getOverview = () => request.get('/admin/overview')

// === 套餐管理 (平台负责人) ===
export const adminListPlans = () => request.get('/admin/plans')
export const adminCreatePlan = (data) => request.post('/admin/plans', data)
export const adminUpdatePlan = (id, data) => request.put(`/admin/plans/${id}`, data)
export const adminDeletePlan = (id) => request.delete(`/admin/plans/${id}`)

// === 订阅与账单 ===
export const adminListSubscriptions = () => request.get('/admin/subscriptions')
export const adminListBillingOrders = (params = {}) => request.get('/admin/billing-orders', { params })
export const adminGetBillingOverview = () => request.get('/admin/billing-overview')
export const adminListUsageDaily = (params = {}) => request.get('/admin/usage-daily', { params })
export const adminListQuotaEvents = (params = {}) => request.get('/admin/quota-events', { params })
export const adminListBillingCoupons = () => request.get('/admin/billing-coupons')
export const adminCreateBillingCoupon = (data) => request.post('/admin/billing-coupons', data)
export const adminUpdateBillingCoupon = (id, data) => request.put(`/admin/billing-coupons/${id}`, data)
export const adminDeleteBillingCoupon = (id) => request.delete(`/admin/billing-coupons/${id}`)
export const adminGetBillingSettings = () => request.get('/admin/billing-settings')
export const adminSetBillingSettings = (data) => request.put('/admin/billing-settings', data)
export const adminGetUserBilling = (id) => request.get(`/admin/users/${id}/billing`)
export const adminGetUserProfile = (id) => request.get(`/admin/users/${id}/profile`)
export const adminActivateSubscription = (id, data) => request.post(`/admin/users/${id}/subscription`, data)
export const adminMarkBillingOrderPaid = (id, data = {}) => request.post(`/admin/billing-orders/${id}/mark-paid`, data)
export const adminCloseBillingOrder = (id, data = {}) => request.post(`/admin/billing-orders/${id}/close`, data)
export const adminRefundBillingOrder = (id, data = {}) => request.post(`/admin/billing-orders/${id}/refund`, data)

// === 注册开关 + SMTP ===
export const getRegistration = () => request.get('/admin/registration')
export const setRegistration = (enabled) => request.put('/admin/registration', { enabled })
export const getEmailConfig = () => request.get('/admin/email-config')
export const setEmailConfig = (data) => request.put('/admin/email-config', data)

// === 公开套餐列表 (注册页用) ===
export const getPublicPlans = () => request.get('/auth/plans', { suppressGlobalError: true })
