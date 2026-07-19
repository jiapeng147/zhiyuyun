<template>
  <div class="topbar zy-shell-header">
    <n-input
      class="zy-shell-search"
      placeholder="搜索账号、商品、订单、消息"
      readonly
      @click="go('data')"
    >
      <template #prefix>
        <n-icon><SearchOutline /></n-icon>
      </template>
      <template #suffix>
        <span>搜索</span>
      </template>
    </n-input>

    <div class="zy-shell-header-spacer"></div>

    <n-tag round :type="sseType" size="small">
      <template #icon>
        <span class="zy-shell-status-dot" :class="sseStatus"></span>
      </template>
      {{ sseLabel }}
    </n-tag>

    <n-badge :value="Number(unreadCount) || 0" :show="Number(unreadCount) > 0" :max="99">
      <n-button quaternary circle @click="toggleNoticePanel">
        <template #icon><n-icon><NotificationsOutline /></n-icon></template>
      </n-button>
    </n-badge>

    <n-button quaternary circle @click="go('settings-about')">
      <template #icon><n-icon><HelpCircleOutline /></n-icon></template>
    </n-button>

    <n-button quaternary circle @click="toggleFullscreen">
      <template #icon><n-icon><ExpandOutline /></n-icon></template>
    </n-button>

    <n-dropdown trigger="click" :options="userOptions" @select="handleUserSelect">
      <button class="zy-shell-user">
        <n-avatar round size="small">{{ initials }}</n-avatar>
        <span>
          <strong>{{ displayName }}</strong>
          <small>{{ roleLabel }}</small>
        </span>
        <n-icon><ChevronDownOutline /></n-icon>
      </button>
    </n-dropdown>

    <n-drawer v-model:show="showNoticePanel" width="380" placement="right">
      <n-drawer-content title="通知中心" closable>
        <EmptyState
          v-if="recentEvents.length === 0"
          icon="∅"
          title="暂无通知"
          description="系统实时事件会在这里出现。"
        />
        <n-list v-else hoverable clickable>
          <n-list-item v-for="(ev, i) in recentEvents" :key="eventKey(ev, i)" @click="onNoticeClick(ev)">
            <n-thing :title="ev.title || ev.type || '事件'" :description="ev.content || ev.message || ''">
              <template #header-extra>
                <span class="zy-shell-notice-time">{{ ev.time || '' }}</span>
              </template>
            </n-thing>
          </n-list-item>
        </n-list>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup>
import { computed, h, onBeforeUnmount, onMounted, ref } from 'vue'
import {
  NAvatar,
  NBadge,
  NButton,
  NDrawer,
  NDrawerContent,
  NDropdown,
  NIcon,
  NInput,
  NList,
  NListItem,
  NTag,
  NThing,
} from 'naive-ui'
import {
  ChevronDownOutline,
  ExpandOutline,
  HelpCircleOutline,
  LogOutOutline,
  NotificationsOutline,
  PersonOutline,
  SearchOutline,
  SettingsOutline,
} from '@vicons/ionicons5'
import EmptyState from './EmptyState.vue'

const props = defineProps({
  user: { type: Object, default: () => ({}) },
  sseStatus: { type: String, default: 'disconnected' },
  unreadCount: { type: [String, Number], default: 0 },
})

const emit = defineEmits(['logout', 'open-profile-center'])

const displayName = computed(() => props.user?.username || props.user?.displayName || props.user?.name || '运营成员')
const roleLabel = computed(() => props.user?.role === 'superadmin' ? '平台负责人' : '运营成员')
const initials = computed(() => (displayName.value || '智鱼').slice(0, 2).toUpperCase())
const sseLabel = computed(() => ({
  connected: '实时在线',
  connecting: '连接中',
  reconnecting: '重连中',
  disconnected: '离线',
  failed: '连接失败',
}[props.sseStatus] || '状态未知'))
const sseType = computed(() => props.sseStatus === 'connected' ? 'success' : props.sseStatus === 'failed' ? 'error' : 'warning')

const userOptions = [
  { label: '个人中心', key: 'profile', icon: renderIcon(PersonOutline) },
  { label: '系统设置', key: 'settings', icon: renderIcon(SettingsOutline) },
  { label: '退出登录', key: 'logout', icon: renderIcon(LogOutOutline) },
]

const showNoticePanel = ref(false)
const recentEvents = ref([])
const isFullscreen = ref(false)

function renderIcon(icon) {
  return () => hIcon(icon)
}

function hIcon(icon) {
  return h(NIcon, null, { default: () => h(icon) })
}

function handleUserSelect(key) {
  if (key === 'profile') emit('open-profile-center')
  if (key === 'settings') go('settings-system')
  if (key === 'logout') emit('logout')
}

function go(page) { location.hash = `#/${page}` }
function toggleNoticePanel() { showNoticePanel.value = !showNoticePanel.value }

function eventKey(event, index) {
  return event?.id || event?.eventId || `${event?.type || 'event'}:${event?.time || ''}:${index}`
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
})

onBeforeUnmount(() => {
  window.removeEventListener('xya-sse-event', onSseEvent)
  document.removeEventListener('fullscreenchange', onFullscreenChange)
})
</script>

<style scoped>
.topbar.zy-shell-header {
  position: static;
  z-index: 40;
  display: flex;
  align-items: center;
  height: var(--topbar);
  margin: 0;
  padding: 0 24px;
  gap: 12px;
  border-bottom: 0;
  background: var(--platform-header);
  box-shadow: none;
  backdrop-filter: none;
}

.zy-shell-search {
  width: min(460px, 42vw);
}

.zy-shell-search :deep(kbd) {
  height: 20px;
  padding: 0 6px;
  border: 1px solid var(--line);
  border-radius: 3px;
  background: #f9fafb;
  color: var(--muted);
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 11px;
}

.zy-shell-header-spacer {
  flex: 1;
}

.zy-shell-user {
  display: inline-flex;
  align-items: center;
  height: 38px;
  padding: 0 8px;
  gap: 8px;
  border: 1px solid var(--line);
  border-radius: 4px;
  background: #fff;
  color: var(--text);
  cursor: pointer;
}

.zy-shell-user:hover {
  border-color: var(--line-strong);
  background: #f9fafb;
}

.zy-shell-user span {
  display: grid;
  text-align: left;
  line-height: 1.12;
}

.zy-shell-user strong {
  color: var(--text);
  font-size: 13px;
}

.zy-shell-user small {
  color: var(--muted);
  font-size: 11px;
}

.zy-shell-status-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--orange);
}

.zy-shell-status-dot.connected {
  background: var(--green);
}

.zy-shell-status-dot.failed,
.zy-shell-status-dot.disconnected {
  background: var(--red);
}

.zy-shell-notice-time {
  color: var(--muted);
  font-size: 12px;
}

@media (max-width: 900px) {
  .topbar.zy-shell-header {
    margin: 0 -14px 14px;
    padding: 0 14px;
  }

  .zy-shell-search {
    display: none;
  }
}
</style>
