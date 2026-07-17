<template>
  <div class="rag-settings-page rag-v9-shell">
    <section class="rag-hero">
      <div class="rag-hero-copy">
        <span class="rag-kicker">Knowledge Operations</span>
        <h1>知识库运营工作台</h1>
        <p>
          集中维护 FAQ、售后说明、商品知识与行业文档。知识库创建、文档上传、
          分块索引和检索验证都在这个工作台完成，避免和系统基础配置混在一起。
        </p>

        <div class="rag-hero-points">
          <span>文档治理</span>
          <span>向量索引</span>
          <span>检索验证</span>
        </div>
      </div>

      <aside class="rag-status-panel" aria-label="知识库工作台状态">
        <span>工作区</span>
        <strong>独立运行</strong>
        <div class="rag-status-track"><i></i></div>
        <p>RAG 文档、分块和语义检索统一在这里维护。</p>
      </aside>
    </section>

    <section class="rag-summary-grid" aria-label="知识库流程">
      <article class="rag-summary-card">
        <span class="rag-summary-icon blue">01</span>
        <div>
          <strong>建立知识库</strong>
          <p>按业务线创建知识库，区分售前问答、售后规则、商品资料和内部说明。</p>
        </div>
      </article>
      <article class="rag-summary-card">
        <span class="rag-summary-icon green">02</span>
        <div>
          <strong>上传并索引</strong>
          <p>文本与 Markdown 文档进入解析流程，生成可被模型召回的分块和向量。</p>
        </div>
      </article>
      <article class="rag-summary-card">
        <span class="rag-summary-icon amber">03</span>
        <div>
          <strong>检索验证</strong>
          <p>上线前用真实问题测试命中效果，确认回答依据来自正确文档。</p>
        </div>
      </article>
    </section>

    <section class="rag-main-panel">
      <RagKnowledgeBasePage />
    </section>
  </div>
</template>

<script setup>
import RagKnowledgeBasePage from './RagKnowledgeBasePage.vue'

defineProps({ active: String })
</script>

<style scoped>
.rag-v9-shell {
  --rag-primary: #2563eb;
  --rag-primary-dark: #1d4ed8;
  --rag-accent: #0f766e;
  --rag-warning: #f59e0b;
  --rag-text: #111827;
  --rag-muted: #64748b;
  --rag-line: #e5e7eb;
  --rag-panel: #ffffff;
  --rag-soft: #f8fafc;
  --rag-ease: cubic-bezier(0.23, 1, 0.32, 1);
  display: grid;
  gap: 16px;
  color: var(--rag-text);
}

.rag-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 16px;
  align-items: stretch;
}

.rag-hero-copy,
.rag-status-panel,
.rag-summary-card,
.rag-main-panel {
  border: 1px solid var(--rag-line);
  border-radius: 8px;
  background: var(--rag-panel);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05), 0 18px 42px rgba(15, 23, 42, 0.06);
}

.rag-hero-copy {
  position: relative;
  overflow: hidden;
  min-height: 236px;
  padding: 28px;
  background:
    linear-gradient(120deg, rgba(255, 255, 255, 0.98), rgba(248, 251, 255, 0.96)),
    repeating-linear-gradient(90deg, rgba(37, 99, 235, 0.06) 0 1px, transparent 1px 40px);
}

.rag-hero-copy::before {
  content: '';
  position: absolute;
  right: 30px;
  bottom: 26px;
  width: 238px;
  height: 132px;
  border: 1px solid rgba(37, 99, 235, 0.14);
  border-radius: 8px;
  background:
    linear-gradient(90deg, rgba(37, 99, 235, 0.12) 1px, transparent 1px),
    linear-gradient(180deg, rgba(15, 118, 110, 0.1) 1px, transparent 1px);
  background-size: 34px 34px;
  opacity: 0.68;
  transform: rotate(-3deg);
}

