<template>
  <aside class="sidebar zy-shell-sidebar" :class="{ open }">
    <button class="sidebar-close" type="button" aria-label="关闭菜单" @click="$emit('close')">
      <Icon name="close" />
    </button>

    <button type="button" class="zy-brand-card" aria-label="返回首页" @click="$emit('navigate', 'dashboard')">
      <span class="zy-brand-orb" aria-hidden="true">ZY</span>
      <span class="zy-brand-text">
        <strong>智鱼云</strong>
        <small>Ops Console</small>
      </span>
    </button>

    <div class="zy-command-card" role="search" @click="$emit('navigate', 'data')">
      <Icon name="search" />
      <span>搜索功能 / 数据 / 订单</span>
      <kbd>⌘K</kbd>
    </div>

    <nav class="nav-scroll zy-nav-scroll" aria-label="主导航">
      <section v-for="group in groups" :key="group.title" class="nav-group zy-nav-group">
        <div class="nav-title zy-nav-title">{{ group.title }}</div>
        <button
          v-for="item in group.items"
          :key="item.key"
          :class="['nav-item zy-nav-item', { active: isActive(item.key), child: item.child }]"
          type="button"
          @click="$emit('navigate', item.key)"
        >
          <span class="nav-icon"><Icon :name="item.icon" /></span>
          <span class="zy-nav-label">{{ item.label }}</span>
          <span v-if="item.badge" class="nav-badge">{{ item.badge }}</span>
        </button>
      </section>
    </nav>

    <div class="zy-sidebar-footer">
      <button type="button" class="side-user zy-user-card" aria-label="打开个人中心" @click="$emit('navigate','profile')">
        <span class="avatar avatar-img zy-avatar">{{ initials }}</span>
        <span class="side-user-main">
          <strong>{{ displayName }}</strong>
          <span>{{ roleLabel }}</span>
        </span>
        <span class="online-dot" aria-hidden="true"></span>
      </button>
      <button class="sidebar-logout zy-logout" type="button" @click="$emit('logout')">
        退出
      </button>
      <div class="version zy-version">v{{ APP_VERSION }} · {{ copyrightYear }}</div>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { navGroups } from '../data/nav.js'
import Icon from './Icon.vue'
import { APP_VERSION, getCopyrightYear } from '../utils/appMeta.js'

defineEmits(['navigate', 'close', 'logout'])

const props = defineProps({
  active: { type: String, required: true },
  user: { type: Object, default: () => ({}) },
  open: { type: Boolean, default: false },
})

const groups = computed(() => {
  const isSuper = props.user?.role === 'superadmin'
  return navGroups
    .filter((g) => !g.superadmin || isSuper)
    .map((g) => ({ ...g, items: g.items.filter((it) => !it.superadmin || isSuper) }))
    .filter((g) => g.items.length > 0)
})

const displayName = computed(() => props.user?.username || props.user?.displayName || props.user?.name || '管理员')
const roleLabel = computed(() => props.user?.role === 'superadmin' ? '超级管理员' : '运营成员')
const initials = computed(() => (displayName.value || 'ZY').slice(0, 2).toUpperCase())
const copyrightYear = getCopyrightYear()

function isActive(key) {
  if (props.active.startsWith('settings-') && props.active !== 'settings-notify' && key === 'settings-system') return true
  return props.active === key
}
</script>
