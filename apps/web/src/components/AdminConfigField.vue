<template>
  <label :class="['ops-config-field', { 'is-wide': wide }]">
    <div class="ops-config-field-head">
      <div class="ops-config-field-copy">
        <div class="ops-config-field-title-row">
          <span class="ops-config-field-label">{{ label }}</span>
          <span v-if="required" class="ops-config-field-required">必填</span>
        </div>
        <p v-if="hint" class="ops-config-field-hint">{{ hint }}</p>
      </div>
      <span v-if="badge" class="ops-config-field-badge">{{ badge }}</span>
    </div>

    <div class="ops-config-field-control">
      <slot />
    </div>

    <p v-if="meta" class="ops-config-field-meta">{{ meta }}</p>
  </label>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  hint: { type: String, default: '' },
  meta: { type: String, default: '' },
  badge: { type: String, default: '' },
  required: Boolean,
  wide: Boolean,
})
</script>

<style scoped>
.ops-config-field {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 18px;
  border-radius: 20px;
  border: 1px solid rgba(223, 232, 247, 0.98);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 251, 255, 0.94));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.82);
  transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease;
}

.ops-config-field:hover {
  transform: translateY(-1px);
  border-color: rgba(243, 205, 189, 0.98);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.9),
    0 14px 28px rgba(94, 50, 31, 0.06);
}

.ops-config-field.is-wide {
  grid-column: 1 / -1;
}

.ops-config-field-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.ops-config-field-copy {
  min-width: 0;
}

.ops-config-field-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.ops-config-field-label {
  display: inline-flex;
  align-items: center;
  min-width: 0;
  font-size: 14px;
  font-weight: 800;
  color: #111111;
  letter-spacing: 0.2px;
}

.ops-config-field-required {
  display: inline-flex;
  align-items: center;
  min-height: 20px;
  padding: 0 8px;
  border-radius: 999px;
  background: rgba(239, 68, 68, 0.08);
  color: #e14d4d;
  font-size: 11px;
  font-weight: 700;
}

.ops-config-field-hint {
  margin: 5px 0 0;
  color: #7786a0;
  font-size: 12px;
  line-height: 1.6;
}

.ops-config-field-badge {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(20, 184, 166, 0.08);
  color: #d45e2c;
  font-size: 11px;
  font-weight: 800;
  white-space: nowrap;
}

.ops-config-field-control {
  display: flex;
  width: 100%;
}

.ops-config-field-control :deep(.config-input),
.ops-config-field-control :deep(.config-textarea) {
  width: 100%;
  border: 1px solid rgba(242, 222, 214, 0.95);
  border-radius: 14px;
  background: #fff;
  color: #5f4033;
  text-align: left;
  transition: border-color .18s ease, box-shadow .18s ease, background .18s ease;
}

.ops-config-field-control :deep(.config-input) {
  height: 46px;
  padding: 0 14px;
}

.ops-config-field-control :deep(.config-textarea) {
  min-height: 112px;
  padding: 12px 14px;
  line-height: 1.72;
  resize: vertical;
}

.ops-config-field-control :deep(.config-input::placeholder),
.ops-config-field-control :deep(.config-textarea::placeholder) {
  color: #a0adc2;
  text-align: left;
}

.ops-config-field-control :deep(.config-input:hover),
.ops-config-field-control :deep(.config-textarea:hover) {
  border-color: #efd3c7;
}

.ops-config-field-control :deep(.config-input:focus),
.ops-config-field-control :deep(.config-input:focus-visible),
.ops-config-field-control :deep(.config-textarea:focus),
.ops-config-field-control :deep(.config-textarea:focus-visible) {
  outline: none;
  border-color: #0f766e;
  box-shadow: 0 0 0 4px rgba(20, 184, 166, 0.11);
  background: #fff;
}

.ops-config-field-control :deep(.secret-input) {
  width: 100%;
  height: 46px;
  border-radius: 14px;
}

.ops-config-field-meta {
  margin: 0;
  color: #5f728f;
  font-size: 12px;
  line-height: 1.6;
}
</style>
