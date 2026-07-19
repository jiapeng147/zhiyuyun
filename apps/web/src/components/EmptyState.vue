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

<style scoped>
.empty-cta {
  min-height: 160px;
  padding: 28px 20px;
  border: 1px dashed var(--line-strong);
  border-radius: 6px;
  background: #fafafa;
  color: var(--muted);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  text-align: center;
  box-sizing: border-box;
}

.empty-cta-icon {
  width: 44px;
  height: 44px;
  border-radius: 6px;
  background: var(--cyan-soft);
  color: var(--cyan);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  font-size: 20px;
  font-weight: 700;
  line-height: 1;
}

.zy-empty-copy {
  display: grid;
  gap: 6px;
  justify-items: center;
}

.zy-empty-copy h3 {
  margin: 0;
  color: var(--text-primary);
  font-size: 15px;
  font-weight: 650;
  line-height: 1.35;
}

.zy-empty-copy p {
  max-width: 420px;
  margin: 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.65;
}

.empty-cta-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
  margin-top: 6px;
}

.empty-cta.error .empty-cta-icon {
  background: var(--red-soft);
  color: var(--red);
}

.empty-cta.dev .empty-cta-icon {
  background: var(--purple-soft);
  color: var(--purple);
}

.empty-cta.search .empty-cta-icon {
  background: var(--blue-soft, #dbeafe);
  color: var(--blue, #2563eb);
}

@media (max-width: 640px) {
  .empty-cta {
    min-height: 136px;
    padding: 22px 16px;
  }
}
</style>
