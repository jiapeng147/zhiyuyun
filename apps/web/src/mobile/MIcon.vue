<template>
  <TrustedSvg :class="['m-icon', sizeClass]" :markup="svgContent" />
</template>

<script setup>
import { computed } from 'vue'
import TrustedSvg from '../components/TrustedSvg.vue'
import { Icons } from './MobileIcons.js'

const props = defineProps({
  name: { type: String, required: true },
  size: { type: Number, default: 24 }
})

const supportedSizes = [6, 8, 10, 11, 12, 14, 16, 18, 20, 22, 24, 26, 28, 32, 40, 48]
const svgContent = computed(() => Icons[props.name] || Icons.help)
const sizeClass = computed(() => {
  const size = supportedSizes.includes(Number(props.size)) ? Number(props.size) : 24
  return `m-icon-${size}`
})
</script>

<style scoped>
.m-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.m-icon-6 { width: 6px; height: 6px; }
.m-icon-8 { width: 8px; height: 8px; }
.m-icon-10 { width: 10px; height: 10px; }
.m-icon-11 { width: 11px; height: 11px; }
.m-icon-12 { width: 12px; height: 12px; }
.m-icon-14 { width: 14px; height: 14px; }
.m-icon-16 { width: 16px; height: 16px; }
.m-icon-18 { width: 18px; height: 18px; }
.m-icon-20 { width: 20px; height: 20px; }
.m-icon-22 { width: 22px; height: 22px; }
.m-icon-24 { width: 24px; height: 24px; }
.m-icon-26 { width: 26px; height: 26px; }
.m-icon-28 { width: 28px; height: 28px; }
.m-icon-32 { width: 32px; height: 32px; }
.m-icon-40 { width: 40px; height: 40px; }
.m-icon-48 { width: 48px; height: 48px; }
.m-icon :deep(svg) {
  width: 100%;
  height: 100%;
}
</style>
