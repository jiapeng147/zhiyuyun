<template>
  <div class="settings-page-v4">
    <n-card class="settings-v4-hero" :bordered="false">
      <div class="settings-v4-hero-main">
        <div class="settings-v4-copy">
          <n-tag size="small" type="success" :bordered="false">System Settings</n-tag>
          <h2>{{ activeTitle }}</h2>
          <p>{{ activeSubtitle }}</p>
        </div>
        <n-space class="settings-v4-actions" :size="8" align="center">
          <n-button
            v-for="item in quickActions"
            :key="item.key"
            size="small"
            :type="item.key === active ? 'primary' : 'default'"
            @click="navigate(item.key)"
          >
            {{ item.label }}
          </n-button>
        </n-space>
      </div>

      <n-tabs
        class="settings-v4-tabs"
        type="line"
        size="small"
        animated
        :value="active"
        @update:value="navigate"
      >
        <n-tab-pane v-for="tab in tabs" :key="tab.key" :name="tab.key" :tab="tab.label" />
      </n-tabs>
    </n-card>

    <div class="settings-v4-layout">
      <ConfigNav :active="active" @navigate="navigate" />
      <div class="settings-v4-main">
        <component :is="current" :active="active" @navigate="navigate" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { NButton, NCard, NSpace, NTabPane, NTabs, NTag } from 'naive-ui'
import ConfigNav from '../components/ConfigNav.vue'
import SystemSettingsPage from './admin/SystemSettingsPage.vue'
import AmapSettingsPage from './admin/AmapSettingsPage.vue'
import ModelSettingsPage from './admin/ModelSettingsPage.vue'
import EmbeddingSettingsPage from './admin/EmbeddingSettingsPage.vue'
import RagSettingsPage from './admin/RagSettingsPage.vue'
import AiCsSettings from './settings/AiCsSettings.vue'
import ProductOpSettings from './settings/ProductOpSettings.vue'
import NotifySettings from './settings/NotifySettings.vue'
import AboutSettings from './settings/AboutSettings.vue'
import { pageTitles, settingsTabs } from '../data/nav.js'

const props = defineProps({ active: String })
const emit = defineEmits(['navigate'])

const map = {
  'settings-system': SystemSettingsPage,
  'settings-ai-cs': AiCsSettings,
  'settings-amap': AmapSettingsPage,
  'settings-model': ModelSettingsPage,
  'settings-embedding': EmbeddingSettingsPage,
  'settings-rag': RagSettingsPage,
  'settings-product': ProductOpSettings,
  'settings-about': AboutSettings,
  'settings-notify': NotifySettings
}

const current = computed(() => map[props.active] || SystemSettingsPage)
const tabs = settingsTabs
const activePageTitle = computed(() => pageTitles[props.active] || pageTitles['settings-system'])
const activeTitle = computed(() => {
  const text = activePageTitle.value?.[0] || '系统设置'
  const parts = String(text).split('/').map(item => item.trim()).filter(Boolean)
  return parts.at(-1) || text
})
const activeSubtitle = computed(() => activePageTitle.value?.[1] || '集中维护站点、模型、通知、知识库和商品操作配置')
const quickActions = computed(() => [
  { key: 'settings-system', label: '系统配置' },
  { key: 'settings-model', label: '模型配置' },
  { key: 'settings-rag', label: '知识库' },
  { key: 'settings-notify', label: '通知设置' },
])

function navigate(key) {
  if (!key || key === props.active) return
  emit('navigate', key)
}
</script>

<style scoped>
.settings-page-v4 {
  display: grid;
  gap: 16px;
}

.settings-v4-hero {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, .04);
}

.settings-v4-hero :deep(.n-card__content) {
  padding: 18px 18px 0;
}

.settings-v4-hero-main {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.settings-v4-copy {
  min-width: 0;
}

.settings-v4-copy h2 {
  margin: 12px 0 6px;
  color: #111827;
  font-size: 22px;
  font-weight: 650;
  line-height: 1.25;
}

.settings-v4-copy p {
  margin: 0;
  color: #64748b;
  font-size: 13px;
  line-height: 1.65;
}

.settings-v4-actions {
  flex: 0 0 auto;
  justify-content: flex-end;
}

.settings-v4-tabs {
  margin-top: 16px;
}

.settings-v4-tabs :deep(.n-tabs-pane-wrapper) {
  display: none;
}

.settings-v4-tabs :deep(.n-tabs-nav) {
  padding-bottom: 0;
}

.settings-v4-layout {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr);
  gap: 16px;
  align-items: start;
}

.settings-v4-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

@media (max-width: 1260px) {
  .settings-v4-layout {
    grid-template-columns: minmax(0, 1fr);
  }

  .settings-v4-hero-main {
    flex-direction: column;
  }

  .settings-v4-actions {
    justify-content: flex-start;
  }
}

@media (max-width: 900px) {
  .settings-page-v4 {
    gap: 12px;
  }

  .settings-v4-hero :deep(.n-card__content) {
    padding: 14px 14px 0;
  }

  .settings-v4-copy h2 {
    font-size: 20px;
  }

  .settings-v4-layout {
    grid-template-columns: minmax(0, 1fr);
    gap: 12px;
  }

  .settings-v4-main {
    gap: 12px;
    min-width: 0;
  }
}
</style>
