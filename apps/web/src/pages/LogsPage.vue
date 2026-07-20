<template>
  <div class="logs-console">
    <div class="logs-notices">
      <div v-if="error" class="global-notice error">{{ error }}</div>
      <div v-if="success" class="global-notice success">{{ success }}</div>
    </div>

    <BusinessSection class="logs-command-section" title="审计日志工作台" eyebrow="操作记录">
        <template #extra>
          <n-tag :type="dataAvailable === false ? 'error' : (loading ? 'warning' : 'success')" size="small" :bordered="false">
            {{ dataAvailable === false ? '列表不可用' : (loading ? '刷新中' : '可操作') }}
          </n-tag>
        </template>
        <div class="logs-command-layout">
          <div class="logs-command-copy">
            <p>按操作类型、关键词和结果状态追踪关键写操作；结果未知的记录会被标记出来，便于人工核对。</p>
            <n-space class="logs-command-meta" :size="[8, 8]">
              <n-tag size="small" :bordered="false" round>{{ dataAvailable === true ? '记录已同步' : '记录待确认' }}</n-tag>
              <n-tag size="small" :bordered="false" round>{{ loading ? '正在查询' : '查询就绪' }}</n-tag>
              <n-tag size="small" :bordered="false" round>第 {{ current }} 页</n-tag>
              <n-tag size="small" :bordered="false" round>{{ detail ? `已选记录 ${detail.id || '-'}` : '未选择详情' }}</n-tag>
            </n-space>
          </div>
          <div class="logs-command-panel">
            <div class="logs-command-panel-head">
              <span>审计动作</span>
              <strong>{{ exporting ? '导出中' : '可操作' }}</strong>
            </div>
            <div class="logs-command-actions">
              <AppButton :disabled="loading" @click="load">{{ loading ? '刷新中...' : '刷新记录' }}</AppButton>
              <AppButton :loading="exporting" :disabled="loading || exporting || dataAvailable !== true" @click="exportCsv">{{ exporting ? '导出中...' : '导出CSV' }}</AppButton>
            </div>
          </div>
        </div>
      </BusinessSection>

      <BusinessStatusStrip :items="logsStatusItems" />

      <section class="logs-metric-grid">
        <BusinessMetricCard
          v-for="item in logStatCards"
          :key="item.key"
          :label="item.title"
          :value="item.value"
          :hint="item.change"
          :tone="item.tone"
          :icon="item.icon"
        />
      </section>

    <section class="logs-metric-rail">
      <article
        v-for="item in logStatCards"
        :key="item.key"
        class="logs-metric-card"
        :class="item.tone"
      >
        <span class="logs-metric-icon">{{ item.symbol }}</span>
        <div>
          <p>{{ item.title }}</p>
          <strong>{{ item.value }}</strong>
          <small>{{ item.change }}</small>
        </div>
      </article>
    </section>

    <section class="logs-workbench">
      <main class="logs-main">
        <section class="logs-panel logs-table-panel">
          <header class="logs-panel-head">
            <div>
              <span>记录列表</span>
              <h3>操作流水</h3>
            </div>
            <b>{{ dataAvailable === true ? `共 ${total} 条` : '列表不可用' }}</b>
          </header>
          <div class="logs-filter-bar">
            <select v-model="filters.operationType" class="input" @change="search">
              <option value="">全部类型</option>
              <option v-for="t in typeOptions" :key="t.value" :value="t.value">{{ t.label }}</option>
            </select>
            <input v-model="filters.keyword" class="input" placeholder="关键词搜索" @keyup.enter="search">
            <AppButton type="primary" :disabled="loading" @click="search">{{ loading ? '查询中...' : '查询' }}</AppButton>
            <AppButton :loading="exporting" :disabled="loading || exporting || dataAvailable !== true" @click="exportCsv">{{ exporting ? '导出中...' : '导出CSV' }}</AppButton>
          </div>
          <EmptyState v-if="dataAvailable === false" icon="!" title="操作记录暂不可用" description="当前无法确认是否存在操作记录，不会把失败显示为空列表。">
            <template #actions><AppButton @click="load">重新加载</AppButton></template>
          </EmptyState>
          <BaseTable v-else :columns="cols" :rows="rows">
            <template #operationType="{row}"><span :title="row.operationType">{{ operationTypeLabel(row.operationType) }}</span></template>
            <template #status="{row}"><Badge :type="auditStatusType(row)">{{ row.status || '已记录' }}</Badge></template>
            <template #createdTime="{row}">{{ formatDateTime(row.createdTime) }}</template>
            <template #op="{row}"><button class="link" @click="showDetail(row)">查看</button></template>
            <template #empty><EmptyState icon="≡" title="暂无操作记录" description="系统操作记录将在此显示。" /></template>
          </BaseTable>
          <Pagination v-if="dataAvailable === true" :total="total" :current="current" :page-size="size" @page-change="goPage" />
        </section>
      </main>

      <aside class="logs-detail-panel">
        <header class="logs-panel-head detail-head">
          <div>
            <span>记录详情</span>
            <h3>审计明细</h3>
          </div>
          <button v-if="detail" class="modal-close" type="button" @click="detail=null"><Icon name="close" /></button>
        </header>
        <template v-if="detail">
          <section class="logs-detail-identity">
            <span>记录 ID</span>
            <b>{{ detail.id || '-' }}</b>
          </section>
          <div class="logs-detail-metrics">
            <div><span>操作类型</span><b :title="detail.operationType">{{ operationTypeLabel(detail.operationType) }}</b></div>
            <div><span>目标类型</span><b>{{ detail.targetType || '-' }}</b></div>
            <div><span>记录状态</span><Badge :type="auditStatusType(detail)">{{ detail.status || '已记录' }}</Badge></div>
            <div><span>操作人</span><b>{{ detail.operator || '-' }}</b></div>
          </div>
          <div class="logs-info-list">
            <div><span>操作时间</span><b>{{ formatDateTime(detail.createdTime) }}</b></div>
            <div><span>目标ID</span><b>{{ detail.targetId || '-' }}</b></div>
          </div>
          <p v-if="detail.description" class="logs-description">描述：{{ detail.description }}</p>
          <div v-if="detail.requiresReconciliation" class="global-notice warning" role="status">
            该写操作没有可验证的最终结果。请按请求编号核对业务数据与外部平台，确认前不要重复执行。
          </div>
          <div v-if="detail.requestParams" class="json-section">
            <div class="json-section-head">
              <button type="button" class="json-toggle" @click="toggleJsonSection('request')">
                <span class="json-toggle-icon">{{ expandedJson.request ? '▾' : '▸' }}</span>
                请求参数
              </button>
              <button type="button" class="json-copy" :disabled="copiedJson === 'request'" @click="copyJson(detail.requestParams, 'request')">{{ copiedJson === 'request' ? '已复制' : '复制' }}</button>
            </div>
            <pre v-show="expandedJson.request" class="trace-json">{{ formatJson(detail.requestParams) }}</pre>
          </div>
          <div v-if="detail.responseResult" class="json-section">
            <div class="json-section-head">
              <button type="button" class="json-toggle" @click="toggleJsonSection('response')">
                <span class="json-toggle-icon">{{ expandedJson.response ? '▾' : '▸' }}</span>
                响应结果
              </button>
              <button type="button" class="json-copy" :disabled="copiedJson === 'response'" @click="copyJson(detail.responseResult, 'response')">{{ copiedJson === 'response' ? '已复制' : '复制' }}</button>
            </div>
            <pre v-show="expandedJson.response" class="trace-json">{{ formatJson(detail.responseResult) }}</pre>
          </div>
        </template>
        <EmptyState v-else icon="≡" title="选择记录查看详情" description="点击左侧列表中的「查看」按钮，这里会展示记录详情。" />
      </aside>
    </section>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ReceiptOutline, CheckmarkDoneCircleOutline, AlertCircleOutline, HelpCircleOutline } from '@vicons/ionicons5'
