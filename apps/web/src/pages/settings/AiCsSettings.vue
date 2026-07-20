<template>
  <div class="aics-page aics-v9-shell">
    <div v-if="error" class="global-notice error">{{ error }}</div>
    <div v-if="success" class="global-notice success">{{ success }}</div>

    <section class="aics-hero">
      <div class="aics-hero-copy">
        <span class="aics-kicker">AI 客服</span>
        <h1>AI 客服策略中心</h1>
        <p>统一配置自动回复工作模式、客服人设、知识库、安全门禁和验证流程。策略保存前先用右侧模拟消息验证，避免错误话术直接进入真实会话。</p>
        <div class="aics-hero-actions">
          <button type="button" class="aics-save-btn" :disabled="saving || loading || configAvailable !== true" @click="save">{{ saving ? '保存中...' : '保存配置' }}</button>
          <button type="button" class="aics-test-btn" :disabled="testing || loading || configAvailable !== true" @click="openTestPanel">{{ testing ? '验证中...' : '验证 AI 回复' }}</button>
          <button type="button" class="aics-retry-btn" :disabled="loading" @click="load">重新加载</button>
        </div>
      </div>

      <aside class="aics-hero-status" aria-label="AI 客服当前状态">
        <span>当前状态</span>
        <strong :class="aiReceptionActive ? 'green' : 'red'">{{ configuredStatusText }}</strong>
        <div class="aics-status-meter" aria-hidden="true">
          <progress :value="statusMeterValue" max="100"></progress>
        </div>
        <p>{{ form.workHours24 ? `全天（${form.timeZone}）` : `${form.workStart}-${form.workEnd}（${form.timeZone}）` }}</p>
      </aside>
    </section>

    <BusinessStatusStrip v-if="aiCsStatusItems.length" :items="aiCsStatusItems" />

    <div v-if="loading" class="aics-loading">配置加载中...</div>
    <div v-else-if="configAvailable === false" class="aics-unavailable" role="alert">
      <strong>AI 客服配置状态未知</strong>
      <p>持久化配置读取失败。为避免用页面默认值覆盖现有配置，编辑、验证、上传与保存均已禁用。</p>
      <button type="button" class="aics-retry-btn" @click="load">重试读取配置</button>
    </div>
    <template v-else>
      <section class="aics-summary-grid" aria-label="AI 客服策略摘要">
        <article class="aics-summary-card">
          <span class="aics-summary-icon blue">01</span>
          <div>
            <strong>{{ modeText }}</strong>
            <p>当前接待模式，决定模型调用、外发回复和人工接管的边界。</p>
          </div>
        </article>
        <article class="aics-summary-card">
          <span class="aics-summary-icon green">02</span>
          <div>
            <strong>{{ form.knowledgeBases.length }} 份知识库</strong>
            <p>自定义知识会优先参与回答，适合维护商品参数、发货和售后口径。</p>
          </div>
        </article>
        <article class="aics-summary-card">
          <span class="aics-summary-icon amber">03</span>
          <div>
            <strong>{{ keywordGateEnabled ? '门禁已开启' : '门禁未开启' }}</strong>
            <p>命中转人工或黑名单关键词时，系统会把会话留给人工处理。</p>
          </div>
        </article>
      </section>

      <div class="aics-grid">
        <div class="aics-main">
          <section class="aics-v9-card">
            <div class="aics-card-head">
              <div>
                <span>运行策略</span>
                <h2>AI 客服工作模式</h2>
              </div>
              <p>主开关开启且选择自动或混合模式后，系统才会按下方运行策略处理买家消息。</p>
            </div>

            <div class="aics-form">
              <div class="aics-row aics-row-toggle">
                <div>
                  <strong>启用 AI 自动回复</strong>
                  <p>是否实际发送还受接待模式、账号/商品范围、工作时段、人工接管、日额度、模型与账号连接状态约束。</p>
                </div>
                <button type="button" :class="['aics-switch', { on: form.enabled }]" :aria-pressed="form.enabled" aria-label="启用 AI 自动回复" @click="form.enabled = !form.enabled">
                  <span class="aics-switch-knob"></span>
                </button>
              </div>

              <div class="aics-field-grid">
                <div class="aics-row">
                  <label>策略时区</label>
                  <select v-model="form.timeZone" class="aics-input">
                    <option value="Asia/Shanghai">Asia/Shanghai（UTC+08:00）</option>
                    <option value="UTC">UTC（UTC+00:00）</option>
                  </select>
                  <p class="aics-hint">工作时段和每日回复额度都按此时区计算。</p>
                </div>

                <div class="aics-row">
                  <label>接待模式</label>
                  <select v-model="form.mode" class="aics-input">
                    <option value="auto">自动模式（按安全模式配置执行关键词门禁）</option>
                    <option value="hybrid">混合模式（命中人工/黑名单关键词时 AI 停答）</option>
                    <option value="manual">人工模式（不调用模型、不自动发送）</option>
                  </select>
                </div>

                <div class="aics-row">
                  <label>回复延时（秒）</label>
                  <input v-model.number="form.replyDelaySeconds" type="number" min="5" max="120" class="aics-input" />
                  <p class="aics-hint">建议保持 8 到 15 秒，便于合并连续咨询。</p>
                </div>

                <div v-if="form.pauseOnHumanIntervene" class="aics-row">
                  <label>人工接管暂停时长（分钟）</label>
                  <input v-model.number="form.humanInterventionPauseMinutes" type="number" min="1" max="1440" class="aics-input" />
                  <p class="aics-hint">窗口结束后，新的买家消息才重新具备自动回复资格。</p>
                </div>
              </div>

              <div class="aics-row aics-row-toggle">
                <div>
                  <strong>全天时段自动回复</strong>
                  <p>开启后配置为全天候处理时段；实际回复仍依赖模型、账号连接和平台服务状态。</p>
                </div>
                <button type="button" :class="['aics-switch', { on: form.workHours24 }]" :aria-pressed="form.workHours24" aria-label="全天时段自动回复" @click="form.workHours24 = !form.workHours24">
                  <span class="aics-switch-knob"></span>
                </button>
              </div>

              <div v-if="!form.workHours24" class="aics-row">
                <label>工作时段</label>
                <div class="aics-time-pair">
                  <input v-model="form.workStart" type="time" class="aics-input" />
                  <span>至</span>
                  <input v-model="form.workEnd" type="time" class="aics-input" />
                </div>
                <p class="aics-hint">开始时间晚于结束时间表示跨午夜，例如 22:00-06:00；结束时刻不包含在工作时段内。</p>
              </div>

              <div class="aics-row aics-row-toggle">
                <div>
                  <strong>携带对话上下文</strong>
                  <p>开启后 AI 会读取最近 10 条历史消息以理解语境。</p>
                </div>
                <button type="button" :class="['aics-switch', { on: form.carryContext }]" :aria-pressed="form.carryContext" aria-label="携带对话上下文" @click="form.carryContext = !form.carryContext">
                  <span class="aics-switch-knob"></span>
                </button>
              </div>

              <div class="aics-row aics-row-toggle">
                <div>
                  <strong>人工干预自动暂停</strong>
                  <p>同一账号、同一会话检测到近期非 AI 客服的卖家端消息后暂停；来源无法确认的卖家消息按人工接管处理。</p>
                </div>
                <button type="button" :class="['aics-switch', { on: form.pauseOnHumanIntervene }]" :aria-pressed="form.pauseOnHumanIntervene" aria-label="人工干预自动暂停" @click="form.pauseOnHumanIntervene = !form.pauseOnHumanIntervene">
                  <span class="aics-switch-knob"></span>
                </button>
              </div>
            </div>
          </section>

          <section class="aics-v9-card">
            <div class="aics-card-head">
              <div>
                <span>话术资产</span>
                <h2>客服角色与知识库</h2>
              </div>
              <p>维护 AI 客服身份、回复语气、系统提示词、知识库和聊天规则。</p>
            </div>

            <div class="aics-form">
              <div class="aics-field-grid compact">
                <div class="aics-row">
                  <label>客服人设</label>
                  <input v-model="form.persona" class="aics-input" placeholder="如：专业客服" />
                </div>

                <div class="aics-row">
                  <label>回复语气</label>
                  <select v-model="form.tone" class="aics-input">
                    <option value="friendly">友好亲切</option>
                    <option value="professional">专业严谨</option>
                    <option value="casual">轻松活泼</option>
                  </select>
                </div>

                <div class="aics-row">
                  <label>回复语言</label>
                  <select v-model="form.language" class="aics-input">
                    <option value="zh-CN">简体中文</option>
                    <option value="en">英文</option>
                  </select>
                </div>
              </div>

              <div class="aics-row">
                <div class="aics-label-row">
                  <label>系统提示词</label>
                  <button type="button" class="aics-restore-btn" @click="restoreDefault('systemPrompt')">恢复默认</button>
                </div>
                <textarea
                  v-model="form.systemPrompt"
                  class="aics-input aics-textarea"
                  rows="5"
                  placeholder="定义 AI 的角色、店铺信息、商品特色与回复边界"
                ></textarea>
              </div>

              <div class="aics-row">
                <div class="aics-label-row">
                  <label>知识库（优先于默认配置）</label>
                  <span class="aics-kb-count">共 {{ form.knowledgeBases.length }} 份</span>
                </div>
                <div class="aics-upload-area">
                  <input
                    ref="kbFileInputRef"
                    type="file"
                    accept=".md,.txt,.pptx,.xlsx,.csv"
                    class="aics-file-input"
                    @change="onKbFileChange"
                  />
                  <button type="button" class="aics-upload-btn" :disabled="kbUploading" @click="kbFileInputRef?.click()">
                    {{ kbUploading ? '正在提取...' : '上传知识库文件' }}
                  </button>
                  <button type="button" class="aics-upload-btn" @click="addKnowledgeBase">新增手动知识库</button>
                  <span class="aics-upload-hint">支持多份内容叠加，AI 会优先读取自定义知识库。</span>
                </div>
                <div class="aics-entry-list">
                  <div v-for="(item, index) in form.knowledgeBases" :key="`kb-${index}`" class="aics-entry-card">
                    <div class="aics-entry-head">
                      <input v-model="item.name" class="aics-input" placeholder="知识库名称" />
                      <button type="button" class="aics-entry-remove" @click="removeKnowledgeBase(index)">删除</button>
                    </div>
                    <textarea
                      v-model="item.content"
                      class="aics-input aics-textarea aics-kb-textarea"
                      rows="6"
                      placeholder="填写商品参数、发货说明、售后口径、店铺边界等"
                    ></textarea>
                    <div class="aics-entry-meta">
                      <span>{{ item.source === 'upload' ? '来自文件' : '手动维护' }}</span>
                      <span>{{ (item.content || '').length }} 字</span>
                    </div>
                  </div>
                  <div v-if="!form.knowledgeBases.length" class="aics-empty-tip">还没有添加自定义知识库，当前将使用系统默认知识库。</div>
                </div>
              </div>

              <div class="aics-row">
                <div class="aics-label-row">
                  <label>聊天规则（优先于默认规则）</label>
                  <span class="aics-kb-count">共 {{ form.chatRules.length }} 条</span>
                </div>
                <div class="aics-entry-list">
                  <div v-for="(item, index) in form.chatRules" :key="`rule-${index}`" class="aics-entry-card">
                    <div class="aics-entry-head">
                      <input v-model="item.name" class="aics-input" placeholder="规则名称" />
                      <button type="button" class="aics-entry-remove" @click="removeChatRule(index)">删除</button>
                    </div>
                    <textarea
                      v-model="item.content"
                      class="aics-input aics-textarea"
                      rows="4"
                      placeholder="例如：只能回答商品本身，不要主动延展售后承诺"
                    ></textarea>
                  </div>
                  <div v-if="!form.chatRules.length" class="aics-empty-tip">暂未添加自定义聊天规则，当前将使用默认规则。</div>
                </div>
                <button type="button" class="aics-upload-btn" @click="addChatRule">新增聊天规则</button>
              </div>
            </div>
          </section>

          <section class="aics-v9-card">
            <div class="aics-card-head">
              <div>
                <span>安全边界</span>
                <h2>安全与会话策略</h2>
              </div>
              <p>命中明确配置的关键词时停止 AI 回复，把会话留给人工处理。</p>
            </div>

            <div class="aics-form">
              <div class="aics-row aics-row-toggle">
                <div>
                  <strong>自动模式启用关键词门禁</strong>
                  <p>自动模式下命中下方任一关键词时 AI 停答；混合模式始终执行该门禁。</p>
                </div>
                <button
                  type="button"
                  :class="['aics-switch', { on: keywordGateEnabled }]"
                  :disabled="form.mode === 'hybrid'"
                  :aria-pressed="keywordGateEnabled"
                  aria-label="关键词安全门禁"
                  @click="form.safeMode = !form.safeMode"
                >
                  <span class="aics-switch-knob"></span>
                </button>
              </div>

              <div class="aics-field-grid">
                <div class="aics-row">
                  <label>转人工关键词</label>
                  <input v-model="form.handoffKeywords" class="aics-input" placeholder="用 、 分隔，如：退款、投诉、维权" />
                  <p class="aics-hint">命中后系统不调用模型、不发送 AI 回复。</p>
                </div>

                <div class="aics-row">
                  <label>会话黑名单关键词</label>
                  <input v-model="form.blacklistKeywords" class="aics-input" placeholder="命中后 AI 不回复，如：低价、加微" />
                </div>

                <div class="aics-row">
                  <label>每日最大回复数</label>
                  <input v-model.number="form.maxDailyReplies" type="number" min="1" max="10000" class="aics-input" />
                  <p class="aics-hint">达到上限后不调用模型也不发送。</p>
                </div>
              </div>
            </div>
          </section>

          <div class="aics-actions">
            <button type="button" class="aics-save-btn" :disabled="saving" @click="save">{{ saving ? '保存中...' : '保存配置' }}</button>
            <button type="button" class="aics-test-btn" :disabled="testing" @click="openTestPanel">{{ testing ? '验证中...' : '验证 AI 回复' }}</button>
          </div>
        </div>

        <aside class="aics-side">
          <section class="aics-v9-card aics-preview-card">
            <div class="aics-card-head compact">
              <div>
                <span>模拟验证</span>
                <h2>回复效果预览</h2>
              </div>
            </div>
            <div class="aics-preview">
              <div class="aics-bubble them">这个价格还能再优惠吗？</div>
              <div v-if="testReply" class="aics-bubble me">{{ testReply }}</div>
              <div v-else class="aics-bubble me">点击下方“生成回复”按钮查看当前模型返回效果。</div>
            </div>

            <div class="aics-test-form">
              <textarea v-model="testMessage" class="aics-input" rows="2" placeholder="输入模拟买家消息..."></textarea>
              <button type="button" class="aics-test-btn" :disabled="testing || !testMessage.trim()" @click="runTest">
                {{ testing ? '生成中...' : '生成回复' }}
              </button>
            </div>

            <div v-if="testError" class="aics-error-box">
              <p class="aics-error">{{ testError }}</p>
              <button type="button" class="aics-retry-btn" :disabled="testing" @click="runTest">{{ testing ? '重试中...' : '重试' }}</button>
            </div>

            <div v-if="testConfigured === false" class="aics-warn-box">
              <p class="aics-warn">AI 模型未配置，请先到「系统设置 / 模型配置」填写 baseUrl、apiKey 与模型名称。</p>
              <button type="button" class="aics-retry-btn" @click="goToModelConfig">前往模型配置</button>
            </div>
          </section>

          <section class="aics-v9-card">
            <div class="aics-card-head compact">
              <div>
                <span>运行概览</span>
                <h2>AI 客服状态</h2>
              </div>
            </div>
            <div class="aics-status-list">
              <div class="aics-status-row">
                <span>当前状态</span>
                <b :class="aiReceptionActive ? 'green' : 'red'">{{ configuredStatusText }}</b>
              </div>
              <div class="aics-status-row">
                <span>工作时段</span>
                <b>{{ form.workHours24 ? `全天（${form.timeZone}）` : `${form.workStart}-${form.workEnd}（${form.timeZone}）` }}</b>
              </div>
              <div class="aics-status-row">
                <span>接待模式</span>
                <b>{{ modeText }}</b>
              </div>
              <div class="aics-status-row">
                <span>安全模式</span>
                <b :class="keywordGateEnabled ? 'green' : 'red'">{{ keywordGateEnabled ? '关键词门禁开启' : '关键词门禁关闭' }}</b>
              </div>
              <div class="aics-status-row">
                <span>自定义知识库</span>
                <b>{{ form.knowledgeBases.length }} 份</b>
              </div>
              <div class="aics-status-row">
                <span>自定义规则</span>
                <b>{{ form.chatRules.length }} 条</b>
              </div>
            </div>
          </section>
        </aside>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import BusinessStatusStrip from '../../components/business/BusinessStatusStrip.vue'
