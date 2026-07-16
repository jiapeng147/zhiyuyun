<template>
  <n-card class="onboarding-card" :bordered="false">
    <template #header>
      <div class="onboarding-card-title">新手三步完成首次成功</div>
    </template>
    <div class="onboarding-head">
      <div>
        <b>{{ completedCount }}/{{ steps.length }} 已完成</b>
        <p>建议按顺序完成账号绑定、商品同步和自动化配置，先跑通一个最小运营闭环。</p>
      </div>
      <div class="onboarding-progress" :style="{ '--progress': `${progress}%` }"><span>{{ progress }}%</span></div>
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
  </n-card>
</template>

<script setup>
import { computed, ref } from 'vue'
import { NCard } from 'naive-ui'

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
function persist() { localStorage.setItem(STORAGE_KEY, JSON.stringify(done.value)) }
function markDone(key) { if (!done.value.includes(key)) { done.value = [...done.value, key]; persist() } }
function go(step) { markDone(step.key); emit('navigate', step.to) }
function resetProgress() { done.value = []; persist() }
</script>

<style scoped>
.onboarding-card{border:1px solid #dfe6f2;border-radius:6px;background:#fff;box-shadow:none}.onboarding-card :deep(.n-card-header){padding:18px 20px 0}.onboarding-card :deep(.n-card__content){padding:14px 20px 20px}.onboarding-card-title{color:#101828;font-size:16px;font-weight:800;line-height:1.3}.onboarding-head{display:flex;align-items:center;justify-content:space-between;gap:18px;margin-bottom:16px}.onboarding-head b{font-size:18px;color:#16213e}.onboarding-head p{margin:6px 0 0;color:#667085;line-height:1.7}.onboarding-progress{--progress:0%;width:72px;height:72px;border-radius:50%;background:conic-gradient(#2563eb var(--progress),#edf2fb 0);display:flex;align-items:center;justify-content:center;flex:0 0 auto}.onboarding-progress span{width:54px;height:54px;border-radius:50%;background:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;color:#2563eb}.onboarding-steps{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.onboarding-step{display:flex;align-items:flex-start;gap:12px;text-align:left;border:1px solid #dfe6f2;background:#fff;border-radius:6px;padding:14px;cursor:pointer;transition:.16s}.onboarding-step:hover{border-color:#b8c4d8;box-shadow:none;transform:none}.onboarding-step.done{background:#f0fdf4;border-color:#abefc6}.step-check{width:28px;height:28px;border-radius:6px;background:#edf4ff;color:#2563eb;display:flex;align-items:center;justify-content:center;font-weight:900;flex:0 0 auto}.done .step-check{background:#dcfae6;color:#067647}.onboarding-step span:nth-child(2){flex:1}.onboarding-step b{display:block;color:#16213e}.onboarding-step em{display:block;margin-top:5px;color:#667085;font-style:normal;line-height:1.5}.onboarding-step strong{color:#2563eb;white-space:nowrap;font-size:13px}.onboarding-actions{display:flex;justify-content:flex-end;gap:14px;margin-top:12px}@media(max-width:1100px){.onboarding-steps{grid-template-columns:minmax(0, 1fr)}.onboarding-steps > *{min-width:0}}
</style>
