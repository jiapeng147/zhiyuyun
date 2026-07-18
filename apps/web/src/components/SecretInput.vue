<template>
  <label class="secret-input">
    <input
      :value="modelValue"
      :placeholder="placeholder"
      :autocomplete="autocomplete || 'off'"
      :class="['secret-input-control', { masked: !revealed }]"
      spellcheck="false"
      autocapitalize="off"
      @input="emit('update:modelValue', $event.target.value)"
    />
    <button type="button" class="secret-input-toggle" @click="revealed = !revealed">
      {{ revealed ? '隐藏' : '显示' }}
    </button>
  </label>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  autocomplete: { type: String, default: 'off' }
})

const emit = defineEmits(['update:modelValue'])
const revealed = ref(false)
</script>

<style scoped>
.secret-input {
  display: flex;
  align-items: stretch;
  width: 100%;
  height: 46px;
  border: 1px solid var(--line, #E5E5E5);
  background: linear-gradient(180deg, #ffffff, #FFFFFF);
  border-radius: 8px;
  overflow: hidden;
  transition: border-color .18s ease, box-shadow .18s ease;
}

.secret-input:hover {
  border-color: #ead2c7;
}

.secret-input:focus-within {
  border-color: var(--primary, #0f766e);
  box-shadow: 0 0 0 3px rgba(20, 184, 166, .12);
}

.secret-input-control {
  flex: 1;
  min-width: 0;
  height: 100%;
  border: 0;
  background: transparent;
  outline: none;
  padding: 0 14px;
  color: #5f4033;
  font-size: 14px;
  text-align: left;
}

.secret-input-control::placeholder {
  color: #a0adc2;
  text-align: left;
}

.secret-input-control.masked {
  -webkit-text-security: disc;
  letter-spacing: 1px;
}

.secret-input-toggle {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 16px;
  border: 0;
  border-left: 1px solid var(--line, #E5E5E5);
  background: linear-gradient(180deg, #f7faff, #eef4ff);
  color: #d45e2c;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: background .15s ease, color .15s ease;
  white-space: nowrap;
}

.secret-input-toggle:hover {
  background: #eaf2ff;
  color: #0f766e;
}

.secret-input-toggle:active {
  background: #dbe8ff;
}
</style>
