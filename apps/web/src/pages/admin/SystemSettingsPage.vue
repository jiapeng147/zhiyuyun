<template>
  <div class="ops-system-settings system-settings-page system-main system-v9-shell">
    <div v-if="error" class="global-notice error">{{ error }}</div>
    <div v-if="success" class="global-notice success">{{ success }}</div>

    <section class="system-hero">
      <div class="system-hero-copy">
        <span class="system-kicker">System Operations</span>
        <h1>系统运营控制台</h1>
        <p>
          这里维护站点基础信息、广告服务运营状态和关键服务概览。高德地图、通用模型、向量模型与 RAG 知识库已经拆分成独立控制台，
          系统总览只保留平台级状态和基础配置。
        </p>

        <div class="system-hero-actions">
          <button type="button" class="system-save-btn" :disabled="saving || !configAvailable" @click="save">{{ saving ? '保存中...' : '保存配置' }}</button>
          <button type="button" class="system-reload-btn" :disabled="loading" @click="loadPage">{{ loading ? '加载中...' : '重新加载' }}</button>
        </div>
      </div>

      <aside class="system-status-panel" :class="{ ready: configAvailable && runtimeStatusAvailable }" aria-label="系统状态">
        <span>平台状态</span>
        <strong>{{ configAvailable ? '配置可用' : '状态未知' }}</strong>
        <div class="system-status-meter">
          <i :style="{ width: adServiceReady ? '82%' : (runtimeStatusAvailable ? '56%' : '28%') }"></i>
        </div>
        <p>{{ adServiceReady ? '广告服务与基础保护均已就绪。' : '站点配置可维护，部分服务请查看下方运行状态。' }}</p>
      </aside>
    </section>

    <section class="system-stat-grid" aria-label="系统服务状态">
      <article
        v-for="item in systemStatCards"
        :key="item.key"
        class="system-stat-card"
        :class="item.tone"
      >
        <span class="system-stat-label">{{ item.title }}</span>
        <strong>{{ item.value }}</strong>
        <span class="system-stat-desc">{{ item.change }}</span>
      </article>
    </section>

    <div class="system-workspace">
      <div class="system-main-column">
        <section class="system-v9-card">
          <div class="system-card-head">
            <div>
              <span>Site Profile</span>
              <h3>站点基础配置</h3>
            </div>
            <p>站点名称、ICP 备案、Logo 与爬虫服务地址，会用于页面展示与平台服务调用。</p>
          </div>

          <div class="field-grid two">
            <label class="field">
              <span>站点名称（siteName）</span>
              <input v-model="form.siteName" class="input" placeholder="智鱼云" />
            </label>

            <label class="field">
              <span>ICP 备案号（icp）</span>
              <input v-model="form.icp" class="input" placeholder="例如：京ICP备XXXXXXXX号" />
            </label>

            <label class="field">
              <span>站点 Logo 地址</span>
              <input v-model="form.logoUrl" class="input" placeholder="例如：/static/logo.png" />
            </label>

            <label class="field">
              <span>爬虫服务地址（服务只读）</span>
              <input
                :value="form.crawlerBaseUrl"
                class="input"
                readonly
                aria-readonly="true"
                title="由 CRAWLER_BASE_URL 配置并在重启后生效"
              />
            </label>
          </div>
        </section>

        <section class="system-v9-card">
          <div class="system-card-head">
            <div>
              <span>Commercial Runtime</span>
              <h3>广告服务运营状态</h3>
            </div>
            <p>广告轮播、文字广告、套餐与投放申请由平台服务统一处理。敏感凭证仅在平台服务保存，页面只展示业务可用性。</p>
          </div>

          <div v-if="!runtimeStatusAvailable" class="service-notice">
            运行状态暂不可用，无法确认广告服务连接状态。点击上方「重新加载」可重试。
          </div>
          <div v-else class="ad-service-panel">
            <div class="ad-service-summary" :class="{ ready: adServiceReady }">
              <span>广告投放能力</span>
              <strong>{{ adServiceReady ? '可用' : '待接通' }}</strong>
              <p>{{ adServiceSummary }}</p>
            </div>

            <div class="ad-service-grid">
              <article
                v-for="item in adServiceCards"
                :key="item.key"
                class="ad-service-card"
                :class="item.tone"
              >
                <span>{{ item.title }}</span>
                <strong>{{ item.value }}</strong>
                <p>{{ item.desc }}</p>
              </article>
            </div>
          </div>

          <div v-if="runtimeStatusAvailable" class="service-capabilities">
            <h4 class="capabilities-title">业务保护</h4>
            <div class="capability-grid">
              <div
                v-for="item in adCapabilityCards"
                :key="item.key"
                class="capability-item"
              >
                <span class="capability-name">{{ item.title }}</span>
                <span class="capability-status" :class="item.ready ? 'ok' : 'warn'">
                  {{ item.ready ? '已就绪' : '待启用' }}
                </span>
                <span class="capability-desc">{{ item.desc }}</span>
              </div>
            </div>
            <p v-if="!allAdCapabilitiesEnabled" class="service-hint">
              业务保护全部就绪后，系统才会开放完整的广告展示、投放申请与支付能力。相关开关由平台服务完成检测后启用。
            </p>
            <p v-else class="service-hint ok">
              全部能力已就绪，系统可正常展示广告并接受用户投放申请。
            </p>
          </div>
        </section>
      </div>

      <aside class="system-side-column">
        <section class="system-v9-card">
          <div class="system-card-head">
            <div>
              <span>Configuration Notes</span>
              <h3>配置说明</h3>
            </div>
            <p>常见配置项的取值规则与注意事项。</p>
          </div>

          <ul class="hint-list">
            <li><strong>站点名称</strong>：显示在浏览器标题栏和登录页，建议保持简短（建议 ≤ 16 个字符）。</li>
            <li><strong>ICP 备案号</strong>：中国大陆服务器必须填写，否则前端底部不显示备案信息。海外服务器可留空。</li>
            <li><strong>站点 Logo 地址</strong>：可填写站内资源路径或公开可访问的图片地址。</li>
            <li><strong>爬虫服务地址</strong>：该地址会接收账号授权信息，只能由平台服务通过 <code>CRAWLER_BASE_URL</code> 配置并在重启后生效，浏览器页面不可修改。</li>
            <li><strong>高德地图 Key</strong>：用于发布商品页的地址搜索，请到"高德地图"页签配置。</li>
            <li><strong>通用模型 / 向量模型</strong>：分别到"模型配置"和"向量模型"页签配置。</li>
            <li><strong>RAG 知识库</strong>：到"RAG 知识库"页签管理文档与检索验证。</li>
          </ul>
        </section>

        <section class="system-v9-card">
          <div class="system-card-head">
            <div>
              <span>Knowledge Snapshot</span>
              <h3>知识库概览</h3>
            </div>
            <p>系统总览页保留一个轻量概览，便于确认 RAG 知识库模块是否已经接入。</p>
          </div>
          <div class="knowledge-summary">
            <strong>{{ knowledgeBaseSummary.available ? knowledgeBaseSummary.total : '—' }}</strong>
            <span>当前知识库数量</span>
            <p v-if="!knowledgeBaseSummary.available" class="global-notice error">知识库概览暂不可用，当前无法确认数量。</p>
            <p>如需查看文档、切片与检索验证，请前往左侧“RAG 知识库”页签继续操作。</p>
          </div>
        </section>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive } from 'vue'
