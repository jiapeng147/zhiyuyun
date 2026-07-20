<template>
  <section class="business-status-strip" aria-label="业务状态">
    <div
      v-for="item in items"
      :key="item.key || item.label"
      class="status-cell"
      :class="`tone-${item.tone || 'neutral'}`"
    >
      <span>{{ item.label }}</span>
      <strong>{{ item.value }}</strong>
    </div>
  </section>
</template>

<script setup>
defineProps({
  items: { type: Array, default: () => [] },
})
</script>

<style scoped>
.business-status-strip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #e5e7eb;
  box-shadow: 0 1px 2px rgba(15, 23, 42, .04);
}

.status-cell {
  display: flex;
  min-width: 0;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  background: #ffffff;
}

.status-cell span {
  color: #6b7280;
  font-size: 12px;
  font-weight: 600;
  line-height: 1.35;
}

.status-cell strong {
  color: #111827;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.35;
  text-align: right;
}

.tone-green strong { color: #18a058; }
.tone-orange strong { color: #d97706; }
.tone-red strong { color: #d03050; }
.tone-blue strong { color: #2563eb; }

@media (max-width: 720px) {
  .business-status-strip {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
