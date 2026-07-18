<template>
  <aside class="config-nav">
    <div class="config-nav-head">
      <span>配置目录</span>
      <p>站点、模型、通知与知识库</p>
    </div>

    <n-menu
      class="config-nav-list"
      :value="active"
      :options="menuOptions"
      :indent="12"
      @update:value="key => emit('navigate', key)"
    />
  </aside>
</template>

<script setup>
import { computed, h } from 'vue'
import { NIcon, NMenu } from 'naive-ui'
import {
  BusinessOutline,
  ChatbubbleEllipsesOutline,
  CodeSlashOutline,
  CubeOutline,
  DocumentTextOutline,
  HardwareChipOutline,
  HelpCircleOutline,
  LocationOutline,
  NotificationsOutline,
  SettingsOutline,
} from '@vicons/ionicons5'
import { settingsTabs } from '../data/nav.js'

defineProps({ active: String })
const emit = defineEmits(['navigate'])
const tabs = settingsTabs

const iconMap = {
  settings: SettingsOutline,
  bell: NotificationsOutline,
  message: ChatbubbleEllipsesOutline,
  opportunity: BusinessOutline,
  product: CubeOutline,
  help: HelpCircleOutline,
  map: LocationOutline,
  ai: HardwareChipOutline,
  key: HardwareChipOutline,
  board: DocumentTextOutline,
  link: LocationOutline,
  default: CodeSlashOutline,
}

const menuOptions = computed(() => tabs.map(tab => ({
  key: tab.key,
  label: tab.label,
  icon: () => h(NIcon, null, { default: () => h(iconMap[tab.icon] || iconMap.default) }),
})))
</script>

<style scoped>
.config-nav {
  border: 1px solid #e5eaf0;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 10px 28px rgba(15, 23, 42, .045);
  min-height: calc(100vh - 188px);
  position: sticky;
  top: 112px;
  overflow: hidden;
}

.config-nav-head {
  padding: 16px 16px 14px;
  margin: 0;
  border-bottom: 1px solid #edf0f5;
  background:
    linear-gradient(135deg, rgba(239, 246, 255, .96), rgba(255, 255, 255, .98)),
    #f8fafc;
}

.config-nav-head span {
  display: block;
  font-size: 15px;
  font-weight: 800;
  color: #111827;
  letter-spacing: 0;
}

.config-nav-head p {
  margin: 6px 0 0;
  font-size: 12px;
  line-height: 1.5;
  color: #64748b;
}

.config-nav-list {
  padding: 10px;
}

.config-nav-list :deep(.n-menu-item-content) {
  height: 40px;
  border-radius: 8px;
  color: #475569;
}

.config-nav-list :deep(.n-menu-item-content:hover) {
  background: #f1f5f9;
  color: #111827;
}

.config-nav-list :deep(.n-menu-item-content.n-menu-item-content--selected) {
  background: #eff6ff;
  color: #1d4ed8;
  font-weight: 750;
}

.config-nav-list :deep(.n-menu-item-content__icon) {
  color: currentColor;
}

@media (max-width: 1260px) {
  .config-nav {
    min-height: auto;
    position: static;
  }
}

@media (max-width: 900px) {
  .config-nav {
    border-radius: 8px;
  }

  .config-nav-head {
    display: none;
  }

  .config-nav-list {
    overflow-x: auto;
    padding: 8px;
    min-width: 0;
    -webkit-overflow-scrolling: touch;
  }
}
</style>
