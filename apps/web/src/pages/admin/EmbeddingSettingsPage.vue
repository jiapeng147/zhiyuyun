<template>
  <div class="embedding-settings-page embedding-v9-shell">
    <div v-if="error" class="global-notice error">{{ error }}</div>
    <div v-if="success" class="global-notice success">{{ success }}</div>

    <section class="embedding-hero">
      <div class="embedding-hero-copy">
        <span class="embedding-kicker">Embedding Gateway</span>
        <h1>向量检索控制台</h1>
        <p>独立维护 Embedding 模型的供应商、模型名、接口地址和密钥。知识库导入、文档向量化、语义召回和 RAG 检索都会读取这里的专用配置。</p>

        <div class="embedding-hero-actions">
          <button type="button" class="embedding-save-btn" :disabled="saving || !configAvailable" @click="save">{{ saving ? '保存中...' : '保存配置' }}</button>
          <button type="button" class="embedding-reload-btn" :disabled="loading" @click="loadPage">{{ loading ? '加载中...' : '重新加载' }}</button>
        </div>
      </div>

      <aside class="embedding-status-panel" :class="runtimeStatusAvailable && runtimeStatus.embeddingModelConfigured ? 'green' : 'orange'" aria-label="向量模型状态">
        <span>向量模型</span>
        <strong>{{ runtimeStatusAvailable ? (runtimeStatus.embeddingModelConfigured ? '已配置' : '未设置') : '状态未知' }}</strong>
        <div class="embedding-status-meter">
          <i :style="{ width: runtimeStatusAvailable && runtimeStatus.embeddingModelConfigured ? '78%' : '32%' }"></i>
        </div>
        <p>Embedding / RAG / Semantic Search</p>
      </aside>
    </section>

    <section class="embedding-summary-grid" aria-label="向量检索摘要">
      <article class="embedding-summary-card">
        <span class="embedding-summary-icon blue">01</span>
        <div>
          <strong>文档向量化</strong>
          <p>知识库导入和切片索引会用这里的模型把文本转换为向量，形成可检索的语义索引。</p>
        </div>
      </article>
      <article class="embedding-summary-card">
        <span class="embedding-summary-icon green">02</span>
        <div>
          <strong>语义召回</strong>
          <p>用户提问会先匹配相似内容，再交给通用模型生成回答，减少凭空发挥。</p>
        </div>
      </article>
      <article class="embedding-summary-card">
        <span class="embedding-summary-icon amber">03</span>
        <div>
          <strong>密钥保护</strong>
          <p>保存后的 Key 不完整回显；切换接口主机时建议重新输入，避免把密钥发往错误地址。</p>
        </div>
      </article>
    </section>

    <div class="embedding-workspace">
      <section class="embedding-v9-card embedding-config-panel">
        <div class="embedding-card-head">
          <div>
            <span>向量模型</span>
            <h2>检索接入参数</h2>
          </div>
          <p>RAG 知识库建索引、召回相似内容与检索增强回答都会优先使用这里的 Embedding 配置。</p>
        </div>

        <div class="config-overview">
          <article class="overview-card">
            <span>用途边界</span>
            <strong>只负责“向量化”和“相似度检索”</strong>
            <p>它不负责对话或文案生成，所以这里的模型能力与通用聊天模型完全不同，不建议混填。</p>
          </article>
          <article class="overview-card">
            <span>配置顺序</span>
            <strong>供应商 → 模型名 → 接口地址 → API Key</strong>
            <p>先保证最基础的可调用链路，再去验证知识库索引、检索和召回质量是否符合预期。</p>
          </article>
        </div>

        <div class="field-grid two">
          <OpsConfigField
            label="模型供应商"
            hint="标记你当前使用的是哪家的向量服务，方便区分 OpenAI、阿里、火山等不同接入。"
            meta="参考填写：openai / dashscope / volcengine。不同供应商的模型名与接口地址可能不一致。"
            badge="第一步"
            required
          >
            <input v-model="form.embeddingModel.provider" class="config-input" placeholder="openai / dashscope / volcengine" />
          </OpsConfigField>

          <OpsConfigField
            label="模型名称"
            hint="填写实际用于生成向量的模型名，知识库索引和检索阶段都会直接调用它。"
            meta="参考填写：text-embedding-3-small、text-embedding-v3、doubao-embedding。"
            badge="核心参数"
            required
          >
            <input v-model="form.embeddingModel.modelName" class="config-input" placeholder="text-embedding-3-small" />
          </OpsConfigField>

          <OpsConfigField
            label="接口地址"
            hint="仅支持可解析的公网 HTTPS API 根地址；系统会拒绝明文 HTTP、本机、内网、重定向与代理环境。"
            meta="大多数兼容接口以 /v1 结尾。切换到不同主机时必须同时重新输入 API Key，避免已保存密钥外泄。"
            badge="第二步"
            required
          >
            <input v-model="form.embeddingModel.baseUrl" class="config-input" placeholder="https://api.openai.com/v1" />
          </OpsConfigField>

          <OpsConfigField
            label="API Key"
            hint="保存后不会回显完整 Key；索引构建与检索时会直接使用这项鉴权。"
            meta="修改接口主机时必须重新输入 Key；若导入时报 401/403，请检查 Key 是否过期以及是否属于当前供应商。"
            badge="第三步"
            required
          >
            <SecretInput
              v-model="form.embeddingModel.apiKey"
              :placeholder="config.embeddingModel.apiKeyConfigured ? '已保存，直接输入新值可覆盖' : 'sk-...'"
              autocomplete="off"
            />
          </OpsConfigField>
        </div>
      </section>

      <aside class="embedding-v9-card embedding-guide-panel">
        <div class="embedding-card-head compact">
          <div>
            <span>检索建议</span>
            <h2>使用说明</h2>
          </div>
          <p>先确认向量模型的职责边界，再去调整供应商和模型选型，可以减少索引失败和召回偏差。</p>
        </div>

        <div class="guide-grid">
          <article class="guide-card">
            <div class="guide-icon">R</div>
            <div>
              <strong>RAG 优先读取这里</strong>
              <p>知识库导入、切片向量化和检索召回都会优先使用这里的配置，不会自动回退到通用聊天模型。</p>
            </div>
          </article>
          <article class="guide-card">
            <div class="guide-icon">V</div>
            <div>
              <strong>只看向量质量，不看文采</strong>
              <p>向量模型评估重点是检索准确率、相似度语义与速度，而不是回答是否自然流畅。</p>
            </div>
          </article>
          <article class="guide-card">
            <div class="guide-icon">K</div>
            <div>
              <strong>索引失败先查 Key 与地址</strong>
              <p>导入知识库时报错时，最常见原因是 Key 不匹配、接口地址错填，或模型名不被当前服务支持。</p>
            </div>
          </article>
        </div>

        <ul class="hint-list">
          <li>向量模型仅用于生成文本向量，不能替代通用对话模型；聊天、改写和文案生成请到“模型配置”页签。</li>
          <li>常见供应商包括 OpenAI（text-embedding-3-small/large）、阿里 DashScope（text-embedding-v2/v3）以及火山引擎的 embedding 服务。</li>
          <li>如果这里没有正确配置，RAG 检索往往只能退化为低质量的关键词匹配，召回效果会明显下降。</li>
          <li>接口地址通常以 <code>/v1</code> 结尾，必须使用公网 HTTPS；当前默认安全策略不允许直接连接本机或内网模型服务。</li>
          <li>API Key 不会完整回显；需要更换时直接覆盖，切换接口主机时也必须重新输入并保存。</li>
        </ul>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, reactive } from 'vue'
