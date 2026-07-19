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
        <div class="auth-v3-eyebrow">商业运营工作台</div>
        <h1>
          {{ titleLead }}
          <span v-if="titleAccent">{{ titleAccent }}</span>
          <template v-if="titleTail"> {{ titleTail }}</template>
        </h1>
        <p>{{ description }}</p>

        <div class="auth-dashboard-preview" aria-hidden="true">
          <div class="auth-preview-sidebar">
            <div class="auth-preview-mark">
              <img src="/xya/brand/zhiyuyun-mark.svg?v=20260717-auth" alt="" />
            </div>
            <span class="active"></span>
            <span></span>
            <span></span>
            <span></span>
          </div>

          <div class="auth-preview-main">
            <div class="auth-preview-toolbar">
              <div>
                <b>运营工作台</b>
                <small>消息、商品、订单集中处理</small>
              </div>
              <span>在线</span>
            </div>

            <div class="auth-preview-stats">
              <div>
                <small>今日咨询</small>
                <b>326</b>
              </div>
              <div>
                <small>自动回复</small>
                <b>89%</b>
              </div>
              <div>
                <small>待发货</small>
                <b>18</b>
              </div>
            </div>

            <div class="auth-preview-content">
              <div class="auth-preview-chart">
                <span class="auth-chart-bar-42"></span>
                <span class="auth-chart-bar-68"></span>
                <span class="auth-chart-bar-54"></span>
                <span class="auth-chart-bar-82"></span>
                <span class="auth-chart-bar-63"></span>
                <span class="auth-chart-bar-74"></span>
              </div>
              <div class="auth-preview-list">
                <div><i></i><span></span><b></b></div>
                <div><i></i><span></span><b></b></div>
                <div><i></i><span></span><b></b></div>
              </div>
            </div>
          </div>

          <div class="auth-preview-float auth-preview-message">
            <strong>新消息</strong>
            <span>买家咨询已进入队列</span>
          </div>
          <div class="auth-preview-float auth-preview-health">
            <strong>96%</strong>
            <span>账号健康度</span>
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
          <span class="auth-v3-brand-dot">
            <img src="/xya/brand/zhiyuyun-mark.svg?v=20260717-auth" alt="" />
          </span>
          <div>
            <span class="auth-panel-kicker">{{ pageKey === 'register' ? '创建商业账户' : '安全登录' }}</span>
            <h2>{{ pageKey === 'register' ? '创建账号' : '登录工作台' }}</h2>
            <p>{{ pageKey === 'register' ? '使用邮箱验证码开通账户' : '进入你的运营工作台' }}</p>
          </div>
        </div>
        <slot />
        <div class="auth-panel-assurance" aria-hidden="true">
          <span>加密会话</span>
          <span>权限隔离</span>
          <span>业务数据</span>
        </div>
      </section>
    </main>

    <footer class="auth-v3-footer">
      <span>© {{ resolvedCopyrightYear }} 智鱼云</span>
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
  background:
    linear-gradient(135deg, rgba(245, 158, 11, .08), transparent 28%),
    linear-gradient(315deg, rgba(20, 184, 166, .08), transparent 30%),
    #f5f7fb !important;
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
  width: min(1160px, calc(100vw - 48px)) !important;
  margin: 22px auto !important;
  display: grid !important;
  grid-template-columns: minmax(0, 1fr) 420px !important;
  gap: 22px !important;
  align-items: start !important;
}

.auth-v8-shell .auth-v3-showcase,
.auth-v8-shell .auth-v3-panel {
  min-width: 0;
  border: 1px solid #dbe4f0 !important;
  border-radius: 8px !important;
  background: #fff !important;
  box-shadow: 0 24px 60px rgba(15, 23, 42, .09) !important;
}

.auth-v8-shell .auth-v3-showcase {
  position: relative;
  min-height: 0 !important;
  padding: 34px !important;
  display: grid !important;
  align-content: start !important;
  gap: 16px !important;
  overflow: hidden;
}