import {
  getAiCsDefaults,
  getBusinessSettings,
  saveBusinessSettings,
  testAiCustomerService,
  uploadKnowledgeBase
} from '../../api/businessSettings.js'
import { confirmAction } from '../../utils/confirmAction.js'

const emit = defineEmits(['navigate'])

const loading = ref(true)
const configAvailable = ref(null)
const saving = ref(false)
const testing = ref(false)
const success = ref('')
const error = ref('')
const aiCsStatusItems = computed(() => [
  { key: 'config', label: '配置', value: configAvailable.value === true ? '已加载' : (configAvailable.value === false ? '加载失败' : '加载中'), tone: configAvailable.value === true ? 'green' : (configAvailable.value === false ? 'red' : 'orange') },
  { key: 'enabled', label: 'AI 自动回复', value: form.enabled ? '已启用' : '未启用', tone: form.enabled ? 'green' : 'gray' },
  { key: 'reception', label: '接待模式', value: aiReceptionActive.value ? '自动接待中' : '已停止', tone: aiReceptionActive.value ? 'green' : 'gray' },
  { key: 'knowledge', label: '知识库', value: form.knowledgeBases && form.knowledgeBases.length ? form.knowledgeBases.length + ' 份' : '未配置', tone: form.knowledgeBases && form.knowledgeBases.length ? 'blue' : 'orange' }
])