import { listKnowledgeBases } from '../../api/rag.js'
import {
  cloneOpenSourceConfig,
  useOpenSourceSettings,
} from '../../composables/useOpenSourceSettings.js'

const {
  loading,
  saving,
  error,
  success,
  config,
  runtimeStatus,
  configAvailable,
  runtimeStatusAvailable,
  loadBundle,
  saveConfig,
} = useOpenSourceSettings()

const form = reactive({
  siteName: '',
  icp: '',
  logoUrl: '',
  crawlerBaseUrl: '',
})

const knowledgeBaseSummary = reactive({
  total: 0,
  available: false,
})

const summary = computed(() => {
  return {
    generalModel: config.generalModel.modelName || '未配置',
    generalModelHint: runtimeStatusAvailable.value
      ? (runtimeStatus.generalModelConfigured ? '已具备必要配置' : '缺少必要参数')
      : '运行状态暂不可用',
    embeddingModel: config.embeddingModel.modelName || '未配置',
    embeddingModelHint: runtimeStatusAvailable.value
      ? (runtimeStatus.embeddingModelConfigured ? '已具备必要配置' : '缺少必要参数')
      : '运行状态暂不可用',
    redisStatus: runtimeStatusAvailable.value ? (runtimeStatus.redisConnected ? '已连接' : '不可用') : '状态未知',
    redisMode: runtimeStatusAvailable.value
      ? (runtimeStatus.redisConnected ? '共享 Redis 正常' : '认证与限流暂不可用')
      : '运行状态暂不可用'
  }
})

