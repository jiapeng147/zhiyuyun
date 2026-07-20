<template>
  <div class="delivery-records-page">
    <div class="delivery-records-notices">
      <div v-if="error" class="global-notice error">{{ error }}</div>
      <div v-if="warning" class="global-notice warning" role="status">{{ warning }}</div>
      <div v-if="success" class="global-notice success">{{ success }}</div>
    </div>

    <section class="delivery-records-command-center">
      <div class="delivery-records-command-main">
        <div class="delivery-records-command-kicker">
          <span>发货审计</span>
          <b>{{ recordsAvailable === true ? `共 ${total} 条` : '记录未确认' }}</b>
        </div>
        <h2>发货记录</h2>
        <p>集中查看真实发货执行结果、失败原因、卡密/文本方式和订单闭环状态。</p>
        <div class="delivery-records-command-meta">
          <span>{{ recordsLoading ? '记录刷新中' : '记录已就绪' }}</span>
          <span>当前页 {{ rows.length }} 条</span>
          <span>{{ detailView ? '详情已展开' : '未选择详情' }}</span>
        </div>
      </div>
      <div class="delivery-records-command-panel">
        <div class="delivery-records-command-panel-head">
          <span>审计动作</span>
          <strong>{{ exportLoading ? '导出中' : '可操作' }}</strong>
        </div>
        <div class="delivery-records-command-buttons">
          <n-button :loading="recordsLoading" @click="load">刷新记录</n-button>
          <n-button type="primary" :disabled="recordsAvailable !== true || exportLoading" @click="exportCsv">
            {{ exportLoading ? '导出中...' : '导出 CSV' }}
          </n-button>
        </div>
      </div>
    </section>

    <div class="delivery-records-safety-note" role="status">
      为确保交易安全，发货记录暂不提供一键自动重试。请先在闲鱼 App 核对买家消息与平台发货状态；确需再次操作时，请前往“订单管理”使用手动发货闭环。
    </div>

    <section class="delivery-records-metric-rail">
      <article
        v-for="item in recordStatCards"
        :key="item.key"
        class="delivery-records-metric-card"
        :class="item.tone"
      >
        <span class="delivery-records-metric-icon">{{ item.symbol }}</span>
        <n-statistic :label="item.title" :value="item.value" />
        <small>{{ item.change }}</small>
      </article>
    </section>

    <section class="delivery-records-panel delivery-records-filter-panel">
      <header class="delivery-records-panel-head">
        <div>
          <span>筛选条件</span>
          <h3>记录检索</h3>
        </div>
        <b>第 {{ query.current }} 页</b>
      </header>
      <div class="delivery-records-filter-grid">
        <n-select v-model:value="query.status" class="delivery-records-select" :options="statusOptions" />
        <n-select v-model:value="query.timing" class="delivery-records-select" :options="timingOptions" />
        <n-select v-model:value="query.deliveryMode" class="delivery-records-select" :options="modeOptions" />
        <n-input v-model:value="query.goodsKeyword" clearable placeholder="商品关键词" />
        <n-input v-model:value="query.buyerKeyword" clearable placeholder="买家关键词" />
        <n-input v-model:value="query.orderKeyword" clearable placeholder="订单号 / 外部订单号" @keyup.enter="search" />
        <div class="delivery-records-filter-actions">
          <n-button type="primary" :loading="recordsLoading" @click="search">搜索</n-button>
          <n-button :disabled="recordsLoading" @click="resetFilters">重置</n-button>
        </div>
      </div>
    </section>

    <section class="delivery-records-panel delivery-records-table-panel">
      <header class="delivery-records-panel-head">
        <div>
          <span>执行流水</span>
          <h3>发货记录</h3>
        </div>
        <b>共 {{ recordsAvailable === true ? total : '—' }} 条</b>
      </header>
      <div v-if="recordsRefreshing" class="refresh-status" role="status" aria-live="polite">
        正在刷新发货记录，现有数据仍可查看。
      </div>
      <EmptyState
        v-if="recordsLoading && recordsAvailable !== true"
        icon="⏳"
        title="正在加载发货记录"
        description="正在读取实际发货执行结果，请稍候。"
      />
      <EmptyState
        v-else-if="recordsAvailable === false"
        icon="⚠️"
        title="发货记录暂不可用"
        description="当前无法确认发货记录与执行结果；请求失败不会显示为空记录。"
      >
        <template #actions><AppButton @click="load">重新加载</AppButton></template>
      </EmptyState>
      <BaseTable
        v-else-if="recordsAvailable === true"
        :columns="columns"
        :rows="rows"
        :row-key="row => row.id"
        @row-click="showDetail"
      >
        <template #status="{ row }">
          <Badge :type="row.deliveryBadge">{{ row.deliveryStatusText }}</Badge>
        </template>
        <template #timing="{ row }">{{ row.timingText }}</template>
        <template #mode="{ row }">{{ row.deliveryModeText }}</template>
        <template #progress="{ row }">{{ row.deliveryProgressText }}</template>
        <template #errorMessage="{ row }">
          <span class="cell-ellipsis" :title="row.errorMessage || ''">{{ row.errorMessage || '-' }}</span>
        </template>
        <template #op="{ row }">
          <div class="inline-actions">
            <button class="link" @click.stop="showDetail(row)">详情</button>
          </div>
        </template>
      </BaseTable>
      <Pagination v-if="recordsAvailable === true" :total="total" :current="query.current" :page-size="query.size" @page-change="goPage" />
    </section>

    <section v-if="detailView" class="delivery-records-panel delivery-records-detail-panel">
      <header class="delivery-records-panel-head">
        <div>
          <span>单据详情</span>
          <h3>发货记录详情</h3>
        </div>
        <b>{{ detailView.deliveryStatusText }}</b>
      </header>
      <div class="detail-grid">
        <div><b>记录 ID：</b> {{ detailView.id || '-' }}</div>
        <div><b>订单号：</b> {{ detailView.orderId || '-' }}</div>
        <div><b>商品：</b> {{ detailView.goodsTitleText }}</div>
        <div><b>买家：</b> {{ detailView.buyerNameText }}</div>
        <div><b>状态：</b> {{ detailView.deliveryStatusText }}</div>
        <div><b>进度：</b> {{ detailView.deliveryProgressText }}</div>
        <div><b>时机：</b> {{ detailView.timingText }}</div>
        <div><b>方式：</b> {{ detailView.deliveryModeText }}</div>
        <div><b>创建时间：</b> {{ detailView.createdTimeText }}</div>
        <div><b>完成时间：</b> {{ detailView.completedTimeText }}</div>
        <div><b>平台同步：</b> {{ detailView.platformSyncTimeText }}</div>
        <div><b>结果：</b> {{ detailView.resultText }}</div>
      </div>

      <div class="panel-block">
        <div class="section-title">发货内容</div>
        <div class="content-box">{{ detailView.deliveryContentText }}</div>
      </div>

      <div class="panel-block">
        <div class="section-title">错误信息</div>
        <div class="content-box">{{ detailView.errorMessageText }}</div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { NButton, NInput, NSelect, NStatistic } from 'naive-ui'