const testMessage = ref('你好，这个商品还能再优惠点吗？')
const testReply = ref('')
const testError = ref('')
const testConfigured = ref(null)

const kbFileInputRef = ref(null)
const kbUploading = ref(false)

const form = reactive({
  enabled: false,
  mode: 'hybrid',
  workHours24: true,
  workStart: '09:00',
  workEnd: '22:00',
  timeZone: 'Asia/Shanghai',
  persona: '专业客服',
  tone: 'friendly',
  language: 'zh-CN',
  replyDelaySeconds: 8,
  carryContext: true,
  pauseOnHumanIntervene: true,
  humanInterventionPauseMinutes: 30,
  systemPrompt: '',
  knowledgeBase: '',
  knowledgeBases: [],
  defaultKnowledgeBases: [],
  chatRules: [],
  defaultChatRules: [],
  blacklistKeywords: '',
  maxDailyReplies: 200,
  safeMode: true,
  handoffKeywords: '退款、投诉、赔付、维权、改地址'
})

const LEGACY_SYSTEM_PROMPT_MARKERS = [
  '你是闲鱼店铺的专业客服助手',
  '你是本店的AI客服',
  '使用“您好”“亲”等称呼'
]

const modeText = computed(() => ({
  auto: '自动模式',
  hybrid: '混合模式',
  manual: '人工模式'
}[form.mode] || '-'))

