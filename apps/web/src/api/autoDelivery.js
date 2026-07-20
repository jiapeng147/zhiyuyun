import request from '../utils/request'
import { pageParams } from '../utils/apiData.js'

// ─── 批量操作 ───
export function batchSetDeliveryRules(data) {
  return request({ url: '/auto-delivery/rules/batch', method: 'post', data })
}

// ─── 商品发货配置（按商品维度） ───
export function getGoodsDeliveryConfig(goodsId) {
  return request({ url: `/auto-delivery/goods/${goodsId}/config`, method: 'get' })
}

export function getGoodsDeliveryConfigs(goodsIds) {
  return request({
    url: '/auto-delivery/goods/configs/query',
    method: 'post',
    data: { goodsIds }
  })
}

export function saveGoodsDeliveryConfig(goodsId, data) {
  return request({ url: `/auto-delivery/goods/${goodsId}/config`, method: 'put', data })
}

// ─── 发货声明 ───
export function getDeliveryStatement() {
  return request({ url: '/auto-delivery/statement', method: 'get' })
}

export function saveDeliveryStatement(data) {
  return request({ url: '/auto-delivery/statement', method: 'put', data })
}

export function toggleDeliveryStatement(enabled) {
  return request({ url: '/auto-delivery/statement/toggle', method: 'patch', data: { enabled } })
}

export function previewDeliveryStatement(data) {
  return request({ url: '/auto-delivery/statement/preview', method: 'post', data })
}

// ─── 发货记录 ───
export function getDeliveryRecords(params = {}, config = {}) {
  return request({ ...config, url: '/auto-delivery/records', method: 'get', params: pageParams(params) })
}

export function getDeliveryRecordDetail(id) {
  return request({ url: `/auto-delivery/records/${id}`, method: 'get' })
}

// ─── 统计 / Dashboard ───
export function getDeliveryStats() {
  return request({ url: '/auto-delivery/stats', method: 'get' })
}

// 文本货源库
export function getDeliverySources(params = {}) {
  return request({ url: '/auto-delivery/sources', method: 'get', params: pageParams(params) })
}

export function createDeliverySource(data) {
  return request({ url: '/auto-delivery/sources', method: 'post', data })
}

export function updateDeliverySource(id, data) {
  return request({ url: `/auto-delivery/sources/${id}`, method: 'put', data })
}

export function deleteDeliverySource(id) {
  return request({ url: `/auto-delivery/sources/${id}`, method: 'delete' })
}

export function getDeliverySourceGoods(id, params = {}) {
  return request({ url: `/auto-delivery/sources/${id}/goods`, method: 'get', params })
}

export function recommendDeliverySourceGoods(id, params = {}) {
  return request({ url: `/auto-delivery/sources/${id}/recommend`, method: 'post', params })
}

export function applyDeliverySourceToGoods(id, data) {
  return request({ url: `/auto-delivery/sources/${id}/apply`, method: 'post', data })
}

export function removeDeliverySourceFromGoods(sourceId, goodsId) {
  return request({ url: `/auto-delivery/sources/${sourceId}/goods/${goodsId}`, method: 'delete' })
}