const systemStatCards = computed(() => [
  {
    key: 'general',
    title: '通用模型',
    value: configAvailable.value ? summary.value.generalModel : '状态未知',
    change: summary.value.generalModelHint,
    tone: runtimeStatusAvailable.value && runtimeStatus.generalModelConfigured ? 'is-ok' : 'is-warn'
  },
  {
    key: 'embedding',
    title: '向量模型',
    value: configAvailable.value ? summary.value.embeddingModel : '状态未知',
    change: summary.value.embeddingModelHint,
    tone: runtimeStatusAvailable.value && runtimeStatus.embeddingModelConfigured ? 'is-ok' : 'is-info'
  },
  {
    key: 'amap',
    title: '高德地图',
    value: runtimeStatusAvailable.value ? (runtimeStatus.amapConfigured ? '已配置' : '待配置') : '状态未知',
    change: configAvailable.value ? (config.amapApiKeyConfigured ? 'Key 已填写' : '未填写 Key') : '配置暂不可用',
    tone: runtimeStatusAvailable.value && runtimeStatus.amapConfigured ? 'is-ok' : 'is-warn'
  },
  {
    key: 'redis',
    title: 'Redis 状态',
    value: summary.value.redisStatus,
    change: summary.value.redisMode,
    tone: runtimeStatusAvailable.value && runtimeStatus.redisConnected ? 'is-ok' : 'is-warn'
  }
])

const allAdCapabilitiesEnabled = computed(() => {
  if (!runtimeStatusAvailable.value) return false
  return Boolean(runtimeStatus.commercialMutationIdempotencyEnabled)
    && Boolean(runtimeStatus.commercialPaymentIdempotencyEnabled)
    && Boolean(runtimeStatus.commercialPaidAdPlacementEnforced)
})

const adServiceReady = computed(() => {
  return runtimeStatusAvailable.value
    && runtimeStatus.commercialBridgeMode === 'commercial'
    && Boolean(runtimeStatus.commercialBridgeConnected)
    && allAdCapabilitiesEnabled.value
})

const adServiceSummary = computed(() => {
  if (!runtimeStatusAvailable.value) return '运行状态暂不可用，请稍后重试。'
  if (!runtimeStatus.commercialBridgeConfigured) return '广告服务尚未接入，前台不会展示未确认的广告内容。'
  if (!runtimeStatus.commercialBridgeConnected) return '广告服务已配置，但当前连通性待恢复。'
  if (!allAdCapabilitiesEnabled.value) return '基础服务已连通，部分业务保护尚未完成检测。'
  return '广告展示、投放申请与支付链路均已就绪。'
})

