<template>
  <div class="model-settings-page model-v9-shell runtime-meter-v24-shell">
    <div v-if="error" class="global-notice error">{{ error }}</div>
    <div v-if="success" class="global-notice success">{{ success }}</div>

    <section class="model-hero">
      <div class="model-hero-copy">
        <span class="model-kicker">模型网关</span>
        <h1>模型接入</h1>
        <p>统一维护通用大模型的供应商、模型名、接口地址、协议模式和密钥。客服回复、文本生成、商品改写等能力都会读取这里的通用模型配置。</p>

        <div class="model-hero-actions">
          <button type="button" class="model-save-btn" :disabled="saving || !configAvailable" @click="save">{{ saving ? '保存中...' : '保存配置' }}</button>
          <button type="button" class="model-reload-btn" :disabled="loading" @click="loadPage">{{ loading ? '加载中...' : '重新加载' }}</button>
        </div>
      </div>

      <aside class="model-status-panel" :class="runtimeStatusAvailable && runtimeStatus.generalModelConfigured ? 'green' : 'orange'" aria-label="通用模型状态">
        <span>通用模型</span>
        <strong>{{ runtimeStatusAvailable ? (runtimeStatus.generalModelConfigured ? '已配置' : '未设置') : '状态未知' }}</strong>
        <div class="model-status-meter">
          <i :class="runtimeStatusAvailable && runtimeStatus.generalModelConfigured ? 'meter-ready' : 'meter-empty'"></i>
        </div>
        <p>对话 / 改写 / 文本生成</p>
      </aside>
    </section>

    <section class="model-summary-grid" aria-label="模型接入摘要">
      <article class="model-summary-card">
        <span class="model-summary-icon blue">01</span>
        <div>
          <strong>兼容协议</strong>
          <p>支持 Chat Completions 与 Responses 两种通用模式，适配官方接口和中转网关。</p>
        </div>
      </article>
      <article class="model-summary-card">
        <span class="model-summary-icon green">02</span>
        <div>
          <strong>密钥保护</strong>
          <p>已保存的 Key 不会完整回显，切换接口主机时必须重新输入，降低误发风险。</p>
        </div>
      </article>
      <article class="model-summary-card">
        <span class="model-summary-icon amber">03</span>
        <div>
          <strong>策略增强</strong>
          <p>润色关键词和禁止润色关键词用于区分文本处理场景，不替代模型能力。</p>
        </div>
      </article>
    </section>

    <div class="model-workspace">
      <section class="model-v9-card model-config-panel">
        <div class="model-card-head">
          <div>
            <span>通用模型</span>
            <h2>接入参数</h2>
          </div>
          <p>所有通用 AI 调用都会优先读取这里的配置。建议按照“供应商 → 模型名 → 地址 → Key”的顺序填写。</p>
        </div>

        <div class="config-overview">
          <article class="overview-card">
            <span>适用场景</span>
            <strong>客服对话、商品润色、文本生成统一走这里</strong>
            <p>如果你的系统里多个功能都依赖同一套通用大模型，那么它们都会共享这组配置。</p>
          </article>
          <article class="overview-card">
            <span>填写原则</span>
            <strong>优先保证可调用，再处理别名与策略配置</strong>
            <p>先把最基础的供应商、模型名、接口地址和 API Key 填对，再补超时、润色策略等增强参数。</p>
          </article>
        </div>

        <div class="field-grid two">
          <OpsConfigField
            label="模型供应商"
            hint="用于标记你当前接入的是哪家服务，方便后续维护与切换。"
            meta="直接从下拉列表中选择供应商即可，无需手动输入。若列表中没有你使用的供应商，可选择“其他 / 自定义”。"
            badge="第一步"
            required
          >
            <select v-model="form.generalModel.provider" class="config-input config-select">
              <option value="" disabled>请选择供应商</option>
              <option v-for="p in providerOptions" :key="p.value" :value="p.value">{{ p.label }}</option>
              <option :value="CUSTOM_PROVIDER_VALUE">其他 / 自定义</option>
            </select>
            <input
              v-if="isCustomProvider"
              v-model="customProvider"
              class="config-input custom-provider-input"
              placeholder="输入自定义供应商标识，如 azure"
            />
          </OpsConfigField>

          <OpsConfigField
            label="模型名称"
            hint="系统默认会按这个名称发起调用，建议填写对外使用的标准模型名。"
            meta="参考填写：gpt-4o-mini。若你使用代理网关，这里通常填写网关要求的模型字段。"
            badge="核心参数"
            required
          >
            <input v-model="form.generalModel.modelName" class="config-input" :placeholder="config.generalModel.modelName || 'gpt-4o-mini'" />
          </OpsConfigField>

          <OpsConfigField
            label="接口地址"
            hint="仅支持可解析的公网 HTTPS OpenAI 兼容根地址；系统会拒绝明文 HTTP、本机、内网、重定向与代理环境。"
            meta="大多数服务以 /v1 结尾。切换到不同主机时必须同时重新输入 API Key，避免把已保存密钥发送到新地址。"
            badge="第二步"
            required
          >
            <input v-model="form.generalModel.baseUrl" class="config-input" :placeholder="config.generalModel.baseUrl || 'https://api.openai.com/v1'" />
          </OpsConfigField>

          <OpsConfigField
            label="自定义 Endpoint"
            hint="中转站/网关与官方 OpenAI 路径不一致时使用。填写后系统会直接使用你提供的完整兼容地址。"
            meta="请填写中转站提供的 HTTPS 完整兼容路径，且域名必须是公网可解析地址。留空则按上方接口地址自动拼接标准路径。"
            badge="中转站适配"
          >
            <input v-model="form.generalModel.endpoint" class="config-input" :placeholder="config.generalModel.endpoint || '留空走默认；完整地址以中转站说明为准'" />
          </OpsConfigField>

          <OpsConfigField
            label="API 模式"
            hint="切换对话协议。Chat Completions 是大多数 OpenAI 兼容中转的常见模式；Responses 适合明确标注支持 Responses 的服务。"
            meta="如不确定，请优先选择 Chat Completions；只有服务商明确要求 Responses 模式时再切换。"
            badge="协议"
          >
            <select v-model="form.generalModel.apiMode" class="config-input config-select">
              <option value="chat_completions">Chat Completions（/v1/chat/completions）</option>
              <option value="responses">Responses（/v1/responses）</option>
            </select>
          </OpsConfigField>

          <OpsConfigField
            label="API Key"
            hint="用于实际鉴权。保存后不会回显完整内容，只显示已保存状态。"
            meta="Key 轮换时直接覆盖即可；修改接口主机时也必须重新输入。若报 401/403，请检查 Key 与地址是否匹配。"
            badge="第三步"
            required
          >
              <SecretInput
              v-model="form.generalModel.apiKey"
              :placeholder="config.generalModel.apiKeyConfigured ? '已保存，直接输入新值可覆盖' : 'sk-...'"
              autocomplete="off"
            />
          </OpsConfigField>

          <OpsConfigField
            label="请求超时（秒）"
            hint="控制调用等待时长，过短会导致长回复或网络抖动时更容易失败。"
            meta="建议从 15 秒起步；如果模型回复较长或服务在海外，可适当提高到 30~60 秒。"
            badge="稳定性"
          >
            <input v-model.number="form.generalModel.requestTimeout" class="config-input" type="number" min="1" max="300" :placeholder="config.generalModel.requestTimeout ? String(config.generalModel.requestTimeout) : '15'" />
          </OpsConfigField>

          <OpsConfigField
            label="润色关键词"
            hint="命中这些词时，系统更倾向走润色、改写或优化描述的处理逻辑。"
            meta="支持逗号、顿号或换行分隔，适合填写“润色、改写、优化标题、增强卖点”等策略词。"
            badge="策略增强"
            wide
          >
            <textarea
              v-model="form.generalModel.polishKeywords"
              class="config-textarea"
              rows="3"
              :placeholder="config.generalModel.polishKeywords || '使用逗号、顿号或换行分隔'"
            />
          </OpsConfigField>

          <OpsConfigField
            label="禁止润色关键词"
            hint="命中这些词时跳过润色，避免把需要原样输出的内容误改写。"
            meta="适合放退款、投诉、售后等敏感语境，确保客服回复或记录类文本保持原意。"
            badge="风险控制"
            wide
          >
            <textarea
              v-model="form.generalModel.polishForbiddenKeywords"
              class="config-textarea"
              rows="3"
              :placeholder="config.generalModel.polishForbiddenKeywords || '使用逗号、顿号或换行分隔'"
            />
          </OpsConfigField>
        </div>
      </section>

      <aside class="model-v9-card model-guide-panel">
        <div class="model-card-head compact">
          <div>
            <span>接入建议</span>
            <h2>配置建议</h2>
          </div>
          <p>下面这些说明可以帮助你更快判断“应该填什么”，也能减少配置时的来回试错。</p>
        </div>

        <div class="guide-grid">
          <article class="guide-card">
            <div class="guide-icon">A</div>
            <div>
              <strong>优先保证基础调用通</strong>
              <p>先确保模型名、接口地址和 API Key 可以正常返回结果，再去优化策略与超时参数。</p>
            </div>
          </article>
          <article class="guide-card">
            <div class="guide-icon">B</div>
            <div>
              <strong>代理网关要看兼容协议</strong>
              <p>如果你不是直连官方接口，而是使用中转服务，模型名和地址请以中转服务文档为准。</p>
            </div>
          </article>
          <article class="guide-card">
            <div class="guide-icon">C</div>
            <div>
              <strong>润色词只做策略提示</strong>
              <p>它们不会替代模型能力本身，更适合用来区分不同业务语境下的回复处理方式。</p>
            </div>
          </article>
        </div>

        <ul class="hint-list">
          <li>通用模型负责站内大部分文本生成能力，和向量模型（Embedding）不是同一个用途。</li>
          <li>如果保存后仍报错，先检查接口地址是否正确、模型名是否被供应商支持、Key 是否和当前供应商匹配。</li>
          <li>如使用代理网关，请直接在“模型名称”中填写网关要求的模型字段，避免同一配置出现两个名称。</li>
          <li>建议为生产环境单独准备一套 API Key，避免与个人用途或其他业务混用，降低定位成本。</li>
        </ul>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
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

