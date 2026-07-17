<template>
  <div class="data-board">
    <div v-if="error" class="global-notice error">{{ error }}</div>

    <section class="data-command-center">
      <div class="data-command-main">
        <div class="data-command-kicker">
          <span>运营数据</span>
          <b>{{ dataAvailable ? '汇总已同步' : '等待汇总' }}</b>
        </div>
        <h2>经营数据指挥台</h2>
        <p>用订单、发货、AI 回复和实时事件组成运营监控视图；接口失败时保留真实状态，不用全零数据伪装正常结果。</p>
        <div class="data-command-meta">
          <span>{{ loading ? '正在刷新' : '刷新就绪' }}</span>
          <span>更新时间 {{ updatedAt }}</span>
          <span>{{ date || '默认统计日' }}</span>
        </div>
      </div>

      <div class="data-control-panel">
        <div class="data-control-head">
          <span>数据口径</span>
          <strong>{{ trendAvailable ? '趋势可用' : '趋势待恢复' }}</strong>
        </div>
        <label class="data-date-field" for="stats-date">
          <span>统计日期</span>
          <input id="stats-date" v-model="date" class="input" type="date" aria-label="统计日期" :disabled="loading" @change="load">
        </label>
        <button class="data-refresh-btn" type="button" :disabled="loading" @click="load">
          {{ loading ? '刷新中...' : '刷新数据' }}
        </button>
      </div>
    </section>

    <section class="data-status-ribbon" aria-label="数据状态">
      <div :class="{ warn: !dataAvailable }">
        <span>汇总服务</span>
        <b>{{ dataAvailable ? '正常' : '不可用' }}</b>
      </div>
      <div :class="{ warn: !trendAvailable }">
        <span>趋势服务</span>
        <b>{{ trendAvailable ? '正常' : '不可用' }}</b>
      </div>
      <div>
        <span>实时事件</span>
        <b>{{ logs.length ? `${logs.length} 条` : '监听中' }}</b>
      </div>
    </section>

    <section class="data-metric-rail">
      <article
        v-for="item in dataStatCards"
        :key="item.key"
        class="data-metric-card"
        :class="item.tone"
      >
        <span class="data-metric-icon">{{ item.symbol }}</span>
        <div>
          <p>{{ item.title }}</p>
          <strong>{{ item.value }}</strong>
          <small>{{ item.change }}</small>
        </div>
      </article>
    </section>

    <section class="data-workbench">
      <article class="data-panel data-panel-wide">
        <header class="data-panel-head">
          <div>
            <span>近 7 天</span>
            <h3>发货成功趋势</h3>
          </div>
          <b>{{ trendAvailable ? '已生成' : '等待数据' }}</b>
        </header>
        <EmptyState v-if="!trendAvailable" icon="△" title="趋势暂不可用" description="汇总与趋势独立加载，可点击刷新重试。" />
        <MiniLineChart v-else :values="trend.deliverySuccess" :labels="trend.dates" />
      </article>

      <article class="data-panel">
        <header class="data-panel-head">
          <div>
            <span>自动接待</span>
            <h3>AI 回复概况</h3>
          </div>
          <b>{{ totalReplies }}</b>
        </header>
        <EmptyState v-if="!dataAvailable" icon="!" title="统计暂不可用" description="当前不会以全零数据代替查询失败。" />
        <DonutChart v-else :center="String(totalReplies)" label="AI回复" :items="replyItems" />
      </article>

      <article class="data-panel">
        <header class="data-panel-head">
          <div>
            <span>履约质量</span>
            <h3>发货失败趋势</h3>
          </div>
          <b>{{ trendAvailable ? '近 7 天' : '待恢复' }}</b>
        </header>
        <EmptyState v-if="!trendAvailable" icon="△" title="趋势暂不可用" description="汇总与趋势独立加载，可点击刷新重试。" />
        <MiniLineChart v-else :values="trend.deliveryFail" :labels="trend.dates" />
      </article>

      <article class="data-panel">
        <header class="data-panel-head">
          <div>
            <span>履约结构</span>
            <h3>发货概况</h3>
          </div>
          <b>{{ successRate }}</b>
        </header>
        <EmptyState v-if="!dataAvailable" icon="□" title="发货统计暂不可用" description="不会把查询失败显示为零。" />
        <template v-else>
          <DonutChart :center="String(totalDelivery)" label="发货合计" :items="deliveryItems" />
          <div class="data-health-grid">
            <div><span>成功率</span><b class="good">{{ successRate }}</b></div>
            <div><span>失败</span><b class="danger">{{ stats.deliveryFailCount }}</b></div>
            <div><span>待处理</span><b>{{ stats.pendingDeliveryCount }}</b></div>
          </div>
        </template>
      </article>

      <article class="data-panel data-panel-wide">
        <header class="data-panel-head">
          <div>
            <span>趋势明细</span>
            <h3>日维度流水</h3>
          </div>
          <b>{{ trendRows.length }} 行</b>
        </header>
        <EmptyState v-if="!trendAvailable" icon="≡" title="明细暂不可用" description="趋势查询恢复后再显示。" />
        <BaseTable v-else :columns="trendCols" :rows="trendRows" />
      </article>

      <article class="data-panel data-feed-panel">
        <header class="data-panel-head">
          <div>
            <span>实时监听</span>
            <h3>最新事件</h3>
          </div>
          <b>{{ logs.length ? '有更新' : '空闲' }}</b>
        </header>
        <EmptyState v-if="logs.length === 0" icon="·" title="暂无实时事件" description="订单、发货、AI 回复等实时事件会在这里显示。" />
        <div v-else class="data-event-list">
          <div v-for="n in logs" :key="n.t+n.time" class="data-event-row">
            <div>
              <b>{{ n.t }}</b>
              <p>{{ n.d }}</p>
            </div>
            <time>{{ n.time }}</time>
          </div>
        </div>
      </article>
    </section>
  </div>
