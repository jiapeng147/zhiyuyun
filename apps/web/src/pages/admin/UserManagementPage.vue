<template>
  <div class="user-mgmt-page">
    <div v-if="notice" :class="['global-notice', noticeType]" role="status">{{ notice }}</div>

    <n-card class="user-v4-hero" :bordered="false">
      <div>
        <n-tag size="small" type="success" :bordered="false">User Operations</n-tag>
        <h2>用户管理</h2>
        <p>集中处理平台概览、套餐、手动建用户、自助注册、SMTP 与账号状态。</p>
      </div>
      <n-space :size="8" align="center" wrap>
        <button class="btn" type="button" @click="loadAll">刷新数据</button>
        <button class="btn primary" type="button" :disabled="planBusy" @click="openCreatePlan">新建套餐</button>
      </n-space>
    </n-card>

    <!-- 平台概览 -->
    <n-card class="dashboard-section user-v4-card" :bordered="false">
      <template #header>平台概览</template>
      <template #header-extra><span class="user-v4-desc">总用户/账号/商品/订单与活跃趋势（仅超管可见）</span></template>
      <div v-if="overview" class="ov-grid">
        <div class="ov-card">
          <div class="ov-label">用户总数</div>
          <div class="ov-value">{{ overview.user.total }}</div>
          <div class="ov-sub">
            <span class="delta up">+{{ overview.user.new_today }} 今日</span>
            <span class="delta up">{{ overview.user.active_7d }} 7日活跃</span>
          </div>
        </div>
        <div class="ov-card">
          <div class="ov-label">店铺账号</div>
          <div class="ov-value">{{ overview.account.total }}</div>
          <div class="ov-sub">跨所有用户的可用账号</div>
        </div>
        <div class="ov-card">
          <div class="ov-label">在售商品</div>
          <div class="ov-value">{{ overview.goods.total }}</div>
          <div class="ov-sub">未软删的商品数</div>
        </div>
        <div class="ov-card">
          <div class="ov-label">订单总数</div>
          <div class="ov-value">{{ overview.order.total }}</div>
          <div class="ov-sub">
            <span class="delta up">+{{ overview.order.new_today }} 今日</span>
          </div>
        </div>
        <div class="ov-card plan-dist">
          <div class="ov-label">套餐分布</div>
          <div v-if="overview.plan_distribution.length === 0" class="ov-sub">暂无用户</div>
          <ul v-else class="plan-list">
            <li v-for="p in overview.plan_distribution" :key="p.plan_code">
              <span class="plan-code">{{ p.plan_code }}</span>
              <span class="plan-count">{{ p.count }}</span>
            </li>
          </ul>
        </div>
      </div>
      <div v-else class="loading">加载中…</div>
    </n-card>

    <!-- 套餐管理 -->
    <n-card class="dashboard-section user-v4-card" :bordered="false">
      <template #header>套餐管理</template>
      <template #header-extra><span class="user-v4-desc">新增/编辑/下架套餐。已被用户引用的套餐会被下架而非删除。</span></template>
      <div class="plan-toolbar">
        <button class="btn primary" type="button" :disabled="planBusy" @click="openCreatePlan">+ 新建套餐</button>
        <span class="muted">共 {{ plans.length }} 个套餐</span>
      </div>
      <div class="table-wrap">
        <table class="table plan-table">
          <thead>
            <tr>
              <th>代码</th><th>名称</th><th>账号配额</th><th>AI 配额/日</th>
              <th>月价</th><th>排序</th><th>状态</th><th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="plans.length === 0">
              <td colspan="8" class="empty-cell">暂无套餐</td>
            </tr>
            <tr v-for="p in plans" :key="p.id">
              <td><code>{{ p.code }}</code></td>
              <td>{{ p.name }}</td>
              <td>{{ p.maxAccounts }}</td>
              <td>{{ p.aiDailyQuota }}</td>
              <td>¥{{ (p.priceCents / 100).toFixed(2) }}</td>
              <td>{{ p.sortOrder }}</td>
              <td>
                <span :class="['status-dot', p.status === 1 ? 'ok' : 'off']"></span>
                {{ p.status === 1 ? '上架' : '下架' }}
              </td>
              <td class="actions">
                <button class="btn small" type="button" :disabled="planBusy" @click="openEditPlan(p)">编辑</button>
                <button class="btn small danger" type="button" :disabled="planBusy" @click="onDeletePlan(p)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </n-card>

    <!-- 手动建用户 -->
    <n-card class="dashboard-section user-v4-card" :bordered="false">
      <template #header>手动建用户</template>
      <template #header-extra><span class="user-v4-desc">超管可直接创建账号，绕过注册开关和邮箱验证。</span></template>
      <form class="create-form" @submit.prevent="onCreateUser">
        <label class="field">
          <span>用户名 *</span>
          <input v-model.trim="createForm.username" class="input" placeholder="如 shop_owner_3" required />
        </label>
        <label class="field">
          <span>邮箱</span>
          <input v-model.trim="createForm.email" class="input" type="email" placeholder="可选, 用于找回密码" />
        </label>
        <label class="field">
          <span>初始密码 *</span>
          <input v-model="createForm.password" class="input" type="text" placeholder="≥ 8 位" required />
        </label>
        <label class="field">
          <span>套餐</span>
          <select v-model="createForm.planCode" class="input">
            <option v-for="p in plans" :key="p.code" :value="p.code">{{ p.name }} ({{ p.code }})</option>
          </select>
        </label>
        <label class="field check">
          <input v-model="createForm.isSuper" type="checkbox" />
          <span>超级管理员（请谨慎勾选）</span>
        </label>
        <div class="form-actions">
          <button class="btn primary" type="submit" :disabled="createBusy">{{ createBusy ? '创建中...' : '创建用户' }}</button>
        </div>
      </form>
    </n-card>

    <!-- 注册开关 -->
    <n-card class="dashboard-section user-v4-card" :bordered="false">
      <template #header>自助注册</template>
      <template #header-extra><span class="user-v4-desc">控制外部用户是否可以通过注册页自助注册账号</span></template>
      <div class="reg-row">
        <div class="reg-info">
          <div class="reg-state">
            当前状态：<strong :class="regEnabled ? 'on' : 'off'">{{ regEnabled ? '已开放注册' : '已关闭注册' }}</strong>
          </div>
          <div class="reg-hint">
            开放后，任何人可在 <code>/#/register</code> 用邮箱验证码注册。请确保下方 SMTP 已配置。
          </div>
        </div>
        <ToggleSwitch :on="regEnabled" interactive :disabled="regBusy" @click="toggleRegistration" />
      </div>
    </n-card>

    <!-- 邮箱 SMTP -->
    <n-card class="dashboard-section user-v4-card" :bordered="false">
      <template #header>邮箱 SMTP 配置</template>
      <template #header-extra><span class="user-v4-desc">用于发送注册/找回密码验证码。密码不回显。</span></template>
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
          <input v-model="email.smtpPass" class="input" type="password" :placeholder="emailConfigured ? '已配置，留空保留' : '邮箱授权码'" />
        </label>
        <label class="field">
          <span>发件人名称</span>
          <input v-model.trim="email.fromName" class="input" placeholder="Lumen Ops" />
        </label>
      </div>
      <div class="form-actions">
        <button class="btn primary" type="button" :disabled="emailBusy" @click="saveEmail">{{ emailBusy ? '保存中...' : '保存邮箱配置' }}</button>
      </div>
    </n-card>

    <!-- 用户列表 -->
    <n-card class="dashboard-section user-v4-card" :bordered="false">
      <template #header>注册用户</template>
      <template #header-extra><span class="user-v4-desc">共 {{ users.length }} 个账号</span></template>
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
              <td class="actions">
                <button
                  v-if="u.role !== 'superadmin'"
                  class="btn small"
                  type="button"
                  :disabled="rowBusy === u.id"
                  @click="toggleStatus(u)"
                >
                  {{ u.status === 1 ? '禁用' : '启用' }}
                </button>
                <button
                  class="btn small"
                  type="button"
                  :disabled="rowBusy === u.id"
                  @click="openResetPwd(u)"
                >
                  重置密码
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </n-card>

    <!-- 重置密码模态 -->
    <div v-if="resetTarget" class="modal-mask" @click.self="resetTarget = null">
      <div class="modal-card small">
        <div class="modal-head">
          <h3>重置 {{ resetTarget.username }} 的密码</h3>
          <button class="modal-close" type="button" aria-label="关闭" @click="resetTarget = null">×</button>
        </div>
        <div class="modal-body">
          <label class="field">
            <span>新密码 (≥ 8 位)</span>
            <input v-model="resetPwd" class="input" type="text" placeholder="新密码" />
          </label>
          <div class="form-actions">
            <button class="btn" type="button" @click="resetTarget = null">取消</button>
            <button class="btn primary" type="button" :disabled="resetBusy || resetPwd.length < 8" @click="onResetPwd">
              {{ resetBusy ? '重置中...' : '确认重置' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 套餐编辑模态 -->
    <div v-if="editingPlan" class="modal-mask" @click.self="editingPlan = null">
      <div class="modal-card small">
        <div class="modal-head">
          <h3>{{ editingPlan.id ? '编辑套餐' : '新建套餐' }}</h3>
          <button class="modal-close" type="button" aria-label="关闭" @click="editingPlan = null">×</button>
        </div>
        <div class="modal-body">
          <label class="field">
            <span>代码 * (英文+下划线,创建后修改需谨慎)</span>
            <input v-model.trim="editingPlan.code" class="input" placeholder="如 starter / pro / max" />
          </label>
          <label class="field">
            <span>名称 *</span>
            <input v-model.trim="editingPlan.name" class="input" placeholder="如 入门版 / 专业版" />
          </label>
          <div class="form-row">
            <label class="field">
              <span>账号配额</span>
              <input v-model.number="editingPlan.maxAccounts" class="input" type="number" min="0" />
            </label>
            <label class="field">
              <span>AI 配额/日</span>
              <input v-model.number="editingPlan.aiDailyQuota" class="input" type="number" min="0" />
            </label>
          </div>
          <div class="form-row">
            <label class="field">
              <span>月价 (分, 0=免费)</span>
              <input v-model.number="editingPlan.priceCents" class="input" type="number" min="0" />
            </label>
            <label class="field">
              <span>排序</span>
              <input v-model.number="editingPlan.sortOrder" class="input" type="number" />
            </label>
          </div>
          <label class="field check">
            <input v-model="editingPlan.statusBool" type="checkbox" />
            <span>上架 (status=1)</span>
          </label>
          <label class="field">
            <span>描述</span>
            <textarea v-model="editingPlan.description" class="input" rows="2" placeholder="显示在注册/升级页"></textarea>
          </label>
          <div class="form-actions">
            <button class="btn" type="button" @click="editingPlan = null">取消</button>
            <button class="btn primary" type="button" :disabled="planBusy" @click="onSavePlan">
              {{ planBusy ? '保存中...' : '保存' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { NCard, NSpace, NTag } from 'naive-ui'
import ToggleSwitch from '../../components/ToggleSwitch.vue'
import { friendlyError } from '../../utils/friendlyError.js'
import {
  listUsers, updateUser, createUser, resetPassword,
  getOverview, adminListPlans, adminCreatePlan, adminUpdatePlan, adminDeletePlan,
  getRegistration, setRegistration, getEmailConfig, setEmailConfig,
} from '../../api/admin.js'

const users = ref([])
const plans = ref([])
const overview = ref(null)
const regEnabled = ref(false)
const regBusy = ref(false)
const emailBusy = ref(false)
const createBusy = ref(false)
const planBusy = ref(false)
const rowBusy = ref(0)
const emailConfigured = ref(false)
const email = reactive({ smtpHost: '', smtpPort: 465, smtpUser: '', smtpPass: '', fromName: '' })

const createForm = reactive({ username: '', email: '', password: '', planCode: 'free', isSuper: false })

const resetTarget = ref(null)
const resetPwd = ref('')
const resetBusy = ref(false)

const editingPlan = ref(null)

const notice = ref('')
const noticeType = ref('success')

function flash(msg, type = 'success') { notice.value = msg; noticeType.value = type; setTimeout(() => { if (notice.value === msg) notice.value = '' }, 4000) }
function fmt(v) { if (!v) return '—'; return String(v).replace('T', ' ').slice(0, 16) }

async function loadAll() {
  try {
    const [uRes, pRes, rRes, eRes, oRes] = await Promise.all([
      listUsers(), adminListPlans(), getRegistration(), getEmailConfig(), getOverview(),
    ])
    users.value = uRes.data || []
    plans.value = pRes.data || []
    regEnabled.value = !!(rRes.data && rRes.data.enabled)
    overview.value = oRes.data || null
    const cfg = eRes.data || {}
    email.smtpHost = cfg.smtpHost || ''
    email.smtpPort = cfg.smtpPort || 465
    email.smtpUser = cfg.smtpUser || ''
    email.fromName = cfg.fromName || ''
    emailConfigured.value = !!(cfg.smtpHost || cfg.smtpUser)
    if (!createForm.planCode && plans.value.length) createForm.planCode = plans.value[0].code
  } catch (e) {
    flash(friendlyError(e, '加载失败，请确认你是超级管理员'), 'error')
  }
}

async function toggleRegistration() {
  if (regBusy.value) return; regBusy.value = true
  try { const r = await setRegistration(!regEnabled.value); regEnabled.value = !!(r.data && r.data.enabled); flash(regEnabled.value ? '已开放自助注册' : '已关闭自助注册') }
  catch (e) { flash(friendlyError(e, '切换失败'), 'error') } finally { regBusy.value = false }
}

async function saveEmail() {
  if (emailBusy.value) return; emailBusy.value = true
  try {
    const payload = { smtpHost: email.smtpHost, smtpPort: email.smtpPort, smtpUser: email.smtpUser, fromName: email.fromName }
    if (email.smtpPass) payload.smtpPass = email.smtpPass
    await setEmailConfig(payload); email.smtpPass = ''; emailConfigured.value = !!(email.smtpHost || email.smtpUser); flash('邮箱配置已保存')
  } catch (e) { flash(friendlyError(e, '保存失败'), 'error') } finally { emailBusy.value = false }
}

async function changePlan(u, planCode) {
  if (!planCode || planCode === u.planCode) return
  rowBusy.value = u.id
  try { await updateUser(u.id, { planCode }); flash(`已将 ${u.username} 的套餐改为 ${planCode}`); await loadAll() }
  catch (e) { flash(friendlyError(e, '修改套餐失败'), 'error') } finally { rowBusy.value = 0 }
}

async function toggleStatus(u) {
  rowBusy.value = u.id
  try { await updateUser(u.id, { status: u.status === 1 ? 0 : 1 }); flash(`已${u.status === 1 ? '禁用' : '启用'} ${u.username}`); await loadAll() }
  catch (e) { flash(friendlyError(e, '操作失败'), 'error') } finally { rowBusy.value = 0 }
}

// === 手动建用户 ===
async function onCreateUser() {
  if (createBusy.value) return; createBusy.value = true
  try {
    const payload = { username: createForm.username, email: createForm.email || null, password: createForm.password, planCode: createForm.planCode, isSuper: createForm.isSuper }
    await createUser(payload)
    flash(`已创建用户 ${createForm.username}`)
    createForm.username = ''; createForm.email = ''; createForm.password = ''; createForm.isSuper = false
    await loadAll()
  } catch (e) { flash(friendlyError(e, '创建失败'), 'error') } finally { createBusy.value = false }
}

// === 重置密码 ===
function openResetPwd(u) { resetTarget.value = u; resetPwd.value = '' }
async function onResetPwd() {
  if (!resetTarget.value) return; if (resetBusy.value) return
  resetBusy.value = true
  try {
    await resetPassword(resetTarget.value.id, resetPwd.value)
    flash(`已重置 ${resetTarget.value.username} 的密码`)
    resetTarget.value = null; resetPwd.value = ''
  } catch (e) { flash(friendlyError(e, '重置失败'), 'error') } finally { resetBusy.value = false }
}

// === 套餐编辑 ===
function openCreatePlan() {
  editingPlan.value = { id: 0, code: '', name: '', maxAccounts: 1, aiDailyQuota: 100, priceCents: 0, sortOrder: plans.value.length + 1, statusBool: true, description: '' }
}
function openEditPlan(p) {
  editingPlan.value = { id: p.id, code: p.code, name: p.name, maxAccounts: p.maxAccounts, aiDailyQuota: p.aiDailyQuota, priceCents: p.priceCents, sortOrder: p.sortOrder, statusBool: p.status === 1, description: p.description || '' }
}
async function onSavePlan() {
  if (!editingPlan.value) return; if (planBusy.value) return
  planBusy.value = true
  try {
    const ep = editingPlan.value
    const payload = { code: ep.code.trim(), name: ep.name.trim(), maxAccounts: ep.maxAccounts, aiDailyQuota: ep.aiDailyQuota, priceCents: ep.priceCents, sortOrder: ep.sortOrder, status: ep.statusBool ? 1 : 0, description: ep.description || null }
    if (ep.id) {
      await adminUpdatePlan(ep.id, payload); flash(`已更新套餐 ${ep.code}`)
    } else {
      await adminCreatePlan(payload); flash(`已创建套餐 ${ep.code}`)
    }
    editingPlan.value = null
    await loadAll()
  } catch (e) { flash(friendlyError(e, '保存失败'), 'error') } finally { planBusy.value = false }
}
async function onDeletePlan(p) {
  if (!window.confirm(`确认删除套餐 ${p.code}？若已被用户引用将自动改为下架。`)) return
  planBusy.value = true
  try { const r = await adminDeletePlan(p.id); flash(r.data || '已删除'); await loadAll() }
  catch (e) { flash(friendlyError(e, '删除失败'), 'error') } finally { planBusy.value = false }
}

onMounted(loadAll)
</script>

<style scoped>
.user-mgmt-page {
  display: grid;
  gap: 16px;
  min-width: 0;
}

.user-v4-hero,
.user-v4-card {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, .04);
}

.user-v4-hero :deep(.n-card__content) {
  padding: 18px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.user-v4-hero h2 {
  margin: 12px 0 6px;
  color: #111827;
  font-size: 22px;
  font-weight: 650;
  line-height: 1.25;
}

.user-v4-hero p {
  margin: 0;
  color: #64748b;
  font-size: 13px;
  line-height: 1.65;
}

.user-v4-card :deep(.n-card__content) {
  padding: 16px;
}

.user-v4-card :deep(.n-card-header) {
  padding: 16px 16px 0;
}

.user-v4-desc {
  max-width: 340px;
  color: #64748b;
  font-size: 12px;
  line-height: 1.5;
}

.dashboard-section { margin-top: 0; }
.muted { color: var(--muted, #6b6b6b); font-size: 12px; }
.loading { padding: 24px 0; text-align: center; color: var(--muted, #6b6b6b); }

/* 概览 */
.ov-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; }
.ov-card { background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 6px; padding: 14px 16px; }
.ov-card.plan-dist { grid-column: span 2; }
.ov-label { font-size: 12px; color: var(--muted, #6b6b6b); margin-bottom: 6px; }
.ov-value { font-size: 28px; font-weight: 700; color: var(--text, #111); }
.ov-sub { margin-top: 6px; font-size: 12px; color: var(--muted, #6b6b6b); display: flex; gap: 10px; flex-wrap: wrap; }
.delta.up { color: #16bf78; }
.plan-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 4px; }
.plan-list li { display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px dashed var(--line, #e5e5e5); font-size: 13px; }
.plan-list li:last-child { border-bottom: 0; }
.plan-list .plan-code { font-family: ui-monospace, monospace; color: var(--text, #111); }
.plan-list .plan-count { color: #0f766e; font-weight: 600; }

/* 套餐管理 */
.plan-toolbar { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.table-wrap { overflow-x: auto; }
.plan-table, .user-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.plan-table th, .plan-table td, .user-table th, .user-table td { padding: 12px 10px; text-align: left; border-bottom: 1px solid var(--line, #e5e5e5); white-space: nowrap; }
.plan-table th, .user-table th { color: var(--muted, #6b6b6b); font-weight: 600; }
.empty-cell { text-align: center; color: var(--muted, #6b6b6b); padding: 28px 0; }
.plan-table code { background: #f2f2f2; padding: 1px 6px; border-radius: 4px; }
.status-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 4px; vertical-align: middle; }
.status-dot.ok { background: #16bf78; }
.status-dot.off { background: #c0c0c0; }
.actions { display: flex; gap: 6px; }
.actions .btn.small { padding: 4px 8px; font-size: 12px; }

/* 注册开关 */
.reg-row { display: flex; align-items: center; justify-content: space-between; gap: 20px; }
.reg-info { min-width: 0; }
.reg-state { font-size: 15px; margin-bottom: 4px; }
.reg-state .on { color: #16bf78; }
.reg-state .off { color: var(--muted, #6b6b6b); }
.reg-hint { color: var(--muted, #6b6b6b); font-size: 13px; line-height: 1.6; }
.reg-hint code { background: #f2f2f2; padding: 1px 6px; border-radius: 5px; }

/* 表单 */
.form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; }
.create-form { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; }
.create-form .form-actions { grid-column: 1 / -1; }
.field { display: flex; flex-direction: column; gap: 6px; font-size: 13px; color: var(--muted, #6b6b6b); }
.field.check { flex-direction: row; align-items: center; gap: 8px; }
.field.check input { width: 16px; height: 16px; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.form-actions { margin-top: 12px; display: flex; gap: 8px; }

/* modal */
.modal-mask { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 200; }
.modal-card { background: #fff; border-radius: 6px; padding: 20px; width: min(520px, 92vw); box-shadow: 0 16px 48px rgba(0,0,0,.18); }
.modal-card.small { width: min(420px, 92vw); }
.modal-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.modal-head h3 { margin: 0; font-size: 16px; }
.modal-close { background: transparent; border: 0; font-size: 22px; line-height: 1; color: var(--muted, #6b6b6b); cursor: pointer; padding: 4px 8px; }
.modal-body { display: flex; flex-direction: column; gap: 12px; }

/* role / status */
.plan-select { padding: 5px 8px; min-width: 96px; }
.role-tag { padding: 2px 8px; border-radius: 6px; font-size: 12px; }
.role-tag.superadmin { background: rgba(20, 184, 166,.1); color: #0f766e; }
.role-tag.user { background: #f0f0f0; color: #555; }
.dim { color: var(--muted, #999); }

/* buttons */
.btn { padding: 6px 14px; border: 1px solid var(--line, #d0d0d0); background: #fff; border-radius: 6px; cursor: pointer; font-size: 13px; }
.btn:hover { border-color: #b0b0b0; }
.btn.primary { background: #2563eb; color: #fff; border-color: #2563eb; }
.btn.primary:hover { background: #1d4ed8; border-color: #1d4ed8; }
.btn.danger { color: #c0392b; border-color: rgba(192,57,43,.3); }
.btn.small { padding: 4px 10px; font-size: 12px; }
.btn:disabled { opacity: .5; cursor: not-allowed; }

@media (max-width: 900px) {
  .user-mgmt-page {
    gap: 12px;
  }

  .user-v4-hero :deep(.n-card__content) {
    flex-direction: column;
    padding: 14px;
  }

  .user-v4-card :deep(.n-card__content) {
    padding: 12px;
  }

  .ov-card.plan-dist {
    grid-column: auto;
  }
}
</style>
