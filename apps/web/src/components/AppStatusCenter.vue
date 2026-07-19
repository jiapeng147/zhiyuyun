<template>
  <div class="app-status-center" aria-atomic="true">
    <section v-if="loading" class="app-status-banner loading" role="status" aria-live="polite">
      <span class="app-status-spinner" aria-hidden="true"></span>
      <div class="app-status-message">正在同步数据...</div>
    </section>

    <section v-if="!online" class="app-status-banner offline" role="alert" aria-live="assertive">
      <span class="app-status-dot" aria-hidden="true"></span>
      <div>
        <strong>当前网络已断开</strong>
        <p>无法提交或刷新数据；网络恢复后页面会自动继续连接。</p>
      </div>
    </section>

    <section
      v-if="notice"
      class="app-status-banner notice"
      :class="notice.type || 'info'"
      :role="isUrgent ? 'alert' : 'status'"
      :aria-live="isUrgent ? 'assertive' : 'polite'"
    >
      <div class="app-status-message">{{ notice.text }}</div>
      <button
        v-if="notice.retry"
        type="button"
        class="app-status-retry"
        :disabled="retrying || !online"
        :aria-busy="retrying"
        @click="emit('retry')"
      >
        {{ retrying ? '重试中...' : '重试' }}
      </button>
      <button type="button" class="app-status-close" aria-label="关闭提示" @click="emit('dismiss')">×</button>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  online: { type: Boolean, default: true },
  notice: { type: Object, default: null },
  loading: Boolean,
  retrying: Boolean,
})
const emit = defineEmits(['dismiss', 'retry'])
const isUrgent = computed(() => ['error', 'warn'].includes(props.notice?.type))
</script>

<style scoped>
.app-status-center {
  position: fixed;
  top: max(14px, env(safe-area-inset-top));
  left: 50%;
  z-index: 2200;
  width: min(560px, calc(100vw - 32px));
  transform: translateX(-50%);
  display: grid;
  gap: 10px;
  pointer-events: none;
}

.app-status-banner {
  min-height: 52px;
  padding: 12px 14px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: rgba(255, 255, 255, .97);
  box-shadow: var(--shadow-md);
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 12px;
  pointer-events: auto;
  backdrop-filter: blur(12px);
}

.app-status-banner.offline,
.app-status-banner.warn {
  border-color: rgba(245, 158, 11, .34);
  background: rgba(255, 251, 235, .98);
  color: #9a6700;
}

.app-status-banner.info,
.app-status-banner.loading {
  border-color: rgba(24, 160, 88, .22);
  background: rgba(240, 253, 244, .98);
  color: var(--primary);
}

.app-status-banner.error {
  border-color: rgba(220, 38, 38, .26);
  background: rgba(254, 242, 242, .98);
  color: var(--red);
}

.app-status-banner.success {
  border-color: rgba(24, 160, 88, .24);
  background: rgba(240, 253, 244, .98);
  color: var(--green);
}

.app-status-banner.loading {
  min-height: 42px;
  padding-block: 9px;
}

.app-status-spinner {
  width: 16px;
  height: 16px;
  flex: 0 0 auto;
  border: 2px solid rgba(24, 160, 88, .28);
  border-top-color: #ff6d2f;
  border-radius: 50%;
  animation: app-status-spin .8s linear infinite;
}

.app-status-retry {
  min-width: 64px;
  height: 32px;
  padding: 0 12px;
  border: 1px solid currentColor;
  border-radius: 4px;
  background: transparent;
  color: inherit;
  font-weight: 650;
  transition: background-color 160ms ease-out, opacity 120ms ease-out, transform 120ms ease-out;
}

.app-status-retry:active:not(:disabled) {
  transform: scale(0.97);
}

.app-status-retry:disabled {
  cursor: not-allowed;
  opacity: .55;
}

@keyframes app-status-spin {
  to { transform: rotate(360deg); }
}

.app-status-dot {
  width: 10px;
  height: 10px;
  flex: 0 0 auto;
  border-radius: 50%;
  background: #e48a00;
  box-shadow: 0 0 0 5px rgba(228, 138, 0, .13);
}

.app-status-banner strong,
.app-status-banner p {
  margin: 0;
}

.app-status-banner p {
  margin-top: 2px;
  font-size: 12px;
  line-height: 1.5;
  font-weight: 500;
}

.app-status-message {
  min-width: 0;
  flex: 1;
  line-height: 1.5;
  font-weight: 700;
}

.app-status-close {
  width: 32px;
  height: 32px;
  flex: 0 0 auto;
  border: 0;
  border-radius: 4px;
  background: transparent;
  color: inherit;
  font-size: 24px;
  line-height: 1;
  transition: background-color 160ms ease-out, transform 120ms ease-out;
}

.app-status-close:active {
  transform: scale(0.97);
}

@media (hover: hover) and (pointer: fine) {
  .app-status-retry:hover:not(:disabled),
  .app-status-close:hover {
    background: rgba(15, 23, 42, .06);
  }
}

@media (prefers-reduced-motion: reduce) {
  .app-status-spinner {
    animation-duration: 1.6s;
  }
}

@media (max-width: 600px) {
  .app-status-center {
    top: max(8px, env(safe-area-inset-top));
    width: calc(100vw - 20px);
  }
}
</style>
