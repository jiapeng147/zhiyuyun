<template>
  <div class="statement-console-page statement-v22-shell">
    <BusinessSection class="statement-command-section" title="发货声明" eyebrow="发货声明">
      <template #extra>
        <n-tag :type="enabled ? 'success' : 'warning'" size="small" :bordered="false">
          {{ enabled ? '声明已启用' : '声明未启用' }}
        </n-tag>
      </template>
      <div class="statement-command-layout">
        <div class="statement-command-copy">
          <p>配置虚拟商品交付前的确认声明、变量内容和生效范围，降低售后争议并保持发货流程可控。</p>
          <n-space class="statement-command-meta" :size="[8, 8]">
            <n-tag size="small" :bordered="false" round>{{ statementLoading ? '配置读取中' : (statementAvailable === true ? '配置可编辑' : '配置不可用') }}</n-tag>
            <n-tag size="small" :bordered="false" round>{{ scope === 'all' ? '全店生效' : '指定商品生效' }}</n-tag>
            <n-tag size="small" :bordered="false" round>{{ previewText ? '预览已生成' : '等待预览' }}</n-tag>
          </n-space>
        </div>
        <div class="statement-command-panel">
          <div class="statement-command-panel-head">
            <span>运营动作</span>
            <strong>{{ saving ? '保存中' : '可操作' }}</strong>
          </div>
          <div class="statement-command-buttons">
            <AppButton :title="statementActionHint" :disabled="statementLoading" @click="load">重新加载</AppButton>
            <AppButton :title="previewActionHint" :loading="previewing" :disabled="previewing || !enabled || statementAvailable !== true" @click="refreshPreview">预览声明</AppButton>
            <AppButton type="primary" :title="saveActionHint" :loading="saving" :disabled="statementAvailable !== true" @click="save">保存配置</AppButton>
          </div>
          <p class="statement-action-hint">{{ statementActionHint }}</p>
        </div>
      </div>
    </BusinessSection>

    <BusinessStatusStrip :items="statementStatusItems" />

    <div v-if="error || success" class="statement-notices">
      <div v-if="error" class="global-notice error">{{ error }}</div>
      <div v-if="success" class="global-notice success">{{ success }}</div>
    </div>

    <EmptyState
      v-if="statementLoading && statementAvailable !== true"
      icon="⏳"
      title="发货声明加载中"
      description="正在读取已保存的声明状态与文案。"
    />
    <EmptyState
      v-else-if="statementAvailable !== true"
      icon="⚠️"
      title="发货声明配置暂不可用"
      description="当前无法确认已保存的声明状态。为避免覆盖未知配置，启停、保存与预览操作均已禁用。"
    >
      <template #actions>
        <AppButton :disabled="statementLoading" @click="load">重新加载</AppButton>
      </template>
    </EmptyState>

    <div v-else class="statement-workspace">
      <div class="statement-main">
        <section class="statement-panel statement-editor-panel">
          <header class="statement-panel-head">
            <div>
              <span>声明策略</span>
              <h3>发货声明配置</h3>
            </div>
            <strong>{{ enabled ? '启用中' : '未启用' }}</strong>
          </header>
          <button
            type="button"
            class="option-line statement-toggle"
            :aria-pressed="enabled"
            :disabled="saving || statementLoading"
            @click="toggleEnabled"
          >
            <span>启用发货声明</span>
            <ToggleSwitch :on="enabled" />
          </button>
          <p class="field-desc">开启后，买家付款后系统先发送声明文案，买家确认后再进入自动发货流程</p>

          <div class="form-row statement-spaced-row">
            <label>生效范围</label>
            <select v-model="scope" class="input statement-full-input">
              <option value="all">全店所有自动发货商品生效</option>
              <option value="specific">仅对单独启用声明的商品生效</option>
            </select>
          </div>

          <div class="form-row statement-spaced-row">
            <label>声明文案</label>
            <textarea
              ref="textareaRef"
              v-model="content"
              placeholder="请输入发货声明内容，支持插入变量..."
              rows="8"
              :disabled="!enabled"
            ></textarea>
          </div>

          <div class="var-buttons">
            <span class="var-label">插入变量：</span>
            <button
              v-for="v in variables"
              :key="v.key"
              class="var-chip"
              :disabled="!enabled"
              @click="insertVariable(v.key)"
            >
              {{ v.key }}
            </button>
          </div>

          <div class="form-actions">
            <AppButton type="primary" :title="saveActionHint" :loading="saving" @click="save">保存配置</AppButton>
            <AppButton :title="statementActionHint" :disabled="saving || !enabled" @click="reset">恢复默认</AppButton>
            <p class="statement-action-hint statement-editor-hint">{{ saveActionHint }}</p>
          </div>
        </section>
      </div>

      <div class="statement-side">
        <section class="statement-panel statement-preview-panel">
          <header class="statement-panel-head">
            <div>
              <span>买家视角</span>
              <h3>声明预览</h3>
            </div>
          </header>
          <div class="preview-box">
            <div v-if="!enabled" class="subtle preview-empty">发货声明已禁用，启用后可预览效果</div>
            <div v-else-if="!previewText" class="subtle preview-empty">点击下方按钮预览声明效果</div>
            <pre v-else class="preview-content">{{ previewText }}</pre>
          </div>
          <div class="preview-actions">
            <AppButton :title="previewActionHint" :loading="previewing" :disabled="previewing || !enabled" @click="refreshPreview">预览声明</AppButton>
            <p class="statement-action-hint">{{ previewActionHint }}</p>
          </div>
        </section>

        <section class="statement-panel statement-variable-panel">
          <header class="statement-panel-head">
            <div>
              <span>变量库</span>
              <h3>变量说明</h3>
            </div>
          </header>
          <div class="var-desc-list">
            <div v-for="v in variables" :key="v.key" class="var-desc-item">
              <code class="var-desc-key">{{ v.key }}</code>
              <span class="var-desc-text">{{ v.desc }}</span>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { NSpace, NTag } from 'naive-ui'
