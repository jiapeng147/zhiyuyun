<template>
  <div class="scheduled-tasks-page">
    <div class="scheduled-tasks-notices">
      <div v-if="error" class="global-notice error">{{ error }}</div>
      <div v-if="success" class="global-notice success">{{ success }}</div>
    </div>

    <section class="scheduled-command-center">
      <div class="scheduled-command-main">
        <div class="scheduled-command-kicker">
          <span>任务调度</span>
          <b>{{ tasksAvailable === true ? `共 ${total} 条` : '任务未确认' }}</b>
        </div>
        <h2>定时任务</h2>
        <p>统一配置商品同步、订单同步和手动触发执行，旧任务类型会被明确标记为不可用。</p>
        <div class="scheduled-command-meta">
          <span>{{ tasksAvailable === null ? '任务读取中' : (tasksAvailable === true ? '任务可管理' : '任务不可用') }}</span>
          <span>{{ runningTaskId ? `任务 #${runningTaskId} 执行中` : '暂无运行任务' }}</span>
          <span>{{ form.id ? `编辑 #${form.id}` : '新建配置' }}</span>
        </div>
      </div>
      <div class="scheduled-command-panel">
        <div class="scheduled-command-panel-head">
          <span>调度动作</span>
          <strong>{{ saving ? '保存中' : '可操作' }}</strong>
        </div>
        <div class="scheduled-command-buttons">
          <n-button :loading="tasksAvailable === null" @click="load">刷新任务</n-button>
          <n-button type="primary" @click="reset">创建任务</n-button>
        </div>
      </div>
    </section>

    <div class="scheduled-service-note" role="status">
      调度服务支持“同步商品”和“同步订单”。旧任务类型不会执行，可在列表中删除后重新创建。
    </div>

    <section class="scheduled-metric-rail">
      <article
        v-for="item in taskStatCards"
        :key="item.key"
        class="scheduled-metric-card"
        :class="item.tone"
      >
        <span class="scheduled-metric-icon">{{ item.symbol }}</span>
        <n-statistic :label="item.title" :value="item.value" />
        <small>{{ item.change }}</small>
      </article>
    </section>

    <div class="scheduled-workspace">
      <section class="scheduled-panel scheduled-table-panel">
        <header class="scheduled-panel-head">
          <div>
            <span>任务队列</span>
            <h3>定时任务</h3>
          </div>
          <b>共 {{ tasksAvailable === true ? total : '—' }} 条</b>
        </header>
        <EmptyState v-if="tasksAvailable === false" icon="⚠️" title="定时任务列表暂不可用" description="当前无法确认是否存在任务，不会把加载失败显示为空列表。">
          <template #actions><AppButton @click="load">重新加载</AppButton></template>
        </EmptyState>
        <BaseTable v-else :columns="columns" :rows="rows">
          <template #taskType="{ row }">
            <div>
              <div class="strong">{{ row.taskTypeLabel }}</div>
              <div class="subtle">{{ row.taskType }}</div>
            </div>
          </template>
          <template #enabled="{ row }">
            <Badge :type="row.enabledBadge">{{ row.enabledText }}</Badge>
          </template>
          <template #lastStatus="{ row }">
            <div>
              <Badge :type="row.lastStatusBadge">{{ row.lastStatusText }}</Badge>
              <div v-if="row.lastResultText" class="subtle result-summary" :title="row.lastResultText">
                {{ row.lastResultText }}
              </div>
            </div>
          </template>
          <template #op="{ row }">
            <div class="inline-actions">
              <button
                class="link"
                type="button"
                :disabled="!row.available || runningTaskId !== null"
                :aria-disabled="!row.available || runningTaskId !== null"
                :title="row.available ? '编辑任务' : '旧任务类型不可编辑'"
                @click.stop="edit(row.raw)"
              >
                编辑
              </button>
              <button
                class="link"
                type="button"
                :disabled="!row.available || runningTaskId !== null"
                :aria-disabled="!row.available || runningTaskId !== null"
                :title="row.available ? '立即同步并等待真实结果' : '该任务类型不可用'"
                @click.stop="run(row.raw.id)"
              >
                {{ runningTaskId === row.raw.id ? '执行中...' : row.available ? '立即执行' : '类型不可用' }}
              </button>
              <button class="link danger-text" @click.stop="remove(row.raw.id)">删除</button>
            </div>
          </template>
        </BaseTable>
        <Pagination v-if="tasksAvailable === true" :total="total" :current="current" :page-size="pageSize" @page-change="goPage" />
      </section>

      <section class="scheduled-panel scheduled-form-panel">
        <header class="scheduled-panel-head">
          <div>
            <span>任务配置</span>
            <h3>{{ form.id ? '编辑任务' : '创建任务' }}</h3>
          </div>
          <b>{{ form.enabled ? '启用' : '禁用' }}</b>
        </header>
        <div class="form-field">
          <label>任务名称</label>
          <n-input ref="taskNameInputRef" v-model:value="form.taskName" />
        </div>
        <div class="form-field">
          <label>账号编号</label>
          <n-input v-model:value="form.accountId" inputmode="numeric" placeholder="必填，例如 8" />
          <span v-if="accountError" class="input-error">{{ accountError }}</span>
        </div>
        <div class="form-field">
          <label>任务类型</label>
          <n-select v-model:value="form.taskType" :options="taskTypeOptions" />
        </div>
        <div class="form-field">
          <label>Cron 表达式</label>
          <n-input v-model:value="form.cronExpression" placeholder="*/30 * * * *" />
          <span v-if="cronError" class="input-error">{{ cronError }}</span>
        </div>
        <div class="form-field">
          <label>配置 JSON</label>
          <n-input v-model:value="form.configJson" type="textarea" :autosize="{ minRows: 8, maxRows: 14 }" />
          <span v-if="jsonError" class="input-error">{{ jsonError }}</span>
        </div>
        <div class="scheduled-switch-row">
          <span>启用自动调度</span>
          <n-switch v-model:value="form.enabled" />
        </div>
        <div class="scheduled-form-actions">
          <n-button type="primary" :loading="saving" @click="save">
            {{ saving ? '保存中...' : '保存任务' }}
          </n-button>
          <n-button @click="reset">重置</n-button>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { NButton, NInput, NSelect, NStatistic, NSwitch } from 'naive-ui'
