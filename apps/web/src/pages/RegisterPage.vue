<template>
  <AuthShell
    page-key="register"
    title-lead="开通智鱼云"
    title-accent="开启多账号"
    title-tail="商用运营"
    description="邮箱验证码开通账户，开通即赠基础体验套餐。"
    legal-description="该页面用于说明智鱼云注册、身份验证与账号安全相关规则。"
    @navigate="emit('navigate', $event)"
  >
    <div v-if="errorMsg" class="form-error" role="alert" aria-live="assertive">{{ errorMsg }}</div>
    <div v-if="okMsg" class="form-error form-success" role="status">{{ okMsg }}</div>

    <form class="auth-form" @submit.prevent="handleRegister">
      <!-- 邮箱 -->
      <label class="auth-field" for="reg-email">
        <TrustedSvg class="auth-field-icon" :markup="authIcons.user" />
        <span class="auth-sr-only">邮箱</span>
        <input id="reg-email" v-model.trim="email" type="email" autocomplete="email" placeholder="请输入邮箱" required autofocus />
      </label>

      <!-- 验证码 + 获取按钮 -->
      <div class="auth-field auth-field-with-action">
        <label class="auth-field-control" for="reg-code">
          <TrustedSvg class="auth-field-icon" :markup="authIcons.lock" />
          <span class="auth-sr-only">验证码</span>
          <input id="reg-code" v-model.trim="code" type="text" inputmode="numeric" maxlength="6" placeholder="邮箱验证码" required />
        </label>
        <button type="button" class="auth-code-btn" :disabled="countdown > 0 || sending || !email" @click="sendCode">
          {{ countdown > 0 ? countdown + 's' : (sending ? '发送中' : '获取验证码') }}
        </button>
      </div>

      <!-- 用户名 -->
      <label class="auth-field" for="reg-username">
        <TrustedSvg class="auth-field-icon" :markup="authIcons.user" />
        <span class="auth-sr-only">用户名</span>
        <input id="reg-username" v-model.trim="username" type="text" autocomplete="username" placeholder="用户名（3-32位，用于登录）" required />
      </label>

      <!-- 密码 -->
      <div class="auth-field auth-field-with-action">
        <label class="auth-field-control" for="reg-password">
          <TrustedSvg class="auth-field-icon" :markup="authIcons.lock" />
          <span class="auth-sr-only">密码</span>
          <input id="reg-password" v-model="password" :type="showPwd ? 'text' : 'password'" autocomplete="new-password" placeholder="密码（至少8位，含字母和数字）" required />
        </label>
        <button type="button" class="auth-eye-btn" :aria-label="showPwd ? '隐藏密码' : '显示密码'" :aria-pressed="showPwd" @click="showPwd = !showPwd">
          <TrustedSvg :markup="showPwd ? authIcons.eyeOff : authIcons.eye" />
        </button>
      </div>

      <!-- 确认密码 -->
      <label class="auth-field" for="reg-password2">
        <TrustedSvg class="auth-field-icon" :markup="authIcons.lock" />
        <span class="auth-sr-only">确认密码</span>
        <input id="reg-password2" v-model="password2" :type="showPwd ? 'text' : 'password'" autocomplete="new-password" placeholder="确认密码" required />
      </label>

      <button class="auth-submit" type="submit" :disabled="!canSubmit" :aria-busy="loading">
        {{ loading ? '注册中...' : '注册并登录' }}
      </button>
    </form>

    <div class="auth-inline-row auth-register-login-row">
      <span class="auth-muted">已有账号？</span>
      <button type="button" class="auth-text-link" @click="emit('navigate', 'login')">去登录</button>
    </div>

    <div class="auth-agreement" role="note">
      注册即视为知悉：平台服务方尚未配置经审核的正式协议文本，商用前须补齐
      <button type="button" class="auth-text-link" @click="openDoc('用户协议')">用户协议</button>
      和
      <button type="button" class="auth-text-link" @click="openDoc('隐私政策')">隐私政策</button>。
    </div>
  </AuthShell>
