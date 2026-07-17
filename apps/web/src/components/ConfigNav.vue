<template>
  <n-card class="config-nav zy-shell-config-nav settings-config-nav-v4" :bordered="false">
    <div class="config-nav-head">
      <span>系统设置</span>
      <p>站点、模型、通知与知识库配置</p>
    </div>

    <n-menu
      class="config-nav-list"
      :value="active"
      :options="menuOptions"
      :indent="12"
      @update:value="key => emit('navigate', key)"
    />
  </n-card>
</template>

<script setup>
import { computed, h } from 'vue'
import { NCard, NIcon, NMenu } from 'naive-ui'
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
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, .04);
  min-height: calc(100vh - 188px);
  position: sticky;
  top: 112px;
  overflow: hidden;
}

.settings-config-nav-v4 {
  top: 112px !important;
  min-height: calc(100vh - 188px) !important;
}

.config-nav :deep(.n-card__content) {
  padding: 0;
}

.config-nav-head {
  padding: 16px;
  margin: 0;
  border-bottom: 1px solid #edf0f5;
  background: #f8fafc;
}

.config-nav-head span {
  display: block;
  font-size: 15px;
  font-weight: 650;
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
  padding: 8px;
}

@media (max-width: 1260px) {
  .config-nav {
    min-height: auto;
    position: static;
  }

  .settings-config-nav-v4 {
    min-height: auto !important;
    position: static !important;
  }
}

@media (max-width: 900px) {
  .config-nav {
    border-radius: 6px;
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
