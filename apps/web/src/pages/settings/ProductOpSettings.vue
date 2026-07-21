<template>
  <div class="po-page po-v9-shell">
    <section class="po-hero">
      <div class="po-hero-copy">
        <span class="po-kicker">商品运营</span>
        <h1>商品运营能力中心</h1>
        <p>集中查看商品自动化能力、上线前置条件和风险控制状态。当前库存归零自动下架仍保持关闭，避免库存误判导致商品被错误下架。</p>
        <div class="po-hero-actions">
          <button type="button" class="po-btn primary" disabled>能力暂未开放</button>
          <button type="button" class="po-btn" disabled>暂无可保存配置</button>
        </div>
      </div>

      <aside class="po-status-card" aria-label="商品运营能力状态">
        <span>能力状态</span>
        <strong>待开放</strong>
        <div class="po-status-bar">
          <i></i>
        </div>
        <p>需完成平台结果核验、异常人工复核与审计追踪后才能启用。</p>
      </aside>
    </section>

    <BusinessStatusStrip :items="poStatusItems" />

    <section class="po-summary-grid" aria-label="商品运营能力概览">
      <article class="po-summary-card">
        <span class="po-summary-icon blue">01</span>
        <div>
          <strong>库存联动</strong>
          <p>检测库存归零、商品状态与平台返回结果，避免误触发自动动作。</p>
        </div>
      </article>
      <article class="po-summary-card">
        <span class="po-summary-icon green">02</span>
        <div>
          <strong>人工复核</strong>
          <p>异常商品必须进入人工确认流程，自动化策略不会直接覆盖高风险操作。</p>
        </div>
      </article>
      <article class="po-summary-card">
        <span class="po-summary-icon amber">03</span>
        <div>
          <strong>审计追踪</strong>
          <p>后续启用前会保留操作原因、触发条件、执行结果和回滚线索。</p>
        </div>
      </article>
    </section>

    <div class="po-workspace">
      <section class="po-panel po-policy-panel">
        <div class="po-panel-head">
          <div>
            <span>策略配置</span>
            <h2>自动上下架策略</h2>
          </div>
          <b class="po-state-pill">当前不可用</b>
        </div>

        <div class="po-policy-card">
          <div class="po-policy-main">
            <div class="po-policy-title">
              <strong>库存归零自动下架</strong>
              <p>为避免库存误操作，此能力暂未开放。请先完成库存核验和商品状态确认后，再进行手动下架。</p>
            </div>
            <button type="button" class="po-switch" disabled aria-label="库存归零自动下架当前不可用">
              <span class="po-switch-knob"></span>
            </button>
          </div>

          <div class="po-policy-meta">
            <span>触发方式：库存归零</span>
            <span>执行方式：人工确认</span>
            <span>当前状态：关闭</span>
          </div>
        </div>

        <div class="po-risk-note" role="status">
          <strong>风险控制说明</strong>
          <p>当前没有可生效的商品运营自动化配置，系统不会自动修改商品上下架状态。</p>
        </div>
      </section>

      <aside class="po-panel po-readiness-panel">
        <div class="po-panel-head compact">
          <div>
            <span>上线校验</span>
            <h2>开放前置条件</h2>
          </div>
        </div>

        <div class="po-checklist">
          <article v-for="item in readinessItems" :key="item.title">
            <i :class="item.tone"></i>
            <div>
              <strong>{{ item.title }}</strong>
              <p>{{ item.desc }}</p>
            </div>
          </article>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import BusinessStatusStrip from '../../components/business/BusinessStatusStrip.vue'
const poStatusItems = [
  { key: 'capability', label: '能力', value: '待开放', tone: 'orange' },
  { key: 'inventory', label: '库存联动', value: '未启用', tone: 'gray' },
  { key: 'audit', label: '审计', value: '待配置', tone: 'gray' },
  { key: 'readonly', label: '可编辑', value: '否', tone: 'red' }
]
const readinessItems = [
  { title: '库存核验链路', desc: '确认库存变动、商品状态和平台返回结果一致。', tone: 'blue' },
  { title: '异常复核机制', desc: '高风险商品进入人工确认，不由自动策略直接处理。', tone: 'green' },
  { title: '操作审计记录', desc: '保留触发条件、执行人、执行结果和回滚依据。', tone: 'amber' },
  { title: '灰度开放开关', desc: '按账号或商品范围逐步开放，避免全量误操作。', tone: 'slate' }
]
</script>

