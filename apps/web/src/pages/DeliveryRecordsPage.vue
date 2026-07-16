<template>
  <div class="delivery-records-v4">
    <div class="delivery-records-v4-notices">
      <div v-if="error" class="global-notice error">{{ error }}</div>
      <div v-if="warning" class="global-notice warning" role="status">{{ warning }}</div>
      <div v-if="success" class="global-notice success">{{ success }}</div>
    </div>

    <n-card class="delivery-records-v4-hero" :bordered="false">
      <div>
        <n-tag size="small" type="success" :bordered="false">Fulfillment Audit</n-tag>
        <h2>发货记录审计</h2>
        <p>集中查看真实发货执行结果、失败原因、卡密/文本方式和订单闭环状态。</p>
      </div>
      <n-space :size="8" align="center" wrap>
        <n-button size="small" :loading="recordsLoading" @click="load">刷新记录</n-button>
        <n-button size="small" type="primary" :disabled="recordsAvailable !== true || exportLoading" @click="exportCsv">
          {{ exportLoading ? '导出中...' : '导出 CSV' }}
        </n-button>
      </n-space>
    </n-card>

    <n-alert class="delivery-records-v4-alert" type="warning" :bordered="false">
      当前版本没有安全的发货记录自动重试执行器。请先在闲鱼 App 核对买家消息与平台发货状态；确需再次操作时，请前往“订单管理”使用手动发货闭环。
    </n-alert>

    <section class="delivery-records-v4-stats">
      <n-card
        v-for="item in recordStatCards"
        :key="item.key"
        class="delivery-records-v4-stat"
        :class="item.tone"
        :bordered="false"
      >
        <span class="delivery-records-v4-stat-icon">{{ item.symbol }}</span>
        <n-statistic :label="item.title" :value="item.value" />
        <small>{{ item.change }}</small>
      </n-card>
    </section>

    <n-card class="delivery-records-v4-filter" :bordered="false">
      <div class="delivery-records-v4-filter-grid">
        <n-select v-model:value="query.status" class="delivery-records-v4-select" :options="statusOptions" />
        <n-select v-model:value="query.timing" class="delivery-records-v4-select" :options="timingOptions" />
        <n-select v-model:value="query.deliveryMode" class="delivery-records-v4-select" :options="modeOptions" />
        <n-input v-model:value="query.goodsKeyword" clearable placeholder="商品关键词" />
        <n-input v-model:value="query.buyerKeyword" clearable placeholder="买家关键词" />
        <n-input v-model:value="query.orderKeyword" clearable placeholder="订单号 / 外部订单号" @keyup.enter="search" />
        <n-space :size="8" align="center" wrap>
          <n-button type="primary" :loading="recordsLoading" @click="search">搜索</n-button>
          <n-button :disabled="recordsLoading" @click="resetFilters">重置</n-button>
        </n-space>
      </div>
    </n-card>

    <n-card class="delivery-records-v4-table" :bordered="false">
      <template #header>发货记录</template>
      <template #header-extra>
        <n-space :size="8" align="center">
          <n-tag size="small" :bordered="false">共 {{ recordsAvailable === true ? total : '—' }} 条</n-tag>
          <n-tag size="small" type="info" :bordered="false">第 {{ query.current }} 页</n-tag>
        </n-space>
      </template>
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
    </n-card>

    <n-card v-if="detailView" class="delivery-records-v4-detail" :bordered="false">
      <template #header>发货记录详情</template>
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
    </n-card>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { NAlert, NButton, NCard, NInput, NSelect, NSpace, NStatistic, NTag } from 'naive-ui'
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
  const EXPORT_PAGE_SIZE = 100    // 分页拉取每页大小（后端 PageUtils 限制 max=100）
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
.delivery-records-v4 {
  display: grid;
  gap: 16px;
  min-width: 0;
}

.delivery-records-v4-notices {
  display: grid;
  gap: 8px;
}

