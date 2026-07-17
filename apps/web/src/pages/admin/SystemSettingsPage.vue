<template>
  <div class="admin-system-settings system-settings-page system-main">
    <div v-if="error" class="global-notice error">{{ error }}</div>
    <div v-if="success" class="global-notice success">{{ success }}</div>

    <section class="page-hero system-hero">
      <div class="page-hero-copy">
        <span class="page-pill">系统总览</span>
        <h1>系统配置</h1>
        <p>
          这里是系统总览页面与站点基础配置入口。高德地图 API Key、通用模型配置、向量模型配置与 RAG 知识库已经拆分为独立导航项，
          可在左侧切换至对应页面单独维护。
        </p>

        <div class="page-actions">
          <AppButton type="primary" :loading="saving" :disabled="!configAvailable" @click="save">保存配置</AppButton>
          <AppButton :loading="loading" @click="loadPage">重新加载</AppButton>
        </div>
      </div>
    </section>

    <div class="grid stat-grid system-v7-stats">
      <n-card
        v-for="item in systemStatCards"
        :key="item.key"
        class="system-v7-stat"
        :class="item.tone"
        :bordered="false"
      >
        <span class="system-v7-stat-label">{{ item.title }}</span>
        <strong>{{ item.value }}</strong>
        <span class="system-v7-stat-desc">{{ item.change }}</span>
      </n-card>
    </div>

    <div class="page-grid">
      <n-card class="system-v7-card" :bordered="false">
        <template #header>
          <div class="system-card-head">
            <h3>站点基础配置</h3>
            <p>站点名称、ICP 备案、Logo 与爬虫服务地址，会用于前端展示与后端服务调用。</p>
          </div>
        </template>
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
            <span>站点 Logo URL（logoUrl）</span>
            <input v-model="form.logoUrl" class="input" placeholder="例如：/static/logo.png" />
          </label>

          <label class="field">
            <span>爬虫服务地址（服务只读）</span>
            <input
              :value="form.crawlerBaseUrl"
              class="input"
              readonly
              aria-readonly="true"
              title="由服务端 CRAWLER_BASE_URL 配置并在重启后生效"
            />
          </label>
        </div>
      </n-card>

      <n-card class="system-v7-card" :bordered="false">
        <template #header>
          <div class="system-card-head">
            <h3>广告服务连接状态</h3>
            <p>系统通过服务端拉取轮播图、文字广告与广告套餐，并提交广告投放申请。服务令牌、URL 等敏感信息仅在服务端配置，浏览器不可见。</p>
          </div>
        </template>
        <div v-if="!runtimeStatusAvailable" class="bridge-notice">
          运行状态暂不可用，无法确认广告服务连接状态。点击上方「重新加载」可重试。
        </div>
        <div v-else class="bridge-grid">
          <div class="bridge-row">
            <span class="bridge-label">服务模式</span>
            <span
              class="bridge-value"
              :class="{ ok: runtimeStatus.commercialBridgeMode === 'commercial', warn: runtimeStatus.commercialBridgeMode !== 'commercial' }"
            >
              {{ runtimeStatus.commercialBridgeMode === 'commercial' ? '已连接广告服务' : '服务未连接' }}
            </span>
          </div>
          <div class="bridge-row">
            <span class="bridge-label">配置状态</span>
            <span
              class="bridge-value"
              :class="{ ok: runtimeStatus.commercialBridgeConfigured, warn: !runtimeStatus.commercialBridgeConfigured }"
            >
              {{ runtimeStatus.commercialBridgeConfigured ? '已配置' : '未配置' }}
            </span>
          </div>
          <div class="bridge-row">
            <span class="bridge-label">服务连通性</span>
            <span
              class="bridge-value"
              :class="{ ok: runtimeStatus.commercialBridgeConnected, warn: !runtimeStatus.commercialBridgeConnected }"
            >
              {{ runtimeStatus.commercialBridgeConnected ? '已连通' : '未连通' }}
            </span>
          </div>
          <div class="bridge-row">
            <span class="bridge-label">管理端健康</span>
            <span
              class="bridge-value"
              :class="{ ok: runtimeStatus.commercialAdminHealthOk, warn: !runtimeStatus.commercialAdminHealthOk }"
            >
              {{ runtimeStatus.commercialAdminHealthOk ? '正常' : '不可达' }}
            </span>
          </div>
          <div class="bridge-row">
            <span class="bridge-label">用户端健康</span>
            <span
              class="bridge-value"
              :class="{ ok: runtimeStatus.commercialUserHealthOk, warn: !runtimeStatus.commercialUserHealthOk }"
            >
              {{ runtimeStatus.commercialUserHealthOk ? '正常' : '不可达' }}
            </span>
          </div>
          <div class="bridge-row">
            <span class="bridge-label">站点代码</span>
            <span class="bridge-value">{{ runtimeStatus.commercialBridgeSiteCode || '—' }}</span>
          </div>
          <div class="bridge-row">
            <span class="bridge-label">用户端地址</span>
            <span class="bridge-value mono">{{ runtimeStatus.commercialFrontendUrl || '—' }}</span>
          </div>
          <div class="bridge-row">
            <span class="bridge-label">管理端地址</span>
            <span class="bridge-value mono">{{ runtimeStatus.commercialAdminUrl || '—' }}</span>
          </div>
          <div v-if="runtimeStatus.commercialBridgeMessage" class="bridge-row">
            <span class="bridge-label">服务消息</span>
            <span class="bridge-value">{{ runtimeStatus.commercialBridgeMessage }}</span>
          </div>
        </div>

        <div v-if="runtimeStatusAvailable" class="bridge-capabilities">
          <h4 class="capabilities-title">能力开关</h4>
          <div class="capability-grid">
            <div class="capability-item">
              <span class="capability-name">写入幂等</span>
              <span
                class="capability-status"
                :class="{ ok: runtimeStatus.commercialMutationIdempotencyEnabled, warn: !runtimeStatus.commercialMutationIdempotencyEnabled }"
              >
                {{ runtimeStatus.commercialMutationIdempotencyEnabled ? '已开启' : '未开启' }}
              </span>
              <span class="capability-desc">广告申请写入支持幂等键，未开启时禁止提交申请。</span>
            </div>
            <div class="capability-item">
              <span class="capability-name">支付幂等</span>
              <span
                class="capability-status"
                :class="{ ok: runtimeStatus.commercialPaymentIdempotencyEnabled, warn: !runtimeStatus.commercialPaymentIdempotencyEnabled }"
              >
                {{ runtimeStatus.commercialPaymentIdempotencyEnabled ? '已开启' : '未开启' }}
              </span>
              <span class="capability-desc">支付订单支持幂等键，未开启时禁止创建订单。</span>
            </div>
            <div class="capability-item">
              <span class="capability-name">付费展示</span>
              <span
                class="capability-status"
                :class="{ ok: runtimeStatus.commercialPaidAdPlacementEnforced, warn: !runtimeStatus.commercialPaidAdPlacementEnforced }"
              >
                {{ runtimeStatus.commercialPaidAdPlacementEnforced ? '已开启' : '未开启' }}
              </span>
              <span class="capability-desc">仅已支付广告可激活展示，未开启时禁止展示广告。</span>
            </div>
          </div>
          <p v-if="!allBridgeCapabilitiesEnabled" class="bridge-hint">
            三个能力开关必须全部开启后，系统才能完整使用广告展示与投放功能。开关由服务端通过检测后启用，前端页面无法直接修改。
          </p>
          <p v-else class="bridge-hint ok">
            全部能力已就绪，系统可正常展示广告并接受用户投放申请。
          </p>
        </div>
      </n-card>

      <n-card class="system-v7-card" :bordered="false">
        <template #header>
          <div class="system-card-head">
            <h3>配置说明</h3>
            <p>常见配置项的取值规则与注意事项。</p>
          </div>
        </template>
        <ul class="hint-list">
          <li><strong>站点名称</strong>：显示在浏览器标题栏和登录页，建议保持简短（建议 ≤ 16 个字符）。</li>
          <li><strong>ICP 备案号</strong>：中国大陆服务器必须填写，否则前端底部不显示备案信息。海外服务器可留空。</li>
          <li><strong>站点 Logo URL</strong>：可填写相对路径（如 <code>/static/logo.png</code>）或绝对 URL（如 <code>https://cdn.example.com/logo.png</code>）。</li>
          <li><strong>爬虫服务地址</strong>：该地址会接收账号授权信息，只能由平台服务通过 <code>CRAWLER_BASE_URL</code> 配置并在重启后生效，浏览器页面不可修改。</li>
          <li><strong>高德地图 Key</strong>：用于发布商品页的地址搜索，请到"高德地图"页签配置。</li>
          <li><strong>通用模型 / 向量模型</strong>：分别到"模型配置"和"向量模型"页签配置。</li>
          <li><strong>RAG 知识库</strong>：到"RAG 知识库"页签管理文档与检索测试。</li>
        </ul>
      </n-card>

      <n-card class="system-v7-card" :bordered="false">
        <template #header>
          <div class="system-card-head">
            <h3>知识库列表</h3>
            <p>系统总览页保留一个轻量概览，便于确认 RAG 知识库模块是否已经接入。</p>
          </div>
        </template>
        <div class="knowledge-summary">
          <strong>{{ knowledgeBaseSummary.available ? knowledgeBaseSummary.total : '—' }}</strong>
          <span>当前知识库数量</span>
          <p v-if="!knowledgeBaseSummary.available" class="global-notice error">知识库概览暂不可用，当前无法确认数量。</p>
          <p>如需查看文档、切片与检索测试，请前往左侧“RAG 知识库”页签继续操作。</p>
        </div>
      </n-card>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive } from 'vue'
