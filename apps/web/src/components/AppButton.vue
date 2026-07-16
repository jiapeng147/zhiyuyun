<template>
  <n-button
    class="app-btn naive-admin-button"
    :class="[type || 'default']"
    :type="naiveType"
    :attr-type="nativeType || 'button'"
    :disabled="disabled"
    :loading="loading"
    :secondary="isSecondary"
    :tertiary="type === 'ghost'"
  >
    <template v-if="loading && loadingText">{{ loadingText }}</template>
    <slot v-else />
  </n-button>
</template>

<script setup>
import { computed } from 'vue'
import { NButton } from 'naive-ui'

const props = defineProps({
  type: String,
  nativeType: { type: String, default: 'button' },
  disabled: Boolean,
  loading: Boolean,
  loadingText: { type: String, default: '处理中...' },
})

const naiveType = computed(() => {
  if (props.type === 'primary') return 'primary'
  if (props.type === 'danger') return 'error'
  if (props.type === 'warn') return 'warning'
  if (props.type === 'success') return 'success'
  return 'default'
})

const isSecondary = computed(() => ['danger', 'warn', 'success'].includes(props.type || ''))
</script>
