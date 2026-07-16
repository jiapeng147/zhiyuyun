import request from '../utils/request.js'

export const getMyBilling = () => request.get('/billing/me')
export const getPaymentConfig = () => request.get('/billing/payment-config')
export const getBillingPlans = () => request.get('/billing/plans')
export const listMyUsageDaily = (params = {}) => request.get('/billing/usage-daily', { params })
export const listMyQuotaEvents = (params = {}) => request.get('/billing/quota-events', { params })
export const listBillingOrders = (params = {}) => request.get('/billing/orders', { params })
export const previewBillingCoupon = (data) => request.post('/billing/coupons/preview', data)
export const createBillingOrder = (data) => request.post('/billing/orders', data)
export const submitBillingPaymentProof = (id, data) => request.post(`/billing/orders/${id}/payment-proof`, data)
export const closeBillingOrder = (id, data = {}) => request.post(`/billing/orders/${id}/close`, data)