import BaseTable from '../components/BaseTable.vue'
import Badge from '../components/Badge.vue'
import AppButton from '../components/AppButton.vue'
import Pagination from '../components/Pagination.vue'
import EmptyState from '../components/EmptyState.vue'
import { getDeliveryRecordDetail, getDeliveryRecords } from '../api/autoDelivery.js'
import { camelizeKeys, recordsOf, totalOf } from '../utils/apiData.js'
import { createLatestRequestGuard, listRefreshRequestConfig } from '../utils/latestRequest.js'
import {
  buildDeliveryRecordDetailViewModel,
  buildDeliveryRecordRowViewModel
} from '../utils/deliveryRecordsPageState.js'

const records = ref([])
const total = ref(0)
const detail = ref(null)
const error = ref('')
const warning = ref('')
const success = ref('')
const recordsAvailable = ref(null)
const recordsLoading = ref(true)
const exportLoading = ref(false)
const recordsRequestGuard = createLatestRequestGuard()

const query = reactive({
  status: '',
  timing: '',
  deliveryMode: '',
  goodsKeyword: '',
  buyerKeyword: '',
  orderKeyword: '',
  current: 1,
  size: 20
})

const columns = [
  { key: 'id', title: 'ID' },
  { key: 'orderId', title: '订单号' },
  { key: 'goodsTitleText', title: '商品' },
  { key: 'buyerNameText', title: '买家' },
  { key: 'timing', title: '时机' },
  { key: 'mode', title: '方式' },
  { key: 'status', title: '状态' },
  { key: 'progress', title: '进度' },
  { key: 'errorMessage', title: '错误' },
  { key: 'createdTimeText', title: '创建时间' },
  { key: 'op', title: '操作' }
]

