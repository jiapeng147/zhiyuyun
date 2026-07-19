<template>
  <Teleport to="body">
    <div v-if="state.visible" class="global-confirm-mask" @click.self="handleMaskClick">
      <section
        ref="modalRef"
        class="global-confirm-modal"
        role="dialog"
        aria-modal="true"
        tabindex="-1"
        :aria-labelledby="titleId"
        :aria-describedby="state.description ? descriptionId : undefined"
        @keydown="handleKeydown"
      >
        <button class="global-confirm-close" aria-label="关闭确认对话框" @click="cancel"><Icon name="close" /></button>

        <!-- 警告图标（仅 confirm/alert 类型） -->
        <div v-if="state.type !== 'prompt'" class="global-confirm-icon" :class="{ dangerous: state.dangerous }">
          <Icon :name="state.dangerous ? 'warning' : 'help'" />
        </div>

        <h2 :id="titleId">{{ state.title }}</h2>

        <p v-if="state.description" :id="descriptionId" class="global-confirm-desc">{{ state.description }}</p>

        <!-- prompt 输入框 -->
        <div v-if="state.type === 'prompt'" class="global-confirm-input-wrap">
          <input
            v-model="state.value"
            class="global-confirm-input"
            :placeholder="state.placeholder"
            @keyup.enter="doConfirm"
          />
        </div>

        <div class="global-confirm-actions">
          <AppButton v-if="state.type !== 'alert'" ref="cancelActionRef" @click="cancel">取消</AppButton>
          <AppButton
            ref="confirmActionRef"
            :type="confirmBtnType"
            @click="doConfirm"
          >
            {{ state.confirmText || (state.type === 'prompt' ? '确定' : '确认') }}
          </AppButton>
        </div>
      </section>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { useConfirmState } from '../composables/confirmState.js'
import Icon from './Icon.vue'
import AppButton from './AppButton.vue'

const { state, cancel, doConfirm } = useConfirmState()

const modalRef = ref(null)
const cancelActionRef = ref(null)
const confirmActionRef = ref(null)
let previouslyFocusedElement = null
const titleId = computed(() => `global-confirm-title-${state.requestId}`)
const descriptionId = computed(() => `global-confirm-description-${state.requestId}`)
const focusableSelector = [
  'button:not([disabled])',
  '[href]',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])'
].join(',')

const confirmBtnType = computed(() => {
  if (state.dangerous) return 'danger'
  return 'primary'
})

function focusControl(control) {
  const element = control?.$el ?? control
  element?.focus?.()
}

watch(
  () => state.visible,
  async (visible) => {
    if (!visible) {
      await nextTick()
      if (previouslyFocusedElement?.isConnected) previouslyFocusedElement.focus()
      previouslyFocusedElement = null
      return
    }

    previouslyFocusedElement = document.activeElement
    await nextTick()
    const safeAction = state.type === 'alert' ? confirmActionRef.value : cancelActionRef.value
    focusControl(safeAction)
  },
  { flush: 'post' }
)

function handleMaskClick() {
  if (state.type !== 'alert') cancel()
}

function handleKeydown(event) {
  if (event.key === 'Escape') {
    event.preventDefault()
    event.stopPropagation()
    cancel()
    return
  }

  trapFocus(event)
}

function trapFocus(event) {
  if (event.key !== 'Tab' || !modalRef.value) return

  const focusable = [...modalRef.value.querySelectorAll(focusableSelector)]
    .filter((element) => element.getAttribute('aria-hidden') !== 'true')
  const firstFocusable = focusable[0]
  const lastFocusable = focusable.at(-1)

  if (!firstFocusable || !lastFocusable) {
    event.preventDefault()
    modalRef.value.focus()
    return
  }

  const focusIsOutside = !modalRef.value.contains(document.activeElement)
  if (event.shiftKey && (focusIsOutside || document.activeElement === firstFocusable)) {
    event.preventDefault()
    lastFocusable.focus()
  } else if (!event.shiftKey && (focusIsOutside || document.activeElement === lastFocusable)) {
    event.preventDefault()
    firstFocusable.focus()
  }
}
</script>

<style scoped>
.global-confirm-mask {
  position: fixed;
  inset: 0;
  z-index: 2000;
  padding: 24px;
  background: rgba(17, 24, 39, .48);
  backdrop-filter: blur(2px);
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}

.global-confirm-modal {
  position: relative;
  width: min(430px, 100%);
  max-height: calc(100vh - 48px);
  overflow: auto;
  padding: 20px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #fff;
  box-shadow: var(--shadow-md);
  text-align: center;
  color: var(--text);
  box-sizing: border-box;
}

.global-confirm-close {
  position: absolute;
  right: 14px;
  top: 14px;
  width: 32px;
  height: 32px;
  border: 1px solid var(--line);
  border-radius: 4px;
  background: #fff;
  color: var(--muted);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background-color 160ms ease-out, border-color 160ms ease-out, color 160ms ease-out, transform 120ms ease-out;
}

@media (hover: hover) and (pointer: fine) {
  .global-confirm-close:hover {
    color: var(--red);
    border-color: #f5c2cc;
    background: var(--red-soft);
  }
}

.global-confirm-close:active {
  transform: scale(0.97);
}

.global-confirm-close .ui-icon {
  width: 18px;
  height: 18px;
}

.global-confirm-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  margin: 4px auto 14px;
  border-radius: 50%;
  background: var(--cyan-soft);
  color: var(--cyan);
}

.global-confirm-icon.dangerous {
  background: var(--red-soft);
  color: var(--red);
}

.global-confirm-icon .ui-icon {
  width: 24px;
  height: 24px;
}

.global-confirm-modal h2 {
  margin: 0 32px 10px;
  font-size: 18px;
  font-weight: 600;
  line-height: 1.35;
  color: var(--text);
  text-align: center;
}

.global-confirm-desc {
  margin: 0 0 18px;
  font-size: 13px;
  line-height: 1.7;
  white-space: pre-wrap;
  color: var(--muted);
  text-align: center;
}

.global-confirm-input-wrap {
  margin: 0 0 18px;
}

.global-confirm-input {
  width: 100%;
  min-height: 34px;
  height: 34px;
  padding: 0 10px;
  border: 1px solid var(--line);
  border-radius: 4px;
  background: #fff;
  font-size: 14px;
  color: var(--text);
  outline: none;
  box-sizing: border-box;
  transition: border-color 160ms ease-out, box-shadow 160ms ease-out;
}

.global-confirm-input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 2px rgba(24, 160, 88, .14);
}

.global-confirm-input::placeholder {
  color: var(--muted-foreground);
}

.global-confirm-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 18px;
}

.global-confirm-actions .app-btn {
  min-width: 96px;
}

@media (max-width: 900px) {
  .global-confirm-mask {
    align-items: flex-end;
    padding: 0;
  }
  .global-confirm-modal {
    width: 100%;
    max-width: 100vw;
    max-height: 90vh;
    overflow-y: auto;
    border-radius: 8px 8px 0 0;
    padding: 32px 20px 22px;
  }
  .global-confirm-modal h2 {
    font-size: 17px;
  }
  .global-confirm-desc {
    font-size: 13px;
    line-height: 1.7;
    margin-bottom: 22px;
  }
  .global-confirm-actions {
    flex-wrap: wrap;
  }
  .global-confirm-actions .app-btn {
    flex: 1 1 auto;
    min-width: 0;
    height: 44px;
  }
}
</style>