const configuredStatusText = computed(() => {
  if (!form.enabled) return '主开关已停用'
  if (form.mode === 'manual') return '人工模式（不外发）'
  return '自动策略已配置'
})

const aiReceptionActive = computed(() => form.enabled && form.mode !== 'manual')
const statusMeterValue = computed(() => aiReceptionActive.value ? 72 : 30)
const keywordGateEnabled = computed(() => form.mode === 'hybrid' || form.safeMode)

function resetNotices() {
  success.value = ''
  error.value = ''
}

function setSuccess(message) {
  success.value = message
  error.value = ''
}

function setError(message) {
  error.value = message
  success.value = ''
}

function normalizeEntry(item, fallbackName) {
  if (!item) return null
  if (typeof item === 'string') {
    const content = item.trim()
    if (!content) return null
    return { name: fallbackName, content, source: 'manual' }
  }
  const content = String(item.content || '').trim()
  if (!content) return null
  return {
    name: String(item.name || item.title || fallbackName),
    content,
    source: String(item.source || 'manual')
  }
}

function normalizeEntries(raw, fallbackText = '', prefix = '内容') {
  const list = Array.isArray(raw)
    ? raw.map((item, index) => normalizeEntry(item, `${prefix}${index + 1}`)).filter(Boolean)
    : []
  if (!list.length && String(fallbackText || '').trim()) {
    list.push({ name: `${prefix}1`, content: String(fallbackText).trim(), source: 'manual' })
  }
  return list
}

function looksLikeLegacyText(value, markers) {
  const text = String(value || '').trim()
  return text && markers.some(marker => text.includes(marker))
}

