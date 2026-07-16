<template>
  <header class="page-head zy-page-head" :class="{ compact: !title && !subtitle }">
    <div v-if="title || subtitle" class="zy-page-title-block">
      <span class="zy-page-kicker">Workspace</span>
      <h1 v-if="title">{{ title }}</h1>
      <p v-if="subtitle">{{ subtitle }}</p>
    </div>
    <div v-if="$slots.default" class="page-head-actions zy-page-actions">
      <slot />
    </div>
  </header>
</template>

<script setup>
defineProps({ title: String, subtitle: String })
</script>