import BusinessSection from '../components/business/BusinessSection.vue'
import BusinessStatusStrip from '../components/business/BusinessStatusStrip.vue'
import AppButton from '../components/AppButton.vue'
import ToggleSwitch from '../components/ToggleSwitch.vue'
import EmptyState from '../components/EmptyState.vue'
import { getDeliveryStatement, previewDeliveryStatement, saveDeliveryStatement, toggleDeliveryStatement } from '../api/autoDelivery.js'

const error = ref('')
const success = ref('')
const saving = ref(false)
const previewing = ref(false)
const statementLoading = ref(true)
const statementStatusItems = computed(() => [
  { key: 'config', label: '配置状态', value: statementLoading.value ? '读取中' : (statementAvailable.value === true ? '可编辑' : '不可用'), tone: statementAvailable.value === false ? 'red' : (statementAvailable.value === true ? 'green' : 'orange') },
  { key: 'scope', label: '生效范围', value: scope.value === 'all' ? '全店' : '指定商品', tone: 'blue' },
  { key: 'preview', label: '预览', value: previewing.value ? '生成中' : (previewText.value ? '已生成' : '等待预览'), tone: previewing.value ? 'orange' : (previewText.value ? 'green' : 'gray') },
  { key: 'save', label: '保存', value: saving.value ? '保存中' : '可保存', tone: saving.value ? 'orange' : 'green' }
])

const statementAvailable = ref(null)
const textareaRef = ref(null)
const previewText = ref('')

const enabled = ref(false)
const content = ref('')
const scope = ref('all')

const variables = [
  { key: '{订单编号}', desc: '订单编号' },
  { key: '{商品标题}', desc: '商品标题' },
  { key: '{买家昵称}', desc: '买家昵称' },
  { key: '{发货确认链接}', desc: '发货确认链接' }
]

const defaultContent = `订单编号：{订单编号}

您好，该订单包含的商品为虚拟商品，发货后不支持退换。如无异议，请点击下方链接确认发货。

{发货确认链接}`