<style scoped>
.po-v9-shell {
  --po-primary: #2563eb;
  --po-primary-dark: #1d4ed8;
  --po-accent: #14b8a6;
  --po-warning: #f59e0b;
  --po-text: #111827;
  --po-muted: #64748b;
  --po-line: #e5e7eb;
  --po-panel: #ffffff;
  --po-soft: #f8fafc;
  --po-ease: cubic-bezier(0.23, 1, 0.32, 1);
  display: grid;
  gap: 16px;
  color: var(--po-text);
}

.po-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 16px;
  align-items: stretch;
}

.po-hero-copy,
.po-status-card,
.po-summary-card,
.po-panel {
  border: 1px solid var(--po-line);
  border-radius: 8px;
  background: var(--po-panel);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05), 0 18px 42px rgba(15, 23, 42, 0.06);
}

.po-hero-copy {
  position: relative;
  overflow: hidden;
  min-height: 230px;
  padding: 28px;
  background:
    linear-gradient(120deg, rgba(255, 255, 255, 0.96), rgba(248, 251, 255, 0.94)),
    radial-gradient(circle at 84% 24%, rgba(37, 99, 235, 0.15), transparent 30%),
    radial-gradient(circle at 72% 90%, rgba(20, 184, 166, 0.13), transparent 24%);
}

.po-hero-copy::before {
  content: '';
  position: absolute;
  right: 28px;
  bottom: 24px;
  width: 230px;
  height: 126px;
  border: 1px solid rgba(37, 99, 235, 0.13);
  border-radius: 8px;
  background:
    linear-gradient(90deg, rgba(37, 99, 235, 0.13) 1px, transparent 1px),
    linear-gradient(180deg, rgba(37, 99, 235, 0.1) 1px, transparent 1px);
  background-size: 32px 32px;
  opacity: 0.6;
  transform: rotate(-3deg);
}

.po-kicker {
  position: relative;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  height: 28px;
  padding: 0 10px;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  background: #eff6ff;
  color: var(--po-primary-dark);
  font-size: 11px;
  font-weight: 850;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.po-hero-copy h1 {
  position: relative;
  z-index: 1;
  margin: 18px 0 10px;
  color: var(--po-text);
  font-size: 34px;
  line-height: 1.12;
  font-weight: 900;
  letter-spacing: 0;
}

.po-hero-copy p {
  position: relative;
  z-index: 1;
  max-width: 680px;
  margin: 0;
  color: var(--po-muted);
  font-size: 14px;
  line-height: 1.8;
}

.po-hero-actions {
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 22px;
}

.po-btn {
  height: 38px;
  padding: 0 14px;
  border: 1px solid var(--po-line);
  border-radius: 8px;
  background: #ffffff;
  color: #475569;
  font-size: 13px;
  font-weight: 800;
  cursor: not-allowed;
  transition:
    transform 140ms var(--po-ease),
    border-color 160ms ease,
    box-shadow 160ms var(--po-ease),
    background-color 160ms ease;
}

.po-btn.primary {
  border-color: transparent;
  background: linear-gradient(135deg, var(--po-primary), var(--po-accent));
  color: #ffffff;
  box-shadow: 0 12px 22px rgba(37, 99, 235, 0.18);
}

.po-status-card {
  display: grid;
  align-content: space-between;
  gap: 14px;
  padding: 22px;
  background:
    linear-gradient(180deg, #ffffff 0%, #f8fafc 100%),
    radial-gradient(circle at 100% 0%, rgba(245, 158, 11, 0.16), transparent 30%);
}

.po-status-card span {
  color: var(--po-muted);
  font-size: 12px;
  font-weight: 850;
}

.po-status-card strong {
  color: var(--po-warning);
  font-size: 44px;
  line-height: 1;
  font-weight: 900;
  letter-spacing: 0;
}

.po-status-card p {
  margin: 0;
  color: var(--po-muted);
  font-size: 13px;
  line-height: 1.7;
}

.po-status-bar {
  height: 8px;
  overflow: hidden;
  border-radius: 999px;
  background: #e5e7eb;
}

.po-status-bar i {
  display: block;
  width: 36%;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--po-warning), var(--po-accent));
}

.po-summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.po-summary-card {
  display: grid;
  grid-template-columns: 48px minmax(0, 1fr);
  gap: 12px;
  align-items: start;
  padding: 16px;
  transition:
    transform 180ms var(--po-ease),
    border-color 180ms ease,
    box-shadow 180ms var(--po-ease);
}

@media (hover: hover) and (pointer: fine) {
  .po-summary-card:hover,
  .po-panel:hover {
    transform: translateY(-2px);
    border-color: #bfdbfe;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05), 0 24px 54px rgba(37, 99, 235, 0.11);
  }
}