const adServiceCards = computed(() => [
  {
    key: 'access',
    title: '服务接入',
    value: runtimeStatus.commercialBridgeConnected ? '已接入' : (runtimeStatus.commercialBridgeConfigured ? '待恢复' : '未接入'),
    desc: runtimeStatus.commercialBridgeConnected ? '平台服务可正常获取广告业务数据' : '广告套餐、申请和支付保持关闭',
    tone: runtimeStatus.commercialBridgeConnected ? 'is-ok' : 'is-warn',
  },
  {
    key: 'application',
    title: '投放申请',
    value: runtimeStatus.commercialMutationIdempotencyEnabled ? '可提交' : '未开放',
    desc: runtimeStatus.commercialMutationIdempotencyEnabled ? '申请提交具备重复提交保护' : '申请入口会保持禁用，避免产生不确定订单',
    tone: runtimeStatus.commercialMutationIdempotencyEnabled ? 'is-ok' : 'is-info',
  },
  {
    key: 'payment',
    title: '支付链路',
    value: runtimeStatus.commercialPaymentIdempotencyEnabled ? '可下单' : '未开放',
    desc: runtimeStatus.commercialPaymentIdempotencyEnabled ? '支付订单具备重复请求保护' : '支付入口会保持禁用，避免重复扣费风险',
    tone: runtimeStatus.commercialPaymentIdempotencyEnabled ? 'is-ok' : 'is-info',
  },
  {
    key: 'display',
    title: '广告展示',
    value: runtimeStatus.commercialPaidAdPlacementEnforced ? '受保护' : '未开放',
    desc: runtimeStatus.commercialPaidAdPlacementEnforced ? '仅已生效广告可进入展示位' : '前台不会回退展示未确认广告',
    tone: runtimeStatus.commercialPaidAdPlacementEnforced ? 'is-ok' : 'is-info',
  },
])

const adCapabilityCards = computed(() => [
  {
    key: 'application',
    title: '申请保护',
    ready: Boolean(runtimeStatus.commercialMutationIdempotencyEnabled),
    desc: '避免同一投放申请被重复创建。',
  },
  {
    key: 'payment',
    title: '支付保护',
    ready: Boolean(runtimeStatus.commercialPaymentIdempotencyEnabled),
    desc: '避免同一支付订单被重复创建或关闭。',
  },
  {
    key: 'display',
    title: '展示保护',
    ready: Boolean(runtimeStatus.commercialPaidAdPlacementEnforced),
    desc: '确保只有已生效广告进入展示位。',
  },
])

onMounted(() => {
  window.addEventListener('xya-header-action', onHeaderAction)
  loadPage()
})

onBeforeUnmount(() => {
  window.removeEventListener('xya-header-action', onHeaderAction)
})

function syncForm() {
  form.siteName = config.siteName || ''
  form.icp = config.icp || ''
  form.logoUrl = config.logoUrl || ''
  form.crawlerBaseUrl = config.crawlerBaseUrl || ''
}

async function loadPage() {
  await Promise.all([
    loadBundle({ includeRuntimeStatus: true }),
    loadKnowledgeBaseSummary(),
  ])
  if (configAvailable.value) syncForm()
}

async function loadKnowledgeBaseSummary() {
  try {
    const res = await listKnowledgeBases({ current: 1, size: 1 })
    knowledgeBaseSummary.total = Number(res?.data?.total) || 0
    knowledgeBaseSummary.available = true
  } catch {
    knowledgeBaseSummary.available = false
  }
}

async function save() {
  if (!configAvailable.value) return
  const payload = cloneOpenSourceConfig(config)
  payload.siteName = form.siteName.trim()
  payload.icp = form.icp.trim()
  payload.logoUrl = form.logoUrl.trim()
  delete payload.crawlerBaseUrl
  const saved = await saveConfig(payload, { successMessage: '站点基础配置已保存' })
  if (!saved) return
  syncForm()
}

function onHeaderAction(event) {
  if (event.detail === 'settings-save') save()
  if (event.detail === 'settings-reload') loadPage()
}
</script>

<style scoped>
.system-v9-shell {
  --system-primary: #2563eb;
  --system-primary-dark: #1d4ed8;
  --system-accent: #0f766e;
  --system-warning: #f59e0b;
  --system-text: #111827;
  --system-muted: #64748b;
  --system-line: #e5e7eb;
  --system-panel: #ffffff;
  --system-soft: #f8fafc;
  --system-ease: cubic-bezier(0.23, 1, 0.32, 1);
  display: grid;
  gap: 16px;
  color: var(--system-text);
}

.system-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 16px;
  align-items: stretch;
}

.system-hero-copy,
.system-status-panel,
.system-stat-card,
.system-v9-card {
  border: 1px solid var(--system-line);
  border-radius: 8px;
  background: var(--system-panel);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05), 0 18px 42px rgba(15, 23, 42, 0.06);
}

