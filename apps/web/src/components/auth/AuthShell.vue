<template>
  <div :class="['auth-shell-v3', `auth-shell-${pageKey}`]">
    <header class="auth-v3-topbar">
      <button type="button" class="auth-v3-brand" @click="emit('navigate', 'dashboard')">
        <span>ZY</span>
        <strong>智鱼云</strong>
      </button>
      <button type="button" class="auth-v3-ghost" @click="openDoc('用户协议')">服务条款</button>
    </header>

    <main class="auth-v3-main">
      <section class="auth-v3-showcase" aria-label="产品概览">
        <div class="auth-v3-eyebrow">Operations workspace</div>
        <h1>
          {{ titleLead }}
          <span v-if="titleAccent">{{ titleAccent }}</span>
          <template v-if="titleTail"> {{ titleTail }}</template>
        </h1>
        <p>{{ description }}</p>

        <div class="auth-v3-console" aria-hidden="true">
          <div class="auth-v3-console-head">
            <i></i><i></i><i></i>
            <span>live workspace</span>
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

        <div class="auth-v3-feature-row">
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
            <h2>{{ pageKey === 'register' ? '创建账号' : '登录控制台' }}</h2>
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