.delivery-records-v4-hero,
.delivery-records-v4-filter,
.delivery-records-v4-table,
.delivery-records-v4-detail,
.delivery-records-v4-stat {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, .04);
}

.delivery-records-v4-hero :deep(.n-card__content) {
  padding: 18px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.delivery-records-v4-hero h2 {
  margin: 12px 0 6px;
  color: #111827;
  font-size: 22px;
  font-weight: 650;
  line-height: 1.25;
}

.delivery-records-v4-hero p {
  margin: 0;
  color: #64748b;
  font-size: 13px;
  line-height: 1.65;
}

.delivery-records-v4-alert {
  border-radius: 6px;
}

.delivery-records-v4-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.delivery-records-v4-stat :deep(.n-card__content) {
  padding: 16px;
  display: grid;
  gap: 8px;
}

.delivery-records-v4-stat-icon {
  width: 36px;
  height: 36px;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
}

.delivery-records-v4-stat.tone-blue .delivery-records-v4-stat-icon { background: #eff6ff; color: #2563eb; }
.delivery-records-v4-stat.tone-green .delivery-records-v4-stat-icon { background: #ecfdf5; color: #059669; }
.delivery-records-v4-stat.tone-cyan .delivery-records-v4-stat-icon { background: #ecfeff; color: #0891b2; }
.delivery-records-v4-stat.tone-orange .delivery-records-v4-stat-icon { background: #fff7ed; color: #ea580c; }

.delivery-records-v4-stat :deep(.n-statistic .n-statistic-label) {
  color: #64748b;
  font-size: 12px;
}

.delivery-records-v4-stat :deep(.n-statistic .n-statistic-value) {
  color: #111827;
  font-size: 24px;
  font-weight: 700;
}

.delivery-records-v4-stat small {
  color: #64748b;
  font-size: 12px;
  line-height: 1.4;
}

.delivery-records-v4-filter :deep(.n-card__content),
.delivery-records-v4-table :deep(.n-card__content),
.delivery-records-v4-detail :deep(.n-card__content) {
  padding: 16px;
}

.delivery-records-v4-table :deep(.n-card-header),
.delivery-records-v4-detail :deep(.n-card-header) {
  padding: 16px 16px 0;
}

.delivery-records-v4-filter-grid {
  display: grid;
  grid-template-columns: 150px 150px 150px repeat(3, minmax(150px, 1fr)) auto;
  gap: 10px;
  align-items: center;
}

.delivery-records-v4-select {
  min-width: 0;
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
  border-radius: 10px;
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

/* ───── 移动端适配 ───── */
@media (max-width: 900px) {
  .delivery-records-v4 {
    gap: 12px;
  }

  .delivery-records-v4-hero :deep(.n-card__content) {
    flex-direction: column;
    padding: 14px;
  }

  .delivery-records-v4-stats {
    grid-template-columns: minmax(0, 1fr);
  }

  .delivery-records-v4-filter :deep(.n-card__content),
  .delivery-records-v4-table :deep(.n-card__content),
  .delivery-records-v4-detail :deep(.n-card__content) {
    padding: 12px;
  }

  .delivery-records-v4-filter-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  /* 筛选工具栏：narrow / grow 全宽堆叠 */
  .narrow {
    max-width: 100%;
    width: 100%;
  }
  .grow {
    flex: 1 1 100%;
    width: 100%;
  }

  /* 详情双列网格 → 单列堆叠 */
  .detail-grid {
    grid-template-columns: minmax(0, 1fr);
    gap: 8px;
  }
  .detail-grid > * {
    min-width: 0;
  }

  /* 面板间距收窄 */
  .panel-block {
    margin-top: 12px;
  }
  .section-title {
    margin-bottom: 6px;
  }

  /* 内容框内边距收窄 */
  .content-box {
    min-height: 48px;
    padding: 10px;
  }

  /* 错误信息省略宽度收窄 */
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
