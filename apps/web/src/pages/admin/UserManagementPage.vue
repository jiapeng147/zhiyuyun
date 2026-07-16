<template>
  <div class="user-mgmt-page">
    <PageHeader title="用户管理" desc="管理注册用户、套餐与自助注册开关（仅超级管理员）" />

    <div v-if="notice" :class="['global-notice', noticeType]" role="status">{{ notice }}</div>

    <!-- 注册开关 -->
    <CardPanel title="自助注册" desc="控制外部用户是否可以通过注册页自助注册账号" class="dashboard-section">
      <div class="reg-row">
        <div class="reg-info">
          <div class="reg-state">
            当前状态：<strong :class="regEnabled ? 'on' : 'off'">{{ regEnabled ? '已开放注册' : '已关闭注册' }}</strong>
          </div>
          <div class="reg-hint">
            开放后，任何人可在
            <code>/#/register</code>
            用邮箱验证码注册（默认赠免费版套餐）。<strong>请先在下方配置邮箱 SMTP</strong>，否则验证码无法发送。
          </div>
        </div>
        <ToggleSwitch :on="regEnabled" interactive :disabled="regBusy" @click="toggleRegistration" />
      </div>
    </CardPanel>

    <!-- 邮箱 SMTP -->
    <CardPanel title="邮箱 SMTP 配置" desc="用于发送注册/找回密码验证码。密码仅在服务端加密存储，不回显。" class="dashboard-section">
      <div class="form-grid">
        <label class="field">
          <span>SMTP 服务器</span>
          <input v-model.trim="email.smtpHost" class="input" placeholder="如 smtp.qq.com" />
        </label>
        <label class="field">
          <span>端口</span>
          <input v-model.number="email.smtpPort" class="input" type="number" placeholder="465" />
        </label>
        <label class="field">
          <span>发件邮箱账号</span>
          <input v-model.trim="email.smtpUser" class="input" placeholder="you@example.com" />
        </label>
        <label class="field">
          <span>授权码 / 密码</span>
          <input v-model="email.smtpPass" class="input" type="password" :placeholder="emailConfigured ? '已配置，留空则保留原值' : '邮箱授权码'" />
        </label>
        <label class="field">
          <span>发件人名称</span>
          <input v-model.trim="email.fromName" class="input" placeholder="智鱼云" />
        </label>
      </div>
      <div class="form-actions">
        <button class="btn primary" type="button" :disabled="emailBusy" @click="saveEmail">{{ emailBusy ? '保存中...' : '保存邮箱配置' }}</button>
      </div>
    </CardPanel>

    <!-- 用户列表 -->
    <CardPanel title="注册用户" :desc="`共 ${users.length} 个账号`" class="dashboard-section">
      <div class="table-wrap">
        <table class="table user-table">
          <thead>
            <tr>
              <th>ID</th><th>用户名</th><th>邮箱</th><th>角色</th><th>套餐</th>
              <th>账号配额</th><th>状态</th><th>注册时间</th><th>最近登录</th><th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="users.length === 0">
              <td colspan="10" class="empty-cell">暂无用户</td>
            </tr>
            <tr v-for="u in users" :key="u.id">
              <td>{{ u.id }}</td>
              <td><strong>{{ u.username }}</strong></td>
              <td>{{ u.email || '—' }}</td>
              <td>
                <span :class="['role-tag', u.role]">{{ u.role === 'superadmin' ? '超级管理员' : '普通用户' }}</span>
              </td>
              <td>
                <select
                  class="input plan-select"
                  :value="u.planCode"
                  :disabled="u.role === 'superadmin' || rowBusy === u.id"
                  @change="changePlan(u, $event.target.value)"
                >
                  <option v-for="p in plans" :key="p.code" :value="p.code">{{ p.name }}</option>
                </select>
              </td>
              <td>{{ u.maxAccounts }} 账号 / {{ u.aiDailyQuota }} AI</td>
              <td>
                <span :class="['status-dot', u.status === 1 ? 'ok' : 'off']"></span>
                {{ u.status === 1 ? '启用' : '禁用' }}
              </td>
              <td class="dim">{{ fmt(u.createdTime) }}</td>
              <td class="dim">{{ fmt(u.lastLoginTime) }}</td>
              <td>
                <button
                  v-if="u.role !== 'superadmin'"
                  class="btn small"
                  type="button"
                  :disabled="rowBusy === u.id"
                  @click="toggleStatus(u)"
                >{{ u.status === 1 ? '禁用' : '启用' }}</button>
                <span v-else class="dim">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </CardPanel>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import PageHeader from '../../components/PageHeader.vue'
import CardPanel from '../../components/CardPanel.vue'
import ToggleSwitch from '../../components/ToggleSwitch.vue'
import { friendlyError } from '../../utils/friendlyError.js'
import {
  listUsers, updateUser, getRegistration, setRegistration,
  getEmailConfig, setEmailConfig, getPlans,
} from '../../api/admin.js'