// 供应商下拉选项：预置常见厂商 + “其他 / 自定义”
const CUSTOM_PROVIDER_VALUE = '__custom__'
const PROVIDER_PRESETS = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'deepseek', label: 'DeepSeek 深度求索' },
  { value: 'qwen', label: '通义千问 Qwen' },
  { value: 'moonshot', label: 'Moonshot 月之暗面 (Kimi)' },
  { value: 'zhipu', label: '智谱 GLM' },
  { value: 'doubao', label: '豆包 Doubao' },
  { value: 'baichuan', label: 'Baichuan 百川' },
  { value: 'minimax', label: 'MiniMax' },
  { value: 'yi', label: '零一万物 Yi' },
  { value: 'stepfun', label: '阶跃星辰 Step' },
  { value: 'siliconflow', label: 'SiliconFlow 硅基流动' },
  { value: 'openrouter', label: 'OpenRouter' },
]

const customProvider = ref('')

// 已保存但不在预置列表中的供应商，作为单独一项展示，避免丢失原值
const providerOptions = computed(() => {
  const list = [...PROVIDER_PRESETS]
  const current = (config.generalModel?.provider || '').trim()
  if (
    current &&
    current !== CUSTOM_PROVIDER_VALUE &&
    !PROVIDER_PRESETS.some((p) => p.value === current)
  ) {
    list.push({ value: current, label: `自定义：${current}` })
  }
  return list
})