.system-hero-copy {
  position: relative;
  overflow: hidden;
  min-height: 236px;
  padding: 28px;
  background:
    linear-gradient(120deg, rgba(255, 255, 255, 0.98), rgba(248, 251, 255, 0.96)),
    repeating-linear-gradient(90deg, rgba(37, 99, 235, 0.06) 0 1px, transparent 1px 40px);
}

.system-hero-copy::before {
  content: '';
  position: absolute;
  right: 30px;
  bottom: 26px;
  width: 238px;
  height: 132px;
  border: 1px solid rgba(37, 99, 235, 0.14);
  border-radius: 8px;
  background:
    linear-gradient(90deg, rgba(37, 99, 235, 0.12) 1px, transparent 1px),
    linear-gradient(180deg, rgba(15, 118, 110, 0.1) 1px, transparent 1px);
  background-size: 34px 34px;
  opacity: 0.68;
  transform: rotate(-3deg);
}

.system-kicker {
  position: relative;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  height: 28px;
  padding: 0 10px;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  background: #eff6ff;
  color: var(--system-primary-dark);
  font-size: 11px;
  font-weight: 850;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.system-hero-copy h1 {
  position: relative;
  z-index: 1;
  margin: 18px 0 10px;
  color: var(--system-text);
  font-size: 34px;
  line-height: 1.12;
  font-weight: 900;
  letter-spacing: 0;
}

.system-hero-copy p {
  position: relative;
  z-index: 1;
  max-width: 760px;
  margin: 0;
  color: var(--system-muted);
  font-size: 14px;
  line-height: 1.8;
}

.system-hero-actions {
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 22px;
}

.system-save-btn,
.system-reload-btn {
  min-height: 38px;
  padding: 0 15px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 850;
  cursor: pointer;
  transition:
    transform 140ms var(--system-ease),
    box-shadow 160ms var(--system-ease),
    border-color 160ms ease,
    background-color 160ms ease,
    color 160ms ease;
}

.system-save-btn {
  border: 1px solid transparent;
  background: linear-gradient(135deg, var(--system-primary), var(--system-accent));
  color: #ffffff;
  box-shadow: 0 12px 22px rgba(37, 99, 235, 0.18);
}

.system-reload-btn {
  border: 1px solid #bfdbfe;
  background: #ffffff;
  color: var(--system-primary-dark);
}

.system-save-btn:disabled,
.system-reload-btn:disabled {
  cursor: not-allowed;
  opacity: 0.62;
}

.system-status-panel {
  display: grid;
  align-content: space-between;
  gap: 14px;
  padding: 22px;
  background:
    linear-gradient(180deg, #ffffff 0%, #fffbeb 100%),
    repeating-linear-gradient(135deg, rgba(245, 158, 11, 0.08) 0 1px, transparent 1px 18px);
}

.system-status-panel.ready {
  background:
    linear-gradient(180deg, #ffffff 0%, #f8fafc 100%),
    repeating-linear-gradient(135deg, rgba(15, 118, 110, 0.06) 0 1px, transparent 1px 18px);
}

.system-status-panel span,
.system-card-head span {
  color: var(--system-muted);
  font-size: 12px;
  font-weight: 850;
}

.system-status-panel strong {
  color: var(--system-warning);
  font-size: 34px;
  line-height: 1.12;
  font-weight: 900;
  letter-spacing: 0;
}

.system-status-panel.ready strong {
  color: var(--system-accent);
}

.system-status-panel p {
  margin: 0;
  color: var(--system-muted);
  font-size: 13px;
  line-height: 1.65;
}

.system-status-meter {
  height: 8px;
  overflow: hidden;
  border-radius: 999px;
  background: #e5e7eb;
}

.system-status-meter i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--system-primary), var(--system-accent));
  transition: width 220ms var(--system-ease);
}

.system-stat-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.system-stat-card {
  display: grid;
  gap: 8px;
  padding: 16px;
  border-top: 3px solid var(--system-primary);
  transition:
    transform 180ms var(--system-ease),
    border-color 180ms ease,
    box-shadow 180ms var(--system-ease);
}

.system-stat-label {
  color: var(--system-muted);
  font-size: 12px;
  font-weight: 850;
}

