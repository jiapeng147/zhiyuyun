<template>
  <div class="dashboard-page dashboard-admin">
    <div v-if="error" class="dashboard-alert error">
      <span>{{ error }}</span>
      <n-button size="small" tertiary :loading="reloading" @click="reloadData">
        {{ reloading ? '重试中' : '重试' }}
      </n-button>
    </div>

    <section class="dashboard-hero-grid">
      <n-card class="dashboard-welcome-card" :bordered="false">
        <div class="welcome-main">
          <n-tag size="small" type="success" :bordered="false">运营工作台</n-tag>
          <h2>今日运营概览</h2>
          <p>{{ guideLeadText }}</p>
          <n-space :size="8" class="welcome-actions">
            <n-button type="primary" size="small" @click="emit('navigate', 'accounts')">账号接入</n-button>
            <n-button size="small" @click="emit('navigate', 'products')">商品管理</n-button>
            <n-button size="small" @click="emit('navigate', 'data')">数据面板</n-button>
            <n-button size="small" tertiary :loading="reloading" @click="reloadData">刷新</n-button>
          </n-space>
        </div>
        <div class="welcome-side">
          <div class="health-card">
            <strong :class="statusSummaryClass">{{ statusSummaryText }}</strong>
            <span>最后刷新 {{ lastLoaded }}</span>
          </div>
          <div class="health-mini-grid">
            <div v-for="item in healthSummary" :key="item.key" class="health-mini">
              <b>{{ item.value }}</b>
              <span>{{ item.label }}</span>
            </div>
          </div>
        </div>
      </n-card>

      <n-card class="dashboard-banner-card" :bordered="false">
        <section v-if="totalSlides > 0" class="dashboard-carousel">
          <div class="dashboard-carousel-viewport">
            <div class="dashboard-carousel-track" :style="{ transform: `translateX(-${currentSlide * 100}%)` }">
              <article
                v-for="(slide, index) in carouselSlides"
                :key="slide.coverId || slide.id || index"
                :class="['dashboard-carousel-slide', { clickable: !!slide.linkUrl }]"
                @click="clickCarousel(slide)"
              >
                <img
                  class="dashboard-carousel-image"
                  :src="slide.imageUrl"
                  :alt="slide.title || `轮播图 ${index + 1}`"
                  decoding="async"
                  :fetchpriority="index === 0 ? 'high' : 'low'"
                  loading="eager"
                />
              </article>
            </div>
          </div>

          <button class="dashboard-carousel-arrow dashboard-carousel-prev" type="button" :disabled="totalSlides <= 1" aria-label="上一张" @click="prevSlide">
            ‹
          </button>
          <button class="dashboard-carousel-arrow dashboard-carousel-next" type="button" :disabled="totalSlides <= 1" aria-label="下一张" @click="nextSlide">
            ›
          </button>

          <div class="dashboard-carousel-dots">
            <button
              v-for="(_, index) in totalSlides"
              :key="`dot-${index}`"
              type="button"
              :aria-label="`切换到第 ${index + 1} 张`"
              :class="['dashboard-carousel-dot', { active: currentSlide === index }]"
              @click="goToSlide(index)"
            ></button>
          </div>
        </section>
        <div v-else class="banner-empty">
          <strong>暂无运营横幅</strong>
          <span>已保留广告服务状态，不展示占位图片。</span>
        </div>
      </n-card>
    </section>

    <section class="metric-grid">
      <n-card
        v-for="item in overviewMetrics"
        :key="item.key"
        class="dashboard-v4-metric-card"
        :class="`tone-${item.tone}`"
        :bordered="false"
      >
        <div class="dashboard-v4-metric-head">
          <span class="dashboard-v4-metric-icon"><Icon :name="item.icon" /></span>
          <n-tag size="small" :type="item.tagType" :bordered="false">{{ item.state }}</n-tag>
        </div>
        <n-statistic :label="item.label" :value="item.value">
          <template #suffix>{{ item.suffix }}</template>
        </n-statistic>
        <p>{{ item.helper }}</p>
      </n-card>
    </section>

    <section class="dashboard-content-grid">
      <main class="dashboard-main">
        <n-card title="业务进度" class="dashboard-card" :bordered="false">
          <div class="progress-grid">
            <button
              v-for="item in workProgress"
              :key="item.key"
              type="button"
              class="progress-item"
              @click="goFeature(item)"
            >
              <div class="progress-item-head">
                <span class="progress-icon"><Icon :name="item.icon" /></span>
                <div>
                  <strong>{{ item.label }}</strong>
                  <span>{{ item.detail }}</span>
                </div>
              </div>
              <n-progress
                type="line"
                :percentage="item.percent"
                :height="6"
                :show-indicator="false"
                :color="item.color"
                rail-color="#edf2f7"
              />
            </button>
          </div>
        </n-card>

        <n-card title="常用入口" class="dashboard-card" :bordered="false">
          <div class="shortcut-grid">
            <button
              v-for="item in primaryShortcuts"
              :key="item.t"
              type="button"
              class="shortcut-card"
              @click="goFeature(item)"
            >
              <span :class="['shortcut-icon', item.c]"><Icon :name="item.i" /></span>
              <strong>{{ item.t }}</strong>
              <span>{{ item.d }}</span>
            </button>
          </div>
        </n-card>

        <n-card title="实时事件" class="dashboard-card" :bordered="false">
          <n-data-table
            v-if="realtimeRows.length"
            size="small"
            :columns="realtimeColumns"
            :data="realtimeRows"
            :bordered="false"
            :single-line="false"
            :pagination="false"
          />
          <n-empty v-else size="small" description="暂无实时事件" />
        </n-card>

        <n-card title="功能矩阵" class="dashboard-card" :bordered="false">
          <div class="dashboard-v4-feature-grid">
            <button v-for="item in features" :key="item.t" type="button" class="dashboard-v4-feature-card" @click="goFeature(item)">
              <span :class="['dashboard-v4-feature-icon', item.c]"><Icon :name="item.i" /></span>
              <span class="dashboard-v4-feature-text">
                <strong>{{ item.t }}</strong>
                <small>{{ item.d }}</small>
              </span>
              <em>{{ item.targetLabel }}</em>
            </button>
          </div>
        </n-card>
      </main>

      <aside class="dashboard-side">
        <n-card title="待办建议" class="dashboard-card side-panel" :bordered="false">
          <div class="todo-list">
            <button v-for="item in guides" :key="item.title" type="button" class="todo-item" @click="goFeature(item)">
              <span :class="['todo-state', item.state]">{{ item.stateText }}</span>
              <strong>{{ item.title }}</strong>
              <small>{{ item.desc }}</small>
            </button>
          </div>
        </n-card>

        <n-card title="系统状态" class="dashboard-card side-panel" :bordered="false">
          <div class="dashboard-v4-status-list">
            <div v-for="item in systemStatus" :key="item.id || item.label" class="dashboard-v4-status-row" :title="item.message || ''">
              <span><i :class="['dashboard-v4-status-dot', { offline: item.ok === false, unknown: item.ok == null }]"></i>{{ item.label }}</span>
              <strong :class="item.ok === true ? 'status-ok' : (item.ok === false ? 'status-bad' : 'status-unknown')">
                {{ item.ok === true ? '正常' : (item.ok === false ? '异常' : '未知') }}
              </strong>
            </div>
          </div>
        </n-card>

        <n-card title="最近通知" class="dashboard-card side-panel" :bordered="false">
          <template #header-extra>
            <n-button text size="small" @click="emit('navigate', 'messages')">查看全部</n-button>
          </template>
          <div v-if="notificationsAvailable === false" class="side-empty" role="status">
            <strong>通知服务暂不可用</strong>
            <span>当前无法确认最近通知。</span>
          </div>
          <n-data-table
            v-else-if="notificationRows.length"
            size="small"
            :columns="notificationColumns"
            :data="notificationRows"
            :bordered="false"
            :single-line="false"
            :pagination="false"
          />
          <n-empty v-else size="small" description="暂无通知" />
        </n-card>

        <n-card title="广告合作" class="dashboard-card side-panel ad-side-panel" :bordered="false">
          <template #header-extra>
            <n-button
              text
              size="small"
              :disabled="adsAvailable !== true"
              :title="adsAvailable === false ? adsUnavailableMessage : ''"
              @click="emit('navigate', 'ad-application')"
            >
              申请投放
            </n-button>
          </template>
          <div v-if="adsAvailable === false" class="side-empty" role="status">
            <strong>广告商业服务不可用</strong>
            <span>{{ adsUnavailableMessage }}</span>
          </div>
          <div v-else-if="adsAvailable === null" class="side-empty" role="status">
            <strong>正在确认广告服务</strong>
            <span>确认真实商业服务可用前，不展示广告或投放入口。</span>
          </div>
          <div v-if="activeTextAds.length" class="ad-text-list">
            <button
              v-for="item in activeTextAds"
              :key="item.id || item.title"
              type="button"
              class="ad-text-item"
              @click="openTextAd(item)"
            >
              <div class="ad-text-head">
                <strong>{{ item.title }}</strong>
                <i v-if="item.badge">{{ item.badge }}</i>
              </div>
              <p v-if="item.summary">{{ item.summary }}</p>
            </button>
          </div>
          <div v-else-if="adsAvailable === true" class="side-empty">
            <strong>暂无可展示广告</strong>
            <span>商业服务当前没有返回可展示的文字广告。</span>
          </div>
        </n-card>
      </aside>
    </section>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { NButton, NCard, NDataTable, NEmpty, NProgress, NSpace, NStatistic, NTag } from 'naive-ui'
