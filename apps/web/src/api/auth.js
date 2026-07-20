import request from '../utils/request.js'
import { clearAuth } from '../utils/auth.js'

// Login owns an inline, focus-adjacent error state. Suppress the global status
// banner for this request so one failure is not announced twice to users and
// assistive technology.
export const login = data => request.post('/auth/login', data, { suppressGlobalError: true })

// 智鱼云: 自助注册
export const sendRegisterCode = data => request.post('/auth/register/send-code', data, { suppressGlobalError: true })
export const register = data => request.post('/auth/register', data, { suppressGlobalError: true })

export async function logout() {
  try {
    return await request.post('/auth/logout', {})
  } finally {
    clearAuth()
  }
}