import BusinessMetricCard from '../components/business/BusinessMetricCard.vue'
import BusinessSection from '../components/business/BusinessSection.vue'
import BusinessStatusStrip from '../components/business/BusinessStatusStrip.vue'

import BaseTable from '../components/BaseTable.vue'
import Badge from '../components/Badge.vue'
import AppButton from '../components/AppButton.vue'
import EmptyState from '../components/EmptyState.vue'
import Pagination from '../components/Pagination.vue'
import Icon from '../components/Icon.vue'
import { getOperationLogs, exportOperationLogs } from '../api/operationLogs.js'
import { recordsOf, totalOf } from '../utils/apiData.js'

const expandedJson = reactive({ request: true, response: true })
const copiedJson = ref('')
let copyResetTimer = null
function toggleJsonSection(key) { expandedJson[key] = !expandedJson[key] }
async function copyJson(text, key) {
  if (!text) return
  const content = formatJson(text)
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(content)
    } else {
      const ta = document.createElement('textarea')
      ta.value = content
      ta.style.position = 'fixed'
      ta.style.opacity = '0'
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
    }
    copiedJson.value = key
    if (copyResetTimer) clearTimeout(copyResetTimer)
    copyResetTimer = setTimeout(() => { copiedJson.value = '' }, 1500)
  } catch {
    error.value = '复制失败，请手动选择文本复制'
    setTimeout(() => { if (error.value) error.value = '' }, 4000)
  }
}