import OpsConfigField from '../../components/OpsConfigField.vue'
import SecretInput from '../../components/SecretInput.vue'
import {
  cloneOpenSourceConfig,
  useOpenSourceSettings,
} from '../../composables/useOpenSourceSettings.js'

defineProps({ active: String })

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
  refreshRuntimeStatus,
  saveConfig,
} = useOpenSourceSettings()

const form = reactive({
  embeddingModel: {
    provider: '',
    modelName: '',
    baseUrl: '',
    apiKey: '',
  },
})

onMounted(() => {
  window.addEventListener('xya-header-action', onHeaderAction)
  loadPage()
})

onBeforeUnmount(() => {
  window.removeEventListener('xya-header-action', onHeaderAction)
})

function syncForm() {
  Object.assign(form.embeddingModel, config.embeddingModel || {})
}

async function loadPage() {
  await loadBundle({ includeRuntimeStatus: true })
  if (configAvailable.value) syncForm()
}

async function save() {
  if (!configAvailable.value) return
  const payload = cloneOpenSourceConfig(config)
  payload.embeddingModel = {
    provider: form.embeddingModel.provider.trim(),
    modelName: form.embeddingModel.modelName.trim(),
    baseUrl: form.embeddingModel.baseUrl.trim(),
    apiKey: form.embeddingModel.apiKey.trim(),
  }
  const saved = await saveConfig(payload, { successMessage: '向量模型配置已保存' })
  if (!saved) return
  syncForm()
  await refreshRuntimeStatus()
}

