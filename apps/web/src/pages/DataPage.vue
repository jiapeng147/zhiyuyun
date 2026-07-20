<template>
  <div class="data-board">
    <n-alert v-if="error" class="data-error" type="error" :bordered="false" closable @close="error = ''">
      {{ error }}
    </n-alert>

    <BusinessSection class="data-hero" title="经营数据指挥台" eyebrow="运营数据">
      <template #extra>
        <n-tag :type="dataAvailable ? 'success' : 'warning'" size="small" :bordered="false">
          {{ dataAvailable ? '汇总已同步' : '等待汇总' }}
        </n-tag>
      </template>

      <div class="data-hero-layout">
        <div class="data-hero-copy">
          <p>
            用订单、发货、AI 回复和实时事件组成运营监控视图。接口失败时保留真实状态，不用全零数据伪装正常结果。
          </p>
          <n-space class="data-meta-row" :size="[8, 8]">
            <n-tag size="small" :bordered="false" round>{{ loading ? '正在刷新' : '刷新就绪' }}</n-tag>
            <n-tag size="small" :bordered="false" round>更新时间 {{ updatedAt }}</n-tag>
            <n-tag size="small" :bordered="false" round>{{ date || '默认统计日' }}</n-tag>
          </n-space>
        </div>

        <div class="data-filter-panel" aria-label="数据口径">
          <div class="filter-title">
            <span>数据口径</span>
            <strong>{{ trendAvailable ? '趋势可用' : '趋势待恢复' }}</strong>
          </div>
          <n-date-picker
            class="date-picker"
            type="date"
            clearable
            :value="datePickerValue"
            :disabled="loading"
            placeholder="选择统计日期"
            @update:value="onDatePickerUpdate"
          />
          <n-button type="primary" block :loading="loading" :disabled="loading" @click="load">
            <template #icon>
              <n-icon :component="RefreshOutline" />
            </template>
            {{ loading ? '刷新中' : '刷新数据' }}
          </n-button>
        </div>
      </div>
    </BusinessSection>

    <BusinessStatusStrip :items="statusItems" />

    <section class="metric-grid" aria-label="核心指标">
      <BusinessMetricCard
        v-for="item in dataStatCards"
        :key="item.key"
        :label="item.title"
        :value="item.value"
        :hint="item.change"
        :tone="item.tone"
        :icon="item.icon"
        :compact-value="item.compactValue"
      />
    </section>

    <section class="data-workbench">
      <BusinessSection class="span-8" title="发货成功趋势" eyebrow="近 7 天">
        <template #extra>
          <n-tag size="small" :type="trendAvailable ? 'success' : 'warning'" :bordered="false">
            {{ trendAvailable ? '已生成' : '等待数据' }}
          </n-tag>
        </template>
        <EmptyState v-if="!trendAvailable" icon="△" title="趋势暂不可用" description="汇总与趋势独立加载，可点击刷新重试。" />
        <MiniLineChart v-else :values="trend.deliverySuccess" :labels="trend.dates" />
      </BusinessSection>

      <BusinessSection class="span-4" title="AI 回复概况" eyebrow="自动接待">
        <template #extra>
          <n-tag size="small" :bordered="false">{{ totalReplies }}</n-tag>
        </template>
        <EmptyState v-if="!dataAvailable" icon="!" title="统计暂不可用" description="当前不会以全零数据代替查询失败。" />
        <DonutChart v-else :center="String(totalReplies)" label="AI回复" :items="replyItems" />
      </BusinessSection>

      <BusinessSection class="span-4" title="发货失败趋势" eyebrow="履约质量">
        <template #extra>
          <n-tag size="small" :type="trendAvailable ? 'info' : 'warning'" :bordered="false">
            {{ trendAvailable ? '近 7 天' : '待恢复' }}
          </n-tag>
        </template>
        <EmptyState v-if="!trendAvailable" icon="△" title="趋势暂不可用" description="汇总与趋势独立加载，可点击刷新重试。" />
        <MiniLineChart v-else :values="trend.deliveryFail" :labels="trend.dates" />
      </BusinessSection>

      <BusinessSection class="span-4" title="发货概况" eyebrow="履约结构">
        <template #extra>
          <n-tag size="small" :type="dataAvailable ? 'success' : 'warning'" :bordered="false">{{ successRate }}</n-tag>
        </template>
        <EmptyState v-if="!dataAvailable" icon="□" title="发货统计暂不可用" description="不会把查询失败显示为零。" />
        <template v-else>
          <DonutChart :center="String(totalDelivery)" label="发货合计" :items="deliveryItems" />
          <div class="data-health-grid">
            <div><span>成功率</span><b class="good">{{ successRate }}</b></div>
            <div><span>失败</span><b class="danger">{{ stats.deliveryFailCount }}</b></div>
            <div><span>待处理</span><b>{{ stats.pendingDeliveryCount }}</b></div>
          </div>
        </template>
      </BusinessSection>

      <BusinessSection class="span-4" title="最新事件" eyebrow="实时监听">
        <template #extra>
          <n-tag size="small" :type="logs.length ? 'success' : 'default'" :bordered="false">
            {{ logs.length ? '有更新' : '空闲' }}
          </n-tag>
        </template>
        <EmptyState v-if="logs.length === 0" icon="·" title="暂无实时事件" description="订单、发货、AI 回复等实时事件会在这里显示。" />
        <div v-else class="data-event-list">
          <div v-for="n in logs" :key="n.t + n.time" class="data-event-row">
            <div>
              <b>{{ n.t }}</b>
              <p>{{ n.d }}</p>
            </div>
            <time>{{ n.time }}</time>
          </div>
        </div>
      </BusinessSection>

      <BusinessSection class="span-8" title="日维度流水" eyebrow="趋势明细">
        <template #extra>
          <n-tag size="small" :bordered="false">{{ trendRows.length }} 行</n-tag>
        </template>
        <EmptyState v-if="!trendAvailable" icon="≡" title="明细暂不可用" description="趋势查询恢复后再显示。" />
        <n-data-table
          v-else
          class="trend-table"
          :columns="trendCols"
          :data="trendRows"
          :pagination="false"
          :bordered="false"
          size="small"
        />
      </BusinessSection>
    </section>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { NAlert, NButton, NDataTable, NDatePicker, NIcon, NSpace, NTag } from 'naive-ui'