const saveActionHint = computed(() => {
  if (saving.value) return '发货声明配置正在保存，请等待服务端确认。'
  if (statementLoading.value && statementAvailable.value !== true) return '配置正在读取，加载完成后才能保存。'
  if (statementAvailable.value !== true) return '配置状态未知，请先重新加载，避免覆盖未知配置。'
  if (!content.value.trim()) return '先填写声明文案，再保存配置。'
  return enabled.value ? '声明已启用，当前配置可以保存。' : '声明未启用，但文案和范围仍可保存为草稿配置。'
})

const previewActionHint = computed(() => {
  if (previewing.value) return '正在生成买家视角预览，请等待结果返回。'
  if (statementAvailable.value !== true) return '配置状态未知，请先重新加载后再预览。'
  if (!enabled.value) return '发货声明未启用，启用后才能预览买家收到的文案。'
  if (!content.value.trim()) return '先填写声明文案，才能生成预览。'
  return previewText.value ? '预览已生成，修改文案后可重新预览。' : '可以生成买家视角预览，确认变量替换效果。'
})

const statementActionHint = computed(() => {
  if (statementLoading.value && statementAvailable.value !== true) return '正在读取发货声明配置，当前不会保存或切换状态。'
  if (statementAvailable.value !== true) return '发货声明配置不可用，请重新加载成功后再操作。'
  if (saving.value) return '配置保存中，保存完成前避免重复操作。'
  return enabled.value ? '发货声明已启用，自动发货前会先发送声明确认。' : '发货声明当前关闭，可先完善文案和范围再启用。'
})

async function load() {
  statementLoading.value = true
  statementAvailable.value = false
  error.value = ''
  success.value = ''
  previewText.value = ''
  try {
    const res = await getDeliveryStatement()
    const data = res?.data
    if (!data || typeof data !== 'object') throw new Error('发货声明响应无效')
    if (!Object.prototype.hasOwnProperty.call(data, 'enabled')) throw new Error('发货声明缺少启用状态')
    if (typeof data.content !== 'string') throw new Error('发货声明文案无效')
    if (!['all', 'specific'].includes(String(data.scope || ''))) throw new Error('发货声明范围无效')
    enabled.value = data.enabled === true || Number(data.enabled) === 1
    content.value = data.content
    scope.value = data.scope
    statementAvailable.value = true
  } catch (e) {
    enabled.value = false
    content.value = ''
    scope.value = 'all'
    statementAvailable.value = false
    error.value = `${e.message || '声明内容加载失败'}。重新加载成功前不会保存或切换声明状态。`
  } finally {
    statementLoading.value = false
  }
}

async function toggleEnabled() {
  if (saving.value || statementLoading.value) return
  if (statementAvailable.value !== true) {
    error.value = '发货声明配置状态未知，重新加载成功前禁止切换。'
    return
  }
  error.value = ''
  success.value = ''
  const newVal = !enabled.value
  enabled.value = newVal
  previewText.value = ''
  try {
    await toggleDeliveryStatement(newVal)
    success.value = newVal ? '发货声明已启用' : '发货声明已禁用'
  } catch (e) {
    enabled.value = !newVal
    error.value = e.message || '状态切换失败'
  }
}

function insertVariable(key) {
  const textarea = textareaRef.value
  if (!textarea) return
  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const text = content.value
  content.value = text.substring(0, start) + key + text.substring(end)
  nextTick(() => {
    textarea.focus()
    textarea.selectionStart = textarea.selectionEnd = start + key.length
  })
}

async function refreshPreview() {
  if (statementAvailable.value !== true) {
    error.value = '发货声明配置状态未知，重新加载成功前禁止预览。'
    return
  }
  if (!content.value.trim()) {
    error.value = '请先输入声明文案'
    return
  }
  if (previewing.value) return
  error.value = ''
  previewing.value = true
  try {
    const res = await previewDeliveryStatement({ content: content.value, scope: scope.value })
    previewText.value = res?.data?.preview || ''
  } catch (e) {
    error.value = e.message || '预览失败'
  } finally {
    previewing.value = false
  }
}

