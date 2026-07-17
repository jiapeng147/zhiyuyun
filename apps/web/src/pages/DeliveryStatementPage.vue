<template>
  <div class="statement-console-page">
    <section class="statement-command-center">
      <div class="statement-command-main">
        <div class="statement-command-kicker">
          <span>发货声明</span>
          <b>{{ enabled ? '声明已启用' : '声明未启用' }}</b>
        </div>
        <h2>发货声明控制台</h2>
        <p>配置虚拟商品交付前的确认声明、变量内容和生效范围，降低售后争议并保持发货流程可控。</p>
        <div class="statement-command-meta">
          <span>{{ statementLoading ? '配置读取中' : (statementAvailable === true ? '配置可编辑' : '配置不可用') }}</span>
          <span>{{ scope === 'all' ? '全店生效' : '指定商品生效' }}</span>
          <span>{{ previewText ? '预览已生成' : '等待预览' }}</span>
        </div>
      </div>
      <div class="statement-command-panel">
        <div class="statement-command-panel-head">
          <span>运营动作</span>
          <strong>{{ saving ? '保存中' : '可操作' }}</strong>
        </div>
        <div class="statement-command-buttons">
          <AppButton :disabled="statementLoading" @click="load">重新加载</AppButton>
          <AppButton :disabled="!enabled || statementAvailable !== true" @click="refreshPreview">预览声明</AppButton>
          <AppButton type="primary" :loading="saving" :disabled="statementAvailable !== true" @click="save">保存配置</AppButton>
        </div>
      </div>
    </section>

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

          <div class="form-row" style="margin-top:16px">
            <label>生效范围</label>
            <select v-model="scope" class="input" style="width:100%">
              <option value="all">全店所有自动发货商品生效</option>
              <option value="specific">仅对单独启用声明的商品生效</option>
            </select>
          </div>

          <div class="form-row" style="margin-top:16px">
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
            <AppButton type="primary" :loading="saving" @click="save">保存配置</AppButton>
            <AppButton :disabled="saving || !enabled" @click="reset">恢复默认</AppButton>
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
            <div v-if="!enabled" class="subtle" style="text-align:center;padding:20px 0">发货声明已禁用，启用后可预览效果</div>
            <div v-else-if="!previewText" class="subtle" style="text-align:center;padding:20px 0">点击下方按钮预览声明效果</div>
            <pre v-else class="preview-content">{{ previewText }}</pre>
          </div>
          <div style="margin-top:12px">
            <AppButton :disabled="!enabled" @click="refreshPreview">预览声明</AppButton>
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
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import AppButton from '../components/AppButton.vue'
import ToggleSwitch from '../components/ToggleSwitch.vue'
import EmptyState from '../components/EmptyState.vue'
import { getDeliveryStatement, previewDeliveryStatement, saveDeliveryStatement, toggleDeliveryStatement } from '../api/autoDelivery.js'

const error = ref('')
const success = ref('')
const saving = ref(false)
const previewing = ref(false)
const statementLoading = ref(true)
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

.statement-command-center {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(300px, 380px);
  gap: 16px;
  min-width: 0;
  padding: 18px;
  border: 1px solid #dbe4ef;
  border-left: 5px solid #2563eb;
  border-radius: 8px;
  background:
    linear-gradient(135deg, rgba(37, 99, 235, .08), rgba(15, 118, 110, .05) 48%, rgba(255, 255, 255, .96)),
    #fff;
  box-shadow: 0 16px 42px rgba(15, 23, 42, .08);
}

.statement-command-main {
  min-width: 0;
  display: grid;
  align-content: start;
  gap: 10px;
}

.statement-command-kicker {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  color: #2563eb;
  font-size: 12px;
  font-weight: 740;
}

.statement-command-kicker span,
.statement-command-kicker b {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 9px;
  border-radius: 999px;
  background: rgba(37, 99, 235, .1);
}

.statement-command-kicker b {
  color: #0f766e;
  background: rgba(15, 118, 110, .1);
}

.statement-command-main h2 {
  margin: 0;
  color: #0f172a;
  font-size: 26px;
  font-weight: 760;
  line-height: 1.2;
}

.statement-command-main p {
  max-width: 760px;
  margin: 0;
  color: #526079;
  font-size: 13px;
  line-height: 1.7;
}

.statement-command-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 2px;
}

.statement-command-meta span {
  min-height: 28px;
  display: inline-flex;
  align-items: center;
  padding: 0 10px;
  border: 1px solid rgba(148, 163, 184, .28);
  border-radius: 6px;
  background: rgba(255, 255, 255, .82);
  color: #334155;
  font-size: 12px;
  font-weight: 650;
}

.statement-command-panel {
  align-self: stretch;
  min-width: 0;
  display: grid;
  gap: 14px;
  padding: 14px;
  border: 1px solid rgba(148, 163, 184, .25);
  border-radius: 8px;
  background: rgba(255, 255, 255, .92);
}

.statement-command-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  color: #64748b;
  font-size: 12px;
}

.statement-command-panel-head strong {
  color: #2563eb;
  font-size: 13px;
}

.statement-command-buttons {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
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
  transition: border-color .15s, background .15s;
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
  transition: all .15s;
  white-space: nowrap;
}
.var-chip:hover:not(:disabled) {
  background: #eef6ff;
  border-color: #93b4ff;
  transform: translateY(-1px);
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
  gap: 10px;
  flex-wrap: wrap;
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

  .statement-command-center,
  .statement-workspace {
    grid-template-columns: minmax(0, 1fr);
  }

  .statement-command-center,
  .statement-panel {
    padding: 14px;
  }

  .statement-command-main h2 {
    font-size: 22px;
  }

  .statement-command-buttons {
    grid-template-columns: minmax(0, 1fr);
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