import {
  AlertCircleOutline,
  CartOutline,
  ChatbubbleEllipsesOutline,
  CheckmarkCircleOutline,
  PulseOutline,
  RefreshOutline,
  TimeOutline,
} from '@vicons/ionicons5'
import BusinessMetricCard from '../components/business/BusinessMetricCard.vue'
import BusinessSection from '../components/business/BusinessSection.vue'
import BusinessStatusStrip from '../components/business/BusinessStatusStrip.vue'
import MiniLineChart from '../components/MiniLineChart.vue'
import DonutChart from '../components/DonutChart.vue'
import EmptyState from '../components/EmptyState.vue'
import { getDashboardSummary, getDashboardSalesTrend } from '../api/dashboard.js'
import { shortText } from '../utils/format.js'

const stats = ref({ orderCount: 0, deliverySuccessCount: 0, deliveryFailCount: 0, pendingDeliveryCount: 0, aiReplyCount: 0, hasData: false })
const trend = ref({ dates: [], deliverySuccess: [], deliveryFail: [], aiReplies: [] })
const updatedAt = ref('-')
const error = ref('')
const loading = ref(false)
const dataAvailable = ref(false)
const trendAvailable = ref(false)
const loadedSummaryDate = ref(null)
const loadedTrendDate = ref(null)
const logs = ref([])
const date = ref('')