import BaseTable from '../components/BaseTable.vue'
import Badge from '../components/Badge.vue'
import AppButton from '../components/AppButton.vue'
import Pagination from '../components/Pagination.vue'
import EmptyState from '../components/EmptyState.vue'
import { confirmDelete } from '../utils/confirmAction.js'
import { camelizeKeys, dateTime, recordsOf, totalOf } from '../utils/apiData.js'
import {
  createScheduledTask,
  deleteScheduledTask,
  getScheduledTasks,
  runScheduledTask,
  updateScheduledTask
} from '../api/scheduledTasks.js'
import {
  DEFAULT_SCHEDULED_TASK_TYPES,
  normalizeScheduledTaskPayload,
  normalizeScheduledTaskTypes,
  resolveScheduledTaskHeaderAction,
  taskTypeLabel
} from '../utils/scheduledTaskState.js'

const tasks = ref([])
const total = ref(0)
const current = ref(1)
const pageSize = ref(20)
const saving = ref(false)
const error = ref('')
const success = ref('')
const cronError = ref('')
const jsonError = ref('')
const accountError = ref('')
const runningTaskId = ref(null)
const tasksAvailable = ref(null)
const taskNameInputRef = ref(null)

const form = reactive({
  id: null,
  taskName: '',
  accountId: '',
  taskType: 'sync_goods',
  cronExpression: '*/30 * * * *',
  configJson: '{}',
  enabled: false
})

const taskTypeOptions = normalizeScheduledTaskTypes(DEFAULT_SCHEDULED_TASK_TYPES)

const columns = [
  { key: 'taskName', title: '任务名称' },
  { key: 'accountId', title: '账号编号' },
  { key: 'taskType', title: '任务类型' },
  { key: 'cronExpression', title: 'Cron' },
  { key: 'enabled', title: '启用状态' },
  { key: 'lastStatus', title: '最近结果' },
  { key: 'lastRunTimeText', title: '上次运行' },
  { key: 'nextRunTimeText', title: '下次运行' },
  { key: 'op', title: '操作' }
]

