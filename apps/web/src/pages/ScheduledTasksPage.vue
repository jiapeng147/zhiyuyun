<template>
  <div class="scheduled-v4">
    <div class="scheduled-v4-notices">
      <div v-if="error" class="global-notice error">{{ error }}</div>
      <div v-if="success" class="global-notice success">{{ success }}</div>
    </div>

    <n-card class="scheduled-v4-hero" :bordered="false">
      <div>
        <n-tag size="small" type="success" :bordered="false">Task Scheduler</n-tag>
        <h2>定时任务编排</h2>
        <p>统一配置商品同步、订单同步和手动触发执行，旧任务类型会被明确标记为不可用。</p>
      </div>
      <n-space :size="8" align="center" wrap>
        <n-button size="small" :loading="tasksAvailable === null" @click="load">刷新任务</n-button>
        <n-button size="small" type="primary" @click="reset">创建任务</n-button>
      </n-space>
    </n-card>

    <n-alert class="scheduled-v4-alert" type="info" :bordered="false">
      调度服务支持“同步商品”和“同步订单”。旧任务类型不会执行，可在列表中删除后重新创建。
    </n-alert>

    <section class="scheduled-v4-stats">
      <n-card
        v-for="item in taskStatCards"
        :key="item.key"
        class="scheduled-v4-stat"
        :class="item.tone"
        :bordered="false"
      >
        <span class="scheduled-v4-stat-icon">{{ item.symbol }}</span>
        <n-statistic :label="item.title" :value="item.value" />
        <small>{{ item.change }}</small>
      </n-card>
    </section>

    <div class="layout-grid scheduled-v4-grid">
      <n-card class="scheduled-v4-table-card" :bordered="false">
        <template #header>定时任务</template>
        <template #header-extra>
          <n-tag size="small" :bordered="false">共 {{ tasksAvailable === true ? total : '—' }} 条</n-tag>
        </template>
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
      </n-card>

      <n-card class="scheduled-v4-form-card" :bordered="false">
        <template #header>{{ form.id ? '编辑任务' : '创建任务' }}</template>
        <div class="form-field">
          <label>任务名称</label>
          <n-input ref="taskNameInputRef" v-model:value="form.taskName" />
        </div>
        <div class="form-field">
          <label>账号 ID</label>
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
        <div class="scheduled-v4-switch-row">
          <span>启用自动调度</span>
          <n-switch v-model:value="form.enabled" />
        </div>
        <n-space :size="8" align="center" wrap>
          <n-button type="primary" :loading="saving" @click="save">
            {{ saving ? '保存中...' : '保存任务' }}
          </n-button>
          <n-button @click="reset">重置</n-button>
        </n-space>
      </n-card>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { NAlert, NButton, NCard, NInput, NSelect, NSpace, NStatistic, NSwitch, NTag } from 'naive-ui'
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
  { key: 'accountId', title: '账号 ID' },
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
  accountError.value = Number.isSafeInteger(accountId) && accountId > 0 ? '' : '账号 ID 必须是正整数'
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
.scheduled-v4 {
  display: grid;
  gap: 16px;
  min-width: 0;
}

.scheduled-v4-notices {
  display: grid;
  gap: 8px;
}

.scheduled-v4-hero,
.scheduled-v4-table-card,
.scheduled-v4-form-card,
.scheduled-v4-stat {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, .04);
}

.scheduled-v4-hero :deep(.n-card__content) {
  padding: 18px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.scheduled-v4-hero h2 {
  margin: 12px 0 6px;
  color: #111827;
  font-size: 22px;
  font-weight: 650;
  line-height: 1.25;
}

.scheduled-v4-hero p {
  margin: 0;
  color: #64748b;
  font-size: 13px;
  line-height: 1.65;
}

.scheduled-v4-alert {
  border-radius: 6px;
}

.scheduled-v4-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.scheduled-v4-stat :deep(.n-card__content) {
  padding: 16px;
  display: grid;
  gap: 8px;
}

.scheduled-v4-stat-icon {
  width: 36px;
  height: 36px;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
}

.scheduled-v4-stat.tone-blue .scheduled-v4-stat-icon { background: #eff6ff; color: #2563eb; }
.scheduled-v4-stat.tone-green .scheduled-v4-stat-icon { background: #ecfdf5; color: #059669; }
.scheduled-v4-stat.tone-cyan .scheduled-v4-stat-icon { background: #ecfeff; color: #0891b2; }
.scheduled-v4-stat.tone-orange .scheduled-v4-stat-icon { background: #fff7ed; color: #ea580c; }

.scheduled-v4-stat :deep(.n-statistic .n-statistic-label) {
  color: #64748b;
  font-size: 12px;
}

.scheduled-v4-stat :deep(.n-statistic .n-statistic-value) {
  color: #111827;
  font-size: 24px;
  font-weight: 700;
}

.scheduled-v4-stat small {
  color: #64748b;
  font-size: 12px;
  line-height: 1.4;
}

.scheduled-v4-table-card :deep(.n-card__content),
.scheduled-v4-form-card :deep(.n-card__content) {
  padding: 16px;
}

.scheduled-v4-table-card :deep(.n-card-header),
.scheduled-v4-form-card :deep(.n-card-header) {
  padding: 16px 16px 0;
}

.layout-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 380px;
  gap: 18px;
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
  border-radius: 10px;
  resize: vertical;
}

.toggle-row {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
}

.scheduled-v4-switch-row {
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
  .layout-grid {
    grid-template-columns: minmax(0, 1fr);
  }
  .layout-grid > * {
    min-width: 0;
  }
}

/* === 移动端适配 (max-width: 900px) === */
@media (max-width: 900px) {
  .scheduled-v4 {
    gap: 12px;
  }

  .scheduled-v4-hero :deep(.n-card__content) {
    flex-direction: column;
    padding: 14px;
  }

  .scheduled-v4-stats {
    grid-template-columns: minmax(0, 1fr);
  }

  .scheduled-v4-table-card :deep(.n-card__content),
  .scheduled-v4-form-card :deep(.n-card__content) {
    padding: 12px;
  }

  .layout-grid {
    grid-template-columns: minmax(0, 1fr);
    gap: 12px;
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
  /* 宽表格横向滚动 */
  :deep(.base-table) {
    display: block;
    overflow-x: auto;
    white-space: nowrap;
    -webkit-overflow-scrolling: touch;
  }
  .card-panel,
  .stat-grid > *,
  .stat-row > *,
  .form-grid > *,
  .two-col > *,
  .three-col > * {
    min-width: 0;
  }
}
</style>