const rows = computed(() => records.value.map(buildDeliveryRecordRowViewModel))
const recordsRefreshing = computed(() => recordsLoading.value && recordsAvailable.value === true)
const detailView = computed(() => (detail.value ? buildDeliveryRecordDetailViewModel(detail.value) : null))
const statusOptions = [
  { label: '全部状态', value: '' },
  { label: '待处理', value: '0' },
  { label: '进行中', value: '1' },
  { label: '成功', value: '2' },
  { label: '失败', value: '3' },
  { label: '缺货', value: '6' },
  { label: '配置错误', value: '7' }
]
const timingOptions = [
  { label: '全部时机', value: '' },
  { label: '付款后', value: 'after_payment' },
  { label: '收货后', value: 'after_receipt' },
  { label: '评价后', value: 'after_review' }
]
const modeOptions = [
  { label: '全部方式', value: '' },
  { label: '文本', value: 'text' },
  { label: '卡密', value: 'card' }
]
const recordStatCards = computed(() => {
  const successCount = rows.value.filter(row => row.deliveryStatusText === '成功' || row.deliveryStatusText === '已完成').length
  const failedCount = rows.value.filter(row => ['失败', '缺货', '配置错误'].includes(row.deliveryStatusText)).length
  const cardCount = rows.value.filter(row => row.deliveryModeText === '卡密').length
  return [
    { key: 'total', title: '记录总数', value: recordsAvailable.value === true ? total.value : '—', change: '当前筛选分页总数', symbol: '总', tone: 'tone-blue' },
    { key: 'page', title: '当前页', value: rows.value.length, change: `每页 ${query.size} 条`, symbol: '页', tone: 'tone-green' },
    { key: 'success', title: '成功记录', value: successCount, change: '当前页成功/已完成', symbol: '成', tone: 'tone-cyan' },
    { key: 'risk', title: '异常记录', value: failedCount, change: `当前页卡密 ${cardCount} 条`, symbol: '异', tone: 'tone-orange' }
  ]
})

function clearNotice() {
  error.value = ''
  warning.value = ''
  success.value = ''
}

function buildQuery() {
  return {
    status: query.status === '' ? undefined : Number(query.status),
    timing: query.timing || undefined,
    deliveryMode: query.deliveryMode || undefined,
    goodsKeyword: query.goodsKeyword || undefined,
    buyerKeyword: query.buyerKeyword || undefined,
    orderKeyword: query.orderKeyword || undefined,
    current: query.current,
    size: query.size
  }
}

async function load() {
  const request = recordsRequestGuard.begin()
  const hadSnapshot = recordsAvailable.value === true
  clearNotice()
  recordsLoading.value = true
  try {
    const res = await getDeliveryRecords(buildQuery(), listRefreshRequestConfig(hadSnapshot))
    if (!request.isCurrent()) return
    records.value = camelizeKeys(recordsOf(res.data))
    total.value = totalOf(res.data, records.value.length)
    recordsAvailable.value = true
  } catch (requestError) {
    if (!request.isCurrent()) return
    if (hadSnapshot) {
      warning.value = `发货记录刷新失败，继续显示上次成功加载的发货记录。${requestError.message ? ` ${requestError.message}` : ''}`
    } else {
      records.value = []
      total.value = 0
      detail.value = null
      recordsAvailable.value = false
      error.value = requestError.message || '加载发货记录失败'
    }
  } finally {
    if (request.isCurrent()) recordsLoading.value = false
  }
}

async function showDetail(row) {
  clearNotice()
  detail.value = null
  try {
    const res = await getDeliveryRecordDetail(row.id)
    if (!res.data) throw new Error('发货记录详情响应为空')
    detail.value = camelizeKeys(res.data)
  } catch (requestError) {
    detail.value = null
    error.value = requestError.message || '加载发货记录详情失败'
  }
}


function search() {
  query.current = 1
  load()
}

function resetFilters() {
  query.status = ''
  query.timing = ''
  query.deliveryMode = ''
  query.goodsKeyword = ''
  query.buyerKeyword = ''
  query.orderKeyword = ''
  query.current = 1
  load()
}

function goPage(page) {
  query.current = page
  load()
}

function escapeCsv(value) {
  return `"${String(value ?? '').replaceAll('"', '""')}"`
}