const totalDelivery = computed(() => Number(stats.value.deliverySuccessCount || 0) + Number(stats.value.deliveryFailCount || 0))
const totalReplies = computed(() => Number(stats.value.aiReplyCount || 0))
const successRate = computed(() => totalDelivery.value ? `${Math.round(Number(stats.value.deliverySuccessCount || 0) * 100 / totalDelivery.value)}%` : '—')
const deliveryItems = computed(() => [
  { label: '成功', value: String(stats.value.deliverySuccessCount || 0) },
  { label: '失败', value: String(stats.value.deliveryFailCount || 0) },
  { label: '待发货', value: String(stats.value.pendingDeliveryCount || 0) },
])
const replyItems = computed(() => [{ label: 'AI回复', value: String(totalReplies.value) }])
const dataStatCards = computed(() => [
  { key: 'orders', title: '订单数', value: metricValue(stats.value.orderCount), change: '订单统计', tone: 'blue', icon: CartOutline },
  { key: 'success', title: '发货成功', value: metricValue(stats.value.deliverySuccessCount), change: '成功发货记录', tone: 'green', icon: CheckmarkCircleOutline },
  { key: 'failed', title: '发货失败', value: metricValue(stats.value.deliveryFailCount), change: '失败发货记录', tone: 'orange', icon: AlertCircleOutline },
  { key: 'pending', title: '待发货', value: metricValue(stats.value.pendingDeliveryCount), change: '待处理发货记录', tone: 'cyan', icon: TimeOutline },
  { key: 'reply', title: 'AI回复', value: metricValue(stats.value.aiReplyCount), change: '自动回复记录', tone: 'purple', icon: ChatbubbleEllipsesOutline },
  {
    key: 'state',
    title: '数据状态',
    value: loading.value ? '加载中' : (dataAvailable.value ? (stats.value.hasData ? '有数据' : '暂无数据') : '不可用'),
    change: '平台统计结果',
    tone: dataAvailable.value ? 'green' : 'orange',
    icon: PulseOutline,
    compactValue: true,
  },
])
const statusItems = computed(() => [
  { key: 'summary', label: '汇总服务', value: dataAvailable.value ? '正常' : '不可用', tone: dataAvailable.value ? 'green' : 'orange' },
  { key: 'trend', label: '趋势服务', value: trendAvailable.value ? '正常' : '不可用', tone: trendAvailable.value ? 'green' : 'orange' },
  { key: 'events', label: '实时事件', value: logs.value.length ? `${logs.value.length} 条` : '监听中', tone: logs.value.length ? 'blue' : 'green' },
])
const trendCols = [
  { key: 'date', title: '日期' },
  { key: 'success', title: '发货成功' },
  { key: 'fail', title: '发货失败' },
  { key: 'reply', title: 'AI回复' },
]
const trendRows = computed(() => (trend.value.dates || []).map((d, i) => ({
  date: d,
  success: trend.value.deliverySuccess?.[i] || 0,
  fail: trend.value.deliveryFail?.[i] || 0,
  reply: trend.value.aiReplies?.[i] || 0,
})))
const datePickerValue = computed(() => (date.value ? new Date(`${date.value}T00:00:00`).getTime() : null))

function metricValue(value) { return dataAvailable.value ? value : '—' }

function formatDateValue(value) {
  if (!value) return ''
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return ''
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function onDatePickerUpdate(value) {
  date.value = formatDateValue(value)
  load()
}

async function load() {
  if (loading.value) return
  const requestDate = date.value || ''
  const hadSummarySnapshot = dataAvailable.value && loadedSummaryDate.value === requestDate
  const hadTrendSnapshot = trendAvailable.value && loadedTrendDate.value === requestDate
  if (!hadSummarySnapshot) dataAvailable.value = false
  if (!hadTrendSnapshot) trendAvailable.value = false
  loading.value = true
  error.value = ''
  try {
    const rangeParams = requestDate ? { date: requestDate } : {}
    const [summaryResult, trendResult] = await Promise.allSettled([
      getDashboardSummary(rangeParams),
      getDashboardSalesTrend(rangeParams),
    ])
    const failures = []
    const summarySucceeded = summaryResult.status === 'fulfilled' && Boolean(summaryResult.value?.data)
    const trendSucceeded = trendResult.status === 'fulfilled' && Boolean(trendResult.value?.data)
    if (summarySucceeded) {
      const sd = summaryResult.value.data
      stats.value = {
        orderCount: sd.todayOrderCount ?? sd.orderCount ?? 0,
        deliverySuccessCount: sd.deliverySuccessCount ?? 0,
        deliveryFailCount: sd.deliveryFailCount ?? 0,
        pendingDeliveryCount: sd.pendingDeliveryCount ?? 0,
        aiReplyCount: sd.autoReplyCount ?? sd.aiReplyCount ?? 0,
        hasData: !!(
          (sd.todayOrderCount ?? sd.orderCount) || sd.deliverySuccessCount ||
          sd.deliveryFailCount || sd.pendingDeliveryCount ||
          (sd.autoReplyCount ?? sd.aiReplyCount)
        ),
      }
      dataAvailable.value = true
      loadedSummaryDate.value = requestDate
    } else {
      dataAvailable.value = hadSummarySnapshot
      failures.push('运营汇总')
    }
    if (trendSucceeded) {
      const td = trendResult.value.data
      trend.value = {
        dates: td.dates || [],
        deliverySuccess: td.deliverySuccess || [],
        deliveryFail: td.deliveryFail || [],
        aiReplies: td.aiReplyCount || td.aiReplies || [],
      }
      trendAvailable.value = true
      loadedTrendDate.value = requestDate
    } else {
      trendAvailable.value = hadTrendSnapshot
      failures.push('趋势')
    }
    const refreshed = summarySucceeded || trendSucceeded
    if (refreshed) updatedAt.value = new Date().toLocaleString('zh-CN', { hour12: false })
    else if (!hadSummarySnapshot && !hadTrendSnapshot) updatedAt.value = '不可用'
    if (failures.length) {
      const preserved = hadSummarySnapshot || hadTrendSnapshot ? '；同一日期的上次成功数据已保留' : ''
      error.value = `${failures.join('、')}暂不可用${preserved}；失败区域不会以全零数据代替。`
    }
  } catch {
    dataAvailable.value = hadSummarySnapshot
    trendAvailable.value = hadTrendSnapshot
    if (!hadSummarySnapshot && !hadTrendSnapshot) updatedAt.value = '不可用'
    error.value = hadSummarySnapshot || hadTrendSnapshot
      ? '统计服务暂不可用，已保留同一日期的上次成功数据。请检查服务状态后重试。'
      : '统计服务暂不可用，当前不会用全零数据代替查询失败。请检查服务状态后重试。'
  } finally {
    loading.value = false
  }
}

function onSse(event) {
  const d = event.detail || {}
  logs.value.unshift({
    t: d.type || d.event || '实时事件',
    d: shortText(d.message || d.content || '状态已更新', 70),
    time: new Date().toLocaleTimeString('zh-CN', { hour12: false }),
  })
  logs.value = logs.value.slice(0, 5)
}

function onHeader(e) {
  if (e.detail === 'refresh-data-panel') load()
}

onMounted(() => {
  window.addEventListener('xya-sse-event', onSse)
  window.addEventListener('xya-header-action', onHeader)
  load()
})
onBeforeUnmount(() => {
  window.removeEventListener('xya-sse-event', onSse)
  window.removeEventListener('xya-header-action', onHeader)
})
</script>

<style scoped>
.data-board {
  display: grid;
  gap: 16px;
  min-width: 0;
}

.data-error {
  border-radius: 8px;
}

.data-hero :deep(.n-card-header) {
  padding-bottom: 8px;
}

.data-hero-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 316px;
  gap: 18px;
  align-items: start;
}