const isCustomProvider = computed(
  () => form.generalModel.provider === CUSTOM_PROVIDER_VALUE
)

const form = reactive({
  generalModel: {
    provider: '',
    modelName: '',
    baseUrl: '',
    apiKey: '',
    requestTimeout: null,
    polishKeywords: '',
    polishForbiddenKeywords: '',
    endpoint: '',
    apiMode: 'chat_completions',
  },
})

onMounted(() => {
  window.addEventListener('xya-header-action', onHeaderAction)
  loadPage()
})

onBeforeUnmount(() => {
  window.removeEventListener('xya-header-action', onHeaderAction)
})

// 仅回填下拉选择项；文本类输入保持为空，已保存值通过 placeholder 以提示文字形式展示，
// 用户选中输入框后可直接输入新值，无需先删除原有内容。
function syncForm() {
  const g = config.generalModel || {}
  const savedProvider = (g.provider || '').trim()
  if (savedProvider && !PROVIDER_PRESETS.some((p) => p.value === savedProvider)) {
    form.generalModel.provider = CUSTOM_PROVIDER_VALUE
    customProvider.value = savedProvider
  } else {
    form.generalModel.provider = savedProvider
    customProvider.value = ''
  }
  form.generalModel.modelName = ''
  form.generalModel.baseUrl = ''
  form.generalModel.apiKey = ''
  form.generalModel.requestTimeout = null
  form.generalModel.polishKeywords = ''
  form.generalModel.polishForbiddenKeywords = ''
  form.generalModel.endpoint = ''
  form.generalModel.apiMode = ''
}

