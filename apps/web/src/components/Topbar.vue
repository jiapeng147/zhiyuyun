<template>
  <div class="topbar zy-topbar">
    <button class="zy-global-search" type="button" @click="go('data')">
      <Icon name="search" />
      <span>搜索账号、商品、订单、消息</span>
      <kbd>⌘K</kbd>
    </button>

    <div class="zy-topbar-spacer"></div>

    <span class="zy-connection-pill" :class="sseStatus">
      <i aria-hidden="true"></i>
      {{ sseLabel }}
    </span>

    <button class="top-icon bell zy-icon-button" type="button" aria-label="通知中心" @click="toggleNoticePanel">
      <span v-if="unreadCount > 0">{{ unreadCount }}</span>
      <Icon name="bell" />
    </button>

    <button class="top-icon zy-icon-button" type="button" aria-label="关于我们" title="关于我们" @click="go('settings-about')">
      <Icon name="help" />
    </button>

    <button
      class="top-icon zy-icon-button"
      type="button"
      :aria-label="isFullscreen ? '退出全屏' : '进入全屏'"
      @click="toggleFullscreen"
    >
      <Icon name="fullscreen" />
    </button>

    <div ref="userWrapEl" class="top-user-wrap zy-user-menu-wrap">
      <button class="top-user zy-top-user" type="button" :aria-expanded="menuOpen" @click="menuOpen = !menuOpen">
        <span class="avatar small avatar-img">{{ initials }}</span>
        <span class="zy-top-user-copy">
          <strong>{{ displayName }}</strong>
          <em>{{ roleLabel }}</em>
        </span>
        <b aria-hidden="true">⌄</b>
      </button>

      <div v-if="menuOpen" class="top-user-menu zy-popover-menu">
        <button type="button" @click="onProfile">个人中心</button>
        <button type="button" @click="go('settings-system')">系统设置</button>
        <button type="button" class="danger" @click="onLogout">退出登录</button>
      </div>
    </div>

    <div v-if="showNoticePanel" class="notice-panel zy-notice-panel" role="dialog" aria-label="通知中心">
      <div class="notice-panel-head">
        <div>
          <h3>通知中心</h3>
          <p>实时事件与系统提醒</p>
        </div>
        <button class="modal-close zy-icon-button" type="button" aria-label="关闭" @click="showNoticePanel = false">
          <Icon name="close" />
        </button>
      </div>

      <div class="notice-panel-body">
        <EmptyState
          v-if="recentEvents.length === 0"
          icon="∅"
          title="暂无通知"
          description="系统实时事件会在这里出现。"
        />
        <button v-for="(ev, i) in recentEvents" :key="eventKey(ev, i)" type="button" class="notice-item" @click="onNoticeClick(ev)">
          <b>{{ ev.title || ev.type || '事件' }}</b>
          <span>{{ ev.content || ev.message || '' }}</span>
          <small>{{ ev.time || '' }}</small>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import Icon from './Icon.vue'
import EmptyState from './EmptyState.vue'

const props = defineProps({
  user: { type: Object, default: () => ({}) },
  sseStatus: { type: String, default: 'disconnected' },
  unreadCount: { type: [String, Number], default: 0 },
})

const emit = defineEmits(['logout', 'open-profile-center'])

const menuOpen = ref(false)
const userWrapEl = ref(null)
function onProfile() { menuOpen.value = false; emit('open-profile-center') }
function onLogout() { menuOpen.value = false; emit('logout') }
function go(page) { location.hash = `#/${page}` }
function onDocClick(e) {
  if (menuOpen.value && userWrapEl.value && !userWrapEl.value.contains(e.target)) {
    menuOpen.value = false
  }
}

const displayName = computed(() => props.user?.username || props.user?.displayName || props.user?.name || '管理员')
const roleLabel = computed(() => props.user?.role === 'superadmin' ? '超级管理员' : '运营成员')
const initials = computed(() => (displayName.value || 'ZY').slice(0, 2).toUpperCase())
const sseLabel = computed(() => ({
  connected: '实时连接',
  connecting: '连接中',
  reconnecting: '重连中',
  disconnected: '离线',
  failed: '连接失败',
}[props.sseStatus] || '状态未知'))

function eventKey(event, index) {
  return event?.id || event?.eventId || `${event?.type || 'event'}:${event?.time || ''}:${index}`
}

const showNoticePanel = ref(false)
const recentEvents = ref([])
const isFullscreen = ref(false)

function toggleNoticePanel() {
  showNoticePanel.value = !showNoticePanel.value
}

function onSseEvent(event) {
  const detail = event.detail || {}
  recentEvents.value.unshift({
    type: detail.type || detail.eventType,
    title: detail.title || detail.eventType,
    content: detail.content || detail.message,
    time: new Date().toLocaleTimeString(),
    raw: detail,
  })
  if (recentEvents.value.length > 50) recentEvents.value.pop()
}

function onNoticeClick(ev) {
  const routeMap = {
    message: 'messages',
    order: 'auto-delivery',
    account: 'accounts',
    workflow: 'logs',
  }
  const key = Object.keys(routeMap).find(item => (ev.type || '').toLowerCase().includes(item))
  if (!key) return
  location.hash = `#/${routeMap[key]}`
  showNoticePanel.value = false
}

function toggleFullscreen() {
  if (document.fullscreenElement) {
    document.exitFullscreen()
    return
  }
  document.documentElement.requestFullscreen().catch(() => {})
}

function onFullscreenChange() {
  isFullscreen.value = !!document.fullscreenElement
}

onMounted(() => {
  window.addEventListener('xya-sse-event', onSseEvent)
  document.addEventListener('fullscreenchange', onFullscreenChange)
  document.addEventListener('click', onDocClick)
})

onBeforeUnmount(() => {
  window.removeEventListener('xya-sse-event', onSseEvent)
  document.removeEventListener('fullscreenchange', onFullscreenChange)
  document.removeEventListener('click', onDocClick)
})
</script>
