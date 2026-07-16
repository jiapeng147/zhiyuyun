<template>
  <div class="billing-page">
    <div v-if="notice" :class="['billing-notice', noticeType]" role="status">{{ notice }}</div>

    <n-card class="billing-hero" :bordered="false">
      <div>
        <span class="eyebrow">Subscription</span>
        <h2>套餐账单</h2>
        <p>查看当前版本、账号配额、AI 调用额度与订阅订单。</p>
      </div>
      <button class="billing-btn" type="button" :disabled="loading" @click="loadAll">
        {{ loading ? '刷新中...' : '刷新' }}
      </button>
    </n-card>

    <div class="billing-grid">
      <n-card class="billing-card plan-summary" :bordered="false">
        <template #header>当前套餐</template>
        <div class="plan-name">{{ state?.plan?.name || '—' }}</div>
        <div class="plan-code">{{ state?.plan?.code || 'free' }}</div>
        <div class="summary-row">
          <span>到期时间</span>
          <strong>{{ state?.plan?.expireTime ? fmt(state.plan.expireTime) : '长期有效' }}</strong>
        </div>
        <div class="summary-row">
          <span>套餐状态</span>
          <strong :class="state?.plan?.expired ? 'danger' : 'ok'">{{ state?.plan?.expired ? '已过期' : '生效中' }}</strong>
        </div>
      </n-card>

      <n-card class="billing-card" :bordered="false">
        <template #header>账号配额</template>
        <div class="quota-main">
          <strong>{{ usage.accounts.used }}</strong>
          <span>/ {{ displayLimit(usage.accounts.limit) }}</span>
        </div>
        <div class="quota-bar"><i :style="{ width: percent(usage.accounts.used, usage.accounts.limit) + '%' }"></i></div>
        <p>剩余 {{ displayRemaining(usage.accounts.remaining, usage.accounts.limit) }} 个闲鱼账号可绑定。</p>
      </n-card>

      <n-card class="billing-card" :bordered="false">
        <template #header>AI 今日额度</template>
        <div class="quota-main">
          <strong>{{ usage.aiCallsToday.used }}</strong>
          <span>/ {{ displayLimit(usage.aiCallsToday.limit) }}</span>
        </div>
        <div class="quota-bar ai"><i :style="{ width: percent(usage.aiCallsToday.used, usage.aiCallsToday.limit) + '%' }"></i></div>
        <p>AI 客服测试、RAG 对话、货源推荐等会计入调用次数。</p>
      </n-card>
    </div>

    <n-card class="billing-card" :bordered="false">
      <template #header>可选套餐</template>
      <template #header-extra>
        <span class="muted">付费订单创建后需等待管理员确认</span>
      </template>
      <div class="plan-catalog">
        <div v-for="plan in plans" :key="plan.code" class="plan-item">
          <div class="plan-item-head">
            <div>
              <strong>{{ plan.name }}</strong>
              <code>{{ plan.code }}</code>
            </div>
            <div class="price">{{ money(plan.priceCents) }}<span>/ 月</span></div>
          </div>
          <p>{{ plan.description || '适合标准闲鱼运营场景，可按需升级。' }}</p>
          <div class="plan-features">
            <span>{{ displayLimit(plan.maxAccounts) }} 个账号</span>
            <span>{{ displayLimit(plan.aiDailyQuota) }} 次 AI/日</span>
          </div>
          <button
            class="billing-btn primary"
            type="button"
            :disabled="orderBusy || currentPlanCode === plan.code"
            @click="createOrder(plan)"
          >
            {{ currentPlanCode === plan.code ? '当前套餐' : (plan.priceCents > 0 ? '创建订阅订单' : '启用免费套餐') }}
          </button>
        </div>
      </div>
    </n-card>

    <n-card class="billing-card" :bordered="false">
      <template #header>订单记录</template>
      <div class="table-wrap">
        <table class="billing-table">
          <thead>
            <tr>
              <th>订单号</th>
              <th>套餐</th>
              <th>金额</th>
              <th>周期</th>
              <th>状态</th>
              <th>创建时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="orders.length === 0">
              <td colspan="6" class="empty-cell">暂无订单</td>
            </tr>
            <tr v-for="order in orders" :key="order.id">
              <td><code>{{ order.orderNo }}</code></td>
              <td>{{ order.planCode }}</td>
              <td>{{ money(order.amountCents) }}</td>
              <td>{{ order.durationDays }} 天</td>
              <td><span :class="['status-pill', order.status]">{{ statusText(order.status) }}</span></td>
              <td>{{ fmt(order.createdTime) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </n-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { NCard } from 'naive-ui'
import { friendlyError } from '../utils/friendlyError.js'
import {
  createBillingOrder,
  getBillingPlans,
  getMyBilling,
  listBillingOrders,
} from '../api/billing.js'

const state = ref(null)
const plans = ref([])
const orders = ref([])
const loading = ref(false)
const orderBusy = ref(false)
const notice = ref('')
const noticeType = ref('success')

const emptyUsage = { used: 0, limit: 0, remaining: 0 }
const usage = computed(() => ({
  accounts: state.value?.usage?.accounts || emptyUsage,
  aiCallsToday: state.value?.usage?.aiCallsToday || emptyUsage,
}))
const currentPlanCode = computed(() => state.value?.plan?.code || 'free')

function flash(message, type = 'success') {
  notice.value = message
  noticeType.value = type
  setTimeout(() => {
    if (notice.value === message) notice.value = ''
  }, 4200)
}

function fmt(value) {
  if (!value) return '—'
  return String(value).replace('T', ' ').slice(0, 16)
}

function money(cents) {
  return `¥${(Number(cents || 0) / 100).toFixed(2)}`
}

function displayLimit(value) {
  const n = Number(value || 0)
  return n >= 999999 ? '不限' : n
}

function displayRemaining(value, limit) {
  return Number(limit || 0) >= 999999 ? '不限' : Number(value || 0)
}

function percent(used, limit) {
  const max = Number(limit || 0)
  if (max <= 0 || max >= 999999) return max >= 999999 ? 8 : 100
  return Math.max(4, Math.min(100, Math.round((Number(used || 0) / max) * 100)))
}

function statusText(status) {
  const map = { pending: '待确认', paid: '已生效', closed: '已关闭', refunded: '已退款' }
  return map[status] || status || '未知'
}

async function loadAll() {
  if (loading.value) return
  loading.value = true
  try {
    const [billingRes, plansRes, ordersRes] = await Promise.all([
      getMyBilling(),
      getBillingPlans(),
      listBillingOrders({ current: 1, size: 50 }),
    ])
    state.value = billingRes.data || null
    plans.value = plansRes.data || []
    orders.value = ordersRes.data?.records || []
  } catch (error) {
    flash(friendlyError(error, '套餐账单加载失败'), 'error')
  } finally {
    loading.value = false
  }
}

async function createOrder(plan) {
  if (!plan || orderBusy.value) return
  orderBusy.value = true
  try {
    const res = await createBillingOrder({
      planCode: plan.code,
      durationDays: 30,
      paymentMethod: 'manual',
    })
    flash(res.data?.message || '订单已创建')
    await loadAll()
  } catch (error) {
    flash(friendlyError(error, '创建订单失败'), 'error')
  } finally {
    orderBusy.value = false
  }
}

onMounted(loadAll)
</script>

<style scoped>
.billing-page {
  display: grid;
  gap: 16px;
  min-width: 0;
}

.billing-notice {
  padding: 10px 12px;
  border-radius: 6px;
  border: 1px solid #bbf7d0;
  background: #f0fdf4;
  color: #166534;
}

.billing-notice.error {
  border-color: #fecaca;
  background: #fef2f2;
  color: #b91c1c;
}

.billing-hero,
.billing-card {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, .04);
}

.billing-hero :deep(.n-card__content) {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 18px;
}

.eyebrow {
  color: #0f766e;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
}

.billing-hero h2 {
  margin: 8px 0 6px;
  color: #111827;
  font-size: 22px;
  line-height: 1.25;
}

.billing-hero p,
.billing-card p,
.muted {
  margin: 0;
  color: #64748b;
  font-size: 13px;
  line-height: 1.6;
}

.billing-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.billing-card :deep(.n-card__content) {
  padding: 16px;
}

.billing-card :deep(.n-card-header) {
  padding: 16px 16px 0;
}

.plan-name {
  color: #111827;
  font-size: 26px;
  font-weight: 750;
}

.plan-code {
  margin: 4px 0 14px;
  color: #0f766e;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 0;
  border-top: 1px solid #eef2f7;
  color: #64748b;
  font-size: 13px;
}

.summary-row strong {
  color: #111827;
}

.summary-row strong.ok { color: #15803d; }
.summary-row strong.danger { color: #b91c1c; }

.quota-main {
  display: flex;
  align-items: baseline;
  gap: 6px;
  margin-bottom: 12px;
}

.quota-main strong {
  color: #111827;
  font-size: 34px;
}

.quota-main span {
  color: #64748b;
}

.quota-bar {
  height: 8px;
  margin-bottom: 10px;
  overflow: hidden;
  border-radius: 999px;
  background: #eef2f7;
}

.quota-bar i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: #0f766e;
}

.quota-bar.ai i {
  background: #2563eb;
}

.plan-catalog {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
}

.plan-item {
  display: grid;
  gap: 12px;
  padding: 14px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #fbfdff;
}

.plan-item-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.plan-item strong {
  display: block;
  color: #111827;
  font-size: 16px;
}

.plan-item code,
.billing-table code {
  padding: 1px 6px;
  border-radius: 4px;
  background: #eef2f7;
  color: #334155;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}

.price {
  color: #111827;
  font-size: 18px;
  font-weight: 750;
  white-space: nowrap;
}

.price span {
  margin-left: 2px;
  color: #64748b;
  font-size: 12px;
  font-weight: 400;
}

.plan-features {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.plan-features span {
  padding: 3px 8px;
  border-radius: 999px;
  background: #eefbf6;
  color: #0f766e;
  font-size: 12px;
}

.billing-btn {
  height: 32px;
  padding: 0 14px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #fff;
  color: #111827;
  cursor: pointer;
}

.billing-btn.primary {
  border-color: #2563eb;
  background: #2563eb;
  color: #fff;
}

.billing-btn:disabled {
  opacity: .55;
  cursor: not-allowed;
}

.table-wrap {
  overflow-x: auto;
}

.billing-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.billing-table th,
.billing-table td {
  padding: 12px 10px;
  border-bottom: 1px solid #e5e7eb;
  text-align: left;
  white-space: nowrap;
}

.billing-table th {
  color: #64748b;
  font-weight: 650;
}

.empty-cell {
  color: #64748b;
  text-align: center;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  background: #eef2f7;
  color: #334155;
}

.status-pill.paid {
  background: #dcfce7;
  color: #15803d;
}

.status-pill.pending {
  background: #fef3c7;
  color: #92400e;
}

@media (max-width: 980px) {
  .billing-grid {
    grid-template-columns: 1fr;
  }

  .billing-hero :deep(.n-card__content) {
    flex-direction: column;
    padding: 14px;
  }
}
</style>
