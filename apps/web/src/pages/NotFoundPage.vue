<template>
  <section class="not-found-page notfound-v9-shell" aria-labelledby="not-found-title">
    <div class="notfound-hero">
      <div class="notfound-copy">
        <span class="notfound-kicker">Route Recovery</span>
        <h1 id="not-found-title">页面暂时无法访问</h1>
        <p>{{ description }}</p>

        <div class="notfound-route-card">
          <span>请求入口</span>
          <strong>{{ requestedRouteLabel }}</strong>
        </div>

        <div class="notfound-actions">
          <AppButton type="primary" @click="emit('navigate', 'data')">返回数据面板</AppButton>
          <AppButton @click="emit('navigate', 'settings-about')">查看使用说明</AppButton>
        </div>
      </div>

      <aside class="notfound-status-panel" aria-label="页面恢复建议">
        <div class="status-code">
          <span>HTTP</span>
          <strong>404</strong>
        </div>
        <div class="status-list">
          <article>
            <span class="status-dot blue"></span>
            <div>
              <strong>导航入口可能已更新</strong>
              <p>建议从左侧菜单或顶部标签重新进入目标功能。</p>
            </div>
          </article>
          <article>
            <span class="status-dot green"></span>
            <div>
              <strong>业务数据不会受影响</strong>
              <p>当前仅是页面路由未匹配，不会修改任何账号、商品或订单。</p>
            </div>
          </article>
          <article>
            <span class="status-dot amber"></span>
            <div>
              <strong>如持续出现请记录入口</strong>
              <p>提供当前链接和触发路径，便于定位菜单配置或权限范围。</p>
            </div>
          </article>
        </div>
      </aside>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import AppButton from '../components/AppButton.vue'

const props = defineProps({ requestedRoute: { type: String, default: '' } })
const emit = defineEmits(['navigate'])
const requestedRouteLabel = computed(() => props.requestedRoute || '未指定路由')
const description = computed(() => props.requestedRoute
  ? `未找到“${props.requestedRoute}”对应的页面。链接可能已失效或功能已下线。`
  : '当前链接可能已失效或功能已下线。')
</script>

<style scoped>
.not-found-page {
  width: 100%;
}

.notfound-v9-shell {
  --nf-primary: #2563eb;
  --nf-accent: #14b8a6;
  --nf-warning: #f59e0b;
  --nf-text: #111827;
  --nf-muted: #64748b;
  --nf-line: #e5e7eb;
  --nf-panel: #ffffff;
  --nf-ease: cubic-bezier(0.23, 1, 0.32, 1);
  min-height: min(680px, calc(100vh - 190px));
  display: grid;
  place-items: center;
  padding: 18px;
  color: var(--nf-text);
}

.notfound-hero {
  width: min(1080px, 100%);
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) 340px;
  gap: 18px;
  align-items: stretch;
}

.notfound-copy,
.notfound-status-panel {
  border: 1px solid var(--nf-line);
  border-radius: 8px;
  background: var(--nf-panel);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05), 0 24px 54px rgba(15, 23, 42, 0.07);
}

.notfound-copy {
  position: relative;
  overflow: hidden;
  min-height: 360px;
  padding: 34px;
  background:
    linear-gradient(120deg, rgba(255, 255, 255, 0.96), rgba(248, 251, 255, 0.94)),
    radial-gradient(circle at 86% 20%, rgba(37, 99, 235, 0.16), transparent 28%),
    radial-gradient(circle at 74% 88%, rgba(20, 184, 166, 0.14), transparent 24%);
}

.notfound-copy::before {
  content: '';
  position: absolute;
  right: 28px;
  bottom: 28px;
  width: 260px;
  height: 148px;
  border: 1px solid rgba(37, 99, 235, 0.13);
  border-radius: 8px;
  background:
    linear-gradient(90deg, rgba(37, 99, 235, 0.13) 1px, transparent 1px),
    linear-gradient(180deg, rgba(37, 99, 235, 0.1) 1px, transparent 1px);
  background-size: 34px 34px;
  transform: rotate(-4deg);
  opacity: 0.65;
}