import { NCard } from 'naive-ui'
import AppButton from '../../components/AppButton.vue'
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
      : '运行探测暂不可用'
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

const allBridgeCapabilitiesEnabled = computed(() => {
  if (!runtimeStatusAvailable.value) return false
  return Boolean(runtimeStatus.commercialMutationIdempotencyEnabled)
    && Boolean(runtimeStatus.commercialPaymentIdempotencyEnabled)
    && Boolean(runtimeStatus.commercialPaidAdPlacementEnforced)
})

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
.admin-system-settings {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 16px;
  padding: 22px;
  border-radius: 6px;
  border: 1px solid #dfe6f2;
  background: #fff;
  box-shadow: none;
}

.page-pill {
  display: inline-flex;
  align-items: center;
  min-height: 26px;
  padding: 0 10px;
  border-radius: 4px;
  background: #eef4ff;
  color: #2563eb;
  font-size: 11px;
  font-weight: 800;
}

.page-hero-copy h1 {
  margin: 10px 0 0;
  font-size: 28px;
  color: #13213d;
}

.page-hero-copy p {
  margin: 10px 0 0;
  max-width: 760px;
  line-height: 1.8;
  color: #60738e;
}

.page-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 18px;
}

.stat-grid {
  display: grid;
  gap: 12px;
}

