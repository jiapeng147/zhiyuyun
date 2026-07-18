<template>
  <section class="onboarding-panel" aria-label="新手三步完成首次成功">
    <header class="onboarding-panel-head">
      <div class="onboarding-kicker">Launch Guide</div>
      <div class="onboarding-title">新手三步完成首次成功</div>
    </header>
    <div class="onboarding-head">
      <div>
        <b>{{ completedCount }}/{{ steps.length }} 已完成</b>
        <p>建议按顺序完成账号绑定、商品同步和自动化配置，先跑通一个最小运营闭环。</p>
      </div>
      <div :class="['onboarding-progress', progressClass]"><span>{{ progress }}%</span></div>
    </div>
    <div class="onboarding-steps">
      <button
        v-for="step in steps"
        :key="step.key"
        type="button"
        :class="['onboarding-step', { done: isDone(step.key) }]"
        @click="go(step)"
      >
        <span class="step-check">{{ isDone(step.key) ? '✓' : step.order }}</span>
        <span><b>{{ step.title }}</b><em>{{ step.desc }}</em></span>
        <strong>{{ step.cta }} ›</strong>
      </button>
    </div>
    <div class="onboarding-actions">
      <button type="button" class="link" @click="markDone('seen-guide')">我已阅读指南</button>
      <button type="button" class="link" @click="resetProgress">重置进度</button>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'

const emit = defineEmits(['navigate'])
const STORAGE_KEY = 'xya:onboarding:done'
const readDone = () => {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]') } catch { return [] }
}
const done = ref(readDone())
const steps = [
  { order: 1, key: 'account', title: '添加闲鱼账号', desc: '扫码或手动 Cookie 添加一个可用账号。', cta: '去添加', to: 'accounts' },
  { order: 2, key: 'sync', title: '同步线上商品', desc: '进入商品管理，同步账号下的在售商品。', cta: '去同步', to: 'products' },
  { order: 3, key: 'automation', title: '开启自动化', desc: '创建一条自动回复或自动发货规则并先用预览验证。', cta: '去配置', to: 'auto-reply' }
]
const isDone = key => done.value.includes(key)
const completedCount = computed(() => steps.filter(s => isDone(s.key)).length)
const progress = computed(() => Math.round((completedCount.value / steps.length) * 100))
const progressClass = computed(() => `progress-${progress.value}`)
function persist() { localStorage.setItem(STORAGE_KEY, JSON.stringify(done.value)) }
function markDone(key) { if (!done.value.includes(key)) { done.value = [...done.value, key]; persist() } }
function go(step) { markDone(step.key); emit('navigate', step.to) }
function resetProgress() { done.value = []; persist() }
</script>

<style scoped>
.onboarding-panel {
  --onboarding-text: #101828;
  --onboarding-muted: #667085;
  --onboarding-line: #dfe6f2;
  --onboarding-primary: #2563eb;
  --onboarding-accent: #0f766e;
  --onboarding-ease: cubic-bezier(0.23, 1, 0.32, 1);
  padding: 18px 20px 20px;
  border: 1px solid var(--onboarding-line);
  border-radius: 8px;
  background: linear-gradient(180deg, #ffffff, #f8fbff);
  box-shadow: 0 10px 28px rgba(15, 23, 42, .05);
}

.onboarding-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.onboarding-kicker {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 9px;
  border: 1px solid rgba(15, 118, 110, .16);
  border-radius: 999px;
  background: rgba(236, 253, 245, .8);
  color: var(--onboarding-accent);
  font-size: 12px;
  font-weight: 800;
}

.onboarding-title {
  color: var(--onboarding-text);
  font-size: 16px;
  font-weight: 800;
  line-height: 1.3;
}

.onboarding-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 16px;
}

.onboarding-head b {
  color: #16213e;
  font-size: 18px;
}

.onboarding-head p {
  margin: 6px 0 0;
  color: var(--onboarding-muted);
  line-height: 1.7;
}

.onboarding-progress {
  --progress: 0%;
  display: flex;
  width: 72px;
  height: 72px;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: conic-gradient(var(--onboarding-primary) 0%, #edf2fb 0);
}

.onboarding-progress.progress-33 {
  background: conic-gradient(var(--onboarding-primary) 33%, #edf2fb 0);
}

.onboarding-progress.progress-67 {
  background: conic-gradient(var(--onboarding-primary) 67%, #edf2fb 0);
}

.onboarding-progress.progress-100 {
  background: conic-gradient(var(--onboarding-primary) 100%, #edf2fb 0);
}

.onboarding-progress span {
  display: flex;
  width: 54px;
  height: 54px;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #fff;
  color: var(--onboarding-primary);
  font-weight: 800;
}

.onboarding-steps {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.onboarding-step {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  min-width: 0;
  padding: 14px;
  border: 1px solid var(--onboarding-line);
  border-radius: 8px;
  background: #fff;
  color: inherit;
  cursor: pointer;
  text-align: left;
  transition: transform 150ms var(--onboarding-ease), border-color 150ms var(--onboarding-ease), background-color 150ms var(--onboarding-ease), box-shadow 150ms var(--onboarding-ease);
}

.onboarding-step:active {
  transform: scale(.98);
}

.onboarding-step.done {
  border-color: #abefc6;
  background: #f0fdf4;
}

.step-check {
  display: flex;
  width: 28px;
  height: 28px;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: #edf4ff;
  color: var(--onboarding-primary);
  font-weight: 900;
}

.done .step-check {
  background: #dcfae6;
  color: #067647;
}

.onboarding-step span:nth-child(2) {
  flex: 1;
  min-width: 0;
}

.onboarding-step b {
  display: block;
  color: #16213e;
}

.onboarding-step em {
  display: block;
  margin-top: 5px;
  color: var(--onboarding-muted);
  font-style: normal;
  line-height: 1.5;
}

.onboarding-step strong {
  color: var(--onboarding-primary);
  font-size: 13px;
  white-space: nowrap;
}

.onboarding-actions {
  display: flex;
  justify-content: flex-end;
  gap: 14px;
  margin-top: 12px;
}

.link {
  border: 0;
  background: transparent;
  color: var(--onboarding-primary);
  cursor: pointer;
  font-size: 13px;
  font-weight: 650;
  transition: transform 150ms var(--onboarding-ease), color 150ms var(--onboarding-ease);
}

.link:active {
  transform: scale(.98);
}

@media (hover: hover) and (pointer: fine) {
  .onboarding-step:hover {
    border-color: #b8c4d8;
    box-shadow: 0 10px 24px rgba(15, 23, 42, .07);
  }

  .link:hover {
    color: #1d4ed8;
  }
}

@media (max-width: 1100px) {
  .onboarding-steps {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 640px) {
  .onboarding-panel {
    padding: 14px;
  }

  .onboarding-panel-head,
  .onboarding-head {
    align-items: flex-start;
    flex-direction: column;
  }

  .onboarding-actions {
    justify-content: flex-start;
    flex-wrap: wrap;
  }
}
</style>