.data-hero-copy {
  min-width: 0;
}

.data-hero-copy p {
  max-width: 760px;
  margin: 0;
  color: #4b5563;
  font-size: 14px;
  line-height: 1.75;
}

.data-meta-row {
  margin-top: 14px;
}

.data-filter-panel {
  display: grid;
  gap: 12px;
  min-width: 0;
  padding: 14px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f9fafb;
}

.filter-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.filter-title span {
  color: #6b7280;
  font-size: 12px;
  font-weight: 600;
}

.filter-title strong {
  color: #111827;
  font-size: 13px;
  font-weight: 700;
}

.date-picker {
  width: 100%;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
}

.data-workbench {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 16px;
}

.span-4 {
  grid-column: span 4;
}

.span-8 {
  grid-column: span 8;
}

.data-health-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-top: 18px;
}

.data-health-grid div {
  min-width: 0;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f9fafb;
}

.data-health-grid span {
  display: block;
  color: #6b7280;
  font-size: 12px;
  line-height: 1.35;
}

.data-health-grid b {
  display: block;
  margin-top: 4px;
  color: #111827;
  font-size: 18px;
  font-weight: 700;
  line-height: 1.2;
}

.data-health-grid .good {
  color: #18a058;
}

.data-health-grid .danger {
  color: #d03050;
}

.data-event-list {
  display: grid;
  gap: 10px;
}

.data-event-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f9fafb;
}

.data-event-row b {
  color: #111827;
  font-size: 13px;
  font-weight: 700;
}

.data-event-row p {
  margin: 4px 0 0;
  color: #6b7280;
  font-size: 12px;
  line-height: 1.55;
}

.data-event-row time {
  color: #6b7280;
  font-size: 12px;
  white-space: nowrap;
}

.trend-table {
  --n-th-color: #f9fafb;
}

@media (max-width: 1200px) {
  .metric-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .span-4,
  .span-8 {
    grid-column: span 6;
  }
}

@media (max-width: 900px) {
  .data-board {
    gap: 12px;
  }

  .data-hero-layout,
  .metric-grid,
  .data-workbench,
  .data-health-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .span-4,
  .span-8 {
    grid-column: span 1;
  }

  .data-event-row {
    grid-template-columns: minmax(0, 1fr);
  }

  .data-event-row time {
    white-space: normal;
  }
}
</style>
