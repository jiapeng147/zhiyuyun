<template>
  <n-card class="business-metric-card" :class="`tone-${tone}`" size="small" :bordered="true">
    <div class="metric-layout">
      <span class="metric-icon" aria-hidden="true">
        <n-icon v-if="icon" :component="icon" :size="20" />
        <span v-else>{{ fallbackIcon }}</span>
      </span>
      <div class="metric-copy">
        <span class="metric-label">{{ label }}</span>
        <strong :class="{ 'is-compact': compactValue || longValue }">{{ value }}</strong>
        <small>{{ hint }}</small>
      </div>
    </div>
  </n-card>
</template>

<script setup>
import { computed } from 'vue'
import { NCard, NIcon } from 'naive-ui'

const props = defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], default: '-' },
  hint: { type: String, default: '' },
  tone: { type: String, default: 'neutral' },
  icon: { type: [Object, Function], default: null },
  fallbackIcon: { type: String, default: '·' },
  compactValue: { type: Boolean, default: false },
})

const longValue = computed(() => {
  const text = String(props.value ?? '')
  return text.length >= 4 && !/^[\d,.\s%]+$/.test(text)
})
</script>

<style scoped>
.business-metric-card {
  min-width: 0;
  border-color: #e5e7eb;
  box-shadow: 0 1px 2px rgba(15, 23, 42, .04);
  transition: border-color 180ms cubic-bezier(0.23, 1, 0.32, 1), box-shadow 180ms cubic-bezier(0.23, 1, 0.32, 1);
}

.metric-layout {
  display: grid;
  grid-template-columns: 40px minmax(0, 1fr);
  gap: 12px;
  align-items: start;
  min-width: 0;
}

.metric-icon {
  display: inline-flex;
  width: 40px;
  height: 40px;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: #f3f4f6;
  color: #374151;
  font-size: 13px;
  font-weight: 700;
}

.metric-copy {
  min-width: 0;
}

.metric-label {
  display: block;
  color: #6b7280;
  font-size: 12px;
  font-weight: 600;
  line-height: 1.35;
}

.metric-copy strong {
  display: block;
  margin-top: 5px;
  color: #111827;
  font-size: 24px;
  font-weight: 700;
  line-height: 1.12;
  overflow-wrap: normal;
  word-break: keep-all;
}

.metric-copy strong.is-compact {
  font-size: 18px;
  line-height: 1.25;
}

.metric-copy small {
  display: block;
  margin-top: 7px;
  color: #6b7280;
  font-size: 12px;
  line-height: 1.45;
}

.tone-blue .metric-icon { background: #e8f2ff; color: #2563eb; }
.tone-green .metric-icon { background: #e7f7ee; color: #18a058; }
.tone-orange .metric-icon { background: #fff7e6; color: #d97706; }
.tone-cyan .metric-icon { background: #ecfeff; color: #0891b2; }
.tone-purple .metric-icon { background: #f3f0ff; color: #7c3aed; }
.tone-red .metric-icon { background: #fff1f3; color: #d03050; }

@media (hover: hover) and (pointer: fine) {
  .business-metric-card:hover {
    border-color: #d1d5db;
    box-shadow: 0 8px 22px rgba(15, 23, 42, .07);
  }
}
</style>