const rows = computed(() => tasks.value.map(task => {
  const available = task.available !== false && DEFAULT_SCHEDULED_TASK_TYPES.includes(task.taskType)
  const enabled = task.enabled === 1 || task.enabled === true
  return {
    ...task,
    accountId: task.accountId ?? '-',
    taskTypeLabel: taskTypeLabel(task.taskType),
    available,
    enabledText: available ? enabled ? '已启用' : '已禁用' : '类型不可用',
    enabledBadge: available ? enabled ? 'green' : 'gray' : 'red',
    lastStatusText: statusText(task.lastStatus),
    lastStatusBadge: statusBadge(task.lastStatus),
    lastResultText: resultText(task.lastResult),
    lastRunTimeText: dateTime(task.lastRunTime),
    nextRunTimeText: available && enabled ? dateTime(task.nextRunTime) : '-',
    raw: task
  }
}))
const taskStatCards = computed(() => {
  const enabledCount = rows.value.filter(row => row.enabledText === '已启用').length
  const runningCount = rows.value.filter(row => row.lastStatusText === '执行中').length
  const failedCount = rows.value.filter(row => ['失败', '超时', '不可用', '类型不可用', '状态保存失败'].includes(row.lastStatusText)).length
  return [
    { key: 'total', title: '任务总数', value: tasksAvailable.value === true ? total.value : '—', change: '当前分页任务总量', symbol: '总', tone: 'tone-blue' },
    { key: 'enabled', title: '已启用', value: enabledCount, change: '当前页启用任务', symbol: '启', tone: 'tone-green' },
    { key: 'running', title: '执行中', value: runningCount, change: runningTaskId.value ? '有任务正在运行' : '暂无运行任务', symbol: '执', tone: 'tone-cyan' },
    { key: 'risk', title: '异常', value: failedCount, change: '当前页失败或不可用', symbol: '异', tone: 'tone-orange' }
  ]
})

function statusText(status) {
  return {
    running: '执行中',
    success: '成功',
    failed: '失败',
    timeout: '超时',
    unavailable: '不可用',
    unsupported: '类型不可用',
    persistence_failed: '状态保存失败'
  }[String(status || '').toLowerCase()] || '尚未执行'
}

function statusBadge(status) {
  const normalized = String(status || '').toLowerCase()
  if (normalized === 'success') return 'green'
  if (normalized === 'running') return 'blue'
  if (['failed', 'timeout', 'unavailable', 'unsupported', 'persistence_failed'].includes(normalized)) return 'red'
  return 'gray'
}

function resultText(lastResult) {
  if (!lastResult) return ''
  const value = typeof lastResult === 'string' ? lastResult : JSON.stringify(lastResult)
  return value.length > 120 ? `${value.slice(0, 120)}…` : value
}

function clearNotice() {
  error.value = ''
  success.value = ''
}

function reset() {
  form.id = null
  form.taskName = ''
  form.accountId = ''
  form.taskType = 'sync_goods'
  form.cronExpression = '*/30 * * * *'
  form.configJson = '{}'
  form.enabled = false
  cronError.value = ''
  jsonError.value = ''
  accountError.value = ''
}

function validateCron(cron) {
  if (!cron) return 'Cron 表达式必填'
  const parts = cron.trim().split(/\s+/)
  if (![5, 6].includes(parts.length)) return 'Cron 应为 5 段，或以秒开头的 6 段格式'
  if (!/^[\d*/,\-?\s]+$/.test(cron)) return 'Cron 包含不支持的字符'
  return ''
}

function validateJson(json) {
  if (!json) return ''
  try {
    const value = JSON.parse(json)
    if (!value || typeof value !== 'object' || Array.isArray(value)) return '配置 JSON 必须是对象'
    return ''
  } catch (jsonValidationError) {
    return `无效 JSON：${jsonValidationError.message}`
  }
}

async function load(preserveNotice = false) {
  if (!preserveNotice) clearNotice()
  try {
    const res = await getScheduledTasks({ current: current.value, size: pageSize.value })
    tasks.value = camelizeKeys(recordsOf(res.data))
    total.value = totalOf(res.data, tasks.value.length)
    tasksAvailable.value = true
  } catch (requestError) {
    tasks.value = []
    total.value = 0
    tasksAvailable.value = false
    error.value = requestError.message || '加载定时任务失败'
  }
}

function edit(task) {
  form.id = task.id
  form.taskName = task.taskName || ''
  form.accountId = task.accountId == null ? '' : String(task.accountId)
  form.taskType = task.taskType || 'sync_goods'
  form.cronExpression = task.cronExpression || '*/30 * * * *'
  form.configJson = typeof task.configJson === 'string' ? task.configJson : JSON.stringify(task.configJson || {}, null, 2)
  form.enabled = task.enabled === 1 || task.enabled === true
  cronError.value = ''
  jsonError.value = ''
  accountError.value = ''
}