import Icon from '../components/Icon.vue'
import { getCarouselList } from '../api/carousel'
import { getTextAds } from '../api/ads.js'
import {
  buildOptionalAdUnavailableMessage,
  resolveOptionalAdSnapshot
} from './dashboard/optional-ad-snapshot.js'
import { shortText, timeText } from '../utils/format.js'
import { getNavigationNotifications, getNavigationOverview, getNavigationSystemStatus } from '../api/navigation.js'
import { openExternalUrl } from '../utils/externalUrl.js'

const emit = defineEmits(['navigate'])

const carousels = ref([])
const currentSlide = ref(0)
const error = ref('')
const reloading = ref(false)
async function reloadData() {
  reloading.value = true
  try {
    await loadData()
  } catch (e) {
    error.value = `加载失败：${e.message || '网络异常'}，请检查后重试`
  } finally {
    reloading.value = false
  }
}
const notifications = ref([])
const notificationsAvailable = ref(null)
const realtimeEvents = ref([])
const textAds = ref([])
const adsAvailable = ref(null)
const adsUnavailableMessage = ref('当前不展示占位广告，配置并接通真实商业桥后才能申请投放。')
const lastLoaded = ref('-')
let autoTimer = null
const defaultOverview = {
  accountCount: 0,
  goodsCount: 0,
  todayOrderCount: 0,
  messageCount: 0,
  pendingCount: 0
}
const overview = ref({ ...defaultOverview })
const overviewAvailable = ref(false)
const fallbackSystemStatus = [
  { id: 'api', label: 'API服务', ok: null },
  { id: 'ws', label: 'WebSocket服务', ok: null },
  { id: 'db', label: '数据库服务', ok: null },
  { id: 'storage', label: '文件存储', ok: null }
]

const systemStatus = ref(fallbackSystemStatus.map(item => ({ ...item })))

const displaySlides = computed(() => {
  return carousels.value
    .filter(item => item?.enabled !== false)
    .sort((a, b) => (a?.sortOrder ?? 0) - (b?.sortOrder ?? 0))
    .flatMap(item => {
      const coverItems = Array.isArray(item.coverItems) && item.coverItems.length
        ? item.coverItems
        : [{
            id: `${item.id || 'legacy'}-0`,
            imageUrl: item.imageUrl || '',
            linkUrl: item.linkUrl || '',
            title: item.title || '',
            description: item.description || '',
            enabled: item.enabled !== false,
            sortOrder: 0
          }]
      return coverItems
        .filter(cover => cover?.enabled !== false && cover?.imageUrl)
        .sort((a, b) => (a?.sortOrder ?? 0) - (b?.sortOrder ?? 0))
        .map((cover, index) => ({
          ...item,
          ...cover,
          coverId: cover.id || `${item.id || 'carousel'}-${index}`,
          title: cover.title || item.title || '',
          description: cover.description || item.description || '',
          imageUrl: cover.imageUrl || item.imageUrl || '',
          linkUrl: cover.linkUrl || item.linkUrl || ''
        }))
    })
})