.system-stat-card strong {
  color: var(--system-text);
  font-size: 24px;
  line-height: 1.15;
  font-weight: 900;
}

.system-stat-desc {
  color: var(--system-muted);
  font-size: 12px;
  line-height: 1.5;
}

.system-stat-card.is-ok {
  border-top-color: #16a34a;
}

.system-stat-card.is-info {
  border-top-color: var(--system-primary);
}

.system-stat-card.is-warn {
  border-top-color: var(--system-warning);
}

.system-workspace {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 380px;
  gap: 16px;
  align-items: start;
}

.system-main-column,
.system-side-column {
  display: grid;
  gap: 16px;
}

.system-side-column {
  position: sticky;
  top: 12px;
}

.system-v9-card {
  padding: 18px;
  transition:
    transform 180ms var(--system-ease),
    border-color 180ms ease,
    box-shadow 180ms var(--system-ease);
}

.system-card-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18px;
  margin-bottom: 16px;
}

.system-card-head h3 {
  margin: 4px 0 0;
  color: var(--system-text);
  font-size: 20px;
  line-height: 1.25;
  font-weight: 900;
  letter-spacing: 0;
}

.system-card-head p {
  max-width: 460px;
  margin: 0;
  color: var(--system-muted);
  font-size: 12px;
  line-height: 1.65;
  font-weight: 400;
}

.field-grid {
  display: grid;
  gap: 14px;
}

.field-grid.two {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.field {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
}

.field span {
  color: var(--system-text);
  font-size: 13px;
  font-weight: 850;
}

.field .input {
  width: 100%;
  height: 40px;
  padding: 0 12px;
  border: 1px solid #dbe3ee;
  border-radius: 8px;
  background: #ffffff;
  color: var(--system-text);
  font-size: 14px;
  outline: none;
  transition:
    border-color 160ms ease,
    box-shadow 160ms ease,
    background-color 160ms ease;
}

.field .input:hover {
  border-color: #bfdbfe;
}

.field .input:focus {
  border-color: var(--system-primary);
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.1);
}

.field .input[readonly] {
  background: var(--system-soft);
  color: var(--system-muted);
}

.service-notice {
  padding: 14px 16px;
  border: 1px dashed #bfdbfe;
  border-radius: 8px;
  background: #f8fbff;
  color: var(--system-muted);
  font-size: 13px;
  line-height: 1.7;
}

.ad-service-panel {
  display: grid;
  grid-template-columns: minmax(220px, 0.85fr) minmax(0, 1.8fr);
  gap: 14px;
}