function onHeaderAction(event) {
  if (event.detail === 'settings-save') save()
  if (event.detail === 'settings-reload') loadPage()
}
</script>

<style scoped>
.embedding-v9-shell {
  --embedding-primary: #2563eb;
  --embedding-primary-dark: #1d4ed8;
  --embedding-accent: #0f766e;
  --embedding-warning: #f59e0b;
  --embedding-text: #111827;
  --embedding-muted: #64748b;
  --embedding-line: #e5e7eb;
  --embedding-panel: #ffffff;
  --embedding-soft: #f8fafc;
  --embedding-ease: cubic-bezier(0.23, 1, 0.32, 1);
  display: grid;
  gap: 16px;
  color: var(--embedding-text);
}

.embedding-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 16px;
  align-items: stretch;
}

.embedding-hero-copy,
.embedding-status-panel,
.embedding-summary-card,
.embedding-v9-card {
  border: 1px solid var(--embedding-line);
  border-radius: 8px;
  background: var(--embedding-panel);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05), 0 18px 42px rgba(15, 23, 42, 0.06);
}

.embedding-hero-copy {
  position: relative;
  overflow: hidden;
  min-height: 236px;
  padding: 28px;
  background:
    linear-gradient(120deg, rgba(255, 255, 255, 0.98), rgba(248, 251, 255, 0.96)),
    repeating-linear-gradient(90deg, rgba(37, 99, 235, 0.06) 0 1px, transparent 1px 40px);
}

.embedding-hero-copy::before {
  content: '';
  position: absolute;
  right: 28px;
  bottom: 24px;
  width: 240px;
  height: 126px;
  border: 1px solid rgba(37, 99, 235, 0.14);
  border-radius: 8px;
  background:
    linear-gradient(90deg, rgba(37, 99, 235, 0.13) 1px, transparent 1px),
    linear-gradient(180deg, rgba(15, 118, 110, 0.11) 1px, transparent 1px);
  background-size: 32px 32px;
  opacity: 0.68;
  transform: rotate(-3deg);
}

.embedding-hero-copy::after {
  content: '';
  position: absolute;
  right: 80px;
  bottom: 60px;
  width: 128px;
  height: 28px;
  border-radius: 8px;
  background: linear-gradient(90deg, rgba(37, 99, 235, 0.18), rgba(15, 118, 110, 0.16));
  opacity: 0.72;
}

.embedding-kicker {
  position: relative;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  height: 28px;
  padding: 0 10px;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  background: #eff6ff;
  color: var(--embedding-primary-dark);
  font-size: 11px;
  font-weight: 850;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.embedding-hero-copy h1 {
  position: relative;
  z-index: 1;
  margin: 18px 0 10px;
  color: var(--embedding-text);
  font-size: 34px;
  line-height: 1.12;
  font-weight: 900;
  letter-spacing: 0;
}

.embedding-hero-copy p {
  position: relative;
  z-index: 1;
  max-width: 720px;
  margin: 0;
  color: var(--embedding-muted);
  font-size: 14px;
  line-height: 1.8;
}

.embedding-hero-actions {
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 22px;
}

.embedding-save-btn,
.embedding-reload-btn {
  min-height: 38px;
  padding: 0 15px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 850;
  cursor: pointer;
  transition:
    transform 140ms var(--embedding-ease),
    box-shadow 160ms var(--embedding-ease),
    border-color 160ms ease,
    background-color 160ms ease,
    color 160ms ease;
}

.embedding-save-btn {
  border: 1px solid transparent;
  background: linear-gradient(135deg, var(--embedding-primary), var(--embedding-accent));
  color: #ffffff;
  box-shadow: 0 12px 22px rgba(37, 99, 235, 0.18);
}

.embedding-reload-btn {
  border: 1px solid #bfdbfe;
  background: #ffffff;
  color: var(--embedding-primary-dark);
}

.embedding-save-btn:disabled,
.embedding-reload-btn:disabled {
  cursor: not-allowed;
  opacity: 0.62;
}

.embedding-status-panel {
  display: grid;
  align-content: space-between;
  gap: 14px;
  padding: 22px;
  background:
    linear-gradient(180deg, #ffffff 0%, #f8fafc 100%),
    repeating-linear-gradient(135deg, rgba(15, 118, 110, 0.06) 0 1px, transparent 1px 18px);
}

.embedding-status-panel.orange {
  background:
    linear-gradient(180deg, #ffffff 0%, #fffbeb 100%),
    repeating-linear-gradient(135deg, rgba(245, 158, 11, 0.08) 0 1px, transparent 1px 18px);
}

.embedding-status-panel span,
.embedding-card-head span {
  color: var(--embedding-muted);
  font-size: 12px;
  font-weight: 850;
}

.embedding-status-panel strong {
  color: var(--embedding-warning);
  font-size: 34px;
  line-height: 1.12;
  font-weight: 900;
  letter-spacing: 0;
}

.embedding-status-panel.green strong {
  color: var(--embedding-accent);
}

.embedding-status-panel p {
  margin: 0;
  color: var(--embedding-muted);
  font-size: 13px;
  line-height: 1.65;
}

.embedding-status-meter {
  height: 8px;
  overflow: hidden;
  border-radius: 999px;
  background: #e5e7eb;
}

.embedding-status-meter i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--embedding-primary), var(--embedding-accent));
  transition: width 220ms var(--embedding-ease);
}