async function loadPage() {
  await loadBundle({ includeRuntimeStatus: true })
  if (configAvailable.value) syncForm()
}

// 留空的字段回退到已保存值，避免误清空配置；输入了新值则覆盖。
function pickNext(next, old) {
  const n = (next == null ? '' : String(next)).trim()
  return n || (old == null ? '' : String(old)).trim()
}

async function save() {
  if (!configAvailable.value) return
  const prev = config.generalModel || {}
  let provider = (form.generalModel.provider || '').trim()
  if (provider === CUSTOM_PROVIDER_VALUE) {
    provider = customProvider.value.trim() || (prev.provider || '').trim()
  }
  if (!provider) provider = (prev.provider || '').trim()

  const payload = cloneOpenSourceConfig(config)
  payload.generalModel = {
    provider,
    modelName: pickNext(form.generalModel.modelName, prev.modelName),
    baseUrl: pickNext(form.generalModel.baseUrl, prev.baseUrl),
    apiKey: pickNext(form.generalModel.apiKey, prev.apiKey),
    requestTimeout:
      Number(form.generalModel.requestTimeout) ||
      Number(prev.requestTimeout) ||
      15,
    polishKeywords: pickNext(form.generalModel.polishKeywords, prev.polishKeywords),
    polishForbiddenKeywords: pickNext(
      form.generalModel.polishForbiddenKeywords,
      prev.polishForbiddenKeywords
    ),
    endpoint: pickNext(form.generalModel.endpoint, prev.endpoint),
    apiMode: pickNext(form.generalModel.apiMode, prev.apiMode || 'chat_completions'),
  }
  const saved = await saveConfig(payload, { successMessage: '通用模型配置已保存' })
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
.model-v9-shell {
  --model-primary: #2563eb;
  --model-primary-dark: #1d4ed8;
  --model-accent: #14b8a6;
  --model-warning: #f59e0b;
  --model-text: #111827;
  --model-muted: #64748b;
  --model-line: #e5e7eb;
  --model-panel: #ffffff;
  --model-soft: #f8fafc;
  --model-ease: cubic-bezier(0.23, 1, 0.32, 1);
  display: grid;
  gap: 16px;
  color: var(--model-text);
}

.model-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 16px;
  align-items: stretch;
}

.model-hero-copy,
.model-status-panel,
.model-summary-card,
.model-v9-card {
  border: 1px solid var(--model-line);
  border-radius: 8px;
  background: var(--model-panel);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05), 0 18px 42px rgba(15, 23, 42, 0.06);
}

.model-hero-copy {
  position: relative;
  overflow: hidden;
  min-height: 236px;
  padding: 28px;
  background:
    linear-gradient(120deg, rgba(255, 255, 255, 0.96), rgba(248, 251, 255, 0.94)),
    radial-gradient(circle at 84% 24%, rgba(37, 99, 235, 0.15), transparent 30%),
    radial-gradient(circle at 72% 90%, rgba(20, 184, 166, 0.13), transparent 24%);
}

.model-hero-copy::before {
  content: '';
  position: absolute;
  right: 28px;
  bottom: 24px;
  width: 236px;
  height: 132px;
  border: 1px solid rgba(37, 99, 235, 0.13);
  border-radius: 8px;
  background:
    linear-gradient(90deg, rgba(37, 99, 235, 0.13) 1px, transparent 1px),
    linear-gradient(180deg, rgba(37, 99, 235, 0.1) 1px, transparent 1px);
  background-size: 32px 32px;
  opacity: 0.62;
  transform: rotate(-3deg);
}

