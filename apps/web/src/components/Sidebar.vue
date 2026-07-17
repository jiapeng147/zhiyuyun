<template>
  <aside class="sidebar naive-admin-sider" :class="{ open, collapsed }">
    <button class="sidebar-close" type="button" aria-label="关闭菜单" @click="$emit('close')">
      <n-icon><CloseOutline /></n-icon>
    </button>

    <button class="naive-admin-logo" type="button" @click="$emit('navigate', 'data')">
      <span class="naive-admin-logo-mark">ZY</span>
      <span v-if="!collapsed" class="naive-admin-logo-text">
        <strong>智鱼云</strong>
        <small>运营工作台</small>
      </span>
    </button>

    <n-scrollbar class="naive-admin-menu-scroll">
      <n-menu
        class="naive-admin-menu"
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

    <div class="naive-admin-sider-bottom">
      <button class="naive-admin-profile" type="button" @click="$emit('navigate', 'profile')">
        <n-avatar round size="small">{{ initials }}</n-avatar>
        <span v-if="!collapsed">
          <strong>{{ displayName }}</strong>
          <small>{{ roleLabel }}</small>
        </span>
      </button>
      <button v-if="!collapsed" class="sidebar-logout naive-admin-logout" type="button" @click="$emit('logout')">
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
const initials = computed(() => (displayName.value || 'ZY').slice(0, 2).toUpperCase())

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
