<template>
  <div class="settings-page settings-v23-shell">
    <section class="settings-command-center">
      <div class="settings-command-main">
        <div class="settings-command-kicker">
          <span>系统配置</span>
          <b>{{ activeTitle }}</b>
        </div>
        <h2>{{ activeTitle }}</h2>
        <p>{{ activeSubtitle }}</p>
        <div class="settings-command-meta">
          <span>站点配置</span>
          <span>模型能力</span>
          <span>通知与知识库</span>
        </div>
      </div>
      <div class="settings-command-panel">
        <div class="settings-command-panel-head">
          <span>常用入口</span>
          <strong>{{ activeTitle }}</strong>
        </div>
        <div class="settings-command-actions">
          <n-button
            v-for="item in quickActions"
            :key="item.key"
            :type="item.key === active ? 'primary' : 'default'"
            :title="settingsActionHint"
            @click="navigate(item.key)"
          >
            {{ item.label }}
          </n-button>
        </div>
        <p class="settings-action-hint">{{ settingsActionHint }}</p>
      </div>
    </section>

    <section class="settings-section-strip" aria-label="设置模块">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        type="button"
        :class="['settings-section-item', { active: tab.key === active }]"
        :title="tab.key === active ? settingsActionHint : `切换到${tab.label}`"
        @click="navigate(tab.key)"
      >
        <span>{{ tab.label }}</span>
        <small>{{ tab.key === active ? '正在配置' : '切换模块' }}</small>
      </button>
    </section>

    <div class="settings-layout">
      <ConfigNav :active="active" @navigate="navigate" />
      <div class="settings-main">
        <component :is="current" :active="active" @navigate="navigate" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { NButton } from 'naive-ui'
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
const settingsActionHint = computed(() => `当前正在配置“${activeTitle.value}”，切换模块不会提交表单，请先保存当前页面需要保留的修改。`)

function navigate(key) {
  if (!key || key === props.active) return
  emit('navigate', key)
}
</script>

<style scoped>
.settings-page {
  display: grid;
  gap: 16px;
}

.settings-command-center {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 16px;
  padding: 18px;
  border: 1px solid #dfe6f1;
  border-radius: 8px;
  background:
    linear-gradient(135deg, rgba(240, 247, 255, .98), rgba(247, 249, 252, .98) 48%, rgba(255, 250, 245, .94)),
    #fff;
  box-shadow: 0 14px 32px rgba(15, 23, 42, .06);
}

.settings-command-main {
  min-width: 0;
  display: grid;
  align-content: center;
  gap: 12px;
}

.settings-command-kicker {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.settings-command-kicker span {
  padding: 4px 8px;
  border-radius: 999px;
  background: rgba(37, 99, 235, .1);
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 800;
}

.settings-command-kicker b {
  min-width: 0;
  color: #475569;
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.settings-command-main h2 {
  margin: 0;
  color: #101828;
  font-size: 28px;
  font-weight: 800;
  line-height: 1.25;
}

.settings-command-main p {
  margin: 0;
  max-width: 720px;
  color: #526079;
  font-size: 13px;
  line-height: 1.65;
}

.settings-command-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.settings-command-meta span {
  padding: 6px 10px;
  border: 1px solid rgba(37, 99, 235, .12);
  border-radius: 999px;
  background: rgba(255, 255, 255, .72);
  color: #334155;
  font-size: 12px;
  font-weight: 650;
}

.settings-command-panel {
  display: grid;
  gap: 12px;
  align-content: center;
  padding: 14px;
  border: 1px solid rgba(148, 163, 184, .24);
  border-radius: 8px;
  background: rgba(255, 255, 255, .82);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, .7);
}

.settings-command-panel-head {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  color: #64748b;
  font-size: 12px;
}

.settings-command-panel-head strong {
  min-width: 0;
  color: #101828;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.settings-command-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.settings-command-actions :deep(.n-button) {
  min-width: 0;
}

.settings-action-hint {
  margin: 0;
  color: #64748b;
  font-size: 12px;
  line-height: 1.55;
}

.settings-section-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.settings-section-item {
  min-width: 0;
  padding: 12px;
  border: 1px solid #e5eaf0;
  border-radius: 8px;
  background: #fff;
  color: #475569;
  text-align: left;
  cursor: pointer;
  box-shadow: 0 8px 24px rgba(15, 23, 42, .035);
  transition:
    transform 180ms cubic-bezier(0.23, 1, 0.32, 1),
    border-color 180ms ease,
    box-shadow 180ms cubic-bezier(0.23, 1, 0.32, 1),
    background-color 180ms ease;
}

.settings-section-item:hover,
.settings-section-item.active {
  border-color: #93c5fd;
  box-shadow: 0 12px 28px rgba(37, 99, 235, .08);
  transform: translateY(-1px);
}

.settings-section-item.active {
  background: linear-gradient(135deg, #eff6ff, #fff);
}

.settings-section-item:active {
  transform: scale(.98);
}

.settings-section-item span {
  display: block;
  color: #101828;
  font-size: 13px;
  font-weight: 800;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.settings-section-item small {
  display: block;
  margin-top: 5px;
  color: #64748b;
  font-size: 12px;
}

.settings-layout {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr);
  gap: 16px;
  align-items: start;
}

.settings-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

@media (max-width: 1260px) {
  .settings-command-center,
  .settings-layout {
    grid-template-columns: minmax(0, 1fr);
  }

  .settings-section-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .settings-page {
    gap: 12px;
  }

  .settings-command-center {
    padding: 14px;
    border-radius: 8px;
  }

  .settings-command-main h2 {
    font-size: 24px;
  }

  .settings-command-actions,
  .settings-section-strip,
  .settings-layout {
    grid-template-columns: minmax(0, 1fr);
  }

  .settings-layout {
    gap: 12px;
  }

  .settings-main {
    gap: 12px;
    min-width: 0;
  }
}
</style>