const carouselSlides = computed(() => {
  return displaySlides.value
    .map(slide => ({
      ...slide,
      imageUrl: resolveCarouselImage(slide?.imageUrl)
    }))
    .filter(slide => slide.imageUrl)
})

const totalSlides = computed(() => carouselSlides.value.length)
const activeTextAds = computed(() => {
  return textAds.value
    .filter(item => item?.enabled !== false && String(item?.title || '').trim())
    .sort((a, b) => (a?.sortOrder ?? 0) - (b?.sortOrder ?? 0))
    .slice(0, 10)
})

function toCount(value) {
  const number = Number(value)
  return Number.isFinite(number) ? number : 0
}

const overviewMetrics = computed(() => {
  const {
    accountCount,
    goodsCount,
    todayOrderCount,
    messageCount
  } = overview.value
  const availableState = overviewAvailable.value ? '已同步' : '待确认'
  return [
    {
      key: 'accounts',
      label: '店铺账号',
      value: toCount(accountCount),
      suffix: '个',
      icon: 'users',
      tone: 'blue',
      tagType: accountCount > 0 ? 'success' : 'warning',
      state: accountCount > 0 ? availableState : '待接入',
      helper: accountCount > 0 ? '账号授权与连接状态可继续巡检' : '先完成账号接入'
    },
    {
      key: 'goods',
      label: '商品数量',
      value: toCount(goodsCount),
      suffix: '件',
      icon: 'product',
      tone: 'green',
      tagType: goodsCount > 0 ? 'success' : 'warning',
      state: goodsCount > 0 ? availableState : '待同步',
      helper: goodsCount > 0 ? '商品数据已进入运营视图' : '同步或发布商品后展示'
    },
    {
      key: 'orders',
      label: '今日订单',
      value: toCount(todayOrderCount),
      suffix: '笔',
      icon: 'record',
      tone: 'orange',
      tagType: todayOrderCount > 0 ? 'success' : 'default',
      state: overviewAvailable.value ? '今日' : '待确认',
      helper: todayOrderCount > 0 ? '关注履约与发货进度' : '今日暂未产生订单'
    },
    {
      key: 'messages',
      label: '消息会话',
      value: toCount(messageCount),
      suffix: '条',
      icon: 'message',
      tone: 'purple',
      tagType: messageCount > 0 ? 'info' : 'default',
      state: overviewAvailable.value ? '累计' : '待确认',
      helper: messageCount > 0 ? '可进入在线消息继续处理' : '暂无可展示会话'
    }
  ]
})

const healthSummary = computed(() => [
  { key: 'ok', label: '正常服务', value: systemStatus.value.filter(item => item.ok === true).length },
  { key: 'bad', label: '异常服务', value: abnormalStatusCount.value },
  { key: 'unknown', label: '待确认', value: unknownStatusCount.value },
  { key: 'notice', label: '通知', value: notifications.value.length }
])

const workProgress = computed(() => {
  const { accountCount, goodsCount, todayOrderCount, messageCount, pendingCount } = overview.value
  const hasOverview = overviewAvailable.value
  return [
    {
      key: 'account',
      label: '账号接入',
      detail: accountCount > 0 ? `${accountCount} 个账号已接入` : '等待账号授权',
      percent: hasOverview ? (accountCount > 0 ? 100 : 12) : 0,
      color: '#2080f0',
      icon: 'users',
      to: 'accounts'
    },
    {
      key: 'goods',
      label: '商品运营',
      detail: goodsCount > 0 ? `${goodsCount} 件商品可管理` : '等待商品同步',
      percent: hasOverview ? (goodsCount > 0 ? 100 : (accountCount > 0 ? 42 : 8)) : 0,
      color: '#18a058',
      icon: 'product',
      to: 'products'
    },
    {
      key: 'orders',
      label: '订单履约',
      detail: pendingCount > 0 ? `${pendingCount} 个待处理任务` : `${todayOrderCount} 笔今日订单`,
      percent: hasOverview ? (pendingCount > 0 ? 68 : (todayOrderCount > 0 ? 88 : 35)) : 0,
      color: pendingCount > 0 ? '#f0a020' : '#18a058',
      icon: 'record',
      to: pendingCount > 0 ? 'orders' : 'auto-delivery'
    },
    {
      key: 'message',
      label: '消息处理',
      detail: messageCount > 0 ? `${messageCount} 条会话记录` : '等待实时消息',
      percent: hasOverview ? (messageCount > 0 ? 78 : 22) : 0,
      color: '#7c3aed',
      icon: 'chat',
      to: 'messages'
    }
  ]
})

const realtimeRows = computed(() => realtimeEvents.value.map((item, index) => ({
  key: item.id || `rt-${index}`,
  type: item.type || '实时事件',
  text: item.text || '-',
  time: item.time || '--:--:--'
})))

const notificationRows = computed(() => notifications.value.map((item, index) => ({
  key: item.id || `notice-${index}`,
  title: item.title || item.typeLabel || '通知',
  type: item.typeLabel,
  status: item.isUnread ? '未读' : '已读',
  time: item.time || '',
  text: item.text || '-'
})))

const realtimeColumns = [
  { title: '类型', key: 'type', width: 98, ellipsis: { tooltip: true } },
  { title: '内容', key: 'text', ellipsis: { tooltip: true } },
  { title: '时间', key: 'time', width: 96 }
]

const notificationColumns = [
  { title: '标题', key: 'title', ellipsis: { tooltip: true } },
  { title: '状态', key: 'status', width: 62 },
  { title: '时间', key: 'time', width: 82 }
]

