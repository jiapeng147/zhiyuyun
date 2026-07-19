<template>
  <aside class="sidebar zy-shell-sider" :class="{ open, collapsed }">
    <button class="sidebar-close" type="button" aria-label="关闭菜单" @click="$emit('close')">
      <n-icon><CloseOutline /></n-icon>
    </button>

    <button class="zy-shell-logo" type="button" @click="$emit('navigate', 'data')">
      <span class="zy-shell-logo-mark">
        <img src="/xya/brand/zhiyuyun-mark.svg?v=20260717-shell" alt="" />
      </span>
      <span v-if="!collapsed" class="zy-shell-logo-text">
        <strong>智鱼云</strong>
        <small>运营工作台</small>
      </span>
    </button>

    <n-scrollbar class="zy-shell-menu-scroll">
      <n-menu
        class="zy-shell-menu"
        :value="activeMenuKey"
        :options="menuOptions"
        :collapsed="collapsed"
        :collapsed-width="64"
        :collapsed-icon-size="18"
        :indent="16"
        :root-indent="14"
        accordion
        inverted
        @update:value="onMenuSelect"
      />
    </n-scrollbar>

    <div class="zy-shell-sider-bottom">
      <button class="zy-shell-profile" type="button" @click="$emit('navigate', 'profile')">
        <n-avatar round size="small">{{ initials }}</n-avatar>
        <span v-if="!collapsed">
          <strong>{{ displayName }}</strong>
          <small>{{ roleLabel }}</small>
        </span>
      </button>
      <button v-if="!collapsed" class="sidebar-logout zy-shell-logout" type="button" @click="$emit('logout')">
        退出登录
      </button>
    </div>
  </aside>
</template>

<script setup>
import { computed, h, ref } from 'vue'
import { NAvatar, NIcon, NMenu, NScrollbar } from 'naive-ui'
import { navGroups } from '../data/nav.js'
import {
  AppsOutline,
  BarChartOutline,
  CartOutline,
  CloseOutline,
  ChatbubblesOutline,
  ClipboardOutline,
  CubeOutline,
  FileTrayFullOutline,
  LayersOutline,
  LinkOutline,
  ListOutline,
  MailOutline,
  MegaphoneOutline,
  PeopleOutline,
  PersonCircleOutline,
  PricetagsOutline,
  SettingsOutline,
  ShieldCheckmarkOutline,
  SyncOutline,
  TimeOutline,
  TrainOutline,
} from '@vicons/ionicons5'

const emit = defineEmits(['navigate', 'close', 'logout'])

const props = defineProps({
  active: { type: String, required: true },
  user: { type: Object, default: () => ({}) },
  open: { type: Boolean, default: false },
})

const collapsed = ref(false)

const iconMap = {
  dashboard: AppsOutline,
  data: BarChartOutline,
  account: PersonCircleOutline,
  users: PeopleOutline,
  link: LinkOutline,
  product: CubeOutline,
  publish: PricetagsOutline,
  record: ClipboardOutline,
  chat: ChatbubblesOutline,
  message: ChatbubblesOutline,
  truck: TrainOutline,
  board: LayersOutline,
  key: FileTrayFullOutline,
  clock: TimeOutline,
  reply: MailOutline,
  log: ListOutline,
  bell: MegaphoneOutline,
  settings: SettingsOutline,
  opportunity: ShieldCheckmarkOutline,
  task: SyncOutline,
  default: CartOutline,
}

const displayName = computed(() => props.user?.username || props.user?.displayName || props.user?.name || '运营成员')
const roleLabel = computed(() => props.user?.role === 'superadmin' ? '平台负责人' : '运营成员')
const initials = computed(() => (displayName.value || '智鱼').slice(0, 2).toUpperCase())

const activeMenuKey = computed(() => {
  if (props.active.startsWith('settings-') && props.active !== 'settings-notify') return 'settings-system'
  return props.active
})

const visibleGroups = computed(() => {
  const isSuper = props.user?.role === 'superadmin'
  return navGroups
    .filter((g) => !g.superadmin || isSuper)
    .map((g) => ({ ...g, items: g.items.filter((it) => !it.superadmin || isSuper) }))
    .filter((g) => g.items.length > 0)
})

const menuOptions = computed(() => visibleGroups.value.map((group) => ({
  type: 'group',
  label: group.title,
  key: `group:${group.title}`,
  children: group.items.map((item) => ({
    label: item.label,
    key: item.key,
    icon: renderMenuIcon(item.icon),
  })),
})))

function renderMenuIcon(name) {
  const Comp = iconMap[name] || iconMap.default
  return () => h(NIcon, null, { default: () => h(Comp) })
}

function onMenuSelect(key) {
  if (key) emit('navigate', key)
}
</script>