async function exportCsv() {
  if (recordsAvailable.value !== true || exportLoading.value) {
    error.value = '发货记录尚不可用，请重新加载成功后再导出。'
    return
  }
  clearNotice()
  exportLoading.value = true
  const EXPORT_MAX_LIMIT = 2000   // 单次导出最大条数，防止浏览器内存压力
  const EXPORT_PAGE_SIZE = 100    // 分页拉取每页大小（PageUtils 限制 max=100）
  const totalCount = total.value || 0
  if (totalCount > EXPORT_MAX_LIMIT) {
    error.value = `当前共 ${totalCount} 条记录，超过单次导出上限 ${EXPORT_MAX_LIMIT} 条，请添加筛选条件缩小范围后再导出`
    exportLoading.value = false
    return
  }
  try {
    success.value = '正在准备导出数据...'
    const exportRows = []
    // 总数为 0 时也尝试拉取一页（可能 total 尚未加载）
    const targetCount = Math.max(totalCount, query.size)
    const totalPages = Math.max(1, Math.ceil(targetCount / EXPORT_PAGE_SIZE))
    for (let page = 1; page <= totalPages; page++) {
      const res = await getDeliveryRecords({
        ...buildQuery(),
        current: page,
        size: EXPORT_PAGE_SIZE
      })
      const pageRecords = camelizeKeys(recordsOf(res.data)).map(buildDeliveryRecordRowViewModel)
      exportRows.push(...pageRecords)
      if (pageRecords.length < EXPORT_PAGE_SIZE) break  // 已到末页
      if (exportRows.length >= EXPORT_MAX_LIMIT) {
        exportRows.length = EXPORT_MAX_LIMIT
        break
      }
      success.value = `正在导出 ${exportRows.length} / ${targetCount} 条...`
    }
    if (!exportRows.length) {
      success.value = ''
      error.value = '没有可导出的发货记录'
      return
    }

    const headers = ['ID', '订单号', '商品', '买家', '时机', '方式', '状态', '进度', '错误', '创建时间']
    const lines = [
      headers.join(','),
      ...exportRows.map(row => ([
        row.id,
        row.orderId,
        row.goodsTitleText,
        row.buyerNameText,
        row.timingText,
        row.deliveryModeText,
        row.deliveryStatusText,
        row.deliveryProgressText,
        row.errorMessage || '',
        row.createdTimeText
      ]).map(escapeCsv).join(','))
    ]

    const blob = new Blob(['\uFEFF' + lines.join('\n')], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `delivery-records-${Date.now()}.csv`
    link.click()
    URL.revokeObjectURL(url)
    success.value = `已导出 ${exportRows.length} 条发货记录`
  } catch (requestError) {
    success.value = ''
    error.value = requestError.message || '导出发货记录失败'
  } finally {
    exportLoading.value = false
  }
}

function onHeaderAction(event) {
  if (event.detail === 'delivery-records-refresh') load()
  if (event.detail === 'delivery-records-export') exportCsv()
}

onMounted(() => {
  window.addEventListener('xya-header-action', onHeaderAction)
  load()
})

onBeforeUnmount(() => {
  recordsRequestGuard.invalidate()
  window.removeEventListener('xya-header-action', onHeaderAction)
})
</script>

<style scoped>
.delivery-records-page {
  display: grid;
  gap: 18px;
  min-width: 0;
  color: #111827;
}

.delivery-records-page * {
  box-sizing: border-box;
}

.delivery-records-notices {
  display: grid;
  gap: 8px;
}

.delivery-records-command-center {
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

.delivery-records-command-main {
  min-width: 0;
  display: grid;
  align-content: start;
  gap: 10px;
}

.delivery-records-command-kicker {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  color: #2563eb;
  font-size: 12px;
  font-weight: 740;
}

.delivery-records-command-kicker span,
.delivery-records-command-kicker b {
  min-height: 24px;
  display: inline-flex;
  align-items: center;
  padding: 0 9px;
  border-radius: 999px;
  background: rgba(37, 99, 235, .1);
}

.delivery-records-command-kicker b {
  color: #0f766e;
  background: rgba(15, 118, 110, .1);
}

.delivery-records-command-main h2 {
  margin: 0;
  color: #0f172a;
  font-size: 26px;
  font-weight: 760;
  line-height: 1.2;
}

.delivery-records-command-main p {
  max-width: 760px;
  margin: 0;
  color: #526079;
  font-size: 13px;
  line-height: 1.7;
}

.delivery-records-command-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 2px;
}

.delivery-records-command-meta span {
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

.delivery-records-command-panel {
  align-self: stretch;
  min-width: 0;
  display: grid;
  gap: 14px;
  padding: 14px;
  border: 1px solid rgba(148, 163, 184, .25);
  border-radius: 8px;
  background: rgba(255, 255, 255, .92);
}

.delivery-records-command-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  color: #64748b;
  font-size: 12px;
}

.delivery-records-command-panel-head strong {
  color: #2563eb;
  font-size: 13px;
}

.delivery-records-command-buttons {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.delivery-records-safety-note {
  padding: 12px 14px;
  border: 1px solid #f7c97a;
  border-left: 4px solid #f59e0b;
  border-radius: 8px;
  background: #fff8e8;
  color: #8a4b08;
  font-size: 13px;
  line-height: 1.65;
}

.delivery-records-metric-rail {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.delivery-records-metric-card {
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

.delivery-records-metric-icon {
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

.delivery-records-metric-card.tone-blue { border-top-color: #2563eb; }
.delivery-records-metric-card.tone-blue .delivery-records-metric-icon { background: #2563eb; }
.delivery-records-metric-card.tone-green { border-top-color: #059669; }
.delivery-records-metric-card.tone-green .delivery-records-metric-icon { background: #059669; }
.delivery-records-metric-card.tone-cyan { border-top-color: #0891b2; }
.delivery-records-metric-card.tone-cyan .delivery-records-metric-icon { background: #0891b2; }
.delivery-records-metric-card.tone-orange { border-top-color: #ea580c; }
.delivery-records-metric-card.tone-orange .delivery-records-metric-icon { background: #ea580c; }

.delivery-records-metric-card :deep(.n-statistic .n-statistic-label) {
  color: #64748b;
  font-size: 12px;
}

.delivery-records-metric-card :deep(.n-statistic .n-statistic-value) {
  color: #111827;
  font-size: 24px;
  font-weight: 760;
}

.delivery-records-metric-card small {
  color: #64748b;
  font-size: 12px;
  line-height: 1.45;
}

.delivery-records-panel {
  min-width: 0;
  padding: 16px;
  border: 1px solid #e4ebf5;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 10px 28px rgba(15, 23, 42, .05);
}

.delivery-records-panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid #eef2f7;
}

.delivery-records-panel-head span {
  color: #2563eb;
  font-size: 12px;
  font-weight: 760;
}

.delivery-records-panel-head h3 {
  margin: 4px 0 0;
  color: #111827;
  font-size: 17px;
  font-weight: 730;
  line-height: 1.35;
}

.delivery-records-panel-head b {
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

.delivery-records-filter-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(140px, .7fr)) repeat(3, minmax(160px, 1fr)) auto;
  gap: 10px;
  align-items: center;
}

.delivery-records-select {
  min-width: 0;
}

.delivery-records-filter-actions {
  display: grid;
  grid-template-columns: auto auto;
  gap: 8px;
  align-items: center;
}

.wrap {
  flex-wrap: wrap;
}

.narrow {
  max-width: 160px;
}

.grow {
  flex: 1 1 180px;
}

.refresh-status {
  margin-bottom: 10px;
  color: #526079;
  font-size: 13px;
}

.warning {
  background: #fff8e8;
  color: #8a4b08;
  border-color: #f7c97a;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 16px;
}

.panel-block {
  margin-top: 16px;
}

.section-title {
  margin-bottom: 8px;
  font-weight: 600;
}

.content-box {
  min-height: 56px;
  padding: 12px;
  border: 1px solid #e6ecf5;
  border-radius: 8px;
  background: #FFFFFF;
  white-space: pre-wrap;
  word-break: break-word;
}

.content-box.compact {
  min-height: auto;
}

.cell-ellipsis {
  display: inline-block;
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.inline-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.form-field {
  display: grid;
  gap: 6px;
  margin-bottom: 12px;
}

.success {
  background: #ecfdf3;
  color: #067647;
  border-color: #abefc6;
}

@media (max-width: 900px) {
  .delivery-records-page {
    gap: 12px;
  }

  .delivery-records-command-center,
  .delivery-records-filter-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .delivery-records-command-center,
  .delivery-records-panel {
    padding: 14px;
  }

  .delivery-records-command-main h2 {
    font-size: 22px;
  }

  .delivery-records-command-buttons,
  .delivery-records-filter-actions {
    grid-template-columns: minmax(0, 1fr);
  }

  .delivery-records-metric-rail {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }

  .delivery-records-metric-card {
    min-height: 124px;
    padding: 12px;
  }

  .delivery-records-panel-head {
    gap: 10px;
    margin-bottom: 12px;
  }

  .narrow {
    max-width: 100%;
    width: 100%;
  }
  .grow {
    flex: 1 1 100%;
    width: 100%;
  }

  .detail-grid {
    grid-template-columns: minmax(0, 1fr);
    gap: 8px;
  }
  .detail-grid > * {
    min-width: 0;
  }

  .panel-block {
    margin-top: 12px;
  }
  .section-title {
    margin-bottom: 6px;
  }

  .content-box {
    min-height: 48px;
    padding: 10px;
  }

  .cell-ellipsis {
    max-width: 140px;
  }

  .inline-actions {
    gap: 8px;
  }

  .form-field {
    gap: 6px;
    margin-bottom: 10px;
  }
}
</style>