.po-summary-icon {
  width: 48px;
  height: 48px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  color: var(--po-primary);
  background: #eff6ff;
  font-family: 'SF Mono', 'JetBrains Mono', 'Cascadia Code', monospace;
  font-size: 13px;
  font-weight: 900;
}

.po-summary-icon.green {
  color: #0f766e;
  background: #f0fdfa;
}

.po-summary-icon.amber {
  color: #b45309;
  background: #fffbeb;
}

.po-summary-card strong,
.po-panel-head h2,
.po-policy-title strong,
.po-risk-note strong,
.po-checklist strong {
  color: var(--po-text);
  font-weight: 850;
}

.po-summary-card p,
.po-policy-title p,
.po-risk-note p,
.po-checklist p {
  margin: 6px 0 0;
  color: var(--po-muted);
  font-size: 12px;
  line-height: 1.7;
}

.po-workspace {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) 360px;
  gap: 16px;
  align-items: start;
}

.po-panel {
  padding: 18px;
  transition:
    transform 180ms var(--po-ease),
    border-color 180ms ease,
    box-shadow 180ms var(--po-ease);
}

.po-panel-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 14px;
  margin-bottom: 16px;
}

.po-panel-head.compact {
  margin-bottom: 12px;
}

.po-panel-head span {
  display: block;
  margin-bottom: 4px;
  color: var(--po-muted);
  font-size: 12px;
  font-weight: 850;
}

.po-panel-head h2 {
  margin: 0;
  font-size: 20px;
  line-height: 1.25;
  letter-spacing: 0;
}

.po-state-pill {
  height: 30px;
  display: inline-flex;
  align-items: center;
  padding: 0 10px;
  border: 1px solid #fed7aa;
  border-radius: 8px;
  background: #fff7ed;
  color: #c2410c;
  font-size: 12px;
}

.po-policy-card {
  display: grid;
  gap: 14px;
  padding: 16px;
  border: 1px solid #dbeafe;
  border-radius: 8px;
  background:
    linear-gradient(180deg, #ffffff 0%, #f8fbff 100%),
    radial-gradient(circle at 100% 0%, rgba(37, 99, 235, 0.1), transparent 24%);
}

.po-policy-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 18px;
}

.po-policy-title {
  min-width: 0;
}

.po-policy-title strong {
  display: block;
  font-size: 16px;
}

.po-switch {
  position: relative;
  width: 52px;
  height: 30px;
  flex: 0 0 auto;
  border: 0;
  border-radius: 999px;
  background: #cbd5e1;
  cursor: not-allowed;
  padding: 0;
}

.po-switch-knob {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #ffffff;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.2);
}

.po-policy-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.po-policy-meta span {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 0 10px;
  border: 1px solid var(--po-line);
  border-radius: 8px;
  background: #ffffff;
  color: #475569;
  font-size: 12px;
  font-weight: 800;
}

.po-risk-note {
  margin-top: 14px;
  padding: 14px 16px;
  border: 1px solid #fed7aa;
  border-radius: 8px;
  background: #fff7ed;
}

.po-risk-note strong {
  display: block;
  color: #9a3412;
}

.po-checklist {
  display: grid;
  gap: 10px;
}

.po-checklist article {
  display: grid;
  grid-template-columns: 10px minmax(0, 1fr);
  gap: 10px;
  padding: 12px;
  border: 1px solid var(--po-line);
  border-radius: 8px;
  background: var(--po-soft);
}

.po-checklist i {
  width: 10px;
  height: 10px;
  margin-top: 5px;
  border-radius: 999px;
  background: var(--po-primary);
}

.po-checklist i.green {
  background: var(--po-accent);
}

.po-checklist i.amber {
  background: var(--po-warning);
}

.po-checklist i.slate {
  background: #64748b;
}

.po-btn:active {
  transform: scale(0.98);
}

@media (max-width: 1120px) {
  .po-hero,
  .po-workspace {
    grid-template-columns: minmax(0, 1fr);
  }

  .po-status-card {
    min-height: 180px;
  }
}

@media (max-width: 820px) {
  .po-summary-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .po-hero-copy {
    min-height: 0;
    padding: 22px;
  }

  .po-hero-copy::before {
    display: none;
  }

  .po-hero-copy h1 {
    font-size: 28px;
  }

  .po-policy-main {
    align-items: flex-start;
  }
}

@media (max-width: 560px) {
  .po-panel-head,
  .po-policy-main {
    flex-direction: column;
  }

  .po-hero-actions,
  .po-btn {
    width: 100%;
  }
}
</style>
