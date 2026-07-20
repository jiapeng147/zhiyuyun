import request from '../utils/request.js'

/**
 * 读取指定分类的业务配置
 * @param {string} category  ai-customer-service | message-settings | delivery-settings | product-op-settings
 */
export function getBusinessSettings(category, requestConfig = {}) {
  return request.get(`/business-settings/${encodeURIComponent(category)}`, requestConfig)
}

/**
 * 保存指定分类的业务配置
 */
export function saveBusinessSettings(category, data) {
  return request.post(`/business-settings/${encodeURIComponent(category)}`, data)
}

/**
 * 验证 AI 客服回复
 */
export function testAiCustomerService(message) {
  return request.post('/business-settings/ai-customer-service/test', { message })
}

/**
 * 获取 AI 客服配置的默认值（用于"恢复默认"按钮）。
 */
export function getAiCsDefaults() {
  return request.get('/business-settings/ai-customer-service/defaults')
}

/**
 * 上传知识库文件，由 AI 自动提取回复规则。
 * @param {File} file 用户选择的文件（.md/.ppt/.pptx/.xlsx/.xls/.csv）
 */
export function uploadKnowledgeBase(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/business-settings/ai-customer-service/upload-knowledge', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  })
}
