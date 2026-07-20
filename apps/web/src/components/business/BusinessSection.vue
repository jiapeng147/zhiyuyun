<template>
  <n-card class="business-section" :class="{ 'is-dense': dense }" :bordered="true">
    <template #header>
      <div class="section-title-block">
        <span v-if="eyebrow">{{ eyebrow }}</span>
        <strong>{{ title }}</strong>
      </div>
    </template>
    <template v-if="$slots.extra" #header-extra>
      <slot name="extra" />
    </template>
    <slot />
  </n-card>
</template>

<script setup>
import { NCard } from 'naive-ui'

defineProps({
  title: { type: String, required: true },
  eyebrow: { type: String, default: '' },
  dense: { type: Boolean, default: false },
})
</script>

<style scoped>
.business-section {
  min-width: 0;
  border-color: #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, .04);
}

.business-section :deep(.n-card-header) {
  align-items: flex-start;
  min-height: 56px;
  padding: 18px 20px 12px;
}

.business-section :deep(.n-card__content) {
  padding: 0 20px 20px;
}

.business-section.is-dense :deep(.n-card-header) {
  min-height: 50px;
  padding: 16px 18px 10px;
}

.business-section.is-dense :deep(.n-card__content) {
  padding: 0 18px 18px;
}

.section-title-block {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.section-title-block span {
  color: #18a058;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.3;
}

.section-title-block strong {
  color: #111827;
  font-size: 16px;
  font-weight: 650;
  line-height: 1.35;
}
</style>