.notfound-copy::after {
  content: '404';
  position: absolute;
  right: 44px;
  top: 28px;
  color: rgba(37, 99, 235, 0.08);
  font-size: 128px;
  line-height: 1;
  font-weight: 900;
  font-family: 'SF Mono', 'JetBrains Mono', 'Cascadia Code', monospace;
}

.notfound-kicker {
  position: relative;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  height: 28px;
  padding: 0 10px;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 11px;
  font-weight: 850;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.notfound-copy h1 {
  position: relative;
  z-index: 1;
  max-width: 560px;
  margin: 18px 0 12px;
  color: var(--nf-text);
  font-size: 42px;
  line-height: 1.1;
  font-weight: 900;
  letter-spacing: 0;
}

.notfound-copy p {
  position: relative;
  z-index: 1;
  max-width: 620px;
  margin: 0;
  color: var(--nf-muted);
  font-size: 15px;
  line-height: 1.8;
}

.notfound-route-card {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 8px;
  max-width: 520px;
  margin: 24px 0;
  padding: 15px 16px;
  border: 1px solid #dbeafe;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.78);
}

.notfound-route-card span {
  color: var(--nf-muted);
  font-size: 12px;
  font-weight: 800;
}

.notfound-route-card strong {
  color: var(--nf-text);
  font-size: 14px;
  line-height: 1.5;
  font-weight: 850;
  word-break: break-all;
}

.notfound-actions {
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.notfound-actions :deep(button) {
  transition:
    transform 140ms var(--nf-ease),
    box-shadow 160ms var(--nf-ease),
    border-color 160ms ease,
    background-color 160ms ease;
}

.notfound-actions :deep(button:active) {
  transform: scale(0.98);
}

.notfound-status-panel {
  padding: 18px;
  background:
    linear-gradient(180deg, #ffffff 0%, #f8fafc 100%),
    radial-gradient(circle at 100% 0%, rgba(20, 184, 166, 0.12), transparent 28%);
}

.status-code {
  display: grid;
  gap: 4px;
  padding: 18px;
  border: 1px solid #dbeafe;
  border-radius: 8px;
  background: #eff6ff;
}

.status-code span {
  color: #1d4ed8;
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.1em;
}

.status-code strong {
  color: var(--nf-primary);
  font-family: 'SF Mono', 'JetBrains Mono', 'Cascadia Code', monospace;
  font-size: 64px;
  line-height: 1;
  font-weight: 900;
}

.status-list {
  display: grid;
  gap: 12px;
  margin-top: 14px;
}

.status-list article {
  display: grid;
  grid-template-columns: 10px minmax(0, 1fr);
  gap: 10px;
  padding: 12px;
  border: 1px solid var(--nf-line);
  border-radius: 8px;
  background: #ffffff;
}

.status-dot {
  width: 10px;
  height: 10px;
  margin-top: 5px;
  border-radius: 999px;
  background: var(--nf-primary);
}

.status-dot.green {
  background: var(--nf-accent);
}

.status-dot.amber {
  background: var(--nf-warning);
}

.status-list strong {
  display: block;
  color: var(--nf-text);
  font-size: 13px;
  font-weight: 850;
}

.status-list p {
  margin: 5px 0 0;
  color: var(--nf-muted);
  font-size: 12px;
  line-height: 1.65;
}

@media (hover: hover) and (pointer: fine) {
  .status-list article {
    transition:
      transform 180ms var(--nf-ease),
      box-shadow 180ms var(--nf-ease),
      border-color 180ms ease;
  }

  .status-list article:hover {
    transform: translateY(-2px);
    border-color: #bfdbfe;
    box-shadow: 0 16px 34px rgba(37, 99, 235, 0.1);
  }
}

@media (max-width: 920px) {
  .notfound-hero {
    grid-template-columns: minmax(0, 1fr);
  }

  .notfound-copy::after {
    font-size: 96px;
  }
}

@media (max-width: 640px) {
  .notfound-v9-shell {
    padding: 0;
    place-items: stretch;
  }

  .notfound-copy,
  .notfound-status-panel {
    padding: 20px;
  }

  .notfound-copy h1 {
    font-size: 30px;
  }

  .notfound-copy::before,
  .notfound-copy::after {
    display: none;
  }
}
</style>