const users = ref([])
const plans = ref([])
const regEnabled = ref(false)
const regBusy = ref(false)
const emailBusy = ref(false)
const rowBusy = ref(0)
const emailConfigured = ref(false)
const email = reactive({ smtpHost: '', smtpPort: 465, smtpUser: '', smtpPass: '', fromName: '' })
const notice = ref('')
const noticeType = ref('success')

function flash(msg, type = 'success') {
  notice.value = msg
  noticeType.value = type
  setTimeout(() => { if (notice.value === msg) notice.value = '' }, 4000)
}

function fmt(v) {
  if (!v) return '—'
  return String(v).replace('T', ' ').slice(0, 16)
}

async function loadAll() {
  try {
    const [uRes, pRes, rRes, eRes] = await Promise.all([
      listUsers(), getPlans(), getRegistration(), getEmailConfig(),
    ])
    users.value = uRes.data || []
    plans.value = pRes.data || []
    regEnabled.value = !!(rRes.data && rRes.data.enabled)
    const cfg = eRes.data || {}
    email.smtpHost = cfg.smtpHost || ''
    email.smtpPort = cfg.smtpPort || 465
    email.smtpUser = cfg.smtpUser || ''
    email.fromName = cfg.fromName || ''
    emailConfigured.value = !!(cfg.smtpHost || cfg.smtpUser)
  } catch (e) {
    flash(friendlyError(e, '加载失败，请确认你是超级管理员'), 'error')
  }
}

async function toggleRegistration() {
  if (regBusy.value) return
  regBusy.value = true
  try {
    const res = await setRegistration(!regEnabled.value)
    regEnabled.value = !!(res.data && res.data.enabled)
    flash(regEnabled.value ? '已开放自助注册' : '已关闭自助注册')
  } catch (e) {
    flash(friendlyError(e, '切换失败'), 'error')
  } finally {
    regBusy.value = false
  }
}

async function saveEmail() {
  if (emailBusy.value) return
  emailBusy.value = true
  try {
    const payload = {
      smtpHost: email.smtpHost, smtpPort: email.smtpPort,
      smtpUser: email.smtpUser, fromName: email.fromName,
    }
    if (email.smtpPass) payload.smtpPass = email.smtpPass
    await setEmailConfig(payload)
    email.smtpPass = ''
    emailConfigured.value = !!(email.smtpHost || email.smtpUser)
    flash('邮箱配置已保存')
  } catch (e) {
    flash(friendlyError(e, '保存失败'), 'error')
  } finally {
    emailBusy.value = false
  }
}

async function changePlan(u, planCode) {
  if (!planCode || planCode === u.planCode) return
  rowBusy.value = u.id
  try {
    await updateUser(u.id, { planCode })
    flash(`已将 ${u.username} 的套餐改为 ${planCode}`)
    await loadAll()
  } catch (e) {
    flash(friendlyError(e, '修改套餐失败'), 'error')
  } finally {
    rowBusy.value = 0
  }
}

async function toggleStatus(u) {
  rowBusy.value = u.id
  try {
    await updateUser(u.id, { status: u.status === 1 ? 0 : 1 })
    flash(`已${u.status === 1 ? '禁用' : '启用'} ${u.username}`)
    await loadAll()
  } catch (e) {
    flash(friendlyError(e, '操作失败'), 'error')
  } finally {
    rowBusy.value = 0
  }
}

onMounted(loadAll)
</script>

<style scoped>
.user-mgmt-page { min-width: 0; }
.dashboard-section { margin-top: 16px; }
.reg-row { display: flex; align-items: center; justify-content: space-between; gap: 20px; }
.reg-info { min-width: 0; }
.reg-state { font-size: 15px; margin-bottom: 4px; }
.reg-state .on { color: #16bf78; }
.reg-state .off { color: var(--muted, #6b6b6b); }
.reg-hint { color: var(--muted, #6b6b6b); font-size: 13px; line-height: 1.6; }
.reg-hint code { background: #f2f2f2; padding: 1px 6px; border-radius: 5px; }
.form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; }
.field { display: flex; flex-direction: column; gap: 6px; font-size: 13px; color: var(--muted, #6b6b6b); }
.form-actions { margin-top: 16px; }
.table-wrap { overflow-x: auto; }
.user-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.user-table th, .user-table td { padding: 12px 10px; text-align: left; border-bottom: 1px solid var(--line, #e5e5e5); white-space: nowrap; }
.user-table th { color: var(--muted, #6b6b6b); font-weight: 600; }
.empty-cell { text-align: center; color: var(--muted, #6b6b6b); padding: 28px 0; }
.plan-select { padding: 5px 8px; min-width: 96px; }
.role-tag { padding: 2px 8px; border-radius: 6px; font-size: 12px; }
.role-tag.superadmin { background: rgba(255,79,0,.1); color: #ff4f00; }
.role-tag.user { background: #f0f0f0; color: #555; }
.status-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 4px; vertical-align: middle; }
.status-dot.ok { background: #16bf78; }
.status-dot.off { background: #c0c0c0; }
.dim { color: var(--muted, #999); }
</style>
