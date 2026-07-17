<template>
  <div class="data-v4">
    <n-card class="data-v4-hero" :bordered="false">
      <div>
        <n-tag size="small" type="success" :bordered="false">运营数据</n-tag>
        <h2>数据面板</h2>
        <p>集中查看订单、发货、AI 回复和实时事件，失败区域不会用全零数据伪装正常结果。</p>
      </div>
      <n-space :size="8" align="center" wrap>
        <span class="data-v4-updated">更新时间：{{ updatedAt }}</span>
        <label class="data-v4-date" for="stats-date">统计日期</label>
        <input id="stats-date" v-model="date" class="input data-v4-date-input" type="date" aria-label="统计日期" :disabled="loading" @change="load">
        <n-button size="small" :loading="loading" @click="load">{{ loading ? '加载中...' : '刷新' }}</n-button>
      </n-space>
    </n-card>

    <div v-if="error" class="global-notice error">{{ error }}</div>

    <section class="data-v4-stats">
      <n-card v-for="item in dataStatCards" :key="item.key" class="data-v4-stat" :class="item.tone" :bordered="false">
        <span class="data-v4-stat-icon">{{ item.symbol }}</span>
        <n-statistic :label="item.title" :value="item.value" />
        <small>{{ item.change }}</small>
      </n-card>
    </section>

    <div class="data-v4-grid three">
      <n-card class="data-v4-card" :bordered="false">
        <template #header>发货成功趋势</template>
        <template #header-extra><n-tag size="small" :bordered="false">近7天</n-tag></template>
        <EmptyState v-if="!trendAvailable" icon="📊" title="趋势暂不可用" description="汇总与趋势独立加载，可点击刷新重试。" />
        <MiniLineChart v-else :values="trend.deliverySuccess" :labels="trend.dates" />
      </n-card>
      <n-card class="data-v4-card" :bordered="false">
        <template #header>发货失败趋势</template>
        <EmptyState v-if="!trendAvailable" icon="📊" title="趋势暂不可用" description="汇总与趋势独立加载，可点击刷新重试。" />
        <MiniLineChart v-else :values="trend.deliveryFail" :labels="trend.dates" />
      </n-card>
      <n-card class="data-v4-card" :bordered="false">
        <template #header>AI 回复概况</template>
        <EmptyState v-if="!dataAvailable" icon="📊" title="统计暂不可用" description="当前不会以全零数据代替查询失败。" />
        <DonutChart v-else :center="String(totalReplies)" label="AI回复" :items="replyItems" />
      </n-card>
    </div>

    <div class="data-v4-grid three">
      <n-card class="data-v4-card" :bordered="false">
        <template #header>趋势明细</template>
        <EmptyState v-if="!trendAvailable" icon="📋" title="明细暂不可用" description="趋势查询恢复后再显示。" />
        <BaseTable v-else :columns="trendCols" :rows="trendRows" />
      </n-card>
      <n-card class="data-v4-card" :bordered="false">
        <template #header>发货概况</template>
        <EmptyState v-if="!dataAvailable" icon="📦" title="发货统计暂不可用" description="不会把查询失败显示为零。" />
        <template v-else>
          <DonutChart :center="String(totalDelivery)" label="发货合计" :items="deliveryItems" />
          <div class="metric-row" style="margin-top:20px"><div class="metric-tile"><span>成功率</span><b style="color:var(--green)">{{ successRate }}</b></div><div class="metric-tile"><span>失败</span><b style="color:#ef4444">{{ stats.deliveryFailCount }}</b></div><div class="metric-tile"><span>待处理</span><b>{{ stats.pendingDeliveryCount }}</b></div></div>
        </template>
      </n-card>
      <n-card class="data-v4-card" :bordered="false">
        <template #header>最新实时事件</template>
        <EmptyState v-if="logs.length === 0" icon="📡" title="暂无实时事件" description="订单、发货、AI 回复等实时事件会在这里显示。" />
        <div v-for="n in logs" :key="n.t+n.time" class="option-line"><div><b>{{ n.t }}</b><p class="subtle" style="margin:4px 0 0">{{ n.d }}</p></div><span class="subtle">{{ n.time }}</span></div>
      </n-card>
    </div>
  </div>
</template>
<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { NButton, NCard, NSpace, NStatistic, NTag } from 'naive-ui'
import MiniLineChart from '../components/MiniLineChart.vue'; import DonutChart from '../components/DonutChart.vue'; import BaseTable from '../components/BaseTable.vue'; import EmptyState from '../components/EmptyState.vue'
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
.data-v4 {
  display: grid;
  gap: 16px;
  min-width: 0;
}

.data-v4-hero,
.data-v4-card,
.data-v4-stat {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, .04);
}

.data-v4-hero :deep(.n-card__content) {
  padding: 18px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.data-v4-hero h2 {
  margin: 12px 0 6px;
  color: #111827;
  font-size: 22px;
  font-weight: 650;
  line-height: 1.25;
}

.data-v4-hero p,
.data-v4-updated,
.data-v4-date {
  margin: 0;
  color: #64748b;
  font-size: 13px;
  line-height: 1.65;
}

.data-v4-date-input {
  max-width: 180px;
}

.data-v4-stats {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
}

.data-v4-stat :deep(.n-card__content) {
  padding: 16px;
  display: grid;
  gap: 8px;
}

.data-v4-stat-icon {
  width: 36px;
  height: 36px;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
}

.data-v4-stat.tone-blue .data-v4-stat-icon { background: #eff6ff; color: #2563eb; }
.data-v4-stat.tone-green .data-v4-stat-icon { background: #ecfdf5; color: #059669; }
.data-v4-stat.tone-orange .data-v4-stat-icon { background: #fff7ed; color: #ea580c; }
.data-v4-stat.tone-cyan .data-v4-stat-icon { background: #ecfeff; color: #0891b2; }
.data-v4-stat.tone-purple .data-v4-stat-icon { background: #f5f3ff; color: #7c3aed; }

.data-v4-stat :deep(.n-statistic .n-statistic-label) {
  color: #64748b;
  font-size: 12px;
}

.data-v4-stat :deep(.n-statistic .n-statistic-value) {
  color: #111827;
  font-size: 24px;
  font-weight: 700;
}

.data-v4-stat small {
  color: #64748b;
  font-size: 12px;
  line-height: 1.4;
}

.data-v4-grid {
  display: grid;
  gap: 16px;
}

.data-v4-grid.three {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.data-v4-card :deep(.n-card__content) {
  padding: 16px;
}

.data-v4-card :deep(.n-card-header) {
  padding: 16px 16px 0;
}

/* ===== 移动端响应式 (max-width: 900px) ===== */
@media (max-width: 900px) {
  .data-v4 {
    gap: 12px;
  }

  .data-v4-hero :deep(.n-card__content) {
    flex-direction: column;
    padding: 14px;
  }

  .data-v4-stats,
  .data-v4-grid.three {
    grid-template-columns: minmax(0, 1fr);
  }

  .data-v4-card :deep(.n-card__content) {
    padding: 12px;
  }

  /* 事件列表项：允许换行，时间另起一行 */
  .option-line {
    flex-wrap: wrap;
    gap: 6px;
    padding: 10px 0;
  }

  .option-line > div {
    flex: 1 1 100%;
    min-width: 0;
  }

  .option-line > span {
    font-size: 11px;
  }

  /* chips 标签收敛 */
  .chip {
    font-size: 11px;
  }
}
</style>