function reset() {
  if (statementAvailable.value !== true) {
    error.value = '发货声明配置状态未知，重新加载成功前禁止修改。'
    return
  }
  content.value = defaultContent
  scope.value = 'all'
  success.value = ''
  error.value = ''
  previewText.value = ''
}

async function save() {
  if (saving.value) return
  if (statementAvailable.value !== true) {
    error.value = '发货声明配置状态未知，重新加载成功前禁止保存。'
    return
  }
  error.value = ''
  success.value = ''
  if (!content.value.trim()) {
    error.value = '请输入声明文案'
    return
  }
  saving.value = true
  try {
    await saveDeliveryStatement({
      enabled: enabled.value,
      content: content.value,
      scope: scope.value
    })
    success.value = '发货声明配置已保存'
  } catch (e) {
    error.value = e.message || '保存失败'
  } finally {
    saving.value = false
  }
}

function onHeaderAction(event) {
  if (event.detail === 'statement-save') save()
  if (event.detail === 'statement-preview') refreshPreview()
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
.statement-console-page {
  display: grid;
  gap: 18px;
  min-width: 0;
  color: #111827;
}

.statement-console-page * {
  box-sizing: border-box;
}

.statement-command-kicker b {
  color: #0f766e;
  background: rgba(15, 118, 110, .1);
}

.statement-action-hint {
  margin: 0;
  color: #64748b;
  font-size: 12px;
  line-height: 1.55;
}

.statement-command-section :deep(.n-card-header) { padding-bottom: 8px; }
.statement-command-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 280px;
  gap: 18px;
  align-items: start;
}
.statement-command-copy { min-width: 0; }
.statement-command-copy p { margin: 0; max-width: 720px; color: #4b5563; font-size: 14px; line-height: 1.75; }
.statement-command-meta { margin-top: 12px; }
@media (max-width: 1280px) {
  .statement-command-layout { grid-template-columns: minmax(0, 1fr); }
}

.statement-notices {
  display: grid;
  gap: 8px;
}

.statement-workspace {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(360px, .48fr);
  gap: 16px;
  align-items: start;
}

.statement-main,
.statement-side {
  min-width: 0;
}

.statement-side {
  display: grid;
  gap: 16px;
}

.statement-panel {
  min-width: 0;
  padding: 16px;
  border: 1px solid #e4ebf5;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 10px 28px rgba(15, 23, 42, .05);
}

.statement-panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid #eef2f7;
}

.statement-panel-head span {
  color: #2563eb;
  font-size: 12px;
  font-weight: 760;
}

.statement-panel-head h3 {
  margin: 4px 0 0;
  color: #111827;
  font-size: 17px;
  font-weight: 730;
  line-height: 1.35;
}

.statement-panel-head strong {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: #eef2ff;
  color: #2563eb;
  font-size: 12px;
}

.statement-toggle {
  width: 100%;
  border: 1px solid #e4ebf5;
  border-radius: 8px;
  background: #f8fafc;
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
  transition:
    border-color 150ms cubic-bezier(0.23, 1, 0.32, 1),
    background-color 150ms cubic-bezier(0.23, 1, 0.32, 1);
}

.statement-toggle:hover:not(:disabled) {
  border-color: #b8c7dc;
  background: #fff;
}

.statement-toggle:disabled {
  cursor: not-allowed;
  opacity: .65;
}

.preview-box {
  min-height: 132px;
  padding: 14px;
  border: 1px solid #dbe4ef;
  border-radius: 8px;
  background:
    linear-gradient(180deg, rgba(248, 250, 252, .9), rgba(255, 255, 255, .98)),
    #fff;
}

.preview-content {
  white-space: pre-wrap;
  font-family: inherit;
  margin: 0;
  color: #1f2937;
  line-height: 1.7;
  font-size: 14px;
}