</template>
<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import MiniLineChart from '../components/MiniLineChart.vue'
import DonutChart from '../components/DonutChart.vue'
import BaseTable from '../components/BaseTable.vue'
import EmptyState from '../components/EmptyState.vue'
import { getDashboardSummary, getDashboardSalesTrend } from '../api/dashboard.js'
import { shortText } from '../utils/format.js'
const stats = ref({ orderCount:0, deliverySuccessCount:0, deliveryFailCount:0, pendingDeliveryCount:0, aiReplyCount:0, hasData:false })
const trend = ref({ dates:[], deliverySuccess:[], deliveryFail:[], aiReplies:[] })
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
const deliveryItems = computed(() => [{label:'成功', value:String(stats.value.deliverySuccessCount || 0)}, {label:'失败', value:String(stats.value.deliveryFailCount || 0)}, {label:'待发货', value:String(stats.value.pendingDeliveryCount || 0)}])
const replyItems = computed(() => [{label:'AI回复', value:String(totalReplies.value)}])
const dataStatCards = computed(() => [
  { key: 'orders', title: '订单数', value: metricValue(stats.value.orderCount), change: '订单统计', symbol: '单', tone: 'tone-blue' },
  { key: 'success', title: '发货成功', value: metricValue(stats.value.deliverySuccessCount), change: '成功发货记录', symbol: '成', tone: 'tone-green' },
  { key: 'failed', title: '发货失败', value: metricValue(stats.value.deliveryFailCount), change: '失败发货记录', symbol: '败', tone: 'tone-orange' },
  { key: 'pending', title: '待发货', value: metricValue(stats.value.pendingDeliveryCount), change: '待处理发货记录', symbol: '待', tone: 'tone-cyan' },
  { key: 'reply', title: 'AI回复', value: metricValue(stats.value.aiReplyCount), change: '自动回复记录', symbol: 'AI', tone: 'tone-purple' },
  { key: 'state', title: '数据状态', value: loading.value ? '加载中' : (dataAvailable.value ? (stats.value.hasData ? '有数据' : '暂无数据') : '不可用'), change: '平台统计结果', symbol: '态', tone: dataAvailable.value ? 'tone-green' : 'tone-orange' }
])
const trendCols=[{key:'date',title:'日期'},{key:'success',title:'发货成功'},{key:'fail',title:'发货失败'},{key:'reply',title:'AI回复'}]
const trendRows = computed(() => (trend.value.dates || []).map((d,i)=>({date:d, success:trend.value.deliverySuccess?.[i] || 0, fail:trend.value.deliveryFail?.[i] || 0, reply:trend.value.aiReplies?.[i] || 0})))
function metricValue(value) { return dataAvailable.value ? value : '—' }
async function load(){
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
      getDashboardSalesTrend(rangeParams)
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
        )
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
        aiReplies: td.aiReplyCount || td.aiReplies || []
      }
      trendAvailable.value = true
      loadedTrendDate.value = requestDate
    } else {
      trendAvailable.value = hadTrendSnapshot
      failures.push('趋势')
    }
    const refreshed = summarySucceeded || trendSucceeded
    if (refreshed) updatedAt.value = new Date().toLocaleString('zh-CN', { hour12:false })
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
function onSse(event){ const d=event.detail||{}; logs.value.unshift({t:d.type||d.event||'实时事件', d:shortText(d.message||d.content||'状态已更新',70), time:new Date().toLocaleTimeString('zh-CN',{hour12:false})}); logs.value=logs.value.slice(0,5) }
function onHeader(e){ if(e.detail === 'refresh-data-panel') load() }
onMounted(()=>{ window.addEventListener('xya-sse-event', onSse); window.addEventListener('xya-header-action', onHeader); load() })
onBeforeUnmount(()=>{ window.removeEventListener('xya-sse-event', onSse); window.removeEventListener('xya-header-action', onHeader) })
</script>
<style scoped>
.data-board {
  display: grid;
  gap: 18px;
  min-width: 0;
}