</template>

<script setup>
import { computed, ref, onBeforeUnmount } from 'vue'
import { register, sendRegisterCode } from '../api/auth.js'
import AuthShell from '../components/auth/AuthShell.vue'
import TrustedSvg from '../components/TrustedSvg.vue'
import { authIcons, openLegalDoc } from '../components/auth/authContent.js'
import { friendlyError } from '../utils/friendlyError.js'

const emit = defineEmits(['navigate', 'login-success'])

const email = ref('')
const code = ref('')
const username = ref('')
const password = ref('')
const password2 = ref('')
const showPwd = ref(false)
const loading = ref(false)
const sending = ref(false)
const errorMsg = ref('')
const okMsg = ref('')
const countdown = ref(0)
let timer = null

const emailValid = computed(() => /.+@.+\..+/.test(email.value))
const canSubmit = computed(() => Boolean(
  !loading.value && emailValid.value && code.value && username.value.trim().length >= 3 &&
  password.value.length >= 8 && password.value === password2.value
))

function openDoc(title) {
  openLegalDoc(title, '该页面用于说明智鱼云注册、身份验证与账号安全相关规则。')
}

function startCountdown() {
  countdown.value = 60
  timer = setInterval(() => {
    countdown.value -= 1
    if (countdown.value <= 0) { clearInterval(timer); timer = null }
  }, 1000)
}
onBeforeUnmount(() => { if (timer) clearInterval(timer) })

async function sendCode() {
  errorMsg.value = ''; okMsg.value = ''
  if (!emailValid.value) { errorMsg.value = '请输入有效邮箱'; return }
  sending.value = true
  try {
    await sendRegisterCode({ email: email.value })
    okMsg.value = '验证码已发送，请查收邮箱（5分钟内有效）'
    startCountdown()
  } catch (error) {
    errorMsg.value = friendlyError(error, '验证码发送失败，请稍后重试')
  } finally {
    sending.value = false
  }
}

async function handleRegister() {
  if (loading.value) return
  errorMsg.value = ''; okMsg.value = ''
  if (!emailValid.value) { errorMsg.value = '请输入有效邮箱'; return }
  if (!code.value) { errorMsg.value = '请输入邮箱验证码'; return }
  if (username.value.trim().length < 3) { errorMsg.value = '用户名至少3位'; return }
  if (password.value.length < 8) { errorMsg.value = '密码至少8位'; return }
  if (password.value !== password2.value) { errorMsg.value = '两次输入的密码不一致'; return }

  loading.value = true
  try {
    const res = await register({
      email: email.value,
      code: code.value,
      username: username.value.trim(),
      password: password.value,
    })
    emit('login-success', { ...(res.data || {}), remember: true })
  } catch (error) {
    errorMsg.value = friendlyError(error, '注册失败，请检查信息后重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.form-success {
  color: var(--green);
  background: rgba(22, 191, 120, .08);
  border-color: rgba(22, 191, 120, .24);
}

.auth-code-btn {
  flex: 0 0 auto;
  height: 34px;
  padding: 0 12px;
  border: 1px solid rgba(37, 99, 235, .32);
  border-radius: 8px;
  background: #eef4ff;
  color: var(--primary);
  font-size: 13px;
  font-weight: 700;
  white-space: nowrap;
  transition: background-color 150ms ease, border-color 150ms ease, color 150ms ease, opacity 150ms ease;
}

.auth-code-btn:hover:not(:disabled) {
  border-color: rgba(37, 99, 235, .5);
  background: #e0ebff;
}

.auth-code-btn:disabled {
  opacity: .5;
  cursor: not-allowed;
}

.auth-muted {
  color: var(--muted);
  font-size: 13px;
  margin-right: 6px;
}

.auth-register-login-row {
  justify-content: center;
  margin-top: 14px;
}

@media (max-width: 520px) {
  .auth-code-btn {
    height: 32px;
    padding: 0 10px;
    font-size: 12px;
  }
}
</style>
