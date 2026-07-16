import request from '../utils/request.js'

export const getMyBilling = () => request.get('/billing/me')
export const getBillingPlans = () => request.get('/billing/plans')
export const listBillingOrders = (params = {}) => request.get('/billing/orders', { params })
export const createBillingOrder = (data) => request.post('/billing/orders', data)
