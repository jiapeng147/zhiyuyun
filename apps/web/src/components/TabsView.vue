<template>
  <section class="tabs-view-shell" aria-label="页面导航">
    <div class="tabs-view-head">
      <n-breadcrumb class="tabs-view-breadcrumb">
        <n-breadcrumb-item v-for="item in breadcrumbItems" :key="item.label">
          <button
            v-if="item.key"
            class="tabs-view-crumb-link"
            type="button"
            @click="$emit('navigate', item.key)"
          >
            {{ item.label }}
          </button>
          <span v-else>{{ item.label }}</span>
        </n-breadcrumb-item>
      </n-breadcrumb>

      <div class="tabs-view-actions">
        <n-button quaternary size="small" title="返回默认页" @click="$emit('navigate', defaultKey)">
          <template #icon>
            <n-icon><HomeOutline /></n-icon>
          </template>
        </n-button>
        <n-dropdown trigger="click" :options="actionOptions" @select="handleAction">
          <n-button quaternary size="small" title="标签页操作">
            <template #icon>
              <n-icon><EllipsisHorizontalOutline /></n-icon>
            </template>
          </n-button>
        </n-dropdown>
      </div>
    </div>

    <div class="tabs-view-strip">
      <div class="tabs-view-track">
        <div
          v-for="tab in tabs"
          :key="tab.key"
          class="tabs-view-tab"
          :class="{ active: tab.key === active }"
        >
          <button class="tabs-view-tab-main" type="button" @click="$emit('navigate', tab.key)">
            {{ tab.label }}
          </button>
          <button
            v-if="tab.closable"
            class="tabs-view-tab-close"
            type="button"
            :aria-label="`关闭${tab.label}`"
            @click.stop="$emit('close', tab.key)"
          >
            <n-icon><CloseOutline /></n-icon>
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { NBreadcrumb, NBreadcrumbItem, NButton, NDropdown, NIcon } from 'naive-ui'
import { CloseOutline, EllipsisHorizontalOutline, HomeOutline } from '@vicons/ionicons5'

const props = defineProps({
  active: { type: String, required: true },
  tabs: { type: Array, default: () => [] },
  breadcrumbItems: { type: Array, default: () => [] },
  defaultKey: { type: String, default: 'data' },
})

const emit = defineEmits(['navigate', 'close', 'close-others', 'close-all'])

const hasClosableTabs = computed(() => props.tabs.some((tab) => tab.closable))
const actionOptions = computed(() => [
  { label: '关闭其他标签', key: 'close-others', disabled: props.tabs.length <= 1 },
  { label: '关闭全部标签', key: 'close-all', disabled: !hasClosableTabs.value },
])

function handleAction(key) {
  if (key === 'close-others') emit('close-others')
  if (key === 'close-all') emit('close-all')
}
</script>

<style scoped>
.tabs-view-shell {
  width: 100%;
  margin: 0 0 14px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, .04);
  overflow: hidden;
}

.tabs-view-head {
  min-height: 38px;
  padding: 0 10px 0 14px;
  border-bottom: 1px solid #edf0f5;
  display: flex;
  align-items: center;
  gap: 12px;
}

.tabs-view-breadcrumb {
  min-width: 0;
  flex: 1;
  font-size: 13px;
}

.tabs-view-crumb-link {
  padding: 0;
  border: 0;
  background: transparent;
  color: #4b5563;
  cursor: pointer;
}

.tabs-view-crumb-link:hover {
  color: #18a058;
}

.tabs-view-actions {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.tabs-view-strip {
  min-height: 42px;
  padding: 6px 8px;
  overflow-x: auto;
  overflow-y: hidden;
}

.tabs-view-track {
  min-width: max-content;
  display: flex;
  align-items: center;
  gap: 6px;
}

.tabs-view-tab {
  height: 30px;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  background: #f8fafc;
  color: #4b5563;
  display: inline-flex;
  align-items: center;
  overflow: hidden;
}

.tabs-view-tab.active {
  border-color: rgba(24, 160, 88, .34);
  background: #f0fdf4;
  color: #0c7a43;
  box-shadow: inset 0 -2px 0 #18a058;
}

.tabs-view-tab-main {
  height: 100%;
  max-width: 176px;
  padding: 0 10px;
  border: 0;
  background: transparent;
  color: inherit;
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;
}

.tabs-view-tab-close {
  width: 28px;
  height: 100%;
  border: 0;
  border-left: 1px solid rgba(148, 163, 184, .22);
  background: transparent;
  color: inherit;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: .78;
}

.tabs-view-tab-close:hover {
  background: rgba(208, 48, 80, .08);
  color: #d03050;
  opacity: 1;
}

@media (max-width: 900px) {
  .tabs-view-shell {
    display: none;
  }
}
</style>