.model-kicker {
  position: relative;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  height: 28px;
  padding: 0 10px;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  background: #eff6ff;
  color: var(--model-primary-dark);
  font-size: 11px;
  font-weight: 850;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.model-hero-copy h1 {
  position: relative;
  z-index: 1;
  margin: 18px 0 10px;
  color: var(--model-text);
  font-size: 34px;
  line-height: 1.12;
  font-weight: 900;
  letter-spacing: 0;
}

.model-hero-copy p {
  position: relative;
  z-index: 1;
  max-width: 720px;
  margin: 0;
  color: var(--model-muted);
  font-size: 14px;
  line-height: 1.8;
}

.model-hero-actions {
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 22px;
}

.model-save-btn,
.model-reload-btn {
  min-height: 38px;
  padding: 0 15px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 850;
  cursor: pointer;
  transition:
    transform 140ms var(--model-ease),
    box-shadow 160ms var(--model-ease),
    border-color 160ms ease,
    background-color 160ms ease,
    color 160ms ease;
}

.model-save-btn {
  border: 1px solid transparent;
  background: linear-gradient(135deg, var(--model-primary), var(--model-accent));
  color: #ffffff;
  box-shadow: 0 12px 22px rgba(37, 99, 235, 0.18);
}

.model-reload-btn {
  border: 1px solid #bfdbfe;
  background: #ffffff;
  color: var(--model-primary-dark);
}

.model-save-btn:disabled,
.model-reload-btn:disabled {
  cursor: not-allowed;
  opacity: 0.62;
}

.model-status-panel {
  display: grid;
  align-content: space-between;
  gap: 14px;
  padding: 22px;
  background:
    linear-gradient(180deg, #ffffff 0%, #f8fafc 100%),
    radial-gradient(circle at 100% 0%, rgba(20, 184, 166, 0.14), transparent 30%);
}

.model-status-panel.orange {
  background:
    linear-gradient(180deg, #ffffff 0%, #fffbeb 100%),
    radial-gradient(circle at 100% 0%, rgba(245, 158, 11, 0.16), transparent 30%);
}

.model-status-panel span,
.model-card-head span {
  color: var(--model-muted);
  font-size: 12px;
  font-weight: 850;
}

.model-status-panel strong {
  color: var(--model-warning);
  font-size: 34px;
  line-height: 1.12;
  font-weight: 900;
  letter-spacing: 0;
}

.model-status-panel.green strong {
  color: #0f766e;
}

.model-status-panel p {
  margin: 0;
  color: var(--model-muted);
  font-size: 13px;
  line-height: 1.65;
}

.model-status-meter {
  height: 8px;
  overflow: hidden;
  border-radius: 999px;
  background: #e5e7eb;
}

.model-status-meter i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--model-primary), var(--model-accent));
  transition: width 220ms var(--model-ease);
}

.model-status-meter i.meter-ready {
  width: 76%;
}

.model-status-meter i.meter-empty {
  width: 34%;
}

.model-status-panel.orange .model-status-meter i {
  background: linear-gradient(90deg, var(--model-warning), var(--model-accent));
}

.model-summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.model-summary-card {
  display: grid;
  grid-template-columns: 48px minmax(0, 1fr);
  gap: 12px;
  align-items: start;
  padding: 16px;
  transition:
    transform 180ms var(--model-ease),
    border-color 180ms ease,
    box-shadow 180ms var(--model-ease);
}

.model-summary-icon {
  width: 48px;
  height: 48px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  color: var(--model-primary);
  background: #eff6ff;
  font-family: 'SF Mono', 'JetBrains Mono', 'Cascadia Code', monospace;
  font-size: 13px;
  font-weight: 900;
}

.model-summary-icon.green {
  color: #0f766e;
  background: #f0fdfa;
}

.model-summary-icon.amber {
  color: #b45309;
  background: #fffbeb;
}

.model-summary-card strong,
.model-card-head h2,
.overview-card strong,
.guide-card strong {
  color: var(--model-text);
  font-weight: 850;
}

.model-summary-card p,
.model-card-head p,
.overview-card p,
.guide-card p {
  margin: 6px 0 0;
  color: var(--model-muted);
  font-size: 12px;
  line-height: 1.7;
}

.model-workspace {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 16px;
  align-items: start;
}

.model-v9-card {
  padding: 18px;
  transition:
    transform 180ms var(--model-ease),
    border-color 180ms ease,
    box-shadow 180ms var(--model-ease);
}

.model-guide-panel {
  position: sticky;
  top: 12px;
}

.model-card-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18px;
  margin-bottom: 16px;
}

.model-card-head.compact {
  display: grid;
  gap: 8px;
}

.model-card-head h2 {
  margin: 4px 0 0;
  font-size: 20px;
  line-height: 1.25;
  letter-spacing: 0;
}