async function load() {
  loading.value = true
  configAvailable.value = null
  resetNotices()
  try {
    const [configResult, defaultsResult] = await Promise.allSettled([
      getBusinessSettings('ai-customer-service'),
      getAiCsDefaults()
    ])
    if (configResult.status !== 'fulfilled') {
      configAvailable.value = false
      setError(configResult.reason?.message || 'AI 客服持久化配置读取失败')
      return
    }
    const configRes = configResult.value
    const defaultsRes = defaultsResult.status === 'fulfilled' ? defaultsResult.value : {}
    const data = configRes?.data ?? configRes ?? {}
    const defaults = defaultsRes?.data ?? defaultsRes ?? {}

    Object.keys(form).forEach(key => {
      if (data[key] !== undefined) {
        form[key] = data[key]
      } else if (defaults[key] !== undefined) {
        form[key] = defaults[key]
      }
    })

    if (looksLikeLegacyText(form.systemPrompt, LEGACY_SYSTEM_PROMPT_MARKERS) && defaults.systemPrompt) {
      form.systemPrompt = defaults.systemPrompt
    }
    form.knowledgeBases = normalizeEntries(data.knowledgeBases, data.knowledgeBase, '知识库')
    form.defaultKnowledgeBases = normalizeEntries(data.defaultKnowledgeBases, '', '默认知识库')
    form.chatRules = normalizeEntries(data.chatRules, '', '规则')
    form.defaultChatRules = normalizeEntries(data.defaultChatRules, '', '默认规则')
    configAvailable.value = true
  } catch (requestError) {
    if (import.meta.env.DEV) console.error('[AiCs] 加载失败')
    configAvailable.value = false
    setError(requestError?.message || 'AI 客服配置加载失败')
  } finally {
    loading.value = false
  }
}

