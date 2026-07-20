import request from '../utils/request.js'

export const getAiProviderStatus = () => request.get('/ai-tools/status')
export const suggestCategoryByAi = (data) => request.post('/ai-tools/category-suggest', data)
