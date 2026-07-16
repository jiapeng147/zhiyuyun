<template>
  <aside class="config-nav naive-admin-config-nav">
    <div class="config-nav-head">
      <span>系统设置</span>
      <p>系统配置 / 高德地图 / 模型配置 / RAG 知识库</p>
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
  DocumentTextOutline,
  HardwareChipOutline,
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
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(248, 251, 255, 0.92));
  border: 1px solid rgba(231, 237, 247, 0.95);
  border-radius: 22px;
  box-shadow: 0 18px 42px rgba(94, 50, 31, 0.08);
  padding: 16px 14px 14px;
  min-height: calc(100vh - 168px);
  position: sticky;
  top: 18px;
  backdrop-filter: blur(10px);
}

.config-nav-head {
  padding: 4px 10px 14px;
  margin-bottom: 10px;
  border-bottom: 1px solid #F0F0F0;
}

.config-nav-head span {
  display: block;
  font-size: 15px;
  font-weight: 800;
  color: #13213d;
  letter-spacing: 0.2px;
}

.config-nav-head p {
  margin: 6px 0 0;
  font-size: 12px;
  line-height: 1.5;
  color: #8b97aa;
}

.config-nav-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.config-link {
  width: 100%;
  height: 48px;
  border: 0;
  background: transparent;
  border-radius: 14px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 14px;
  color: #5a6880;
  font-weight: 700;
  text-align: left;
  transition: transform 0.18s ease, background 0.18s ease, box-shadow 0.18s ease, color 0.18s ease;
}

.config-link:hover {
  background: #f3f8ff;
  color: #0f766e;
  transform: translateX(1px);
}

.config-link.active {
  background: linear-gradient(135deg, #edf4ff, #e7f0ff);
  color: #0f766e;
  box-shadow: inset 0 0 0 1px rgba(20, 184, 166, 0.12), 0 8px 20px rgba(20, 184, 166, 0.08);
}

.config-link span {
  width: 18px;
  height: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.config-link :deep(.ui-icon),
.config-link :deep(.ui-icon-img) {
  width: 18px;
  height: 18px;
}

@media (max-width: 1260px) {
  .config-nav {
    min-height: auto;
    position: static;
  }
}

@media (max-width: 900px) {
  .config-nav {
    padding: 10px 12px;
    border-radius: 16px;
    overflow: hidden;
  }
  .config-nav-head {
    display: none;
  }
  .config-nav-list {
    display: flex;
    flex-direction: row;
    overflow-x: auto;
    gap: 8px;
    padding-bottom: 2px;
    min-width: 0;
    -webkit-overflow-scrolling: touch;
  }
  .config-link {
    width: auto;
    flex-shrink: 0;
    height: 40px;
    padding: 0 14px;
    white-space: nowrap;
    font-size: 13px;
    border-radius: 12px;
  }
}
</style>