.preview-empty {
  padding: 20px 0;
  text-align: center;
}

.preview-actions {
  display: grid;
  gap: 8px;
  margin-top: 12px;
}

.var-buttons {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-top: 12px;
}
.var-label {
  color: #667085;
  font-size: 13px;
  margin-right: 2px;
  white-space: nowrap;
}
.var-chip {
  display: inline-flex;
  align-items: center;
  min-height: 32px;
  padding: 0 11px;
  background: #fff;
  border: 1px solid #cfe0ff;
  border-radius: 7px;
  font-size: 12px;
  color: #2563eb;
  cursor: pointer;
  font-weight: 650;
  transition:
    transform 150ms cubic-bezier(0.23, 1, 0.32, 1),
    border-color 150ms ease,
    background-color 150ms ease,
    color 150ms ease;
  white-space: nowrap;
}
.var-chip:hover:not(:disabled) {
  background: #eef6ff;
  border-color: #93b4ff;
  transform: translateY(-1px);
}
.var-chip:active:not(:disabled) {
  transform: scale(.97);
}
.var-chip:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.var-desc-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.var-desc-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 10px;
  border: 1px solid #e4ebf5;
  border-radius: 8px;
  background: #f8fafc;
}

.var-desc-key {
  background: #e0f2fe;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 12px;
  color: #0369a1;
  white-space: nowrap;
}

.var-desc-text {
  color: #344054;
  font-size: 13px;
}

.field-desc {
  color: #667085;
  font-size: 13px;
  margin: 6px 0 0 0;
  line-height: 1.4;
}
.form-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-row label {
  font-size: 13px;
  font-weight: 700;
  color: #34425d;
}

.form-row textarea {
  width: 100%;
  min-height: 190px;
  padding: 12px;
  border: 1px solid #dbe4ef;
  border-radius: 8px;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.65;
  resize: vertical;
  box-sizing: border-box;
  outline: none;
  background: #fff;
}

.form-row textarea:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, .1);
}

.form-actions {
  margin-top: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.statement-editor-hint {
  flex: 1 1 260px;
}

.statement-spaced-row {
  margin-top: 16px;
}

.statement-full-input {
  width: 100%;
}

.subtle {
  color: #758198;
  font-size: 13px;
}

.success {
  background: #ecfdf3;
  color: #067647;
  border-color: #abefc6;
}

@media (max-width: 1200px) {
  .statement-workspace {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 900px) {
  .statement-console-page {
    gap: 12px;
  }

  .statement-command-layout,
  .statement-workspace {
    grid-template-columns: minmax(0, 1fr);
  }

  .statement-command-layout,
  .statement-panel {
    padding: 14px;
  }

  .statement-panel-head {
    gap: 10px;
    margin-bottom: 12px;
  }

  .statement-side {
    gap: 12px;
  }

  .preview-box {
    padding: 10px;
    min-height: 96px;
  }

  .preview-content {
    font-size: 13px;
    line-height: 1.5;
  }

  .var-buttons {
    gap: 6px;
    margin-top: 10px;
  }
  .var-label {
    font-size: 13px;
  }
  .var-chip {
    min-height: 34px;
    padding: 0 12px;
    font-size: 12px;
  }

  .var-desc-list {
    gap: 8px;
  }
  .var-desc-item {
    flex-wrap: wrap;
    gap: 8px;
    padding: 8px 10px;
  }
  .var-desc-key {
    font-size: 12px;
    padding: 2px 8px;
  }
  .var-desc-text {
    font-size: 13px;
  }

  .field-desc {
    font-size: 13px;
    line-height: 1.5;
  }

  .form-row {
    gap: 6px;
  }
  .form-row label {
    font-size: 13px;
  }
  .form-row textarea {
    min-height: 100px;
    padding: 10px;
  }

  .form-actions {
    margin-top: 14px;
    gap: 8px;
    flex-wrap: wrap;
  }

  .subtle {
    font-size: 13px;
  }
}
</style>