.ad-service-summary {
  min-height: 178px;
  padding: 18px;
  border: 1px solid #fde68a;
  border-radius: 8px;
  background:
    linear-gradient(180deg, #fffbeb 0%, #ffffff 100%),
    repeating-linear-gradient(135deg, rgba(245, 158, 11, 0.08) 0 1px, transparent 1px 18px);
}

.ad-service-summary.ready {
  border-color: #99f6e4;
  background:
    linear-gradient(180deg, #f0fdfa 0%, #ffffff 100%),
    repeating-linear-gradient(135deg, rgba(15, 118, 110, 0.08) 0 1px, transparent 1px 18px);
}

.ad-service-summary span,
.ad-service-card span {
  display: block;
  color: var(--system-muted);
  font-size: 12px;
  font-weight: 850;
}

.ad-service-summary strong {
  display: block;
  margin-top: 12px;
  color: var(--system-text);
  font-size: 34px;
  line-height: 1;
  font-weight: 900;
  letter-spacing: 0;
}

.ad-service-summary p,
.ad-service-card p {
  margin: 12px 0 0;
  color: var(--system-muted);
  line-height: 1.7;
}

.ad-service-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.ad-service-card {
  min-height: 83px;
  padding: 14px;
  border: 1px solid var(--system-line);
  border-radius: 8px;
  background: var(--system-soft);
  border-top: 3px solid var(--system-primary);
}

.ad-service-card strong {
  display: block;
  margin-top: 8px;
  color: var(--system-text);
  font-size: 20px;
  line-height: 1.2;
  font-weight: 900;
}

.ad-service-card.is-ok {
  border-top-color: #16a34a;
}

.ad-service-card.is-info {
  border-top-color: var(--system-primary);
}

.ad-service-card.is-warn {
  border-top-color: var(--system-warning);
}

.service-capabilities {
  margin-top: 14px;
  padding: 14px 16px;
  border: 1px solid var(--system-line);
  border-radius: 8px;
  background: #ffffff;
}

.capabilities-title {
  margin: 0 0 10px;
  color: var(--system-text);
  font-size: 14px;
  font-weight: 900;
}

.capability-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.capability-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
  border: 1px solid var(--system-line);
  border-radius: 8px;
  background: var(--system-soft);
}

.capability-name {
  color: var(--system-primary-dark);
  font-size: 13px;
  font-weight: 850;
}

.capability-status {
  font-size: 13px;
  font-weight: 850;
}

.capability-status.ok {
  color: #0f766e;
}

.capability-status.warn {
  color: #b45309;
}

.capability-desc {
  color: var(--system-muted);
  font-size: 12px;
  line-height: 1.6;
}

.service-hint {
  margin: 12px 0 0;
  padding: 10px 12px;
  border-radius: 8px;
  background: #fffbeb;
  color: #92400e;
  font-size: 12px;
  line-height: 1.7;
}

.service-hint.ok {
  background: #f0fdfa;
  color: #0f766e;
}

.hint-list {
  display: grid;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
  color: var(--system-muted);
  font-size: 12px;
  line-height: 1.75;
}

.hint-list li {
  position: relative;
  padding-left: 16px;
}

.hint-list li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0.72em;
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: var(--system-accent);
}

.hint-list code {
  padding: 1px 6px;
  border-radius: 6px;
  background: #eff6ff;
  color: var(--system-primary-dark);
  font-size: 12px;
}

.hint-list strong {
  color: var(--system-text);
}

.knowledge-summary {
  padding: 18px;
  border: 1px dashed #bfdbfe;
  border-radius: 8px;
  background:
    linear-gradient(180deg, #ffffff 0%, #f8fbff 100%),
    repeating-linear-gradient(90deg, rgba(37, 99, 235, 0.04) 0 1px, transparent 1px 28px);
}

.knowledge-summary strong {
  display: block;
  color: var(--system-text);
  font-size: 34px;
  line-height: 1;
  font-weight: 900;
}

.knowledge-summary span {
  display: block;
  margin-top: 8px;
  color: var(--system-primary-dark);
  font-size: 13px;
  font-weight: 850;
}

.knowledge-summary p {
  margin: 10px 0 0;
  color: var(--system-muted);
  line-height: 1.7;
}

@media (hover: hover) and (pointer: fine) {
  .system-stat-card:hover,
  .system-v9-card:hover {
    transform: translateY(-2px);
    border-color: #bfdbfe;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05), 0 24px 54px rgba(37, 99, 235, 0.11);
  }

  .system-save-btn:hover:not(:disabled),
  .system-reload-btn:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 12px 24px rgba(37, 99, 235, 0.1);
  }
}

.system-save-btn:active,
.system-reload-btn:active {
  transform: scale(0.98);
}

@media (max-width: 1220px) {
  .system-hero,
  .system-workspace {
    grid-template-columns: minmax(0, 1fr);
  }

  .system-side-column {
    position: static;
  }
}

@media (max-width: 1100px) {
  .ad-service-panel,
  .ad-service-grid,
  .capability-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 920px) {
  .system-stat-grid,
  .field-grid.two {
    grid-template-columns: minmax(0, 1fr);
  }

  .system-hero-copy {
    min-height: 0;
    padding: 22px;
  }

  .system-hero-copy::before {
    display: none;
  }

  .system-hero-copy h1 {
    font-size: 28px;
  }

  .system-card-head {
    flex-direction: column;
  }
}

@media (max-width: 620px) {
  .system-hero-actions,
  .system-save-btn,
  .system-reload-btn {
    width: 100%;
  }

  .system-status-panel strong,
  .ad-service-summary strong,
  .knowledge-summary strong {
    font-size: 28px;
  }
}
</style>
