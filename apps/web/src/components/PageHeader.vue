<template>
  <header class="page-head zy-shell-page-head" :class="{ compact: !title && !subtitle }">
    <div v-if="title || subtitle" class="zy-shell-title-block">
      <n-breadcrumb v-if="showBreadcrumb" class="zy-shell-breadcrumb">
        <n-breadcrumb-item>数据面板</n-breadcrumb-item>
        <n-breadcrumb-item>{{ title || '页面' }}</n-breadcrumb-item>
      </n-breadcrumb>
      <div class="zy-shell-title-row">
        <h1 v-if="title">{{ title }}</h1>
        <p v-if="subtitle">{{ subtitle }}</p>
      </div>
    </div>
    <n-space v-if="$slots.default" class="page-head-actions zy-shell-page-actions" :size="8" align="center">
      <slot />
    </n-space>
  </header>
</template>

<script setup>
import { NBreadcrumb, NBreadcrumbItem, NSpace } from 'naive-ui'

defineProps({
  title: String,
  subtitle: String,
  showBreadcrumb: { type: Boolean, default: true },
})
</script>

<style scoped>
.page-head.zy-shell-page-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  min-height: 74px;
  margin: 0 0 16px;
  padding: 0;
  gap: 16px;
  border: 0;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
}

.zy-shell-title-block {
  display: grid;
  min-width: 0;
  gap: 8px;
}

.zy-shell-breadcrumb {
  font-size: 13px;
}

.zy-shell-title-row {
  display: flex;
  align-items: baseline;
  min-width: 0;
  gap: 12px;
}

.page-head h1 {
  margin: 0;
  color: var(--text);
  font-size: 22px;
  font-weight: 600;
  line-height: 1.25;
}

.page-head p {
  margin: 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.5;
}

.page-head-actions,
.zy-shell-page-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 8px;
}

.page-head-actions :deep(.head-actions) {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 8px;
}

@media (max-width: 900px) {
  .page-head.zy-shell-page-head {
    flex-direction: column;
    align-items: flex-start;
    min-height: auto;
  }

  .zy-shell-title-row {
    display: grid;
    gap: 4px;
  }
}
</style>