async function save() {
  resetNotices()
  if (configAvailable.value !== true) {
    setError('配置状态未知，无法保存；请先重试读取配置')
    return
  }
  const policyError = validatePolicyForm()
  if (policyError) {
    setError(policyError)
    return
  }
  saving.value = true
  try {
    const payload = {
      ...form,
      knowledgeBases: form.knowledgeBases.filter(item => item?.content?.trim()),
      chatRules: form.chatRules.filter(item => item?.content?.trim()),
      knowledgeBase: form.knowledgeBases
        .map(item => item?.content?.trim())
        .filter(Boolean)
        .join('\n\n')
    }
    await saveBusinessSettings('ai-customer-service', payload)
    setSuccess('AI 客服配置已保存')
  } catch (requestError) {
    setError(requestError?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

function validatePolicyForm() {
  if (!['Asia/Shanghai', 'UTC'].includes(form.timeZone)) {
    return '请选择页面提供的策略时区'
  }
  const timePattern = /^(?:[01]\d|2[0-3]):[0-5]\d$/
  if (!timePattern.test(String(form.workStart || '')) || !timePattern.test(String(form.workEnd || ''))) {
    return '工作时段必须使用 HH:MM 格式'
  }
  if (!form.workHours24 && form.workStart === form.workEnd) {
    return '非全天工作时段的开始与结束时间不能相同'
  }
  const maxDailyReplies = Number(form.maxDailyReplies)
  if (!Number.isInteger(maxDailyReplies) || maxDailyReplies < 1 || maxDailyReplies > 10000) {
    return '每日最大回复数必须是 1 到 10000 之间的整数'
  }
  const pauseMinutes = Number(form.humanInterventionPauseMinutes)
  if (!Number.isInteger(pauseMinutes) || pauseMinutes < 1 || pauseMinutes > 1440) {
    return '人工接管暂停时长必须是 1 到 1440 之间的整数'
  }
  return ''
}

function openTestPanel() {
  // A previous successful test used to make this button a no-op. Always run a
  // fresh request so operators can validate a newly saved model configuration.
  if (configAvailable.value !== true) {
    setError('配置状态未知，无法验证；请先重试读取配置')
    return
  }
  runTest()
}

async function runTest() {
  if (configAvailable.value !== true) {
    setError('配置状态未知，无法验证；请先重试读取配置')
    return
  }
  if (!testMessage.value.trim()) return

  testing.value = true
  testReply.value = ''
  testError.value = ''
  testConfigured.value = null
  resetNotices()

  try {
    const res = await testAiCustomerService(testMessage.value.trim())
    const data = res?.data ?? res ?? {}
    if (data?.ok) {
      testReply.value = data.reply || '（无回复内容）'
      return
    }

    if (data?.errorCode === 'NOT_CONFIGURED' || data?.configured === false) {
      testConfigured.value = false
      return
    }

    if (data?.errorCode === 'AI_ERROR') {
      testError.value = data?.reply || data?.message || 'AI 调用失败，请稍后重试'
      return
    }

    testError.value = data?.reply || data?.message || 'AI 未返回有效回复'
  } catch (requestError) {
    const message = requestError?.message || '网络异常，请检查网络连接后重试'
    if (Number(requestError?.status) === 503 && message.includes('未配置')) {
      testConfigured.value = false
    } else {
      testError.value = message
    }
  } finally {
    testing.value = false
  }
}

async function onKbFileChange(event) {
  if (configAvailable.value !== true) {
    setError('配置状态未知，无法上传；请先重试读取配置')
    return
  }
  const file = event.target.files?.[0]
  if (!file) return
  event.target.value = ''

  if (file.size > 10 * 1024 * 1024) {
    setError('文件不能超过 10MB')
    return
  }

  const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase()
  if (!['.md', '.txt', '.pptx', '.xlsx', '.csv'].includes(ext)) {
    setError('仅支持 .md / .txt / .pptx / .xlsx / .csv；旧版 .ppt / .xls 请先另存为新版格式')
    return
  }

  kbUploading.value = true
  resetNotices()
  try {
    const res = await uploadKnowledgeBase(file)
    const data = res?.data ?? res ?? {}
    const extractedText = data?.extractedText || ''
    const ruleCount = data?.ruleCount || 0
    const fileName = data?.fileName || file.name
    if (!extractedText) {
      setError('未能从文件中提取有效内容')
      return
    }
    form.knowledgeBases.push({
      name: fileName,
      content: extractedText,
      source: 'upload'
    })
    setSuccess(`已从 ${fileName} 提取 ${ruleCount} 条内容，并加入知识库`)
  } catch (requestError) {
    setError(requestError?.message || '文件上传失败')
  } finally {
    kbUploading.value = false
  }
}

function addKnowledgeBase() {
  form.knowledgeBases.push({ name: `知识库${form.knowledgeBases.length + 1}`, content: '', source: 'manual' })
}

function removeKnowledgeBase(index) {
  form.knowledgeBases.splice(index, 1)
}

function addChatRule() {
  form.chatRules.push({ name: `规则${form.chatRules.length + 1}`, content: '', source: 'manual' })
}

function removeChatRule(index) {
  form.chatRules.splice(index, 1)
}

async function restoreDefault(field) {
  if (configAvailable.value !== true) {
    setError('配置状态未知，无法恢复默认值；请先重试读取配置')
    return
  }
  if (field !== 'systemPrompt') return
  const label = '系统提示词'
  const confirmed = await confirmAction({
    title: `恢复默认${label}？`,
    description: `恢复默认将覆盖当前${label}内容，是否继续？`,
    confirmText: '恢复默认'
  })
  if (!confirmed) return

  resetNotices()
  try {
    const res = await getAiCsDefaults()
    const data = res?.data ?? res ?? {}
    if (data[field] !== undefined) {
      form[field] = data[field]
      setSuccess(`已恢复默认${label}，请记得保存配置`)
    }
  } catch (requestError) {
    setError(requestError?.message || `恢复默认${label}失败`)
  }
}

function goToModelConfig() {
  emit('navigate', 'settings-model')
}

function onHeaderAction(event) {
  if (event.detail === 'aics-save') save()
  if (event.detail === 'aics-test') openTestPanel()
  if (event.detail === 'aics-reload') load()
}

onMounted(() => {
  window.addEventListener('xya-header-action', onHeaderAction)
  load()
})

onBeforeUnmount(() => {
  window.removeEventListener('xya-header-action', onHeaderAction)
})
</script>

<style scoped>
.aics-v9-shell {
  --aics-primary: #2563eb;
  --aics-primary-dark: #1d4ed8;
  --aics-accent: #14b8a6;
  --aics-warning: #f59e0b;
  --aics-danger: #ef4444;
  --aics-text: #111827;
  --aics-muted: #64748b;
  --aics-line: #e5e7eb;
  --aics-panel: #ffffff;
  --aics-soft: #f8fafc;
  --aics-ease: cubic-bezier(0.23, 1, 0.32, 1);
  display: grid;
  gap: 16px;
  color: var(--aics-text);
}

.aics-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 16px;
  align-items: stretch;
}

.aics-hero-copy,
.aics-hero-status,
.aics-summary-card,
.aics-v9-card,
.aics-loading,
.aics-unavailable {
  border: 1px solid var(--aics-line);
  border-radius: 8px;
  background: var(--aics-panel);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05), 0 18px 42px rgba(15, 23, 42, 0.06);
}

.aics-hero-copy {
  position: relative;
  overflow: hidden;
  min-height: 238px;
  padding: 28px;
  background:
    linear-gradient(120deg, rgba(255, 255, 255, 0.96), rgba(248, 251, 255, 0.94)),
    radial-gradient(circle at 84% 24%, rgba(37, 99, 235, 0.15), transparent 30%),
    radial-gradient(circle at 72% 90%, rgba(20, 184, 166, 0.13), transparent 24%);
}

.aics-hero-copy::before {
  content: '';
  position: absolute;
  right: 28px;
  bottom: 24px;
  width: 238px;
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

.aics-kicker {
  position: relative;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  height: 28px;
  padding: 0 10px;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  background: #eff6ff;
  color: var(--aics-primary-dark);
  font-size: 11px;
  font-weight: 850;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.aics-hero-copy h1 {
  position: relative;
  z-index: 1;
  margin: 18px 0 10px;
  color: var(--aics-text);
  font-size: 34px;
  line-height: 1.12;
  font-weight: 900;
  letter-spacing: 0;
}

.aics-hero-copy p {
  position: relative;
  z-index: 1;
  max-width: 720px;
  margin: 0;
  color: var(--aics-muted);
  font-size: 14px;
  line-height: 1.8;
}

.aics-hero-actions {
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 22px;
}

.aics-hero-status {
  display: grid;
  align-content: space-between;
  gap: 14px;
  padding: 22px;
  background:
    linear-gradient(180deg, #ffffff 0%, #f8fafc 100%),
    radial-gradient(circle at 100% 0%, rgba(20, 184, 166, 0.14), transparent 30%);
}

.aics-hero-status span,
.aics-card-head span {
  color: var(--aics-muted);
  font-size: 12px;
  font-weight: 850;
}

.aics-hero-status strong {
  color: var(--aics-danger);
  font-size: 30px;
  line-height: 1.15;
  font-weight: 900;
  letter-spacing: 0;
}

.aics-hero-status strong.green {
  color: #0f766e;
}

.aics-hero-status p {
  margin: 0;
  color: var(--aics-muted);
  font-size: 13px;
  line-height: 1.65;
}

.aics-status-meter {
  height: 8px;
  overflow: hidden;
  border-radius: 999px;
  background: #e5e7eb;
}

.aics-status-meter progress {
  display: block;
  width: 100%;
  height: 100%;
  overflow: hidden;
  appearance: none;
  border: 0;
  border-radius: inherit;
  background: transparent;
}

.aics-status-meter progress::-webkit-progress-bar {
  border-radius: inherit;
  background: #e5e7eb;
}

.aics-status-meter progress::-webkit-progress-value {
  border-radius: inherit;
  background: linear-gradient(90deg, var(--aics-primary), var(--aics-accent));
  transition: inline-size 220ms var(--aics-ease);
}

.aics-status-meter progress::-moz-progress-bar {
  border-radius: inherit;
  background: linear-gradient(90deg, var(--aics-primary), var(--aics-accent));
}

.aics-file-input {
  display: none;
}

.aics-loading {
  padding: 44px;
  text-align: center;
  color: var(--aics-muted);
  font-size: 14px;
  font-weight: 800;
}

.aics-unavailable {
  display: grid;
  gap: 10px;
  align-items: start;
  padding: 22px;
  border-color: #fecaca;
  background: #fff7f7;
  color: #991b1b;
}

.aics-unavailable p {
  margin: 0;
  color: #7f1d1d;
  font-size: 13px;
  line-height: 1.7;
}

.aics-summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.aics-summary-card {
  display: grid;
  grid-template-columns: 48px minmax(0, 1fr);
  gap: 12px;
  align-items: start;
  padding: 16px;
  transition:
    transform 180ms var(--aics-ease),
    border-color 180ms ease,
    box-shadow 180ms var(--aics-ease);
}

.aics-summary-icon {
  width: 48px;
  height: 48px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  color: var(--aics-primary);
  background: #eff6ff;
  font-family: 'SF Mono', 'JetBrains Mono', 'Cascadia Code', monospace;
  font-size: 13px;
  font-weight: 900;
}

.aics-summary-icon.green {
  color: #0f766e;
  background: #f0fdfa;
}

.aics-summary-icon.amber {
  color: #b45309;
  background: #fffbeb;
}

.aics-summary-card strong,
.aics-card-head h2,
.aics-row-toggle strong,
.aics-status-row b {
  color: var(--aics-text);
  font-weight: 850;
}

.aics-summary-card p,
.aics-card-head p,
.aics-row-toggle p {
  margin: 6px 0 0;
  color: var(--aics-muted);
  font-size: 12px;
  line-height: 1.7;
}

.aics-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 380px;
  gap: 16px;
  align-items: start;
}

.aics-main,
.aics-side {
  display: grid;
  gap: 16px;
  min-width: 0;
}

.aics-side {
  position: sticky;
  top: 12px;
}

.aics-v9-card {
  padding: 18px;
  transition:
    transform 180ms var(--aics-ease),
    border-color 180ms ease,
    box-shadow 180ms var(--aics-ease);
}

.aics-card-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 16px;
}

.aics-card-head.compact {
  margin-bottom: 12px;
}

.aics-card-head h2 {
  margin: 4px 0 0;
  font-size: 20px;
  line-height: 1.25;
  letter-spacing: 0;
}

.aics-card-head p {
  max-width: 380px;
  margin-top: 0;
}

.aics-form {
  display: grid;
  gap: 16px;
}

.aics-field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.aics-field-grid.compact {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.aics-row {
  display: grid;
  gap: 7px;
  min-width: 0;
}

.aics-row > label,
.aics-label-row label {
  color: #475569;
  font-size: 12px;
  font-weight: 850;
}

.aics-row-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px;
  border: 1px solid var(--aics-line);
  border-radius: 8px;
  background: var(--aics-soft);
}

.aics-row-toggle > div {
  min-width: 0;
}

.aics-input {
  width: 100%;
  height: 40px;
  box-sizing: border-box;
  padding: 0 12px;
  border: 1px solid #dbe3ee;
  border-radius: 8px;
  background: #ffffff;
  color: var(--aics-text);
  font-size: 13px;
  outline: 0;
  transition:
    border-color 160ms ease,
    box-shadow 160ms ease,
    background-color 160ms ease;
}

.aics-input:focus {
  border-color: var(--aics-primary);
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.1);
}

.aics-textarea {
  height: auto;
  min-height: 96px;
  padding: 10px 12px;
  resize: vertical;
  line-height: 1.65;
}

.aics-kb-textarea {
  min-height: 160px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 12px;
}

.aics-time-pair {
  display: flex;
  gap: 8px;
  align-items: center;
}

.aics-time-pair .aics-input {
  flex: 1;
}

.aics-hint,
.aics-upload-hint,
.aics-kb-count,
.aics-entry-meta,
.aics-empty-tip {
  color: #94a3b8;
  font-size: 11px;
  line-height: 1.55;
}

.aics-hint {
  margin: 0;
}

.aics-switch {
  position: relative;
  width: 50px;
  height: 28px;
  flex: 0 0 auto;
  border: 0;
  border-radius: 999px;
  background: #cbd5e1;
  cursor: pointer;
  padding: 0;
  transition:
    background-color 180ms ease,
    transform 140ms var(--aics-ease);
}

.aics-switch.on {
  background: linear-gradient(135deg, var(--aics-primary), var(--aics-accent));
}

.aics-switch:disabled {
  cursor: not-allowed;
  opacity: 0.72;
}

.aics-switch-knob {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #ffffff;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.22);
  transition: left 180ms var(--aics-ease);
}

.aics-switch.on .aics-switch-knob {
  left: 25px;
}

.aics-actions,
.aics-hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.aics-save-btn,
.aics-test-btn,
.aics-upload-btn,
.aics-retry-btn,
.aics-restore-btn,
.aics-entry-remove {
  min-height: 36px;
  padding: 0 14px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
  transition:
    transform 140ms var(--aics-ease),
    border-color 160ms ease,
    box-shadow 160ms var(--aics-ease),
    background-color 160ms ease,
    color 160ms ease;
}

.aics-save-btn {
  border: 1px solid transparent;
  background: linear-gradient(135deg, var(--aics-primary), var(--aics-accent));
  color: #ffffff;
  box-shadow: 0 12px 22px rgba(37, 99, 235, 0.18);
}

.aics-test-btn,
.aics-upload-btn,
.aics-retry-btn,
.aics-restore-btn {
  border: 1px solid #bfdbfe;
  background: #ffffff;
  color: var(--aics-primary-dark);
}

.aics-entry-remove {
  border: 1px solid #fecaca;
  background: #ffffff;
  color: var(--aics-danger);
}

.aics-save-btn:disabled,
.aics-test-btn:disabled,
.aics-upload-btn:disabled,
.aics-retry-btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.aics-preview {
  display: grid;
  gap: 10px;
  padding: 4px 0 12px;
}

.aics-bubble {
  max-width: 92%;
  padding: 10px 13px;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.65;
}

.aics-bubble.them {
  justify-self: start;
  background: #f1f5f9;
  color: #334155;
}

.aics-bubble.me {
  justify-self: end;
  background: linear-gradient(135deg, var(--aics-primary), var(--aics-accent));
  color: #ffffff;
}

.aics-test-form {
  display: grid;
  gap: 8px;
  margin-top: 8px;
}

.aics-status-list {
  display: grid;
  gap: 10px;
}

.aics-status-row {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  padding: 10px 0;
  border-bottom: 1px solid var(--aics-line);
  font-size: 13px;
}

.aics-status-row:last-child {
  border-bottom: 0;
}

.aics-status-row span {
  color: var(--aics-muted);
}

.aics-status-row b {
  text-align: right;
}

.aics-status-row b.green {
  color: #0f766e;
}

.aics-status-row b.red {
  color: var(--aics-danger);
}

.aics-upload-area {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  padding: 12px;
  border: 1px dashed #bfdbfe;
  border-radius: 8px;
  background: #f8fbff;
}

.aics-entry-list {
  display: grid;
  gap: 12px;
  margin-top: 10px;
}

.aics-entry-card {
  display: grid;
  gap: 8px;
  padding: 12px;
  border: 1px solid var(--aics-line);
  border-radius: 8px;
  background: #ffffff;
}

.aics-entry-head {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px;
  align-items: center;
}

.aics-entry-meta,
.aics-label-row {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
}

.aics-empty-tip {
  padding: 10px 0 2px;
}

.aics-error-box,
.aics-warn-box {
  display: grid;
  gap: 8px;
  margin-top: 8px;
  padding: 12px;
  border-radius: 8px;
}

.aics-error-box {
  border: 1px solid #fecaca;
  background: #fef2f2;
}

.aics-warn-box {
  border: 1px solid #fde68a;
  background: #fffbeb;
}

.aics-error,
.aics-warn {
  margin: 0;
  font-size: 12px;
  line-height: 1.65;
}

.aics-error {
  color: var(--aics-danger);
}

.aics-warn {
  color: #b45309;
}

@media (hover: hover) and (pointer: fine) {
  .aics-summary-card:hover,
  .aics-v9-card:hover {
    transform: translateY(-2px);
    border-color: #bfdbfe;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05), 0 24px 54px rgba(37, 99, 235, 0.11);
  }

  .aics-save-btn:hover:not(:disabled),
  .aics-test-btn:hover:not(:disabled),
  .aics-upload-btn:hover:not(:disabled),
  .aics-retry-btn:hover:not(:disabled),
  .aics-restore-btn:hover:not(:disabled),
  .aics-entry-remove:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 12px 24px rgba(37, 99, 235, 0.1);
  }
}

