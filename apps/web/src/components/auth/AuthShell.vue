<template>
  <div :class="['auth-shell-v3', 'auth-v8-shell', `auth-shell-${pageKey}`]">
    <header class="auth-v3-topbar">
      <button type="button" class="auth-v3-brand" @click="emit('navigate', 'data')">
        <span><img src="/xya/brand/zhiyuyun-mark.svg?v=20260717-auth" alt="" /></span>
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
  min-height: 100vh !important;
  display: grid !important;
  grid-template-rows: 64px minmax(0, 1fr) 48px !important;
  background: #f4f7fb !important;
  color: #101828;
  overflow-x: hidden;
}

.auth-v8-shell .auth-v3-topbar,
.auth-v8-shell .auth-v3-footer {
  height: auto !important;
  min-height: 0 !important;
  padding: 0 36px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: space-between !important;
  gap: 18px !important;
  border: 0 !important;
  background: rgba(255, 255, 255, .92) !important;
}

.auth-v8-shell .auth-v3-topbar {
  border-bottom: 1px solid #e6ebf2 !important;
}

.auth-v8-shell .auth-v3-footer {
  justify-content: center !important;
  border-top: 1px solid #e6ebf2 !important;
  color: #667085;
  font-size: 12px;
}

.auth-v8-shell .auth-v3-footer button,
.auth-v8-shell .auth-v3-ghost,
.auth-v8-shell .auth-v3-brand {
  appearance: none;
  border: 0;
  background: transparent;
  font: inherit;
}

.auth-v8-shell .auth-v3-brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  padding: 0;
  color: #101828;
}

.auth-v8-shell .auth-v3-brand span,
.auth-v8-shell .auth-v3-brand-dot {
  width: 34px !important;
  height: 34px !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  flex: 0 0 auto !important;
  border: 1px solid #d8e2f1 !important;
  border-radius: 8px !important;
  background: #fff !important;
  color: #2563eb !important;
  box-shadow: 0 1px 2px rgba(16, 24, 40, .06) !important;
}

.auth-v8-shell .auth-v3-brand span img {
  width: 24px;
  height: 24px;
  display: block;
}

.auth-v8-shell .auth-v3-brand strong {
  color: #101828 !important;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0;
}

.auth-v8-shell .auth-v3-ghost,
.auth-v8-shell .auth-v3-footer button {
  min-height: 32px;
  padding: 0 10px;
  color: #475467;
  border-radius: 6px !important;
}

.auth-v8-shell .auth-v3-ghost:hover,
.auth-v8-shell .auth-v3-footer button:hover {
  color: #2563eb;
  background: #eef4ff;
}

.auth-v8-shell .auth-v3-main {
  width: min(1180px, calc(100vw - 48px)) !important;
  margin: 28px auto !important;
  display: grid !important;
  grid-template-columns: minmax(0, 1fr) 430px !important;
  gap: 18px !important;
  align-items: stretch !important;
}

.auth-v8-shell .auth-v3-showcase,
.auth-v8-shell .auth-v3-panel {
  min-width: 0;
  border: 1px solid #dfe6f2 !important;
  border-radius: 8px !important;
  background: #fff !important;
  box-shadow: 0 18px 40px rgba(15, 23, 42, .08) !important;
}

.auth-v8-shell .auth-v3-showcase {
  min-height: 560px !important;
  padding: 40px !important;
  display: grid !important;
  align-content: start !important;
  gap: 24px !important;
  overflow: hidden;
}

.auth-v8-shell .auth-v3-eyebrow {
  width: fit-content;
  padding: 5px 10px;
  color: #2563eb !important;
  background: #eef4ff;
  border: 1px solid #dbe7ff;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: .08em;
  text-transform: uppercase;
}

.auth-v8-shell .auth-v3-showcase h1 {
  max-width: 620px;
  margin: 0 !important;
  color: #101828 !important;
  font-size: clamp(36px, 4vw, 56px) !important;
  line-height: 1.08 !important;
  font-weight: 800 !important;
  letter-spacing: 0 !important;
}

.auth-v8-shell .auth-v3-showcase h1 span {
  color: #2563eb !important;
}

