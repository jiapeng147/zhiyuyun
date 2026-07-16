<template>
  <div class="empty-cta zy-empty-state" :class="variant" role="status">
    <div class="empty-cta-icon zy-empty-icon" aria-hidden="true">{{ displayIcon }}</div>
    <div class="zy-empty-copy">
      <h3>{{ title }}</h3>
      <p v-if="description">{{ description }}</p>
      <div v-if="$slots.actions" class="empty-cta-actions">
        <slot name="actions" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  icon: { type: String, default: '' },
  title: { type: String, default: '暂无数据' },
  description: { type: String, default: '完成基础配置后，这里会展示对应数据。' },
  variant: { type: String, default: 'default' },
})

const variantIcons = { default: '∅', search: '⌕', error: '!', dev: '◇' }
const displayIcon = computed(() => props.icon || variantIcons[props.variant] || '∅')
</script>
