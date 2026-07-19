<template>
  <button
    v-bind="$attrs"
    type="button"
    role="switch"
    :class="['switch', { on }]"
    :aria-checked="on"
    :aria-label="label || (on ? '已开启' : '已关闭')"
    :disabled="disabled || !isInteractive"
  ></button>
</template>

<script setup>
import { computed, useAttrs } from 'vue'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  on: { type: Boolean, default: true },
  disabled: { type: Boolean, default: false },
  interactive: { type: Boolean, default: false },
  label: { type: String, default: '' },
})
const attrs = useAttrs()
const isInteractive = computed(() => props.interactive || typeof attrs.onClick === 'function')
</script>

<style scoped>
.switch {
  width: 42px;
  height: 22px;
  border: 0;
  border-radius: 999rem;
  padding: 0;
  background: #cbd5e1;
  position: relative;
  display: inline-block;
  vertical-align: middle;
  cursor: pointer;
  transition: background-color 160ms ease-out, opacity 120ms ease-out;
}
.switch::after {
  content: "";
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, .14);
  position: absolute;
  top: 2px;
  left: 2px;
  transition: transform 160ms ease-out;
}
.switch.on {
  background: #0f766e;
}
.switch.on::after {
  transform: translateX(20px);
}
.switch:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}
.switch:active:not(:disabled)::after {
  transform: scale(0.94);
}
.switch.on:active:not(:disabled)::after {
  transform: translateX(20px) scale(0.94);
}
.switch:focus-visible {
  outline: 3px solid rgba(20, 184, 166, 0.35);
  outline-offset: 2px;
}
</style>