.auth-v8-shell .auth-v3-showcase p {
  max-width: 560px;
  margin: -8px 0 0;
  color: #667085;
  font-size: 15px;
  line-height: 1.8;
}

.auth-v8-shell .auth-v3-console {
  margin-top: 6px;
  border: 1px solid #1e2d49 !important;
  border-radius: 8px !important;
  background: #101828 !important;
  color: #fff;
  box-shadow: 0 18px 38px rgba(16, 24, 40, .22) !important;
  overflow: hidden;
}

.auth-v8-shell .auth-v3-console-head {
  min-height: 42px;
  padding: 0 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, .1);
  color: #98a2b3;
  font-size: 12px;
}

.auth-v8-shell .auth-v3-console-head i {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #475467;
}

.auth-v8-shell .auth-v3-console-head i:first-child {
  background: #ef4444;
}

.auth-v8-shell .auth-v3-console-head i:nth-child(2) {
  background: #f59e0b;
}

.auth-v8-shell .auth-v3-console-head i:nth-child(3) {
  background: #22c55e;
}

.auth-v8-shell .auth-v3-console-head span {
  margin-left: auto;
  letter-spacing: .04em;
  text-transform: uppercase;
}

.auth-v8-shell .auth-v3-console-grid {
  padding: 16px;
  display: grid !important;
  grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  gap: 12px !important;
}

.auth-v8-shell .auth-v3-metric {
  min-height: 104px;
  padding: 14px;
  border: 1px solid rgba(255, 255, 255, .1) !important;
  border-radius: 8px !important;
  background: rgba(255, 255, 255, .06) !important;
  display: grid;
  align-content: space-between;
  box-shadow: none !important;
}

.auth-v8-shell .auth-v3-metric small,
.auth-v8-shell .auth-v3-metric em {
  color: #98a2b3;
  font-size: 12px;
  font-style: normal;
}

.auth-v8-shell .auth-v3-metric b {
  color: #fff;
  font-size: 28px;
  line-height: 1;
}

.auth-v8-shell .auth-v3-metric em {
  color: #60a5fa !important;
}

.auth-v8-shell .auth-v3-metric.wide {
  grid-column: 1 / -1;
  min-height: 78px;
}

.auth-v8-shell .auth-v3-metric.wide span {
  height: 8px;
  border-radius: 999px;
  background: rgba(255, 255, 255, .12);
  overflow: hidden;
}

.auth-v8-shell .auth-v3-metric.wide span i {
  height: 100%;
  display: block;
  border-radius: inherit;
  background: #60a5fa;
}

.auth-v8-shell .auth-v3-timeline {
  padding: 0 16px 16px;
  display: grid;
  gap: 8px;
}

.auth-v8-shell .auth-v3-timeline span {
  height: 10px;
  border-radius: 999px !important;
  background: rgba(255, 255, 255, .1);
}

.auth-v8-shell .auth-v3-timeline span:nth-child(1) {
  width: 86%;
}

.auth-v8-shell .auth-v3-timeline span:nth-child(2) {
  width: 66%;
}

.auth-v8-shell .auth-v3-timeline span:nth-child(3) {
  width: 74%;
}

.auth-v8-shell .auth-v3-timeline span:nth-child(4) {
  width: 52%;
}

.auth-v8-shell .auth-v3-feature-row {
  display: grid !important;
  grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
  gap: 12px !important;
}

.auth-v8-shell .auth-v3-feature-row > div {
  min-height: 86px;
  padding: 14px !important;
  display: grid;
  align-content: start;
  gap: 6px;
  border: 1px solid #dfe6f2 !important;
  border-radius: 8px !important;
  background: #f8fbff !important;
  box-shadow: none !important;
}

.auth-v8-shell .auth-v3-feature-row b {
  color: #101828;
  font-size: 14px;
}

.auth-v8-shell .auth-v3-feature-row span {
  color: #667085;
  font-size: 12px;
  line-height: 1.55;
}

.auth-v8-shell .auth-v3-panel {
  padding: 28px !important;
  display: grid;
  align-content: start;
}