.system-v7-stats {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.system-v7-stat,
.system-v7-card {
  border: 1px solid #dfe6f2;
  border-radius: 6px;
  background: #fff;
  box-shadow: none;
}

.system-v7-stat :deep(.n-card__content) {
  display: grid;
  gap: 8px;
  padding: 16px;
}

.system-v7-stat-label {
  color: #667085;
  font-size: 12px;
  font-weight: 700;
}

.system-v7-stat strong {
  color: #101828;
  font-size: 24px;
  line-height: 1.15;
  font-weight: 800;
}

.system-v7-stat-desc {
  color: #667085;
  font-size: 12px;
  line-height: 1.5;
}

.system-v7-stat.is-ok {
  border-top: 3px solid #16a34a;
}

.system-v7-stat.is-info {
  border-top: 3px solid #2563eb;
}

.system-v7-stat.is-warn {
  border-top: 3px solid #f59e0b;
}

.system-v7-card :deep(.n-card-header) {
  padding: 18px 20px 0;
}

.system-v7-card :deep(.n-card__content) {
  padding: 14px 20px 20px;
}

.system-card-head {
  display: grid;
  gap: 5px;
}

.system-card-head h3 {
  margin: 0;
  color: #101828;
  font-size: 16px;
  line-height: 1.3;
  font-weight: 800;
}

.system-card-head p {
  margin: 0;
  color: #667085;
  font-size: 12px;
  line-height: 1.6;
  font-weight: 400;
}

.page-grid {
  display: grid;
  gap: 16px;
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
}

.field span {
  font-size: 13px;
  font-weight: 700;
  color: #6a7c98;
}

.field .input {
  height: 40px;
  padding: 0 12px;
  border-radius: 10px;
  border: 1px solid #ebdcd6;
  background: #fff;
  font-size: 14px;
  color: #1f2a44;
  outline: none;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.field .input:focus {
  border-color: #0f766e;
  box-shadow: 0 0 0 3px rgba(20, 184, 166, 0.15);
}

.hint-list {
  margin: 0;
  padding-left: 18px;
  color: #667892;
  line-height: 1.8;
}

.knowledge-summary {
  padding: 18px;
  border-radius: 6px;
  border: 1px dashed #cfd8e8;
  background: #f8fafc;
}

.knowledge-summary strong {
  display: block;
  color: #13213d;
  font-size: 30px;
  line-height: 1;
}

.knowledge-summary span {
  display: block;
  margin-top: 8px;
  color: #d45e2c;
  font-size: 13px;
  font-weight: 700;
}

.knowledge-summary p {
  margin: 10px 0 0;
  color: #6e7e98;
  line-height: 1.7;
}

.bridge-notice {
  padding: 14px 16px;
  border-radius: 6px;
  border: 1px dashed #cfd8e8;
  background: #f8fafc;
  color: #6e7e98;
  font-size: 13px;
  line-height: 1.7;
}

.bridge-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 18px;
  padding: 14px 16px;
  border-radius: 6px;
  border: 1px dashed #cfd8e8;
  background: #f8fafc;
}

.bridge-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.bridge-label {
  font-size: 12px;
  font-weight: 700;
  color: #6a7c98;
}

.bridge-value {
  font-size: 14px;
  color: #1f2a44;
  word-break: break-all;
}

.bridge-value.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 13px;
}