.data-command-center {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 18px;
  padding: 22px;
  border: 1px solid #dbe3ef;
  border-radius: 8px;
  background:
    linear-gradient(135deg, rgba(14, 116, 144, .08), rgba(34, 197, 94, .06) 44%, rgba(245, 158, 11, .08)),
    #ffffff;
  box-shadow: 0 16px 38px rgba(15, 23, 42, .07);
}

.data-command-main {
  min-width: 0;
}

.data-command-kicker,
.data-command-meta,
.data-control-head,
.data-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.data-command-kicker {
  justify-content: flex-start;
}

.data-command-kicker span,
.data-panel-head span,
.data-control-head span {
  color: #0f766e;
  font-size: 12px;
  font-weight: 750;
}

.data-command-kicker b,
.data-panel-head b,
.data-control-head strong {
  color: #475569;
  font-size: 12px;
  font-weight: 700;
}

.data-command-main h2 {
  margin: 12px 0 8px;
  color: #0f172a;
  font-size: 26px;
  font-weight: 780;
  line-height: 1.2;
}

.data-command-main p {
  max-width: 760px;
  margin: 0;
  color: #475569;
  font-size: 14px;
  line-height: 1.8;
}

.data-command-meta {
  justify-content: flex-start;
  flex-wrap: wrap;
  margin-top: 18px;
}

.data-command-meta span,
.data-status-ribbon div,
.data-date-field {
  border: 1px solid rgba(148, 163, 184, .32);
  border-radius: 8px;
  background: rgba(255, 255, 255, .78);
}

.data-command-meta span {
  padding: 7px 10px;
  color: #334155;
  font-size: 12px;
}

.data-control-panel {
  display: grid;
  align-content: start;
  gap: 12px;
  padding: 16px;
  border: 1px solid rgba(15, 118, 110, .18);
  border-radius: 8px;
  background: rgba(255, 255, 255, .76);
}

.data-date-field {
  display: grid;
  gap: 8px;
  padding: 10px;
}

.data-date-field span {
  color: #64748b;
  font-size: 12px;
}

.data-date-field input {
  width: 100%;
  border: 0;
  background: transparent;
}

.data-date-field input:focus {
  outline: none;
}