.auth-v8-shell .auth-v3-eyebrow {
  width: fit-content;
  padding: 5px 10px;
  color: #2563eb !important;
  background: #eef4ff;
  border: 1px solid #dbe7ff;
  border-radius: 999rem;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}

.auth-v8-shell .auth-v3-showcase h1 {
  max-width: 560px;
  margin: 0 !important;
  color: #101828 !important;
  font-size: clamp(34px, 3.8vw, 50px) !important;
  line-height: 1.06 !important;
  font-weight: 800 !important;
  letter-spacing: 0 !important;
}

.auth-v8-shell .auth-v3-showcase h1 span {
  color: #2563eb !important;
}

.auth-v8-shell .auth-v3-showcase p {
  max-width: 560px;
  margin: -4px 0 0;
  color: #667085;
  font-size: 15px;
  line-height: 1.65;
}

.auth-v8-shell .auth-dashboard-preview {
  position: relative;
  margin-top: 4px;
  min-height: 242px;
  display: grid;
  grid-template-columns: 60px minmax(0, 1fr);
  border: 1px solid #d9e3f1;
  border-radius: 8px;
  background: #0f172a;
  color: #fff;
  overflow: hidden;
  box-shadow: 0 22px 48px rgba(15, 23, 42, .22);
}

.auth-v8-shell .auth-preview-sidebar {
  padding: 14px 10px;
  display: grid;
  align-content: start;
  justify-items: center;
  gap: 14px;
  background: rgba(255, 255, 255, .06);
  border-right: 1px solid rgba(255, 255, 255, .1);
}

.auth-v8-shell .auth-preview-mark {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  background: #fff;
  overflow: hidden;
}

.auth-v8-shell .auth-preview-mark img {
  width: 28px;
  height: 28px;
  display: block;
  object-fit: contain;
}

.auth-v8-shell .auth-preview-sidebar span {
  width: 32px;
  height: 8px;
  border-radius: 999rem;
  background: rgba(255, 255, 255, .18);
}

.auth-v8-shell .auth-preview-sidebar span.active {
  width: 38px;
  background: #60a5fa;
}

.auth-v8-shell .auth-preview-main {
  min-width: 0;
  padding: 14px;
  display: grid;
  grid-template-rows: auto auto minmax(0, 1fr);
  gap: 10px;
  background:
    linear-gradient(135deg, rgba(96, 165, 250, .16), transparent 42%),
    linear-gradient(315deg, rgba(20, 184, 166, .12), transparent 38%),
    #111827;
}

.auth-v8-shell .auth-preview-toolbar,
.auth-v8-shell .auth-preview-stats,
.auth-v8-shell .auth-preview-content,
.auth-v8-shell .auth-preview-list div,
.auth-v8-shell .auth-preview-float {
  border: 1px solid rgba(255, 255, 255, .12);
  background: rgba(255, 255, 255, .07);
  border-radius: 8px;
}