async function save() {
  if (saving.value) return
  clearNotice()

  cronError.value = validateCron(form.cronExpression)
  jsonError.value = validateJson(form.configJson)
  const accountId = Number(String(form.accountId || '').trim())
  accountError.value = Number.isSafeInteger(accountId) && accountId > 0 ? '' : '账号编号必须是正整数'
  if (cronError.value || jsonError.value || accountError.value) return

  saving.value = true
  try {
    const payload = normalizeScheduledTaskPayload(form)
    if (form.id) {
      await updateScheduledTask(form.id, payload)
      success.value = payload.enabled ? '任务已更新并进入自动调度' : '任务已更新并保持禁用'
    } else {
      await createScheduledTask(payload)
      success.value = payload.enabled ? '任务已创建并进入自动调度' : '任务已创建并保持禁用'
    }
    reset()
    await load(true)
  } catch (requestError) {
    error.value = requestError.message || '保存定时任务失败'
  } finally {
    saving.value = false
  }
}

async function run(id) {
  if (runningTaskId.value !== null) return
  clearNotice()
  runningTaskId.value = id
  try {
    const response = await runScheduledTask(id)
    const result = response?.data?.result || {}
    const summary = Object.keys(result).length ? `：${resultText(result)}` : ''
    success.value = `任务 #${id} 执行成功${summary}`
    await load(true)
  } catch (requestError) {
    error.value = requestError.message || `任务 #${id} 执行失败`
    await load(true)
  } finally {
    runningTaskId.value = null
  }
}

async function remove(id) {
  const confirmed = await confirmDelete('定时任务')
  if (!confirmed) return

  clearNotice()
  try {
    await deleteScheduledTask(id)
    success.value = `任务 #${id} 已删除`
    await load(true)
  } catch (requestError) {
    error.value = requestError.message || '删除定时任务失败'
  }
}

function goPage(page) {
  current.value = page
  load()
}

function focusTaskName() {
  taskNameInputRef.value?.focus?.()
}

