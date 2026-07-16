<template>
  <div :class="['auth-shell-v3', 'auth-v8-shell', `auth-shell-${pageKey}`]">
    <header class="auth-v3-topbar">
      <button type="button" class="auth-v3-brand" @click="emit('navigate', 'data')">
        <span>ZY</span>
        <strong>智鱼云</strong>
      </button>
      <button type="button" class="auth-v3-ghost" @click="openDoc('用户协议')">服务条款</button>
    </header>

    <main class="auth-v3-main auth-v4-main">
      <section class="auth-v3-showcase" aria-label="产品概览">
        <div class="auth-v3-eyebrow">Zhiyuyun Admin</div>
        <h1>
          {{ titleLead }}
          <span v-if="titleAccent">{{ titleAccent }}</span>
          <template v-if="titleTail"> {{ titleTail }}</template>
        </h1>
        <p>{{ description }}</p>

        <div class="auth-v3-console" aria-hidden="true">
          <div class="auth-v3-console-head">
            <i></i><i></i><i></i>
            <span>operations map</span>
          </div>
          <div class="auth-v3-console-grid">
            <div class="auth-v3-metric">
              <small>Accounts</small>
              <b>24</b>
              <em>+12.8%</em>
            </div>
            <div class="auth-v3-metric">
              <small>Orders</small>
              <b>1,286</b>
              <em>+8.4%</em>
            </div>
            <div class="auth-v3-metric wide">
              <small>Automation</small>
              <span><i style="width:78%"></i></span>
            </div>
          </div>
          <div class="auth-v3-timeline">
            <span></span><span></span><span></span><span></span>
          </div>
        </div>

        <div class="auth-v3-feature-row auth-v4-feature-row">
          <div v-for="item in featureItems" :key="item.title">
            <b>{{ item.title }}</b>
            <span>{{ item.desc }}</span>
          </div>
        </div>
      </section>

      <section class="auth-v3-panel">
        <div class="auth-v3-panel-head">
          <span class="auth-v3-brand-dot">ZY</span>
          <div>
            <h2>{{ pageKey === 'register' ? '创建账号' : '登录后台' }}</h2>
            <p>{{ pageKey === 'register' ? '使用邮箱验证码开通账户' : '进入你的运营工作台' }}</p>
          </div>
        </div>
        <slot />
      </section>
    </main>

    <footer class="auth-v3-footer">
      <span>© {{ resolvedCopyrightYear }} Zhiyuyun</span>
      <button type="button" @click="openDoc('隐私政策')">隐私政策</button>
      <button type="button" @click="openDoc('用户协议')">用户协议</button>
    </footer>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { openLegalDoc } from './authContent.js'
import { getCopyrightYear } from '../../utils/appMeta.js'

const props = defineProps({
  pageKey: { type: String, required: true },
  titleLead: { type: String, required: true },
  titleAccent: { type: String, default: '' },
  titleTail: { type: String, default: '' },
  description: { type: String, required: true },
  copyrightYear: { type: [String, Number], default: null },
  legalDescription: { type: String, default: '' },
})

const emit = defineEmits(['navigate'])
const resolvedCopyrightYear = computed(() => `${props.copyrightYear ?? getCopyrightYear()}`)
const featureItems = computed(() => [
  { title: '多账号', desc: '统一连接、同步与健康状态' },
  { title: '自动化', desc: '发货、回复、任务集中编排' },
  { title: '实时监控', desc: '消息、订单、异常即时反馈' },
])

function openDoc(title) {
  openLegalDoc(title, props.legalDescription)
}
</script>

<style scoped>
.auth-v8-shell {
  min-height: 100vh;
  background: #f6f7f9;
  color: #101828;
}

.auth-v8-shell .auth-v3-topbar,
.auth-v8-shell .auth-v3-panel,
.auth-v8-shell .auth-v3-console,
.auth-v8-shell .auth-v3-metric,
.auth-v8-shell .auth-v3-feature-row > div {
  border: 1px solid #dfe6f2;
  border-radius: 6px;
  background: #fff;
  box-shadow: none;
}

.auth-v8-shell .auth-v3-brand span,
.auth-v8-shell .auth-v3-brand-dot {
  border-radius: 6px;
  background: #2563eb;
  color: #fff;
  box-shadow: none;
}

.auth-v8-shell .auth-v3-ghost,
.auth-v8-shell .auth-v3-console-head,
.auth-v8-shell .auth-v3-console-grid,
.auth-v8-shell .auth-v3-timeline span {
  border-radius: 6px;
  box-shadow: none;
}

.auth-v8-shell .auth-v3-showcase h1,
.auth-v8-shell .auth-v3-panel-head h2,
.auth-v8-shell .auth-v3-brand strong {
  color: #101828;
  letter-spacing: 0;
}

.auth-v8-shell .auth-v3-showcase h1 span,
.auth-v8-shell .auth-v3-eyebrow,
.auth-v8-shell .auth-v3-metric em {
  color: #2563eb;
}

.auth-v8-shell .auth-v3-console {
  background: #0f172a;
  color: #fff;
}

.auth-v8-shell :deep(input),
.auth-v8-shell :deep(button),
.auth-v8-shell :deep(.app-btn) {
  border-radius: 6px;
  box-shadow: none;
}

.auth-v8-shell :deep(.app-btn.primary),
.auth-v8-shell :deep(button[type='submit']) {
  background: #2563eb;
  border-color: #2563eb;
  color: #fff;
}
</style>
