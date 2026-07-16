<template>
  <header class="page-head naive-admin-page-head" :class="{ compact: !title && !subtitle }">
    <div v-if="title || subtitle" class="naive-admin-title-block">
      <n-breadcrumb v-if="showBreadcrumb" class="naive-admin-breadcrumb">
        <n-breadcrumb-item>控制台</n-breadcrumb-item>
        <n-breadcrumb-item>{{ title || '页面' }}</n-breadcrumb-item>
      </n-breadcrumb>
      <div class="naive-admin-title-row">
        <h1 v-if="title">{{ title }}</h1>
        <p v-if="subtitle">{{ subtitle }}</p>
      </div>
    </div>
    <n-space v-if="$slots.default" class="page-head-actions naive-admin-page-actions" :size="8" align="center">
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
