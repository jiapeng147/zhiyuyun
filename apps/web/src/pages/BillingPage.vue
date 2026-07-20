<template>
  <div class="billing-page billing-quota-v25-shell">
    <div v-if="notice" :class="['billing-notice', noticeType]" role="status">{{ notice }}</div>

    <section class="billing-command-center">
      <div class="billing-command-main">
        <div class="billing-command-kicker">
          <span>套餐订阅</span>
          <b>{{ state?.plan?.expired ? '套餐已过期' : '服务生效中' }}</b>
        </div>
        <h2>订阅与账单</h2>
        <p>查看当前套餐、账号配额、AI 调用额度、订阅订单和付款凭证状态。</p>
        <div class="billing-command-meta">
          <span>当前套餐 {{ state?.plan?.name || '—' }}</span>
          <span>周期 {{ durationDays }} 天</span>
          <span>{{ pendingOrders.length }} 个待确认订单</span>
        </div>
      </div>
      <div class="billing-command-panel">
        <div class="billing-command-panel-head">
          <span>账单动作</span>
          <strong>{{ loading ? '刷新中' : '可操作' }}</strong>
        </div>
        <button class="billing-btn primary" type="button" :disabled="loading" @click="loadAll">
          {{ loading ? '刷新中...' : '刷新账单' }}
        </button>
        <div class="billing-command-stats">
          <div>
            <span>订单流水</span>
            <strong>{{ orders.length }}</strong>
          </div>
          <div>
            <span>待确认</span>
            <strong>{{ pendingOrders.length }}</strong>
          </div>
          <div>
            <span>账号用量</span>
            <strong>{{ usage.accounts.used }} / {{ displayLimit(usage.accounts.limit) }}</strong>
          </div>
        </div>
      </div>
    </section>

    <section class="billing-overview-grid">
      <article class="billing-panel plan-summary-panel">
        <header class="billing-panel-head">
          <div>
            <span>当前套餐</span>
            <h3>套餐状态</h3>
          </div>
          <b>{{ state?.plan?.code || 'free' }}</b>
        </header>
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
        <div class="current-features">
          <span
            v-for="feature in currentFeatureItems"
            :key="feature.key"
            :class="{ off: !feature.enabled }"
          >
            {{ feature.label }}
          </span>
        </div>
      </article>

      <article class="billing-panel quota-panel">
        <header class="billing-panel-head">
          <div>
            <span>账号配额</span>
            <h3>账号绑定</h3>
          </div>
          <b>剩余 {{ displayRemaining(usage.accounts.remaining, usage.accounts.limit) }}</b>
        </header>
        <div class="quota-main">
          <strong>{{ usage.accounts.used }}</strong>
          <span>/ {{ displayLimit(usage.accounts.limit) }}</span>
        </div>
        <div class="quota-bar">
          <progress :value="percent(usage.accounts.used, usage.accounts.limit)" max="100" aria-label="账号配额使用率"></progress>
        </div>
        <p>剩余 {{ displayRemaining(usage.accounts.remaining, usage.accounts.limit) }} 个闲鱼账号可绑定。</p>
      </article>

      <article class="billing-panel quota-panel">
        <header class="billing-panel-head">
          <div>
            <span>AI 今日额度</span>
            <h3>模型调用</h3>
          </div>
          <b>{{ displayLimit(usage.aiCallsToday.limit) }}</b>
        </header>
        <div class="quota-main">
          <strong>{{ usage.aiCallsToday.used }}</strong>
          <span>/ {{ displayLimit(usage.aiCallsToday.limit) }}</span>
        </div>
        <div class="quota-bar ai">
          <progress :value="percent(usage.aiCallsToday.used, usage.aiCallsToday.limit)" max="100" aria-label="AI 今日额度使用率"></progress>
        </div>
        <p>AI 客服验证、RAG 对话、货源推荐等会计入调用次数。</p>
      </article>
    </section>

    <section class="billing-panel audit-panel-shell">
      <header class="billing-panel-head">
        <div>
          <span>用量审计</span>
          <h3>用量与配额事件</h3>
        </div>
        <b>最近 20 条记录</b>
      </header>
      <div class="audit-grid">
        <section class="audit-panel">
          <div class="audit-title">
            <strong>每日用量</strong>
            <span>{{ usageDailyRows.length }} 条</span>
          </div>
          <div class="table-wrap">
            <table class="billing-table compact">
              <thead>
                <tr>
                  <th>日期</th>
                  <th>指标</th>
                  <th>已用</th>
                  <th>上限</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="usageDailyRows.length === 0">
                  <td colspan="4" class="empty-cell">暂无用量记录</td>
                </tr>
                <tr v-for="row in usageDailyRows" :key="row.id">
                  <td>{{ row.usageDate || '—' }}</td>
                  <td>{{ row.metricLabel || row.metric }}</td>
                  <td>{{ row.usedCount }}</td>
                  <td>{{ displayLimit(row.limitCount) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
        <section class="audit-panel">
          <div class="audit-title">
            <strong>配额事件</strong>
            <span>{{ quotaEventRows.length }} 条</span>
          </div>
          <div class="table-wrap">
            <table class="billing-table compact">
              <thead>
                <tr>
                  <th>时间</th>
                  <th>指标</th>
                  <th>变化</th>
                  <th>来源</th>
                  <th>原因</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="quotaEventRows.length === 0">
                  <td colspan="5" class="empty-cell">暂无配额事件</td>
                </tr>
                <tr v-for="row in quotaEventRows" :key="row.id">
                  <td>{{ fmt(row.createdTime) }}</td>
                  <td>{{ row.metricLabel || row.metric }}</td>
                  <td><span :class="['delta-pill', Number(row.delta || 0) > 0 ? 'plus' : 'zero']">{{ eventDelta(row.delta) }}</span></td>
                  <td>{{ sourceText(row.sourceType) }}</td>
                  <td class="reason-cell">{{ row.reason || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </section>

    <section class="billing-panel plan-catalog-panel">
      <header class="billing-panel-head catalog-head">
        <div>
          <span>订阅升级</span>
          <h3>可选套餐</h3>
        </div>
        <div class="order-options">
          <label class="duration-picker">
            <span>周期</span>
            <select v-model.number="durationDays" @change="clearCouponPreview">
              <option :value="30">1 个月</option>
              <option :value="90">3 个月</option>
              <option :value="180">6 个月</option>
              <option :value="365">12 个月</option>
            </select>
          </label>
          <label class="coupon-picker">
            <span>优惠码</span>
            <input v-model.trim="couponCode" type="text" placeholder="可选" @input="clearCouponPreview" />
          </label>
        </div>
      </header>
      <div class="plan-catalog">
        <div v-for="plan in plans" :key="plan.code" :class="['plan-item', { active: currentPlanCode === plan.code }]">
          <div class="plan-item-head">
            <div class="plan-title-stack">
              <strong>{{ plan.name }}</strong>
              <span>
                <code>{{ plan.code }}</code>
                <i v-if="currentPlanCode === plan.code" class="plan-current-tag">当前</i>
              </span>
            </div>
            <div class="price">
              <template v-if="previewFor(plan)">
                <em>{{ money(previewFor(plan).listAmountCents) }}</em>
                {{ money(previewFor(plan).payableAmountCents) }}
                <span>/ 当前周期</span>
              </template>
              <template v-else>
                {{ money(plan.priceCents) }}<span>/ 月</span>
              </template>
            </div>
          </div>
          <p>{{ plan.description || '适合标准闲鱼运营场景，可按需升级。' }}</p>
          <div class="plan-features">
            <span>{{ displayLimit(plan.maxAccounts) }} 个账号</span>
            <span>{{ displayLimit(plan.aiDailyQuota) }} 次 AI/日</span>
          </div>
          <div class="plan-feature-grid">
            <span
              v-for="feature in plan.featureItems || []"
              :key="feature.key"
              :class="{ off: !feature.enabled }"
            >
              {{ feature.label }}
            </span>
          </div>
          <div v-if="previewFor(plan)" class="coupon-result">
            <span>{{ previewFor(plan).couponCode }}</span>
            已抵扣 {{ money(previewFor(plan).discountCents) }}
          </div>
          <div class="plan-actions">
            <button
              v-if="couponCode && plan.priceCents > 0"
              class="billing-btn"
              type="button"
              :disabled="couponBusy === plan.code || orderBusy"
              @click="previewCoupon(plan)"
            >
              {{ couponBusy === plan.code ? '试算中...' : '试算优惠' }}
            </button>
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
      </div>
    </section>

    <section v-if="paymentConfig.enabled || pendingOrders.length" class="billing-panel payment-panel">
      <header class="billing-panel-head">
        <div>
          <span>支付说明</span>
          <h3>付款与确认</h3>
        </div>
        <b>付费订单需平台确认后生效</b>
      </header>
      <div class="payment-layout">
        <div class="payment-copy">
          <p>{{ paymentConfig.instructions || '请联系平台确认付款方式。付款完成后，平台会确认订单并开通套餐。' }}</p>
          <div v-if="paymentConfig.contact" class="payment-line">
            <span>联系方式</span>
            <strong>{{ paymentConfig.contact }}</strong>
          </div>
          <div v-if="paymentConfig.bankAccount" class="payment-line">
            <span>收款账户</span>
            <strong>{{ paymentConfig.bankAccount }}</strong>
          </div>
          <div class="payment-line">
            <span>订单有效期</span>
            <strong>{{ Math.round((paymentConfig.orderExpireMinutes || 1440) / 60) }} 小时</strong>
          </div>
        </div>
        <div class="payment-qr-list">
          <figure v-if="paymentConfig.alipayQrUrl">
            <img :src="paymentConfig.alipayQrUrl" alt="支付宝收款码" />
            <figcaption>支付宝</figcaption>
          </figure>
          <figure v-if="paymentConfig.wechatQrUrl">
            <img :src="paymentConfig.wechatQrUrl" alt="微信收款码" />
            <figcaption>微信</figcaption>
          </figure>
        </div>
      </div>
    </section>

    <section class="billing-panel order-panel">
      <header class="billing-panel-head">
        <div>
          <span>订单流水</span>
          <h3>订单记录</h3>
        </div>
        <b>{{ orders.length }} 条</b>
      </header>
      <div class="table-wrap">
        <table class="billing-table">
          <thead>
            <tr>
              <th>订单号</th>
              <th>套餐</th>
              <th>优惠</th>
              <th>金额</th>
              <th>周期</th>
              <th>状态</th>
              <th>付款凭证</th>
              <th>有效期</th>
              <th>创建时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="orders.length === 0">
              <td colspan="10" class="empty-cell">暂无订单</td>
            </tr>
            <tr v-for="order in orders" :key="order.id">
              <td><code>{{ order.orderNo }}</code></td>
              <td>{{ order.planCode }}</td>
              <td>{{ order.discountCents ? `${order.couponCode || '优惠'} -${money(order.discountCents)}` : '—' }}</td>
              <td>{{ money(order.amountCents) }}</td>
              <td>{{ order.durationDays }} 天</td>
              <td><span :class="['status-pill', order.status]">{{ statusText(order.status) }}</span></td>
              <td>
                <span :class="['proof-pill', proofStatus(order)]" :title="proofTitle(order)">
                  {{ proofStatusText(order) }}
                </span>
              </td>
              <td>{{ fmt(order.expireTime) }}</td>
              <td>{{ fmt(order.createdTime) }}</td>
              <td class="order-actions">
                <button
                  v-if="order.status === 'pending' && order.amountCents > 0"
                  class="billing-btn small primary"
                  type="button"
                  :disabled="orderBusy"
                  @click="openPaymentProof(order)"
                >
                  {{ order.paymentProof ? '更新凭证' : '提交凭证' }}
                </button>
                <button
                  v-if="order.status === 'pending'"
                  class="billing-btn small"
                  type="button"
                  :disabled="orderBusy"
                  @click="closeOrder(order)"
                >
                  取消
                </button>
                <span v-else class="muted">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <div v-if="paymentProofTarget" class="billing-modal-mask" @click.self="closePaymentProof">
      <div class="billing-modal-card">
        <div class="billing-modal-head">
          <div>
            <h3>提交付款凭证</h3>
            <p>{{ paymentProofTarget.orderNo }} · 应付 {{ money(paymentProofTarget.amountCents) }}</p>
          </div>
          <button type="button" aria-label="关闭" @click="closePaymentProof">×</button>
        </div>
        <div class="proof-form">
          <label>
            <span>实付金额（元）</span>
            <input v-model.trim="paymentProofForm.paidAmountYuan" type="number" min="0.01" step="0.01" />
          </label>
          <label>
            <span>付款时间</span>
            <input v-model="paymentProofForm.paidAt" type="datetime-local" />
          </label>
          <label>
            <span>支付渠道</span>
            <input v-model.trim="paymentProofForm.channel" placeholder="支付宝 / 微信 / 银行转账" />
          </label>
          <label>
            <span>付款人</span>
            <input v-model.trim="paymentProofForm.payerName" placeholder="付款账户名或昵称" />
          </label>
          <label class="wide">
            <span>交易单号</span>
            <input v-model.trim="paymentProofForm.transactionNo" placeholder="转账流水号 / 交易号" />
          </label>
          <label class="wide">
            <span>凭证图片 URL</span>
            <input v-model.trim="paymentProofForm.proofUrl" placeholder="https://..." />
          </label>
          <label class="wide">
            <span>备注</span>
            <textarea v-model.trim="paymentProofForm.remark" rows="3" placeholder="补充说明，例如付款账号后四位"></textarea>
          </label>
          <div class="proof-actions">
            <button class="billing-btn" type="button" @click="closePaymentProof">取消</button>
            <button class="billing-btn primary" type="button" :disabled="paymentProofBusy" @click="submitPaymentProof">
              {{ paymentProofBusy ? '提交中...' : '提交凭证' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { friendlyError } from '../utils/friendlyError.js'
import {
  closeBillingOrder,
  createBillingOrder,
  getBillingPlans,
  getMyBilling,
  getPaymentConfig,
  listMyQuotaEvents,
  listMyUsageDaily,
  listBillingOrders,
  previewBillingCoupon,
  submitBillingPaymentProof,
} from '../api/billing.js'

const state = ref(null)
const plans = ref([])
const orders = ref([])
const usageDailyRows = ref([])
const quotaEventRows = ref([])
const paymentConfig = ref({})
const loading = ref(false)
const orderBusy = ref(false)
const durationDays = ref(30)
const couponCode = ref('')
const couponPreview = ref(null)
const couponBusy = ref('')
const paymentProofTarget = ref(null)
const paymentProofBusy = ref(false)
const paymentProofForm = reactive({
  paidAmountYuan: '',
  paidAt: '',
  channel: '',
  payerName: '',
  transactionNo: '',
  proofUrl: '',
  remark: '',
})
const notice = ref('')
const noticeType = ref('success')

const emptyUsage = { used: 0, limit: 0, remaining: 0 }
const usage = computed(() => ({
  accounts: state.value?.usage?.accounts || emptyUsage,
  aiCallsToday: state.value?.usage?.aiCallsToday || emptyUsage,
}))
const currentPlanCode = computed(() => state.value?.plan?.code || 'free')
const pendingOrders = computed(() => orders.value.filter(order => order.status === 'pending'))
const currentFeatureItems = computed(() => state.value?.plan?.featureItems || [])

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

function yuanToCents(value) {
  return Math.round(Number(value || 0) * 100)
}

function centsToYuan(value) {
  return (Number(value || 0) / 100).toFixed(2)
}

function toDatetimeLocal(value) {
  if (!value) return ''
  return String(value).replace('T', ' ').slice(0, 16).replace(' ', 'T')
}

function proofStatus(order) {
  return order?.paymentProof?.status || 'none'
}

function proofStatusText(order) {
  const map = {
    submitted: '待核对',
    confirmed: '已确认',
    rejected: '已退回',
    none: '未提交',
  }
  return map[proofStatus(order)] || '未提交'
}

function proofTitle(order) {
  const proof = order?.paymentProof
  if (!proof) return '未提交付款凭证'
  return [
    proof.channel ? `渠道：${proof.channel}` : '',
    proof.payerName ? `付款人：${proof.payerName}` : '',
    proof.transactionNo ? `交易号：${proof.transactionNo}` : '',
    proof.paidAmountCents ? `实付：${money(proof.paidAmountCents)}` : '',
    proof.remark ? `备注：${proof.remark}` : '',
  ].filter(Boolean).join('\n') || '已提交付款凭证'
}

function clearCouponPreview() {
  couponPreview.value = null
}

function previewFor(plan) {
  return couponPreview.value?.planCode === plan.code ? couponPreview.value : null
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

function eventDelta(delta) {
  const n = Number(delta || 0)
  return n > 0 ? `+${n}` : String(n)
}

function sourceText(sourceType) {
  const map = {
    ai: 'AI 调用',
    quota_block: '配额拦截',
    feature_block: '权益拦截',
  }
  return map[sourceType] || sourceType || '系统'
}

async function loadAll() {
  if (loading.value) return
  loading.value = true
  try {
    const [billingRes, plansRes, ordersRes, paymentRes, usageRes, eventRes] = await Promise.all([
      getMyBilling(),
      getBillingPlans(),
      listBillingOrders({ current: 1, size: 50 }),
      getPaymentConfig(),
      listMyUsageDaily({ current: 1, size: 20 }),
      listMyQuotaEvents({ current: 1, size: 20 }),
    ])
    state.value = billingRes.data || null
    plans.value = plansRes.data || []
    orders.value = ordersRes.data?.records || []
    paymentConfig.value = paymentRes.data || {}
    usageDailyRows.value = usageRes.data?.records || []
    quotaEventRows.value = eventRes.data?.records || []
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
      durationDays: durationDays.value || 30,
      paymentMethod: 'manual',
      couponCode: couponCode.value || '',
    })
    if (res.data?.paymentConfig) paymentConfig.value = res.data.paymentConfig
    flash(res.data?.message || '订单已创建')
    await loadAll()
  } catch (error) {
    flash(friendlyError(error, '创建订单失败'), 'error')
  } finally {
    orderBusy.value = false
  }
}

async function previewCoupon(plan) {
  if (!plan || !couponCode.value || couponBusy.value) return
  couponBusy.value = plan.code
  try {
    const res = await previewBillingCoupon({
      planCode: plan.code,
      durationDays: durationDays.value || 30,
      couponCode: couponCode.value,
    })
    couponPreview.value = res.data || null
    flash(`优惠码已抵扣 ${money(couponPreview.value?.discountCents)}`)
  } catch (error) {
    couponPreview.value = null
    flash(friendlyError(error, '优惠码不可用'), 'error')
  } finally {
    couponBusy.value = ''
  }
}

function openPaymentProof(order) {
  if (!order) return
  const proof = order.paymentProof || {}
  paymentProofTarget.value = order
  paymentProofForm.paidAmountYuan = centsToYuan(proof.paidAmountCents || order.amountCents)
  paymentProofForm.paidAt = toDatetimeLocal(proof.paidAt)
  paymentProofForm.channel = proof.channel || ''
  paymentProofForm.payerName = proof.payerName || ''
  paymentProofForm.transactionNo = proof.transactionNo || ''
  paymentProofForm.proofUrl = proof.proofUrl || ''
  paymentProofForm.remark = proof.remark || ''
}

function closePaymentProof() {
  paymentProofTarget.value = null
  paymentProofBusy.value = false
}

async function submitPaymentProof() {
  if (!paymentProofTarget.value || paymentProofBusy.value) return
  const paidAmountCents = yuanToCents(paymentProofForm.paidAmountYuan)
  if (paidAmountCents <= 0) {
    flash('请填写有效的实付金额', 'error')
    return
  }
  paymentProofBusy.value = true
  try {
    await submitBillingPaymentProof(paymentProofTarget.value.id, {
      paidAmountCents,
      paidAt: paymentProofForm.paidAt || null,
      channel: paymentProofForm.channel,
      payerName: paymentProofForm.payerName,
      transactionNo: paymentProofForm.transactionNo,
      proofUrl: paymentProofForm.proofUrl,
      remark: paymentProofForm.remark,
    })
    flash('付款凭证已提交')
    closePaymentProof()
    await loadAll()
  } catch (error) {
    flash(friendlyError(error, '提交付款凭证失败'), 'error')
  } finally {
    paymentProofBusy.value = false
  }
}

async function closeOrder(order) {
  if (!order || orderBusy.value) return
  if (!window.confirm(`确认取消订单 ${order.orderNo}？`)) return
  orderBusy.value = true
  try {
    await closeBillingOrder(order.id, { reason: 'user_cancel' })
    flash('订单已取消')
    await loadAll()
  } catch (error) {
    flash(friendlyError(error, '取消订单失败'), 'error')
  } finally {
    orderBusy.value = false
  }
}

onMounted(loadAll)
</script>

<style scoped>
.billing-page {
  --billing-ease: cubic-bezier(0.23, 1, 0.32, 1);
  --billing-ink: #0f172a;
  --billing-muted: #64748b;
  --billing-line: #dfe7f1;
  --billing-surface: #ffffff;
  display: grid;
  gap: 18px;
  min-width: 0;
  color: var(--billing-ink);
}

.billing-notice {
  padding: 11px 13px;
  border-radius: 8px;
  border: 1px solid #bbf7d0;
  background: #f0fdf4;
  color: #166534;
  box-shadow: 0 8px 20px rgba(22, 101, 52, .06);
}

.billing-notice.error {
  border-color: #fecaca;
  background: #fef2f2;
  color: #b91c1c;
}

.billing-command-center {
  position: relative;
  overflow: hidden;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 18px;
  padding: 22px;
  border: 1px solid #dbe3ef;
  border-radius: 8px;
  background:
    linear-gradient(135deg, rgba(15, 118, 110, .08), rgba(37, 99, 235, .06) 44%, rgba(245, 158, 11, .08)),
    #ffffff;
  box-shadow: 0 16px 38px rgba(15, 23, 42, .07);
}

.billing-command-center::before {
  content: "";
  position: absolute;
  inset: 0 0 auto;
  height: 3px;
  background: linear-gradient(90deg, #0f766e, #2563eb, #f59e0b);
}

.billing-command-main {
  position: relative;
  min-width: 0;
}

.billing-command-kicker,
.billing-command-meta,
.billing-command-panel-head,
.billing-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.billing-command-kicker {
  justify-content: flex-start;
}

.billing-command-kicker span,
.billing-command-panel-head span,
.billing-panel-head span {
  color: #0f766e;
  font-size: 12px;
  font-weight: 750;
}

.billing-command-kicker b,
.billing-command-panel-head strong,
.billing-panel-head b {
  color: #475569;
  font-size: 12px;
  font-weight: 700;
}

.billing-command-main h2 {
  margin: 12px 0 8px;
  color: #0f172a;
  font-size: 26px;
  font-weight: 780;
  line-height: 1.25;
}

.billing-command-main p,
.billing-panel p,
.muted {
  margin: 0;
  color: #64748b;
  font-size: 14px;
  line-height: 1.7;
}

.billing-command-meta {
  justify-content: flex-start;
  flex-wrap: wrap;
  margin-top: 18px;
}

.billing-command-meta span,
.billing-command-panel {
  border: 1px solid rgba(148, 163, 184, .32);
  border-radius: 8px;
  background: rgba(255, 255, 255, .78);
}

.billing-command-meta span {
  padding: 7px 10px;
  color: #334155;
  font-size: 12px;
}

.billing-command-panel {
  position: relative;
  display: grid;
  align-content: start;
  gap: 12px;
  padding: 16px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, .72);
}

.billing-command-panel > .billing-btn {
  width: 100%;
}

.billing-command-stats {
  display: grid;
  gap: 8px;
  padding-top: 4px;
}

.billing-command-stats div {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 9px 10px;
  border-radius: 7px;
  background: rgba(248, 250, 252, .86);
}

.billing-command-stats span {
  color: #64748b;
  font-size: 12px;
}

.billing-command-stats strong {
  color: #0f172a;
  font-size: 13px;
  font-weight: 760;
}

.billing-overview-grid {
  display: grid;
  grid-template-columns: 1.2fr repeat(2, minmax(0, .9fr));
  gap: 16px;
  align-items: stretch;
}

.billing-panel {
  min-width: 0;
  padding: 16px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 10px 26px rgba(15, 23, 42, .05);
}

.plan-summary-panel {
  position: relative;
  overflow: hidden;
  border-color: rgba(15, 23, 42, .92);
  background:
    linear-gradient(160deg, rgba(20, 184, 166, .18), rgba(37, 99, 235, .06) 38%, transparent 62%),
    #101827;
  box-shadow: 0 18px 36px rgba(15, 23, 42, .18);
}

.plan-summary-panel .billing-panel-head span,
.plan-summary-panel .billing-panel-head h3,
.plan-summary-panel .billing-panel-head b,
.plan-summary-panel .plan-name,
.plan-summary-panel .summary-row strong {
  color: #f8fafc;
}

.plan-summary-panel .plan-code {
  color: #67e8f9;
}

.plan-summary-panel .summary-row {
  border-top-color: rgba(148, 163, 184, .24);
  color: #cbd5e1;
}

.plan-summary-panel .current-features span {
  background: rgba(20, 184, 166, .15);
  color: #99f6e4;
}

.plan-summary-panel .current-features span.off {
  background: rgba(148, 163, 184, .14);
  color: #94a3b8;
}

.quota-panel {
  position: relative;
  overflow: hidden;
  min-height: 190px;
}

.quota-panel::before {
  content: "";
  position: absolute;
  inset: 0 0 auto;
  height: 3px;
  background: #0f766e;
}

.billing-overview-grid .quota-panel:nth-child(3)::before {
  background: #2563eb;
}

.billing-panel-head {
  align-items: flex-start;
  margin-bottom: 14px;
}

.billing-panel-head h3 {
  margin: 4px 0 0;
  color: #0f172a;
  font-size: 17px;
  font-weight: 760;
  line-height: 1.25;
}

.catalog-head {
  align-items: center;
}

.duration-picker {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #64748b;
  font-size: 13px;
}

.order-options {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.coupon-picker {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #64748b;
  font-size: 13px;
}

.duration-picker select,
.coupon-picker input {
  height: 30px;
  padding: 0 8px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #fff;
  color: #111827;
}

.coupon-picker input {
  width: 138px;
  text-transform: uppercase;
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

.current-features {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 12px;
}

.current-features span,
.plan-feature-grid span {
  padding: 2px 7px;
  border-radius: 999px;
  background: #eefbf6;
  color: #0f766e;
  font-size: 12px;
}

.current-features span.off,
.plan-feature-grid span.off {
  background: #f1f5f9;
  color: #94a3b8;
  text-decoration: line-through;
}

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

.quota-bar progress {
  display: block;
  width: 100%;
  height: 100%;
  overflow: hidden;
  appearance: none;
  border: 0;
  border-radius: inherit;
  background: transparent;
}

.quota-bar progress::-webkit-progress-bar {
  border-radius: inherit;
  background: #eef2f7;
}

.quota-bar progress::-webkit-progress-value {
  border-radius: inherit;
  background: #0f766e;
}

.quota-bar progress::-moz-progress-bar {
  border-radius: inherit;
  background: #0f766e;
}

.quota-bar.ai progress::-webkit-progress-value {
  background: #2563eb;
}

.quota-bar.ai progress::-moz-progress-bar {
  background: #2563eb;
}

.plan-catalog {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 14px;
}

.plan-item {
  position: relative;
  display: grid;
  gap: 12px;
  padding: 14px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fbfdff;
  transition:
    transform 160ms var(--billing-ease),
    border-color 160ms var(--billing-ease),
    box-shadow 160ms var(--billing-ease),
    background 160ms var(--billing-ease);
}

.plan-item:hover {
  transform: translateY(-1px);
  border-color: #cbd5e1;
  box-shadow: 0 14px 28px rgba(15, 23, 42, .08);
}

.plan-item.active {
  border-color: #0f766e;
  background: linear-gradient(180deg, #f0fdfa, #ffffff);
}

.plan-item.active::before {
  content: "";
  position: absolute;
  inset: 0 0 auto;
  height: 3px;
  border-radius: 8px 8px 0 0;
  background: #0f766e;
}

.plan-item-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.plan-title-stack {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.plan-title-stack span {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
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

.plan-current-tag {
  display: inline-flex;
  align-items: center;
  height: 20px;
  padding: 0 7px;
  border-radius: 999px;
  background: #ccfbf1;
  color: #0f766e;
  font-size: 12px;
  font-style: normal;
  font-weight: 760;
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

.price em {
  display: block;
  color: #94a3b8;
  font-size: 12px;
  font-style: normal;
  font-weight: 500;
  text-decoration: line-through;
}

.coupon-result {
  padding: 8px 10px;
  border: 1px solid #bfdbfe;
  border-radius: 6px;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 12px;
}

.coupon-result span {
  margin-right: 6px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-weight: 700;
}

.plan-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
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

.plan-feature-grid {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.payment-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 18px;
  align-items: start;
}

.payment-copy {
  display: grid;
  gap: 10px;
  min-width: 0;
}

.payment-line {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  color: #64748b;
  font-size: 13px;
}

.payment-line span {
  width: 72px;
  flex: 0 0 auto;
}

.payment-line strong {
  min-width: 0;
  color: #111827;
  font-weight: 650;
  white-space: pre-wrap;
  word-break: break-word;
}

.payment-qr-list {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.payment-qr-list figure {
  margin: 0;
  width: 112px;
  text-align: center;
  color: #64748b;
  font-size: 12px;
}

.payment-qr-list img {
  width: 112px;
  height: 112px;
  object-fit: cover;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #fff;
  box-shadow: 0 10px 22px rgba(15, 23, 42, .08);
}

.audit-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.audit-panel {
  min-width: 0;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #fbfdff;
}

.audit-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.audit-title strong {
  color: #111827;
  font-size: 14px;
}

.audit-title span {
  color: #64748b;
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
  font-weight: 650;
  transition:
    transform 140ms var(--billing-ease),
    border-color 140ms var(--billing-ease),
    background 140ms var(--billing-ease),
    box-shadow 140ms var(--billing-ease);
}

.billing-btn:not(:disabled):hover {
  border-color: #94a3b8;
  background: #f8fafc;
  box-shadow: 0 8px 18px rgba(15, 23, 42, .08);
}

.billing-btn:not(:disabled):active {
  transform: scale(.97);
}

.billing-btn.primary {
  border-color: #2563eb;
  background: #2563eb;
  color: #fff;
}

.billing-btn.primary:not(:disabled):hover {
  border-color: #1d4ed8;
  background: #1d4ed8;
}

.billing-btn.small {
  height: 28px;
  padding: 0 10px;
  font-size: 12px;
}

.billing-btn:disabled {
  opacity: .55;
  cursor: not-allowed;
}

.order-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.table-wrap {
  overflow-x: auto;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
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
  background: #f8fafc;
  color: #64748b;
  font-weight: 650;
}

.billing-table tbody tr:last-child td {
  border-bottom: 0;
}

.billing-table tbody tr:hover td {
  background: #f8fafc;
}

.billing-table.compact {
  font-size: 12px;
}

.billing-table.compact th,
.billing-table.compact td {
  padding: 9px 8px;
}

.reason-cell {
  max-width: 220px;
  white-space: normal !important;
  word-break: break-word;
}

.delta-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  padding: 2px 7px;
  border-radius: 999px;
  background: #f1f5f9;
  color: #64748b;
}

.delta-pill.plus {
  background: #dcfce7;
  color: #15803d;
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

.proof-pill {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  background: #f1f5f9;
  color: #64748b;
  font-size: 12px;
}

.proof-pill.submitted {
  background: #dbeafe;
  color: #1d4ed8;
}

.proof-pill.confirmed {
  background: #dcfce7;
  color: #15803d;
}

.proof-pill.rejected {
  background: #fee2e2;
  color: #b91c1c;
}

.billing-modal-mask {
  position: fixed;
  inset: 0;
  z-index: 80;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: rgba(15, 23, 42, .36);
  backdrop-filter: blur(5px);
}

.billing-modal-card {
  width: min(680px, 94vw);
  max-height: 90vh;
  overflow: auto;
  border: 1px solid rgba(226, 232, 240, .9);
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 18px 50px rgba(15, 23, 42, .22);
  padding: 18px;
}

.billing-modal-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}

.billing-modal-head h3 {
  margin: 0 0 4px;
  color: #111827;
  font-size: 17px;
}

.billing-modal-head p {
  margin: 0;
}

.billing-modal-head button {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  border: 0;
  background: #f8fafc;
  color: #64748b;
  cursor: pointer;
  font-size: 24px;
  line-height: 1;
  transition: transform 140ms var(--billing-ease), background 140ms var(--billing-ease);
}

.billing-modal-head button:hover {
  background: #eef2f7;
}

.billing-modal-head button:active {
  transform: scale(.94);
}

.proof-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.proof-form label {
  display: grid;
  gap: 6px;
  color: #64748b;
  font-size: 13px;
}

.proof-form .wide,
.proof-actions {
  grid-column: 1 / -1;
}

.proof-form input,
.proof-form textarea {
  width: 100%;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #fff;
  color: #111827;
  font: inherit;
  padding: 8px 9px;
}

.proof-form input:focus,
.proof-form textarea:focus,
.duration-picker select:focus,
.coupon-picker input:focus {
  outline: 2px solid rgba(37, 99, 235, .18);
  border-color: #2563eb;
}

.proof-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

@media (max-width: 980px) {
  .billing-command-center,
  .billing-overview-grid {
    grid-template-columns: 1fr;
  }

  .billing-command-center {
    padding: 18px;
  }

  .catalog-head {
    align-items: flex-start;
    flex-direction: column;
  }

  .order-options {
    justify-content: flex-start;
  }

  .payment-layout {
    grid-template-columns: 1fr;
  }

  .payment-qr-list {
    justify-content: flex-start;
  }

  .audit-grid {
    grid-template-columns: 1fr;
  }

  .proof-form {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .billing-command-main h2 {
    font-size: 22px;
  }

  .billing-command-kicker,
  .billing-command-panel-head,
  .billing-panel-head,
  .plan-item-head,
  .payment-line,
  .order-actions {
    align-items: flex-start;
    flex-direction: column;
  }

  .billing-panel,
  .billing-command-center {
    padding: 14px;
  }

  .duration-picker,
  .coupon-picker,
  .duration-picker select,
  .coupon-picker input,
  .plan-actions .billing-btn,
  .proof-actions .billing-btn {
    width: 100%;
  }

  .payment-line span {
    width: auto;
  }

  .payment-qr-list figure,
  .payment-qr-list img {
    width: 96px;
  }

  .payment-qr-list img {
    height: 96px;
  }

  .proof-actions {
    flex-direction: column-reverse;
  }
}
</style>