.data-refresh-btn {
  width: 100%;
  min-height: 40px;
  border: 0;
  border-radius: 8px;
  background: #0f766e;
  color: #ffffff;
  font-size: 14px;
  font-weight: 750;
  cursor: pointer;
}

.data-refresh-btn:disabled {
  cursor: wait;
  opacity: .72;
}

.data-status-ribbon {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.data-status-ribbon div {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-width: 0;
  padding: 12px 14px;
}

.data-status-ribbon span {
  color: #64748b;
  font-size: 12px;
}

.data-status-ribbon b {
  color: #047857;
  font-size: 13px;
}

.data-status-ribbon .warn b {
  color: #b45309;
}

.data-metric-rail {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
}

.data-metric-card {
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

.data-metric-icon {
  width: 38px;
  height: 38px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 800;
}

.data-metric-card p {
  margin: 0;
  color: #64748b;
  font-size: 12px;
}

.data-metric-card strong {
  display: block;
  margin-top: 3px;
  color: #0f172a;
  font-size: 24px;
  font-weight: 800;
  line-height: 1.2;
}

.data-metric-card small {
  display: block;
  margin-top: 6px;
  color: #64748b;
  font-size: 12px;
  line-height: 1.4;
}

.data-metric-card.tone-blue .data-metric-icon { background: #e0f2fe; color: #0369a1; }
.data-metric-card.tone-green .data-metric-icon { background: #dcfce7; color: #15803d; }
.data-metric-card.tone-orange .data-metric-icon { background: #ffedd5; color: #c2410c; }
.data-metric-card.tone-cyan .data-metric-icon { background: #ccfbf1; color: #0f766e; }
.data-metric-card.tone-purple .data-metric-icon { background: #ede9fe; color: #6d28d9; }

.data-workbench {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 16px;
}

.data-panel {
  grid-column: span 4;
  min-width: 0;
  padding: 16px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 10px 26px rgba(15, 23, 42, .05);
}

.data-panel-wide {
  grid-column: span 8;
}

.data-panel-head {
  align-items: flex-start;
  margin-bottom: 14px;
}

.data-panel-head h3 {
  margin: 4px 0 0;
  color: #0f172a;
  font-size: 17px;
  font-weight: 760;
  line-height: 1.25;
}

.data-panel :deep(.chart-wrap) {
  width: 100%;
  overflow: hidden;
}

.data-panel :deep(.line-chart) {
  width: 100%;
  height: auto;
  display: block;
}

.data-panel :deep(.base-table-wrap) {
  border-radius: 8px;
}

.data-health-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-top: 18px;
}

.data-health-grid div {
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f8fafc;
}

.data-health-grid span {
  display: block;
  color: #64748b;
  font-size: 12px;
}

.data-health-grid b {
  display: block;
  margin-top: 4px;
  color: #0f172a;
  font-size: 18px;
}

.data-health-grid .good {
  color: #047857;
}

.data-health-grid .danger {
  color: #dc2626;
}

.data-feed-panel {
  align-self: stretch;
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
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f8fafc;
}

.data-event-row b {
  color: #0f172a;
  font-size: 13px;
}

.data-event-row p {
  margin: 4px 0 0;
  color: #64748b;
  font-size: 12px;
  line-height: 1.55;
}

.data-event-row time {
  color: #64748b;
  font-size: 12px;
  white-space: nowrap;
}

@media (max-width: 900px) {
  .data-board {
    gap: 12px;
  }

  .data-command-center {
    grid-template-columns: minmax(0, 1fr);
    padding: 16px;
  }

  .data-status-ribbon,
  .data-metric-rail,
  .data-health-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .data-workbench {
    grid-template-columns: minmax(0, 1fr);
  }

  .data-panel,
  .data-panel-wide {
    grid-column: span 1;
  }

  .data-command-meta,
  .data-status-ribbon div,
  .data-panel-head,
  .data-event-row {
    grid-template-columns: minmax(0, 1fr);
  }

  .data-command-meta,
  .data-panel-head {
    align-items: flex-start;
    justify-content: flex-start;
  }

  .data-event-row time {
    white-space: normal;
  }
}
</style>