const loading = ref(false)
const exporting = ref(false)
const error = ref('')
const success = ref('')
const rows = ref([])
const total = ref(0)
const current = ref(1)
const size = ref(20)
const detail = ref(null)
const dataAvailable = ref(null)
const filters = reactive({ operationType: '', keyword: '' })

// 操作类型枚举映射（原始值 -> 中文标签）
const OPERATION_TYPE_MAP = {
  LOGIN: '登录',
  LOGOUT: '退出登录',
  SEND_MESSAGE: '发送消息',
  MESSAGE_SEND_TEXT: '发送消息',
  AUTO_DELIVERY: '自动发货',
  DELIVERY_CARD: '卡密发货',
  AUTO_REPLY: '自动回复',
  CONFIRM_RECEIPT: '确认收货',
  SYNC_PRODUCTS: '同步商品',
  WEBSOCKET_START: '启动连接',
  WEBSOCKET_STOP: '断开连接',
  PUBLISH_PRODUCT: '发布商品',
  DELETE_LOCAL: '删除系统记录',
  OFF_SHELF: '下架商品',
  CARD_IMPORT: '卡密导入',
  CARD_DELETE: '卡密删除',
  RULE_SAVE: '保存规则',
  RULE_DELETE: '删除规则',
  AUDIT_RETENTION: '记录留存清理',
  HTTP_MUTATION_STARTED: '写操作（待核对）',
  HTTP_MUTATION_COMPLETED: '写请求（已结束）',
  HTTP_MUTATION_REJECTED: '写请求（已拒绝）',
  HTTP_MUTATION_RESULT_UNKNOWN: '写操作（结果未知）',
  OTHER: '其他'
}

const typeOptions = [
  { value: 'LOGIN', label: '登录' },
  { value: 'SEND_MESSAGE', label: '发送消息' },
  { value: 'AUTO_DELIVERY', label: '自动发货' },
  { value: 'AUTO_REPLY', label: '自动回复' },
  { value: 'CONFIRM_RECEIPT', label: '确认收货' },
  { value: 'SYNC_PRODUCTS', label: '同步商品' },
  { value: 'WEBSOCKET_START', label: '启动连接' },
  { value: 'WEBSOCKET_STOP', label: '断开连接' },
  { value: 'PUBLISH_PRODUCT', label: '发布商品' },
  { value: 'CARD_IMPORT', label: '卡密导入' },
  { value: 'AUDIT_RETENTION', label: '记录留存清理' },
  { value: 'HTTP_MUTATION_STARTED', label: '写操作（待核对）' },
  { value: 'HTTP_MUTATION_RESULT_UNKNOWN', label: '写操作（结果未知）' },
  { value: 'HTTP_MUTATION_REJECTED', label: '写请求（已拒绝）' },
  { value: 'HTTP_MUTATION_COMPLETED', label: '写请求（已结束）' }
]