.embedding-status-panel.orange .embedding-status-meter i {
  background: linear-gradient(90deg, var(--embedding-warning), var(--embedding-accent));
}

.embedding-summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.embedding-summary-card {
  display: grid;
  grid-template-columns: 48px minmax(0, 1fr);
  gap: 12px;
  align-items: start;
  padding: 16px;
  transition:
    transform 180ms var(--embedding-ease),
    border-color 180ms ease,
    box-shadow 180ms var(--embedding-ease);
}

.embedding-summary-icon {
  width: 48px;
  height: 48px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  color: var(--embedding-primary);
  background: #eff6ff;
  font-family: 'SF Mono', 'JetBrains Mono', 'Cascadia Code', monospace;
  font-size: 13px;
  font-weight: 900;
}

.embedding-summary-icon.green {
  color: var(--embedding-accent);
  background: #f0fdfa;
}

.embedding-summary-icon.amber {
  color: #b45309;
  background: #fffbeb;
}

.embedding-summary-card strong,
.embedding-card-head h2,
.overview-card strong,
.guide-card strong {
  color: var(--embedding-text);
  font-weight: 850;
}

.embedding-summary-card p,
.embedding-card-head p,
.overview-card p,
.guide-card p {
  margin: 6px 0 0;
  color: var(--embedding-muted);
  font-size: 12px;
  line-height: 1.7;
}

.embedding-workspace {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 16px;
  align-items: start;
}

.embedding-v9-card {
  padding: 18px;
  transition:
    transform 180ms var(--embedding-ease),
    border-color 180ms ease,
    box-shadow 180ms var(--embedding-ease);
}

.embedding-guide-panel {
  position: sticky;
  top: 12px;
}

.embedding-card-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18px;
  margin-bottom: 16px;
}

.embedding-card-head.compact {
  display: grid;
  gap: 8px;
}

.embedding-card-head h2 {
  margin: 4px 0 0;
  font-size: 20px;
  line-height: 1.25;
  letter-spacing: 0;
}

.embedding-card-head p {
  max-width: 420px;
  margin-top: 0;
}