const abnormalStatusCount = computed(() => systemStatus.value.filter(item => item.ok === false).length)
const unknownStatusCount = computed(() => systemStatus.value.filter(item => item.ok == null).length)
const statusSummaryText = computed(() => {
  if (abnormalStatusCount.value > 0) return `${abnormalStatusCount.value} 个服务需关注`
  if (unknownStatusCount.value > 0) return '服务状态待确认'
  if (error.value) return '导航数据加载异常'
  return '已探测服务均正常'
})
const statusSummaryClass = computed(() => {
  if (abnormalStatusCount.value > 0 || error.value) return 'status-error'
  if (unknownStatusCount.value > 0) return 'status-unknown'
  return 'status-success'
})
const guideLeadText = computed(() => {
  if (!overviewAvailable.value) return '导航概览暂不可用，当前无法确认账号、商品与待处理记录状态。'
  const { accountCount, goodsCount, pendingCount } = overview.value
  if (accountCount === 0) return '首次使用建议先添加店铺账号并完成授权，再继续配置商品与自动化功能。'
  if (goodsCount === 0) return `当前已接入 ${accountCount} 个账号，下一步建议完善商品信息与发布流程。`
  if (pendingCount > 0) return `当前有 ${pendingCount} 个待处理任务，建议优先跟进订单履约和自动化发货配置。`
  return `当前已接入 ${accountCount} 个账号、同步 ${goodsCount} 个商品，可以继续优化自动化和消息处理效率。`
})
const guides = computed(() => {
  if (!overviewAvailable.value) {
    return [
      {
        title: '连接店铺账号',
        desc: '当前无法确认账号接入状态，请恢复导航概览服务后重试。',
        to: 'accounts',
        state: 'unknown',
        stateText: '状态未知'
      },
      {
        title: '完善商品与订单配置',
        desc: '当前无法确认商品与待处理记录，请恢复导航概览服务后重试。',
        to: 'products',
        state: 'unknown',
        stateText: '状态未知'
      }
    ]
  }
  const { accountCount, goodsCount, messageCount, pendingCount } = overview.value
  return [
    {
      title: '连接店铺账号',
      desc: accountCount > 0
        ? `已接入 ${accountCount} 个账号，可继续检查授权与在线状态。`
        : '先添加店铺账号并完成授权，后续商品、订单与消息功能才会正常联动。',
      to: 'accounts',
      state: accountCount > 0 ? 'done' : 'todo',
      stateText: accountCount > 0 ? '已完成' : '待开始'
    },
    {
      title: '完善商品与订单配置',
      desc: goodsCount > 0
        ? pendingCount > 0
          ? `当前已同步 ${goodsCount} 个商品，另有 ${pendingCount} 个待处理任务需要跟进。`
          : `当前已同步 ${goodsCount} 个商品，可继续检查发布、库存与订单流程。`
        : '建议优先进入商品管理完善商品信息，再联动订单与自动发货配置。',
      to: goodsCount > 0 ? 'orders' : 'products',
      state: goodsCount > 0 ? (pendingCount > 0 ? 'progress' : 'done') : 'todo',
      stateText: goodsCount > 0 ? (pendingCount > 0 ? '处理中' : '已完成') : '待开始'
    },
    {
      title: '开启自动化与消息联动',
      desc: messageCount > 0
        ? `已有 ${messageCount} 条会话数据，可继续配置自动回复、通知策略和数据统计。`
        : '进入自动发货、定时任务或数据面板，逐步建立自动化处理链路。',
      to: messageCount > 0 ? 'messages' : 'auto-delivery',
      state: messageCount > 0 || pendingCount > 0 ? 'progress' : 'suggest',
      stateText: messageCount > 0 || pendingCount > 0 ? '进行中' : '建议体验'
    }
  ]
})
function resolveCarouselImage(imageUrl) {
  const value = String(imageUrl || '').trim()
  if (!value) return ''
  if (/^(https?:)?\/\//.test(value) || value.startsWith('/')) return value
  return `/${value.replace(/^\/+/, '')}`
}

function nextSlide() {
  if (totalSlides.value <= 1) return
  currentSlide.value = (currentSlide.value + 1) % totalSlides.value
  restartAuto()
}

function prevSlide() {
  if (totalSlides.value <= 1) return
  currentSlide.value = (currentSlide.value - 1 + totalSlides.value) % totalSlides.value
  restartAuto()
}

function goToSlide(index) {
  if (index < 0 || index >= totalSlides.value) return
  currentSlide.value = index
  restartAuto()
}

function restartAuto() {
  if (autoTimer) clearInterval(autoTimer)
  if (totalSlides.value <= 1) return
  autoTimer = setInterval(() => {
    currentSlide.value = (currentSlide.value + 1) % totalSlides.value
  }, 5000)
}

function toArray(data) {
  if (Array.isArray(data)) return data
  if (Array.isArray(data?.records)) return data.records
  if (Array.isArray(data?.list)) return data.list
  return []
}

function formatNoticeTime(value) {
  const text = timeText(value)
  if (!text || text === '-') return ''
  const normalized = String(text).replace('T', ' ')
  if (!normalized.includes(' ')) return normalized
  const [date, clock = ''] = normalized.split(' ')
  return `${date.slice(5)} ${clock.slice(0, 5)}`
}

function formatEventTime(value) {
  const text = timeText(value)
  if (!text || text === '-') return '--:--:--'
  const normalized = String(text).replace('T', ' ')
  return normalized.includes(' ') ? normalized.split(' ').pop().slice(0, 8) : normalized.slice(-8)
}

function mapNoticeType(type) {
  switch (String(type || '').toLowerCase()) {
    case 'system':
      return { label: '系统', className: 'system' }
    case 'warning':
      return { label: '预警', className: 'warning' }
    case 'info':
      return { label: '通知', className: 'info' }
    default:
      return { label: '消息', className: 'info' }
  }
}

function normalizeNotification(item, index) {
  const type = mapNoticeType(item?.type)
  return {
    id: item?.id || `notice-${index}`,
    title: item?.title || type.label,
    text: shortText(item?.content || item?.message || '-', 72),
    time: formatNoticeTime(item?.createdTime || item?.time || item?.createdAt),
    typeLabel: type.label,
    typeClass: type.className,
    isUnread: Number(item?.status ?? 0) === 0
  }
}

function normalizeSystemStatus(item, index) {
  const rawStatus = item?.status
  const ok = rawStatus === null || rawStatus === undefined || rawStatus === ''
    ? null
    : Number(rawStatus) === 1
  return {
    id: item?.id || `status-${index}`,
    label: item?.nodeName || fallbackSystemStatus[index]?.label || `服务节点 ${index + 1}`,
    ok,
    message: item?.message || ''
  }
}

function pushRealtimeEvent(eventItem) {
  if (!eventItem?.text) return
  const current = realtimeEvents.value.filter(item => item?.id !== eventItem.id)
  realtimeEvents.value = [eventItem, ...current].slice(0, 5)
}

function buildRealtimeSeedEvents() {
  const seedTime = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  const seeded = []
  const { accountCount, goodsCount, todayOrderCount, pendingCount } = overview.value
  if (accountCount > 0 || goodsCount > 0 || todayOrderCount > 0) {
    seeded.push({
      id: 'seed-overview',
      type: '数据同步',
      text: `已同步 ${accountCount} 个账号、${goodsCount} 个商品，今日订单 ${todayOrderCount} 笔。`,
      time: seedTime
    })
  }
  if (pendingCount > 0) {
    seeded.push({
      id: 'seed-pending',
      type: '待处理提醒',
      text: `当前有 ${pendingCount} 个待处理任务，建议优先跟进订单与发货流程。`,
      time: seedTime
    })
  }
  if (unknownStatusCount.value === 0) {
    seeded.push({
      id: 'seed-status',
      type: abnormalStatusCount.value > 0 ? '服务预警' : '服务状态',
      text: abnormalStatusCount.value > 0
        ? `${abnormalStatusCount.value} 个服务状态异常，请留意右侧系统状态面板。`
        : '状态接口确认已探测的服务均正常。',
      time: seedTime
    })
  }
  if (notifications.value.length > 0) {
    const latestNotice = notifications.value[0]
    seeded.push({
      id: `seed-notice-${latestNotice.id}`,
      type: '通知同步',
      text: `最近通知：${shortText(latestNotice.title || latestNotice.text, 30)}`,
      time: latestNotice.time || seedTime
    })
  }
  return seeded.slice(0, 5)
}

function ensureRealtimeSeedEvents() {
  const seeded = buildRealtimeSeedEvents()
  if (seeded.length === 0) return
  if (realtimeEvents.value.length === 0) {
    realtimeEvents.value = seeded
    return
  }
  const merged = [...realtimeEvents.value]
  for (const item of seeded) {
    if (merged.length >= 5) break
    if (!merged.some(eventItem => eventItem.id === item.id)) {
      merged.push(item)
    }
  }
  realtimeEvents.value = merged.slice(0, 5)
}

async function loadData() {
  error.value = ''
  const failures = []
  const [carouselRes, overviewRes, notificationsRes, systemStatusRes, textAdsRes] = await Promise.allSettled([
    getCarouselList(),
    getNavigationOverview(),
    getNavigationNotifications({ limit: 5 }),
    getNavigationSystemStatus(),
    getTextAds()
  ])

  const carouselSnapshot = resolveOptionalAdSnapshot(carousels.value, carouselRes)
  carousels.value = carouselSnapshot.items

  if (overviewRes.status === 'fulfilled' && overviewRes.value?.data) {
    overviewAvailable.value = true
    overview.value = {
      ...defaultOverview,
      ...overviewRes.value.data
    }
  } else {
    overviewAvailable.value = false
    overview.value = { ...defaultOverview }
    failures.push('overview')
  }

  if (notificationsRes.status === 'fulfilled') {
    notificationsAvailable.value = true
    notifications.value = toArray(notificationsRes.value?.data)
      .slice(0, 5)
      .map((item, index) => normalizeNotification(item, index))
  } else {
    notificationsAvailable.value = false
    notifications.value = []
    failures.push('notifications')
  }

  if (systemStatusRes.status === 'fulfilled') {
    const list = toArray(systemStatusRes.value?.data).map((item, index) => normalizeSystemStatus(item, index))
    systemStatus.value = list.length ? list : fallbackSystemStatus.map(item => ({ ...item }))
  } else {
    systemStatus.value = fallbackSystemStatus.map(item => ({ ...item }))
    failures.push('system-status')
  }

  const textAdsSnapshot = resolveOptionalAdSnapshot(textAds.value, textAdsRes)
  textAds.value = textAdsSnapshot.items
  if (textAdsSnapshot.refreshed) {
    adsAvailable.value = true
    adsUnavailableMessage.value = ''
  } else {
    adsAvailable.value = false
    const status = Number(textAdsRes.reason?.status || textAdsRes.reason?.code || 0)
    adsUnavailableMessage.value = buildOptionalAdUnavailableMessage(status, {
      hasSnapshot: textAds.value.length > 0
    })
  }

  if (failures.length > 0) {
    error.value = '部分导航数据加载失败'
  }
  ensureRealtimeSeedEvents()
  lastLoaded.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  if (currentSlide.value >= totalSlides.value) currentSlide.value = 0
  restartAuto()
}

function clickCarousel(item) {
  if (item?.linkUrl) {
    if (!openExternalUrl(item.linkUrl)) error.value = '广告链接无效或使用了不安全的协议'
  }
}

function openTextAd(item) {
  const link = String(item?.linkUrl || '').trim()
  if (!link) {
    emit('navigate', 'ad-application')
    return
  }
  if (link.startsWith('#/')) {
    emit('navigate', link.replace('#/', ''))
    return
  }
  if (link.startsWith('/#/')) {
    emit('navigate', link.replace('/#/', ''))
    return
  }
  if (!openExternalUrl(link)) error.value = '广告链接无效或使用了不安全的协议'
}

function onSse(event) {
  const detail = event.detail || {}
  pushRealtimeEvent({
    id: detail.id ? `sse-${detail.id}` : `sse-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    type: detail.title || detail.name || formatRealtimeType(detail.type || detail.event),
    text: shortText(detail.message || detail.content || detail.description || JSON.stringify(detail), 80),
    time: formatEventTime(detail.createdTime || detail.time || detail.timestamp || Date.now())
  })
}

function formatRealtimeType(type) {
  switch (String(type || '').toLowerCase()) {
    case 'order':
      return '订单事件'
    case 'message':
      return '消息事件'
    case 'warning':
      return '预警事件'
    case 'workflow':
      return '工作流事件'
    case 'delivery':
      return '发货事件'
    case 'system':
      return '系统事件'
    default:
      return '实时事件'
  }
}

const quickStarts = [
  { t: '添加账号', d: '添加店铺账号，开始管理您的店铺', i: 'users', c: 'dash-tone-blue', to: 'accounts' },
  { t: 'WebSocket连接', d: '建立实时连接，接收消息和数据', i: 'link', c: 'dash-tone-purple', to: 'connections' },
  { t: '商品管理', d: '发布管理商品，优化商品信息', i: 'product', c: 'dash-tone-green', to: 'products' },
  { t: '自动化发货', d: '设置发货规则并查看实际执行结果', i: 'truck', c: 'dash-tone-orange', to: 'auto-delivery' }
]

const features = [
  { t: '多账号管理', d: '集中查看账号、授权与连接状态', i: 'users', c: 'dash-tone-purple', to: 'accounts', targetLabel: '管理账号' },
  { t: '商品同步', d: '按需同步商品；发布与改价结果以平台确认为准', i: 'product', c: 'dash-tone-green', to: 'products', targetLabel: '商品管理' },
  { t: '订单管理', d: '按需同步订单并查看后端实际记录状态', i: 'record', c: 'dash-tone-blue', to: 'orders', targetLabel: '订单管理' },
  { t: '自动发货', d: '按已配置规则处理发货，异常与未知结果需人工复核', i: 'truck', c: 'dash-tone-orange', to: 'auto-delivery', targetLabel: '自动化' },
  { t: '广告合作', d: '查看商业服务返回的真实套餐；未配置时页面会明确禁用提交与支付。', i: 'opportunity', c: 'dash-tone-purple', to: 'ad-application', targetLabel: '广告申请' },
  { t: '系统设置', d: '集中管理通用模型、向量模型、RAG 知识库与高德地图配置。', i: 'settings', c: 'dash-tone-cyan', to: 'settings-system', targetLabel: '系统配置' },
  { t: '卡密仓库', d: '管理卡密资源，安全存储和使用', i: 'key', c: 'dash-tone-orange', to: 'card-warehouse', targetLabel: '卡密仓库' },
  { t: '数据统计', d: '查看订单、发货与自动回复的实际汇总', i: 'data', c: 'dash-tone-blue', to: 'data', targetLabel: '数据面板' }
]

const primaryShortcuts = computed(() => {
  const extra = features.filter(item => ['订单管理', '数据统计', '系统设置', '卡密仓库'].includes(item.t))
  return [...quickStarts, ...extra]
})

function goFeature(item) {
  if (item?.to) emit('navigate', item.to)
}

onMounted(() => {
  window.addEventListener('xya-sse-event', onSse)
  loadData()
})

onBeforeUnmount(() => {
  window.removeEventListener('xya-sse-event', onSse)
  if (autoTimer) clearInterval(autoTimer)
})
</script>

<style scoped>
/* Stage 3 dashboard shell */
.dashboard-admin {
  max-width: 100%;
  display: grid;
  gap: 16px;
}

.dashboard-admin :deep(.n-card) {
  border-radius: 6px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, .04);
}

.dashboard-admin :deep(.n-card__content) {
  min-width: 0;
}

.dashboard-alert {
  min-height: 42px;
  padding: 8px 12px;
  border: 1px solid #f3d1d8;
  border-radius: 6px;
  background: #fff7f8;
  color: #d03050;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 13px;
}

.dashboard-hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(340px, .85fr);
  gap: 16px;
  align-items: stretch;
}

.dashboard-welcome-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
}

.dashboard-welcome-card :deep(.n-card__content) {
  min-height: 224px;
  padding: 22px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 250px;
  gap: 20px;
  align-items: stretch;
}

.welcome-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.welcome-main h2 {
  margin: 14px 0 8px;
  color: #111827;
  font-size: 24px;
  font-weight: 650;
  line-height: 1.25;
}

.welcome-main p {
  max-width: 760px;
  margin: 0;
  color: #4b5563;
  font-size: 14px;
  line-height: 1.75;
}

.welcome-actions {
  margin-top: 20px;
}

.welcome-side {
  min-width: 0;
  display: grid;
  grid-template-rows: 1fr auto;
  gap: 10px;
}

.health-card {
  min-height: 112px;
  padding: 16px;
  border: 1px solid #edf0f5;
  border-radius: 6px;
  background: #f8fafc;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 8px;
}

.health-card strong {
  font-size: 17px;
  font-weight: 650;
}

.health-card span {
  color: #64748b;
  font-size: 12px;
}

.health-mini-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.health-mini {
  min-width: 0;
  padding: 10px 8px;
  border: 1px solid #edf0f5;
  border-radius: 6px;
  background: #fff;
  text-align: center;
}

.health-mini b {
  display: block;
  color: #111827;
  font-size: 16px;
  line-height: 1.2;
}

.health-mini span {
  display: block;
  margin-top: 4px;
  color: #64748b;
  font-size: 11px;
  white-space: nowrap;
}

.dashboard-banner-card {
  border: 1px solid #e5e7eb;
  background: #fff;
}

.dashboard-banner-card :deep(.n-card__content) {
  height: 100%;
  padding: 10px;
}

.dashboard-admin .dashboard-carousel {
  height: 100%;
  min-height: 224px;
  padding: 0;
  border: 0;
  border-radius: 6px;
  background: #f8fafc;
  box-shadow: none;
  position: relative;
  overflow: hidden;
}

.dashboard-admin .dashboard-carousel-viewport {
  height: 100%;
  min-height: 224px;
  aspect-ratio: auto;
  border-radius: 6px;
  overflow: hidden;
}

.dashboard-admin .dashboard-carousel-track,
.dashboard-admin .dashboard-carousel-slide,
.dashboard-admin .dashboard-carousel-image {
  height: 100%;
}

.dashboard-admin .dashboard-carousel-track {
  display: flex;
  transition: transform 0.55s cubic-bezier(0.22, 0.61, 0.36, 1);
}

.dashboard-admin .dashboard-carousel-slide {
  min-width: 100%;
  position: relative;
  cursor: default;
}

.dashboard-admin .dashboard-carousel-slide.clickable {
  cursor: pointer;
}

.dashboard-admin .dashboard-carousel-image {
  width: 100%;
  display: block;
  object-fit: cover;
  object-position: center;
}

.dashboard-admin .dashboard-carousel-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 30px;
  height: 30px;
  padding: 0;
  border: 1px solid rgba(15, 23, 42, .08);
  border-radius: 6px;
  background: rgba(255, 255, 255, .92);
  color: #111827;
  font-size: 22px;
  line-height: 1;
  box-shadow: 0 6px 16px rgba(15, 23, 42, .10);
}

.dashboard-admin .dashboard-carousel-arrow:disabled {
  opacity: .45;
  cursor: not-allowed;
}

.dashboard-admin .dashboard-carousel-prev {
  left: 10px;
}

.dashboard-admin .dashboard-carousel-next {
  right: 10px;
}

.dashboard-admin .dashboard-carousel-dots {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  bottom: 10px;
  display: flex;
  align-items: center;
  gap: 7px;
}

.dashboard-admin .dashboard-carousel-dot {
  width: 7px;
  height: 7px;
  padding: 0;
  border: 0;
  border-radius: 999px;
  background: rgba(255, 255, 255, .62);
}

.dashboard-admin .dashboard-carousel-dot.active {
  width: 20px;
  background: #18a058;
}

.banner-empty {
  height: 100%;
  min-height: 224px;
  border: 1px dashed #cbd5e1;
  border-radius: 6px;
  background: #f8fafc;
  color: #64748b;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  text-align: center;
}

.banner-empty strong {
  color: #111827;
  font-size: 15px;
}

.banner-empty span {
  font-size: 12px;
}

.dashboard-admin .metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.dashboard-v4-metric-card {
  border: 1px solid #e5e7eb;
  background: #fff;
}

.dashboard-v4-metric-card :deep(.n-card__content) {
  padding: 16px;
}

.dashboard-v4-metric-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.dashboard-v4-metric-icon {
  width: 38px;
  height: 38px;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.dashboard-v4-metric-icon :deep(.ui-icon) {
  width: 20px;
  height: 20px;
}

.tone-blue .dashboard-v4-metric-icon,
.dashboard-admin .dash-tone-blue {
  background: #eff6ff;
  color: #2563eb;
}

.tone-green .dashboard-v4-metric-icon,
.dashboard-admin .dash-tone-green {
  background: #ecfdf5;
  color: #059669;
}

.tone-orange .dashboard-v4-metric-icon,
.dashboard-admin .dash-tone-orange {
  background: #fff7ed;
  color: #ea580c;
}

.tone-purple .dashboard-v4-metric-icon,
.dashboard-admin .dash-tone-purple {
  background: #f5f3ff;
  color: #7c3aed;
}

.dashboard-admin .dash-tone-cyan {
  background: #ecfeff;
  color: #0891b2;
}

.dashboard-v4-metric-card :deep(.n-statistic .n-statistic-value) {
  color: #111827;
  font-size: 28px;
  font-weight: 700;
}

.dashboard-v4-metric-card :deep(.n-statistic .n-statistic-label) {
  color: #64748b;
  font-size: 13px;
}

.dashboard-v4-metric-card p {
  margin: 8px 0 0;
  color: #64748b;
  font-size: 12px;
  line-height: 1.55;
}

.dashboard-content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 16px;
  align-items: start;
}

.dashboard-admin .dashboard-main,
.dashboard-admin .dashboard-side {
  min-width: 0;
  display: grid;
  gap: 16px;
}

.dashboard-admin .dashboard-side {
  position: sticky;
  top: 118px;
}

.dashboard-card {
  border: 1px solid #e5e7eb;
  background: #fff;
}

.dashboard-card :deep(.n-card-header) {
  padding: 16px 16px 0;
  font-size: 15px;
  font-weight: 650;
}

.dashboard-card :deep(.n-card__content) {
  padding: 16px;
}

.progress-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.progress-item {
  min-width: 0;
  min-height: 112px;
  padding: 14px;
  border: 1px solid #edf0f5;
  border-radius: 6px;
  background: #fff;
  text-align: left;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 12px;
  cursor: pointer;
  transition: border-color .16s ease, box-shadow .16s ease, transform .16s ease;
}

.progress-item:hover,
.shortcut-card:hover,
.dashboard-v4-feature-card:hover,
.todo-item:hover,
.ad-text-item:hover {
  transform: translateY(-1px);
  border-color: rgba(24, 160, 88, .36);
  box-shadow: 0 8px 18px rgba(15, 23, 42, .08);
}

.progress-item-head {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.progress-icon,
.shortcut-icon,
.dashboard-v4-feature-icon {
  width: 34px;
  height: 34px;
  border-radius: 6px;
  flex: 0 0 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.progress-icon {
  background: #f1f5f9;
  color: #334155;
}

.progress-item strong,
.shortcut-card strong,
.dashboard-v4-feature-card strong,
.todo-item strong {
  display: block;
  color: #111827;
  font-size: 14px;
  font-weight: 650;
  line-height: 1.35;
}

.progress-item span,
.shortcut-card span,
.dashboard-v4-feature-card small,
.todo-item small {
  color: #64748b;
  font-size: 12px;
  line-height: 1.55;
}

.shortcut-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.shortcut-card {
  min-width: 0;
  min-height: 122px;
  padding: 14px;
  border: 1px solid #edf0f5;
  border-radius: 6px;
  background: #fff;
  text-align: left;
  display: grid;
  grid-template-rows: auto auto 1fr;
  gap: 8px;
  cursor: pointer;
  transition: border-color .16s ease, box-shadow .16s ease, transform .16s ease;
}

.shortcut-card > span:last-child {
  display: -webkit-box;
  overflow: hidden;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.dashboard-admin .dashboard-v4-feature-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.dashboard-admin .dashboard-v4-feature-card {
  min-height: 72px;
  padding: 12px;
  border: 1px solid #edf0f5;
  border-radius: 6px;
  background: #fff;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  text-align: left;
  cursor: pointer;
  transition: border-color .16s ease, box-shadow .16s ease, transform .16s ease;
}

.dashboard-v4-feature-text {
  min-width: 0;
}

.dashboard-v4-feature-text small {
  display: block;
  margin-top: 3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dashboard-admin .dashboard-v4-feature-card em {
  color: #18a058;
  font-size: 12px;
  font-style: normal;
  font-weight: 650;
  white-space: nowrap;
}

.dashboard-admin :deep(.n-data-table) {
  font-size: 12px;
}

.dashboard-admin :deep(.n-data-table-th) {
  background: #f8fafc;
  color: #475569;
  font-weight: 650;
}

.todo-list {
  display: grid;
  gap: 10px;
}

.todo-item {
  min-width: 0;
  padding: 12px;
  border: 1px solid #edf0f5;
  border-radius: 6px;
  background: #fff;
  text-align: left;
  display: grid;
  gap: 6px;
  cursor: pointer;
  transition: border-color .16s ease, box-shadow .16s ease, transform .16s ease;
}

.todo-state {
  width: fit-content;
  height: 22px;
  padding: 0 8px;
  border-radius: 4px;
  background: #f1f5f9;
  color: #475569;
  display: inline-flex;
  align-items: center;
  font-size: 11px;
  font-weight: 650;
}

.todo-state.done {
  background: #ecfdf5;
  color: #059669;
}

.todo-state.progress {
  background: #fff7ed;
  color: #ea580c;
}

.todo-state.todo,
.todo-state.suggest {
  background: #eff6ff;
  color: #2563eb;
}

.todo-state.unknown {
  background: #f8fafc;
  color: #64748b;
}

.dashboard-admin .dashboard-v4-status-list {
  display: grid;
}

.dashboard-admin .dashboard-v4-status-row {
  min-height: 38px;
  border-bottom: 1px solid #edf0f5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.dashboard-admin .dashboard-v4-status-row:last-child {
  border-bottom: 0;
}

.dashboard-admin .dashboard-v4-status-row span {
  color: #334155;
  font-size: 13px;
  display: inline-flex;
  align-items: center;
  min-width: 0;
}

.dashboard-admin .dashboard-v4-status-row strong {
  flex: 0 0 auto;
  font-size: 12px;
}

.dashboard-admin .dashboard-v4-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #18a058;
  display: inline-block;
  margin-right: 8px;
}

.dashboard-admin .dashboard-v4-status-dot.offline {
  background: #d03050;
}

.dashboard-admin .dashboard-v4-status-dot.unknown {
  background: #f0a020;
}

.dashboard-admin .status-ok,
.dashboard-admin .status-success {
  color: #18a058;
}

.dashboard-admin .status-bad,
.dashboard-admin .status-error {
  color: #d03050;
}

.dashboard-admin .status-unknown {
  color: #a16207;
}

.dashboard-admin .side-empty {
  padding: 10px 0;
  color: #64748b;
  font-size: 12px;
  display: grid;
  gap: 6px;
}

.dashboard-admin .side-empty strong {
  color: #111827;
  font-size: 13px;
}

.ad-text-list {
  display: grid;
  gap: 10px;
}

.dashboard-admin .ad-text-item {
  width: 100%;
  padding: 12px;
  border: 1px solid #edf0f5;
  border-radius: 6px;
  background: #fff;
  text-align: left;
  cursor: pointer;
  transition: border-color .16s ease, box-shadow .16s ease, transform .16s ease;
}

.dashboard-admin .ad-text-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.dashboard-admin .ad-text-head strong {
  min-width: 0;
  color: #111827;
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dashboard-admin .ad-text-head i {
  flex: 0 0 auto;
  height: 22px;
  padding: 0 8px;
  border-radius: 4px;
  background: #eff6ff;
  color: #2563eb;
  font-size: 11px;
  font-style: normal;
  font-weight: 650;
  display: inline-flex;
  align-items: center;
}

.dashboard-admin .ad-text-item p {
  margin: 6px 0 0;
  color: #64748b;
  font-size: 12px;
  line-height: 1.55;
}

@media (max-width: 1500px) {
  .dashboard-admin .metric-grid,
  .shortcut-grid,
  .progress-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 1200px) {
  .dashboard-hero-grid,
  .dashboard-content-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .dashboard-admin .dashboard-side {
    position: static;
  }

  .dashboard-welcome-card :deep(.n-card__content) {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 900px) {
  .dashboard-admin {
    gap: 12px;
  }

  .dashboard-hero-grid,
  .dashboard-content-grid {
    gap: 12px;
  }

  .dashboard-welcome-card :deep(.n-card__content),
  .dashboard-card :deep(.n-card__content),
  .dashboard-v4-metric-card :deep(.n-card__content) {
    padding: 14px;
  }

  .welcome-main h2 {
    font-size: 20px;
  }

  .health-mini-grid,
  .dashboard-admin .metric-grid,
  .shortcut-grid,
  .progress-grid,
  .dashboard-admin .dashboard-v4-feature-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .dashboard-admin .dashboard-carousel,
  .dashboard-admin .dashboard-carousel-viewport,
  .banner-empty {
    min-height: 150px;
  }

  .dashboard-admin .dashboard-v4-feature-card {
    grid-template-columns: auto minmax(0, 1fr);
  }

  .dashboard-admin .dashboard-v4-feature-card em {
    display: none;
  }
}
</style>