function operationTypeLabel(code) {
  if (!code) return '-'
  // 1. 精确匹配
  if (OPERATION_TYPE_MAP[code]) return OPERATION_TYPE_MAP[code]
  // 2. 大写下划线格式直接匹配
  const upper = String(code).toUpperCase()
  if (OPERATION_TYPE_MAP[upper]) return OPERATION_TYPE_MAP[upper]
  // 3. 包含匹配（如 MESSAGE_SEND_TEXT 含 MESSAGE_SEND）
  for (const key of Object.keys(OPERATION_TYPE_MAP)) {
    if (upper.includes(key)) return OPERATION_TYPE_MAP[key]
  }
  // 4. 兜底：已经是中文则原样返回，否则截断
  if (/[\u4e00-\u9fa5]/.test(code)) return code
  return code
}

function formatDateTime(value) {
  if (!value) return '-'
  const s = String(value)
  // 兼容 ISO "2026-06-29T10:03:01" 和 "2026-06-29 10:03:01"
  return s.replace('T', ' ').replace(/\.\d+$/, '').slice(0, 19)
}

const cols = [
  { key: 'id', title: '记录ID' },
  { key: 'operationType', title: '操作类型' },
  { key: 'targetType', title: '目标类型' },
  { key: 'description', title: '描述' },
  { key: 'status', title: '状态' },
  { key: 'operator', title: '操作人' },
  { key: 'createdTime', title: '操作时间' },
  { key: 'op', title: '操作' }
]

const logStatCards = computed(() => [
  { key: 'total', title: '操作记录总数', value: dataAvailable.value === true ? total.value : '—', change: '当前分页记录', icon: ReceiptOutline, tone: 'blue' },
  { key: 'success', title: '成功记录', value: successCount.value, change: '当前页成功/已确认', icon: CheckmarkDoneCircleOutline, tone: 'green' },
  { key: 'fail', title: '失败记录', value: failedCount.value, change: '当前页失败/异常', icon: AlertCircleOutline, tone: 'red' },
  { key: 'unknown', title: '结果未知', value: unknownCount.value, change: '需人工核对', icon: HelpCircleOutline, tone: 'orange' }
])
const successCount = computed(() => rows.value.filter(row => String(row.status || '').includes('成功') || row.status === 'OK').length)
const failedCount = computed(() => rows.value.filter(row => String(row.status || '').includes('失败')).length)
const unknownCount = computed(() => rows.value.filter(row => row.requiresReconciliation || !row.status).length)

const logsStatusItems = computed(() => [
  { key: 'data', label: '审计数据', value: dataAvailable.value === true ? '已加载' : (dataAvailable.value === false ? '加载失败' : '加载中'), tone: dataAvailable.value === true ? 'green' : (dataAvailable.value === false ? 'red' : 'orange') },
  { key: 'export', label: '导出', value: exporting.value ? '导出中' : (dataAvailable.value === true ? '可导出' : '不可导出'), tone: exporting.value ? 'orange' : (dataAvailable.value === true ? 'green' : 'gray') },
  { key: 'success', label: '成功/已确认', value: `${successCount.value} 条`, tone: successCount.value ? 'green' : 'gray' },
  { key: 'risk', label: '失败/异常', value: `${failedCount.value} 条`, tone: failedCount.value ? 'red' : 'green' }
])

function auditStatusType(row) {
  if (row?.requiresReconciliation) return 'orange'
  if (String(row?.operationType || '').toUpperCase() === 'HTTP_MUTATION_REJECTED') return 'red'
  return 'gray'
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const res = await getOperationLogs({
      current: current.value,
      size: size.value,
      operationType: filters.operationType,
      keyword: filters.keyword
    })
    rows.value = recordsOf(res.data)
    total.value = totalOf(res.data, rows.value.length)
    dataAvailable.value = true
  } catch (e) {
    error.value = e.message || '记录加载失败'
    rows.value = []
    total.value = 0
    detail.value = null
    dataAvailable.value = false
  } finally {
    loading.value = false
  }
}