.config-overview {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.overview-card {
  padding: 16px;
  border: 1px solid #dbe3ee;
  border-radius: 8px;
  background:
    linear-gradient(180deg, #ffffff 0%, #f8fbff 100%),
    repeating-linear-gradient(90deg, rgba(37, 99, 235, 0.04) 0 1px, transparent 1px 28px);
}

.overview-card span {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 8px;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  background: #eff6ff;
  color: var(--embedding-primary-dark);
  font-size: 11px;
  font-weight: 850;
}

.overview-card strong {
  display: block;
  margin-top: 12px;
  font-size: 15px;
  line-height: 1.45;
}

.field-grid {
  display: grid;
  gap: 14px;
}

.field-grid.two {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.embedding-v9-shell :deep(.ops-config-field) {
  border-color: var(--embedding-line);
  border-radius: 8px;
  background: var(--embedding-soft);
  box-shadow: none;
  transition:
    transform 180ms var(--embedding-ease),
    border-color 180ms ease,
    box-shadow 180ms var(--embedding-ease);
}

.embedding-v9-shell :deep(.ops-config-field:hover) {
  border-color: #bfdbfe;
  box-shadow: 0 16px 34px rgba(37, 99, 235, 0.08);
}

.embedding-v9-shell :deep(.ops-config-field-label) {
  color: var(--embedding-text);
  letter-spacing: 0;
}

.embedding-v9-shell :deep(.ops-config-field-badge) {
  border-radius: 8px;
  background: #eff6ff;
  color: var(--embedding-primary-dark);
}

.embedding-v9-shell :deep(.ops-config-field-required) {
  border-radius: 8px;
}

.embedding-v9-shell :deep(.ops-config-field-hint),
.embedding-v9-shell :deep(.ops-config-field-meta) {
  color: var(--embedding-muted);
}

.embedding-v9-shell :deep(.config-input),
.embedding-v9-shell :deep(.config-textarea),
.embedding-v9-shell :deep(.secret-input) {
  border-color: #dbe3ee;
  border-radius: 8px;
  color: var(--embedding-text);
  background: #ffffff;
}

.embedding-v9-shell :deep(.config-input:hover),
.embedding-v9-shell :deep(.config-textarea:hover),
.embedding-v9-shell :deep(.secret-input:hover) {
  border-color: #bfdbfe;
}

.embedding-v9-shell :deep(.config-input:focus),
.embedding-v9-shell :deep(.config-input:focus-visible),
.embedding-v9-shell :deep(.config-textarea:focus),
.embedding-v9-shell :deep(.config-textarea:focus-visible),
.embedding-v9-shell :deep(.secret-input:focus-within) {
  border-color: var(--embedding-primary);
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.1);
}

.embedding-v9-shell :deep(.secret-input-control) {
  color: var(--embedding-text);
}

.embedding-v9-shell :deep(.secret-input-toggle) {
  border-left-color: var(--embedding-line);
  background: #f8fbff;
  color: var(--embedding-primary-dark);
  transition:
    background-color 160ms ease,
    color 160ms ease;
}

.guide-grid {
  display: grid;
  gap: 12px;
  margin-bottom: 16px;
}

.guide-card {
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr);
  gap: 12px;
  padding: 14px;
  border: 1px solid var(--embedding-line);
  border-radius: 8px;
  background: var(--embedding-soft);
}

.guide-icon {
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: #eff6ff;
  color: var(--embedding-primary-dark);
  font-size: 13px;
  font-weight: 900;
}

.guide-card strong {
  display: block;
  font-size: 14px;
}

.hint-list {
  display: grid;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
  color: var(--embedding-muted);
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
  background: var(--embedding-accent);
}

.hint-list code {
  padding: 1px 6px;
  border-radius: 6px;
  background: #eff6ff;
  color: var(--embedding-primary-dark);
  font-size: 12px;
}

@media (hover: hover) and (pointer: fine) {
  .embedding-summary-card:hover,
  .embedding-v9-card:hover {
    transform: translateY(-2px);
    border-color: #bfdbfe;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05), 0 24px 54px rgba(37, 99, 235, 0.11);
  }

  .embedding-save-btn:hover:not(:disabled),
  .embedding-reload-btn:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 12px 24px rgba(37, 99, 235, 0.1);
  }
}

.embedding-save-btn:active,
.embedding-reload-btn:active {
  transform: scale(0.98);
}

@media (max-width: 1220px) {
  .embedding-hero,
  .embedding-workspace {
    grid-template-columns: minmax(0, 1fr);
  }

  .embedding-guide-panel {
    position: static;
  }
}

@media (max-width: 920px) {
  .embedding-summary-grid,
  .config-overview,
  .field-grid.two {
    grid-template-columns: minmax(0, 1fr);
  }

  .embedding-hero-copy {
    min-height: 0;
    padding: 22px;
  }

  .embedding-hero-copy::before,
  .embedding-hero-copy::after {
    display: none;
  }

  .embedding-hero-copy h1 {
    font-size: 28px;
  }

  .embedding-card-head {
    flex-direction: column;
  }
}

@media (max-width: 620px) {
  .embedding-hero-actions,
  .embedding-save-btn,
  .embedding-reload-btn {
    width: 100%;
  }

  .embedding-status-panel strong {
    font-size: 28px;
  }
}
</style>