.rag-kicker {
  position: relative;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  height: 28px;
  padding: 0 10px;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  background: #eff6ff;
  color: var(--rag-primary-dark);
  font-size: 11px;
  font-weight: 850;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.rag-hero-copy h1 {
  position: relative;
  z-index: 1;
  margin: 18px 0 10px;
  color: var(--rag-text);
  font-size: 34px;
  line-height: 1.12;
  font-weight: 900;
  letter-spacing: 0;
}

.rag-hero-copy p {
  position: relative;
  z-index: 1;
  max-width: 720px;
  margin: 0;
  color: var(--rag-muted);
  font-size: 14px;
  line-height: 1.8;
}

.rag-hero-points {
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 22px;
}

.rag-hero-points span {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 0 10px;
  border: 1px solid #dbe3ee;
  border-radius: 8px;
  background: #ffffff;
  color: var(--rag-primary-dark);
  font-size: 12px;
  font-weight: 850;
}

.rag-status-panel {
  display: grid;
  align-content: space-between;
  gap: 14px;
  padding: 22px;
  background:
    linear-gradient(180deg, #ffffff 0%, #f8fafc 100%),
    repeating-linear-gradient(135deg, rgba(15, 118, 110, 0.06) 0 1px, transparent 1px 18px);
}

.rag-status-panel span {
  color: var(--rag-muted);
  font-size: 12px;
  font-weight: 850;
}

.rag-status-panel strong {
  color: var(--rag-accent);
  font-size: 34px;
  line-height: 1.12;
  font-weight: 900;
  letter-spacing: 0;
}

.rag-status-panel p {
  margin: 0;
  color: var(--rag-muted);
  font-size: 13px;
  line-height: 1.65;
}

.rag-status-track {
  height: 8px;
  overflow: hidden;
  border-radius: 999px;
  background: #e5e7eb;
}

.rag-status-track i {
  display: block;
  width: 78%;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--rag-primary), var(--rag-accent));
}

.rag-summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.rag-summary-card {
  display: grid;
  grid-template-columns: 48px minmax(0, 1fr);
  gap: 12px;
  align-items: start;
  padding: 16px;
  transition:
    transform 180ms var(--rag-ease),
    border-color 180ms ease,
    box-shadow 180ms var(--rag-ease);
}

.rag-summary-icon {
  width: 48px;
  height: 48px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  color: var(--rag-primary);
  background: #eff6ff;
  font-family: 'SF Mono', 'JetBrains Mono', 'Cascadia Code', monospace;
  font-size: 13px;
  font-weight: 900;
}

.rag-summary-icon.green {
  color: var(--rag-accent);
  background: #f0fdfa;
}

.rag-summary-icon.amber {
  color: #b45309;
  background: #fffbeb;
}

.rag-summary-card strong {
  color: var(--rag-text);
  font-weight: 850;
}

.rag-summary-card p {
  margin: 6px 0 0;
  color: var(--rag-muted);
  font-size: 12px;
  line-height: 1.7;
}

.rag-main-panel {
  padding: 18px;
}

@media (hover: hover) and (pointer: fine) {
  .rag-summary-card:hover,
  .rag-main-panel:hover {
    transform: translateY(-2px);
    border-color: #bfdbfe;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05), 0 24px 54px rgba(37, 99, 235, 0.11);
  }
}

@media (max-width: 1080px) {
  .rag-hero {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 900px) {
  .rag-v9-shell,
  .rag-summary-grid {
    grid-template-columns: minmax(0, 1fr);
    gap: 12px;
  }

  .rag-hero > *,
  .rag-summary-grid > * {
    min-width: 0;
  }

  .rag-hero-copy {
    min-height: 0;
    padding: 22px;
  }

  .rag-hero-copy::before {
    display: none;
  }

  .rag-hero-copy h1 {
    font-size: 28px;
  }

  .rag-main-panel {
    padding: 12px;
  }
}

@media (max-width: 620px) {
  .rag-status-panel strong {
    font-size: 28px;
  }
}
</style>