function goPage(p) {
  current.value = p
  load()
}

function search() {
  current.value = 1
  load()
}

function showDetail(row) { detail.value = row }

function formatJson(str) {
  if (!str) return ''
  try { return JSON.stringify(JSON.parse(str), null, 2) } catch { return str }
}

async function exportCsv() {
  exporting.value = true
  error.value = ''
  try {
    const blob = await exportOperationLogs({ operationType: filters.operationType, keyword: filters.keyword })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `operation-logs-${Date.now()}.csv`
    a.click()
    URL.revokeObjectURL(url)
    success.value = '记录导出成功'
    setTimeout(() => { success.value = '' }, 3000)
  } catch (e) {
    error.value = e.message || '导出失败，请稍后重试'
  } finally {
    exporting.value = false
  }
}

function onHeaderAction(event) {
  if (event.detail === 'logs-export') exportCsv()
  if (event.detail === 'logs-refresh') load()
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
.logs-console {
  display: grid;
  gap: 18px;
  min-width: 0;
}

.logs-notices {
  display: grid;
  gap: 10px;
}

.logs-command-center {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 18px;
  padding: 22px;
  border: 1px solid #dbe3ef;
  border-radius: 8px;
  background:
    linear-gradient(135deg, rgba(71, 85, 105, .08), rgba(37, 99, 235, .06) 45%, rgba(245, 158, 11, .08)),
    #ffffff;
  box-shadow: 0 16px 38px rgba(15, 23, 42, .07);
}

.logs-command-main {
  min-width: 0;
}

.logs-command-kicker,
.logs-command-meta,
.logs-command-panel-head,
.logs-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.logs-command-kicker {
  justify-content: flex-start;
}

.logs-command-kicker span,
.logs-command-panel-head span,
.logs-panel-head span {
  color: #475569;
  font-size: 12px;
  font-weight: 750;
}

.logs-command-kicker b,
.logs-command-panel-head strong,
.logs-panel-head b {
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
}

.logs-command-main h2 {
  margin: 12px 0 8px;
  color: #0f172a;
  font-size: 26px;
  font-weight: 780;
  line-height: 1.2;
}

.logs-command-main p {
  max-width: 760px;
  margin: 0;
  color: #475569;
  font-size: 14px;
  line-height: 1.8;
}

.logs-command-meta {
  justify-content: flex-start;
  flex-wrap: wrap;
  margin-top: 18px;
}

.logs-command-meta span,
.logs-command-panel {
  border: 1px solid rgba(148, 163, 184, .32);
  border-radius: 8px;
  background: rgba(255, 255, 255, .78);
}

.logs-command-meta span {
  padding: 7px 10px;
  color: #334155;
  font-size: 12px;
}

.logs-command-panel {
  display: grid;
  align-content: start;
  gap: 12px;
  padding: 16px;
}

.logs-command-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.logs-metric-rail {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
}

.logs-metric-card {
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr);
  gap: 12px;
  min-width: 0;
  padding: 15px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 10px 24px rgba(15, 23, 42, .05);
}

.logs-metric-icon {
  width: 38px;
  height: 38px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 800;
}

.logs-metric-card p {
  margin: 0;
  color: #64748b;
  font-size: 12px;
}

.logs-metric-card strong {
  display: block;
  margin-top: 3px;
  color: #0f172a;
  font-size: 24px;
  font-weight: 800;
  line-height: 1.2;
}

.logs-metric-card small {
  display: block;
  margin-top: 6px;
  color: #64748b;
  font-size: 12px;
  line-height: 1.4;
}