<style scoped>
.sidebar.zy-shell-sider {
  position: fixed;
  inset: 0 auto 0 0;
  z-index: 50;
  display: flex;
  flex-direction: column;
  width: var(--sidebar);
  padding: 0;
  border: 0;
  background: var(--platform-sider);
  box-shadow: 2px 0 8px rgba(29, 35, 41, 0.05);
  color: rgba(255, 255, 255, 0.82);
}

:global(.zy-layout-sider) .sidebar.zy-shell-sider {
  position: relative;
  inset: auto;
  z-index: auto;
  width: 100%;
  height: 100dvh;
  min-height: 100dvh;
  overflow: hidden;
  box-shadow: none;
}

.sidebar-close {
  display: none;
}

.zy-shell-logo {
  display: flex;
  align-items: center;
  width: 100%;
  height: 56px;
  padding: 0 18px;
  gap: 10px;
  border: 0;
  border-radius: 0;
  background: transparent;
  color: #ffffff;
  cursor: pointer;
}

.zy-shell-logo-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  overflow: hidden;
  border-radius: 6px;
  background: transparent;
  box-shadow: none;
}

.zy-shell-logo-mark img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.zy-shell-logo-text {
  display: grid;
  gap: 0;
  line-height: 1.15;
}

.zy-shell-logo-text strong {
  color: #fff;
  font-size: 16px;
  font-weight: 700;
}

.zy-shell-logo-text small {
  color: rgba(255, 255, 255, 0.48);
  font-size: 11px;
}

.zy-shell-menu-scroll {
  flex: 1;
  min-height: 0;
  padding: 8px 10px 12px;
}

.zy-shell-sider :deep(.zy-shell-menu),
.zy-shell-sider :deep(.n-menu) {
  background: transparent;
}

.zy-shell-sider :deep(.zy-shell-menu .n-menu-item-content) {
  height: 40px;
  margin: 1px 0;
  padding-right: 12px;
  border-radius: 4px;
  color: rgba(255, 255, 255, 0.74);
  font-weight: 500;
  line-height: 40px;
  transition: background-color 160ms ease, color 160ms ease;
}

.zy-shell-sider :deep(.zy-shell-menu .n-menu-item-content:hover) {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.zy-shell-sider :deep(.zy-shell-menu .n-menu-item-content--selected),
.zy-shell-sider :deep(.zy-shell-menu .n-menu-item-content--selected:hover) {
  background: var(--primary);
  color: #fff;
}

.zy-shell-sider :deep(.zy-shell-menu .n-menu-item-content-header) {
  display: flex;
  align-items: center;
  min-width: 0;
  height: 40px;
  overflow: hidden;
  color: inherit;
  font-size: 13px;
  line-height: 40px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.zy-shell-sider :deep(.zy-shell-menu .n-menu-item-content__icon) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  min-width: 20px;
  height: 40px;
  margin-right: 10px;
  color: inherit;
}

.zy-shell-sider :deep(.zy-shell-menu .n-menu-item-group-title) {
  height: auto;
  min-height: 22px;
  padding: 14px 12px 5px;
  color: rgba(255, 255, 255, 0.42);
  font-size: 11px;
  font-weight: 650;
  letter-spacing: 0;
  line-height: 1.2;
}

.zy-shell-sider :deep(.zy-shell-menu .n-menu-item-group:first-child .n-menu-item-group-title) {
  padding-top: 6px;
}

.zy-shell-sider-bottom {
  display: grid;
  gap: 10px;
  padding: 12px;
  border-top: 0;
}

.zy-shell-profile {
  display: flex;
  align-items: center;
  width: 100%;
  height: 50px;
  padding: 0 8px;
  gap: 10px;
  border: 0;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.04);
  color: #fff;
  text-align: left;
  cursor: pointer;
}

.zy-shell-profile span {
  display: grid;
  min-width: 0;
  line-height: 1.2;
}

.zy-shell-profile strong {
  color: #fff;
  font-size: 13px;
}

.zy-shell-profile small {
  color: rgba(255, 255, 255, 0.48);
  font-size: 11px;
}

.zy-shell-logout {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 34px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 4px;
  background: transparent;
  color: rgba(255, 255, 255, 0.76);
  font-weight: 500;
}

.zy-shell-logout:hover {
  border-color: rgba(208, 48, 80, 0.45);
  background: rgba(208, 48, 80, 0.12);
  color: #fff;
}

@media (max-width: 900px) {
  .sidebar.zy-shell-sider {
    z-index: 60;
    max-width: 86vw;
    transform: translateX(-100%);
    transition: transform 200ms ease;
  }

  .sidebar.zy-shell-sider.open {
    transform: translateX(0);
  }

  .sidebar-close {
    position: absolute;
    top: 10px;
    right: 10px;
    z-index: 2;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border: 1px solid rgba(255, 255, 255, 0.16);
    border-radius: 4px;
    background: rgba(255, 255, 255, 0.08);
    color: #fff;
  }
}
</style>