function onHeaderAction(event) {
  const action = resolveScheduledTaskHeaderAction(event.detail, form)
  if (action === 'new') {
    reset()
    focusTaskName()
    return
  }
  if (action === 'focus-name') {
    error.value = '请先填写任务名称，再保存任务'
    focusTaskName()
    return
  }
  if (action === 'save') {
    save()
    return
  }
  if (action === 'run') {
    run(form.id)
    return
  }
  if (action === 'select-task') {
    error.value = '请先从左侧列表选择一个任务后再执行'
  }
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
.scheduled-tasks-page {
  display: grid;
  gap: 18px;
  min-width: 0;
  color: #111827;
}

.scheduled-tasks-page * {
  box-sizing: border-box;
}

.scheduled-tasks-notices {
  display: grid;
  gap: 8px;
}

.scheduled-command-center {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(290px, 360px);
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

.scheduled-command-main {
  min-width: 0;
  display: grid;
  align-content: start;
  gap: 10px;
}

.scheduled-command-kicker {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  color: #2563eb;
  font-size: 12px;
  font-weight: 740;
}

.scheduled-command-kicker span,
.scheduled-command-kicker b {
  min-height: 24px;
  display: inline-flex;
  align-items: center;
  padding: 0 9px;
  border-radius: 999px;
  background: rgba(37, 99, 235, .1);
}

.scheduled-command-kicker b {
  color: #0f766e;
  background: rgba(15, 118, 110, .1);
}

.scheduled-command-main h2 {
  margin: 0;
  color: #0f172a;
  font-size: 26px;
  font-weight: 760;
  line-height: 1.2;
}

.scheduled-command-main p {
  max-width: 760px;
  margin: 0;
  color: #526079;
  font-size: 13px;
  line-height: 1.7;
}

.scheduled-command-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 2px;
}

.scheduled-command-meta span {
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

.scheduled-command-panel {
  align-self: stretch;
  min-width: 0;
  display: grid;
  gap: 14px;
  padding: 14px;
  border: 1px solid rgba(148, 163, 184, .25);
  border-radius: 8px;
  background: rgba(255, 255, 255, .92);
}

.scheduled-command-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  color: #64748b;
  font-size: 12px;
}

.scheduled-command-panel-head strong {
  color: #2563eb;
  font-size: 13px;
}

.scheduled-command-buttons {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.scheduled-service-note {
  padding: 12px 14px;
  border: 1px solid #bcd7ff;
  border-left: 4px solid #2563eb;
  border-radius: 8px;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 13px;
  line-height: 1.65;
}

.scheduled-metric-rail {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.scheduled-metric-card {
  min-width: 0;
  min-height: 132px;
  display: grid;
  grid-template-rows: auto 1fr auto;
  gap: 8px;
  padding: 14px;
  border: 1px solid #e4ebf5;
  border-top: 3px solid #64748b;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 10px 28px rgba(15, 23, 42, .06);
}

.scheduled-metric-icon {
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  color: #fff;
  background: #64748b;
  font-size: 12px;
  font-weight: 750;
}

.scheduled-metric-card.tone-blue { border-top-color: #2563eb; }
.scheduled-metric-card.tone-blue .scheduled-metric-icon { background: #2563eb; }
.scheduled-metric-card.tone-green { border-top-color: #059669; }
.scheduled-metric-card.tone-green .scheduled-metric-icon { background: #059669; }
.scheduled-metric-card.tone-cyan { border-top-color: #0891b2; }
.scheduled-metric-card.tone-cyan .scheduled-metric-icon { background: #0891b2; }
.scheduled-metric-card.tone-orange { border-top-color: #ea580c; }
.scheduled-metric-card.tone-orange .scheduled-metric-icon { background: #ea580c; }

.scheduled-metric-card :deep(.n-statistic .n-statistic-label) {
  color: #64748b;
  font-size: 12px;
}

.scheduled-metric-card :deep(.n-statistic .n-statistic-value) {
  color: #111827;
  font-size: 24px;
  font-weight: 760;
}

.scheduled-metric-card small {
  color: #64748b;
  font-size: 12px;
  line-height: 1.45;
}

.scheduled-workspace {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(380px, .48fr);
  gap: 16px;
  align-items: start;
}

.scheduled-panel {
  min-width: 0;
  padding: 16px;
  border: 1px solid #e4ebf5;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 10px 28px rgba(15, 23, 42, .05);
}

.scheduled-panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid #eef2f7;
}

.scheduled-panel-head span {
  color: #2563eb;
  font-size: 12px;
  font-weight: 760;
}

.scheduled-panel-head h3 {
  margin: 4px 0 0;
  color: #111827;
  font-size: 17px;
  font-weight: 730;
  line-height: 1.35;
}

.scheduled-panel-head b {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: #f1f5f9;
  color: #475569;
  font-size: 12px;
}

.form-field {
  display: grid;
  gap: 6px;
  margin-bottom: 12px;
}

.textarea {
  width: 100%;
  min-height: 160px;
  padding: 10px 12px;
  border: 1px solid #f0e0d9;
  border-radius: 8px;
  resize: vertical;
}

.toggle-row {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
}

.scheduled-switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin: 2px 0 16px;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #f8fafc;
  color: #334155;
  font-size: 13px;
  font-weight: 600;
}

.scheduled-form-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.inline-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.strong {
  font-weight: 600;
}

.success {
  background: #ecfdf3;
  color: #067647;
  border-color: #abefc6;
}

.scheduler-info {
  background: #eff8ff;
  color: #d34f17;
  border-color: #ffc9b2;
}

.result-summary {
  max-width: 220px;
  margin-top: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.inline-actions .link:disabled {
  cursor: not-allowed;
  color: #98a2b3;
  text-decoration: none;
}

@media (max-width: 1080px) {
  .scheduled-workspace {
    grid-template-columns: minmax(0, 1fr);
  }
  .scheduled-workspace > * {
    min-width: 0;
  }
}

@media (max-width: 900px) {
  .scheduled-tasks-page {
    gap: 12px;
  }

  .scheduled-command-center,
  .scheduled-workspace {
    grid-template-columns: minmax(0, 1fr);
  }

  .scheduled-command-center,
  .scheduled-panel {
    padding: 14px;
  }

  .scheduled-command-main h2 {
    font-size: 22px;
  }

  .scheduled-command-buttons {
    grid-template-columns: minmax(0, 1fr);
  }

  .scheduled-metric-rail {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }

  .scheduled-metric-card {
    min-height: 124px;
    padding: 12px;
  }

  .scheduled-panel-head {
    gap: 10px;
    margin-bottom: 12px;
  }

  .form-field {
    gap: 5px;
    margin-bottom: 10px;
  }
  .textarea {
    min-height: 120px;
    padding: 8px 10px;
    border-radius: 8px;
  }
  .toggle-row {
    margin-bottom: 10px;
  }
  .inline-actions {
    gap: 6px;
  }
  .inline-actions :deep(.app-button),
  .inline-actions .link {
    font-size: 13px;
  }

  :deep(.base-table) {
    display: block;
    overflow-x: auto;
    white-space: nowrap;
    -webkit-overflow-scrolling: touch;
  }
  .stat-grid > *,
  .stat-row > *,
  .form-grid > *,
  .two-col > *,
  .three-col > * {
    min-width: 0;
  }
}
</style>