.bridge-value.ok {
  color: #1f8a4c;
  font-weight: 700;
}

.bridge-value.warn {
  color: #b26a00;
  font-weight: 700;
}

.bridge-capabilities {
  margin-top: 14px;
  padding: 14px 16px;
  border-radius: 6px;
  border: 1px solid #e3eaf5;
  background: #fff;
}

.capabilities-title {
  margin: 0 0 10px;
  font-size: 14px;
  font-weight: 800;
  color: #13213d;
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
  border-radius: 10px;
  border: 1px solid #e3eaf5;
  background: #FFFFFF;
}

.capability-name {
  font-size: 13px;
  font-weight: 700;
  color: #d45e2c;
}

.capability-status {
  font-size: 13px;
  font-weight: 700;
}

.capability-status.ok {
  color: #1f8a4c;
}

.capability-status.warn {
  color: #b26a00;
}

.capability-desc {
  font-size: 12px;
  color: #6e7e98;
  line-height: 1.6;
}

.bridge-hint {
  margin: 12px 0 0;
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(178, 106, 0, 0.08);
  color: #8a4a00;
  font-size: 12px;
  line-height: 1.7;
}

.bridge-hint.ok {
  background: rgba(31, 138, 76, 0.08);
  color: #1f6b3a;
}

@media (max-width: 1100px) {
  .bridge-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .capability-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}

.hint-list code {
  background: rgba(20, 184, 166, 0.08);
  color: #d45e2c;
  padding: 1px 6px;
  border-radius: 6px;
  font-size: 12px;
}

.hint-list strong {
  color: #13213d;
}

@media (max-width: 1200px) {
  .stat-grid {
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) !important;
  }
}

@media (max-width: 920px) {
  .stat-grid {
    grid-template-columns: minmax(0, 1fr) !important;
  }

  .field-grid.two {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 900px) {
  .admin-system-settings {
    gap: 12px;
  }

  .page-hero {
    padding: 14px;
    border-radius: 16px;
  }

  .page-hero-copy h1 {
    font-size: 20px;
  }

  .page-hero-copy p {
    font-size: 13px;
    line-height: 1.6;
  }

  .page-actions {
    gap: 8px;
    margin-top: 12px;
  }

  .stat-grid {
    grid-template-columns: minmax(0, 1fr) !important;
    gap: 10px;
  }

  .page-grid {
    gap: 12px;
  }

  .field-grid {
    gap: 12px;
  }

  .field-grid.two {
    grid-template-columns: minmax(0, 1fr);
  }

  .stat-grid > *,
  .field-grid.two > * {
    min-width: 0;
  }

  .field .input {
    height: 40px;
    font-size: 13px;
  }

  .knowledge-summary {
    padding: 12px;
    border-radius: 14px;
  }

  .knowledge-summary strong {
    font-size: 22px;
  }

  .knowledge-summary span {
    font-size: 12px;
  }

  .knowledge-summary p {
    font-size: 13px;
    line-height: 1.6;
  }

  .hint-list {
    padding-left: 16px;
    font-size: 13px;
    line-height: 1.7;
  }

  .hint-list code {
    font-size: 11px;
    word-break: break-all;
  }
}
</style>