.aics-save-btn:active,
.aics-test-btn:active,
.aics-upload-btn:active,
.aics-retry-btn:active,
.aics-restore-btn:active,
.aics-entry-remove:active,
.aics-switch:active {
  transform: scale(0.98);
}

@media (max-width: 1220px) {
  .aics-hero,
  .aics-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .aics-side {
    position: static;
  }
}

@media (max-width: 900px) {
  .aics-summary-grid,
  .aics-field-grid,
  .aics-field-grid.compact {
    grid-template-columns: minmax(0, 1fr);
  }

  .aics-hero-copy {
    min-height: 0;
    padding: 22px;
  }

  .aics-hero-copy::before {
    display: none;
  }

  .aics-hero-copy h1 {
    font-size: 28px;
  }

  .aics-card-head {
    flex-direction: column;
  }
}

@media (max-width: 620px) {
  .aics-row-toggle,
  .aics-entry-head,
  .aics-status-row {
    grid-template-columns: minmax(0, 1fr);
  }

  .aics-row-toggle {
    flex-direction: column;
    align-items: flex-start;
  }

  .aics-save-btn,
  .aics-test-btn,
  .aics-upload-btn,
  .aics-retry-btn,
  .aics-hero-actions,
  .aics-actions {
    width: 100%;
  }

  .aics-entry-head {
    display: grid;
  }

  .aics-status-row {
    display: grid;
  }

  .aics-status-row b {
    text-align: left;
  }
}
</style>