.model-card-head p {
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
    radial-gradient(circle at 100% 0%, rgba(37, 99, 235, 0.1), transparent 28%);
}

.overview-card span {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 8px;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  background: #eff6ff;
  color: var(--model-primary-dark);
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

.model-v9-shell :deep(.ops-config-field) {
  border-color: var(--model-line);
  border-radius: 8px;
  background: var(--model-soft);
  box-shadow: none;
  transition:
    transform 180ms var(--model-ease),
    border-color 180ms ease,
    box-shadow 180ms var(--model-ease);
}

.model-v9-shell :deep(.ops-config-field:hover) {
  border-color: #bfdbfe;
  box-shadow: 0 16px 34px rgba(37, 99, 235, 0.08);
}

.model-v9-shell :deep(.ops-config-field-label) {
  color: var(--model-text);
  letter-spacing: 0;
}

.model-v9-shell :deep(.ops-config-field-badge) {
  border-radius: 8px;
  background: #eff6ff;
  color: var(--model-primary-dark);
}

.model-v9-shell :deep(.ops-config-field-required) {
  border-radius: 8px;
}

.model-v9-shell :deep(.ops-config-field-hint),
.model-v9-shell :deep(.ops-config-field-meta) {
  color: var(--model-muted);
}

.model-v9-shell :deep(.config-input),
.model-v9-shell :deep(.config-textarea),
.model-v9-shell :deep(.secret-input) {
  border-color: #dbe3ee;
  border-radius: 8px;
  color: var(--model-text);
  background: #ffffff;
}

.model-v9-shell :deep(.config-input:hover),
.model-v9-shell :deep(.config-textarea:hover),
.model-v9-shell :deep(.secret-input:hover) {
  border-color: #bfdbfe;
}

.model-v9-shell :deep(.config-input:focus),
.model-v9-shell :deep(.config-input:focus-visible),
.model-v9-shell :deep(.config-textarea:focus),
.model-v9-shell :deep(.config-textarea:focus-visible),
.model-v9-shell :deep(.secret-input:focus-within) {
  border-color: var(--model-primary);
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.1);
}

.model-v9-shell :deep(.secret-input-control) {
  color: var(--model-text);
}

.model-v9-shell :deep(.secret-input-toggle) {
  border-left-color: var(--model-line);
  background: #f8fbff;
  color: var(--model-primary-dark);
  transition:
    background-color 160ms ease,
    color 160ms ease;
}

:deep(.config-select) {
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  padding-right: 38px;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'><polyline points='6 9 12 15 18 9'></polyline></svg>");
  background-repeat: no-repeat;
  background-position: right 14px center;
  cursor: pointer;
}

.custom-provider-input {
  margin-top: 10px;
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
  border: 1px solid var(--model-line);
  border-radius: 8px;
  background: var(--model-soft);
}

.guide-icon {
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: #eff6ff;
  color: var(--model-primary-dark);
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
  color: var(--model-muted);
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
  background: var(--model-accent);
}

@media (hover: hover) and (pointer: fine) {
  .model-summary-card:hover,
  .model-v9-card:hover {
    transform: translateY(-2px);
    border-color: #bfdbfe;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05), 0 24px 54px rgba(37, 99, 235, 0.11);
  }

  .model-save-btn:hover:not(:disabled),
  .model-reload-btn:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 12px 24px rgba(37, 99, 235, 0.1);
  }
}

.model-save-btn:active,
.model-reload-btn:active {
  transform: scale(0.98);
}

@media (max-width: 1220px) {
  .model-hero,
  .model-workspace {
    grid-template-columns: minmax(0, 1fr);
  }

  .model-guide-panel {
    position: static;
  }
}

@media (max-width: 920px) {
  .model-summary-grid,
  .config-overview,
  .field-grid.two {
    grid-template-columns: minmax(0, 1fr);
  }

  .model-hero-copy {
    min-height: 0;
    padding: 22px;
  }

  .model-hero-copy::before {
    display: none;
  }

  .model-hero-copy h1 {
    font-size: 28px;
  }

  .model-card-head {
    flex-direction: column;
  }
}

@media (max-width: 620px) {
  .model-hero-actions,
  .model-save-btn,
  .model-reload-btn {
    width: 100%;
  }

  .model-status-panel strong {
    font-size: 28px;
  }
}
</style>