.auth-v8-shell .auth-v3-panel-head {
  margin-bottom: 20px !important;
  padding-bottom: 18px !important;
  display: flex !important;
  align-items: center !important;
  gap: 12px !important;
  border-bottom: 1px solid #edf0f5 !important;
}

.auth-v8-shell .auth-v3-brand-dot {
  background: #2563eb !important;
  color: #fff !important;
  border-color: #2563eb !important;
  font-weight: 800;
  font-size: 12px;
}

.auth-v8-shell .auth-v3-panel-head h2 {
  margin: 0;
  color: #101828 !important;
  font-size: 22px;
  line-height: 1.25;
  letter-spacing: 0;
}

.auth-v8-shell .auth-v3-panel-head p {
  margin: 5px 0 0;
  color: #667085;
  font-size: 13px;
}

.auth-v8-shell :deep(input),
.auth-v8-shell :deep(button),
.auth-v8-shell :deep(.app-btn) {
  border-radius: 6px;
  box-shadow: none;
}

.auth-v8-shell :deep(.app-btn.primary),
.auth-v8-shell :deep(button[type='submit']) {
  background: #2563eb !important;
  border-color: #2563eb !important;
  color: #fff !important;
}

.auth-v8-shell :deep(.auth-form) {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 14px;
}

.auth-v8-shell :deep(.auth-field) {
  min-height: 50px !important;
  padding: 0 14px !important;
  border: 1px solid #dfe6f2 !important;
  border-radius: 8px !important;
  background: #fff !important;
}

.auth-v8-shell :deep(.auth-field-control) {
  min-height: 48px;
  border: 0 !important;
}

.auth-v8-shell :deep(.auth-field input) {
  color: #101828;
  font-size: 14px;
}

.auth-v8-shell :deep(.auth-field-icon) {
  color: #98a2b3;
}

.auth-v8-shell :deep(.auth-eye-btn) {
  width: 34px;
  height: 34px;
  color: #667085;
  background: transparent;
  border: 0;
}

.auth-v8-shell :deep(.auth-inline-row) {
  min-height: 30px;
}

.auth-v8-shell :deep(.auth-check) {
  color: #475467;
}

.auth-v8-shell :deep(.auth-submit) {
  height: 46px !important;
  margin-top: 0 !important;
  border: 0 !important;
  border-radius: 8px !important;
  font-weight: 700;
  letter-spacing: 0;
}

.auth-v8-shell :deep(.auth-text-link) {
  color: #2563eb;
}

.auth-v8-shell :deep(.auth-agreement) {
  margin-top: 16px;
  color: #667085;
  font-size: 12px;
  line-height: 1.7;
}

.auth-v8-shell :deep(.form-error) {
  margin: 0 0 14px;
  border-radius: 8px;
}

@media (max-width: 980px) {
  .auth-v8-shell {
    grid-template-rows: 56px minmax(0, 1fr) auto !important;
  }

  .auth-v8-shell .auth-v3-topbar,
  .auth-v8-shell .auth-v3-footer {
    padding: 0 18px !important;
  }

  .auth-v8-shell .auth-v3-main {
    width: min(100%, calc(100vw - 28px)) !important;
    margin: 18px auto !important;
    grid-template-columns: minmax(0, 1fr) !important;
  }

  .auth-v8-shell .auth-v3-showcase {
    display: none !important;
  }

  .auth-v8-shell .auth-v3-panel {
    width: min(100%, 460px);
    margin: 0 auto;
  }
}

@media (max-width: 520px) {
  .auth-v8-shell {
    background: #fff !important;
  }

  .auth-v8-shell .auth-v3-ghost {
    display: none;
  }

  .auth-v8-shell .auth-v3-main {
    width: 100% !important;
    margin: 0 !important;
  }

  .auth-v8-shell .auth-v3-panel {
    width: 100%;
    min-height: calc(100vh - 104px);
    border: 0 !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    padding: 24px 18px !important;
  }

  .auth-v8-shell .auth-v3-footer {
    padding: 12px 18px !important;
    flex-wrap: wrap;
  }

  .auth-v8-shell :deep(.auth-inline-row) {
    align-items: flex-start;
    gap: 10px;
  }
}
</style>