.auth-v8-shell .auth-preview-toolbar {
  min-height: 48px;
  padding: 9px 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.auth-v8-shell .auth-preview-toolbar b,
.auth-v8-shell .auth-preview-toolbar small {
  display: block;
}

.auth-v8-shell .auth-preview-toolbar b {
  font-size: 15px;
  line-height: 1.2;
}

.auth-v8-shell .auth-preview-toolbar small {
  margin-top: 4px;
  color: #a7b3c7;
  font-size: 12px;
}

.auth-v8-shell .auth-preview-toolbar > span {
  height: 24px;
  padding: 0 10px;
  display: inline-flex;
  align-items: center;
  border-radius: 999rem;
  color: #86efac;
  background: rgba(22, 163, 74, .14);
  font-size: 11px;
  font-weight: 800;
}

.auth-v8-shell .auth-preview-stats {
  padding: 10px 12px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  background: rgba(255, 255, 255, .045);
}

.auth-v8-shell .auth-preview-stats div {
  min-width: 0;
}

.auth-v8-shell .auth-preview-stats small {
  display: block;
  color: #a7b3c7;
  font-size: 11px;
}

.auth-v8-shell .auth-preview-stats b {
  display: block;
  margin-top: 5px;
  color: #fff;
  font-size: 20px;
  line-height: 1;
}

.auth-v8-shell .auth-preview-content {
  padding: 12px;
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(0, .95fr);
  gap: 14px;
  background: rgba(255, 255, 255, .045);
}

.auth-v8-shell .auth-preview-chart {
  min-height: 82px;
  display: flex;
  align-items: end;
  gap: 8px;
}

.auth-v8-shell .auth-preview-chart span {
  flex: 1;
  min-width: 8px;
  border-radius: 8px 8px 5px 5px;
  background: linear-gradient(180deg, #60a5fa, #14b8a6);
}

.auth-v8-shell .auth-chart-bar-42 { height: 42%; }
.auth-v8-shell .auth-chart-bar-68 { height: 68%; }
.auth-v8-shell .auth-chart-bar-54 { height: 54%; }
.auth-v8-shell .auth-chart-bar-82 { height: 82%; }
.auth-v8-shell .auth-chart-bar-63 { height: 63%; }
.auth-v8-shell .auth-chart-bar-74 { height: 74%; }

.auth-v8-shell .auth-preview-list {
  display: grid;
  gap: 9px;
  align-content: center;
}

.auth-v8-shell .auth-preview-list div {
  min-height: 26px;
  padding: 0 9px;
  display: grid;
  grid-template-columns: 8px minmax(0, 1fr) 34px;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, .06);
}

.auth-v8-shell .auth-preview-list i {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #f59e0b;
}

.auth-v8-shell .auth-preview-list div:nth-child(2) i {
  background: #14b8a6;
}

.auth-v8-shell .auth-preview-list div:nth-child(3) i {
  background: #60a5fa;
}

.auth-v8-shell .auth-preview-list span,
.auth-v8-shell .auth-preview-list b {
  height: 7px;
  border-radius: 999rem;
  background: rgba(255, 255, 255, .18);
}

.auth-v8-shell .auth-preview-list b {
  background: rgba(255, 255, 255, .28);
}

.auth-v8-shell .auth-preview-float {
  position: absolute;
  display: grid;
  gap: 4px;
  box-shadow: 0 14px 34px rgba(15, 23, 42, .22);
  backdrop-filter: blur(16px);
}

.auth-v8-shell .auth-preview-float strong {
  font-size: 14px;
  line-height: 1.2;
}

.auth-v8-shell .auth-preview-float span {
  color: #d6e1f1;
  font-size: 12px;
}

.auth-v8-shell .auth-preview-message {
  left: 76px;
  bottom: 14px;
  width: 166px;
  padding: 10px;
  background: rgba(37, 99, 235, .78);
}

.auth-v8-shell .auth-preview-health {
  right: 14px;
  top: 76px;
  width: 122px;
  padding: 10px;
  background: rgba(15, 23, 42, .78);
}

.auth-v8-shell .auth-v3-feature-row {
  display: grid !important;
  grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
  gap: 12px !important;
}

.auth-v8-shell .auth-v3-feature-row > div {
  min-height: 70px;
  padding: 12px !important;
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
  padding: 30px !important;
  display: grid;
  align-content: start;
  align-self: start;
  min-height: 0 !important;
}

.auth-v8-shell .auth-v3-panel-head {
  margin-bottom: 22px !important;
  padding-bottom: 20px !important;
  display: flex !important;
  align-items: flex-start !important;
  gap: 12px !important;
  border-bottom: 1px solid #edf0f5 !important;
}

.auth-v8-shell .auth-v3-brand-dot {
  background: #fff !important;
  color: #2563eb !important;
  border-color: #d8e2f1 !important;
  margin-top: 2px;
}

.auth-v8-shell .auth-v3-brand-dot img {
  width: 24px;
  height: 24px;
  display: block;
  object-fit: contain;
}

.auth-v8-shell .auth-panel-kicker {
  display: block;
  margin-bottom: 5px;
  color: #2563eb;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0;
  text-transform: uppercase;
}

.auth-v8-shell .auth-v3-panel-head h2 {
  margin: 0;
  color: #101828 !important;
  font-size: 24px;
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
  min-width: 0;
  gap: 14px;
}

.auth-v8-shell :deep(.auth-sr-only) {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  clip-path: inset(50%);
  white-space: nowrap;
  border: 0;
}

.auth-v8-shell :deep(.auth-field) {
  min-height: 52px !important;
  padding: 0 15px !important;
  display: flex !important;
  align-items: center !important;
  gap: 12px !important;
  border: 1px solid #dfe6f2 !important;
  border-radius: 8px !important;
  background: #fbfcff !important;
  transition: border-color 160ms ease, background-color 160ms ease, box-shadow 160ms ease;
}

.auth-v8-shell :deep(.auth-field:focus-within) {
  border-color: #2563eb !important;
  background: #fff !important;
  box-shadow: 0 0 0 4px rgba(37, 99, 235, .1) !important;
}

.auth-v8-shell :deep(.auth-field-control) {
  flex: 1;
  min-width: 0;
  min-height: 48px;
  border: 0 !important;
  display: flex;
  align-items: center;
  gap: 12px;
}

.auth-v8-shell :deep(.auth-field input) {
  flex: 1;
  min-width: 0;
  border: 0 !important;
  outline: none !important;
  background: transparent !important;
  color: #101828;
  font-size: 14px;
  box-shadow: none !important;
}

.auth-v8-shell :deep(.auth-field input::placeholder) {
  color: #98a2b3;
}

.auth-v8-shell :deep(.auth-field-icon) {
  width: 20px;
  color: #98a2b3;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.auth-v8-shell :deep(.auth-field-icon .ui-icon),
.auth-v8-shell :deep(.auth-eye-btn .ui-icon) {
  width: 18px;
  height: 18px;
}

.auth-v8-shell :deep(.auth-field-with-action) {
  justify-content: space-between;
}

.auth-v8-shell :deep(.auth-eye-btn) {
  width: 34px;
  height: 34px;
  color: #667085;
  background: transparent;
  border: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
}

.auth-v8-shell :deep(.auth-eye-btn:hover:not(:disabled)) {
  background: #f2f5fa;
  color: #344054;
}

.auth-v8-shell :deep(.auth-inline-row) {
  min-height: 30px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.auth-v8-shell :deep(.auth-check) {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: #475467;
  font-size: 14px;
}

.auth-v8-shell :deep(.auth-check input) {
  width: 18px;
  height: 18px;
  margin: 0;
  accent-color: #2563eb;
}

.auth-v8-shell :deep(.auth-submit) {
  height: 48px !important;
  margin-top: 2px !important;
  border: 0 !important;
  border-radius: 8px !important;
  background: #2563eb !important;
  color: #fff !important;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0;
  box-shadow: 0 12px 24px rgba(37, 99, 235, .18) !important;
  transition: background-color 160ms ease, transform 120ms ease, box-shadow 160ms ease, opacity 160ms ease;
}

.auth-v8-shell :deep(.auth-submit:hover:not(:disabled)) {
  background: #1d4ed8 !important;
}

.auth-v8-shell :deep(.auth-submit:active:not(:disabled)) {
  transform: scale(.98);
}

.auth-v8-shell :deep(.auth-text-link) {
  color: #2563eb;
  font-size: 14px;
  font-weight: 700;
}

.auth-v8-shell :deep(.auth-text-link:hover:not(:disabled)) {
  color: #1d4ed8;
}

.auth-v8-shell :deep(.auth-agreement) {
  margin-top: 14px;
  padding: 12px 14px;
  color: #667085;
  background: #f8fafc;
  border: 1px solid #edf0f5;
  border-radius: 8px;
  font-size: 12px;
  line-height: 1.7;
}

.auth-v8-shell .auth-panel-assurance {
  margin-top: 18px;
  padding-top: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-top: 1px solid #edf0f5;
  color: #667085;
  font-size: 12px;
}

.auth-v8-shell .auth-panel-assurance span {
  padding: 4px 8px;
  border-radius: 999rem;
  background: #f8fafc;
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
    flex-wrap: wrap;
    gap: 10px;
  }
}
</style>