.logs-metric-card.tone-blue .logs-metric-icon { background: #dbeafe; color: #1d4ed8; }
.logs-metric-card.tone-green .logs-metric-icon { background: #dcfce7; color: #15803d; }
.logs-metric-card.tone-cyan .logs-metric-icon { background: #ccfbf1; color: #0f766e; }
.logs-metric-card.tone-purple .logs-metric-icon { background: #ede9fe; color: #6d28d9; }
.logs-metric-card.tone-orange .logs-metric-icon { background: #ffedd5; color: #c2410c; }

.logs-workbench {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 420px;
  align-items: start;
  gap: 16px;
}

.logs-main {
  min-width: 0;
}

.logs-panel,
.logs-detail-panel {
  min-width: 0;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 10px 26px rgba(15, 23, 42, .05);
}

.logs-panel {
  padding: 16px;
}

.logs-table-panel {
  overflow: hidden;
}

.logs-panel-head {
  align-items: flex-start;
  margin-bottom: 14px;
}

.logs-panel-head h3 {
  margin: 4px 0 0;
  color: #0f172a;
  font-size: 17px;
  font-weight: 760;
  line-height: 1.25;
}

.logs-filter-bar {
  display: grid;
  grid-template-columns: 190px minmax(220px, 1fr) auto auto;
  gap: 10px;
  align-items: center;
  margin-bottom: 14px;
}

.logs-filter-bar .input {
  min-width: 0;
}

.logs-table-panel :deep(.base-table-wrap) {
  border-radius: 8px;
}

.logs-detail-panel {
  position: sticky;
  top: 16px;
  display: grid;
  gap: 14px;
  padding: 16px;
}

.detail-head {
  margin-bottom: 0;
}

.logs-detail-identity {
  display: grid;
  gap: 6px;
  padding: 14px;
  border: 1px solid #dbeafe;
  border-radius: 8px;
  background: #f8fafc;
}

.logs-detail-identity span,
.logs-detail-metrics span,
.logs-info-list span {
  color: #64748b;
  font-size: 12px;
}

.logs-detail-identity b {
  color: #0f172a;
  font-size: 18px;
  font-weight: 800;
}

.logs-detail-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.logs-detail-metrics div,
.logs-info-list div {
  display: grid;
  gap: 6px;
  padding: 11px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f8fafc;
}

.logs-detail-metrics b,
.logs-info-list b {
  color: #0f172a;
  font-size: 12px;
  word-break: break-word;
}

.logs-info-list {
  display: grid;
  gap: 9px;
}

.logs-description {
  margin: 0;
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #ffffff;
  color: #475569;
  font-size: 13px;
  line-height: 1.65;
}

.json-section {
  display: grid;
  gap: 8px;
}

.json-section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.json-toggle,
.json-copy {
  border: 1px solid #dbe3ef;
  border-radius: 8px;
  background: #ffffff;
  color: #334155;
  font-size: 12px;
  cursor: pointer;
}

.json-toggle {
  min-height: 32px;
  padding: 0 10px;
  font-weight: 750;
}

.json-copy {
  min-height: 30px;
  padding: 0 10px;
}

.json-copy:disabled {
  cursor: default;
  opacity: .65;
}

.trace-json {
  max-height: 320px;
  margin: 0;
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #0f172a;
  color: #e2e8f0;
  font-size: 12px;
  line-height: 1.55;
  overflow: auto;
}

@media (max-width: 900px) {
  .logs-console {
    gap: 12px;
  }

  .logs-command-center,
  .logs-metric-rail,
  .logs-workbench,
  .logs-filter-bar,
  .logs-command-actions,
  .logs-detail-metrics {
    grid-template-columns: minmax(0, 1fr);
  }

  .logs-command-center {
    padding: 16px;
  }

  .logs-detail-panel {
    position: static;
  }

  .trace-json {
    font-size: 11px;
    padding: 8px;
  }

  .json-section-head {
    flex-wrap: wrap;
    gap: 6px;
  }

  .logs-table-panel :deep(.base-table) {
    display: block;
    overflow-x: auto;
    white-space: nowrap;
    -webkit-overflow-scrolling: touch;
  }
}
</style>
