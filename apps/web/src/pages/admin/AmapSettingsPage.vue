<template>
  <div class="amap-settings-page amap-v9-shell">
    <div v-if="error" class="global-notice error">{{ error }}</div>
    <div v-if="success" class="global-notice success">{{ success }}</div>

    <section class="amap-hero">
      <div class="amap-hero-copy">
        <span class="amap-kicker">Map Gateway</span>
        <h1>地图服务控制台</h1>
        <p>独立维护高德地图 API Key，用于商品发布地址搜索、POI 选择和工作流地址联想。授权轮换、服务校验和异常定位都在这里完成。</p>

        <div class="amap-hero-actions">
          <button type="button" class="amap-save-btn" :disabled="saving || !configAvailable" @click="save">{{ saving ? '保存中...' : '保存配置' }}</button>
          <button type="button" class="amap-reload-btn" :disabled="loading" @click="loadPage">{{ loading ? '加载中...' : '重新加载' }}</button>
        </div>
      </div>

      <aside class="amap-status-panel" :class="runtimeStatusAvailable && runtimeStatus.amapConfigured ? 'green' : 'orange'" aria-label="地图服务状态">
        <span>地图状态</span>
        <strong>{{ runtimeStatusAvailable ? (runtimeStatus.amapConfigured ? '已配置' : '未配置') : '状态未知' }}</strong>
        <div class="amap-status-meter">
          <i :style="{ width: runtimeStatusAvailable && runtimeStatus.amapConfigured ? '76%' : '34%' }"></i>
        </div>
        <p>地址搜索 / POI 选择 / 发布校验</p>
      </aside>
    </section>

    <section class="amap-summary-grid" aria-label="地图服务摘要">
      <article class="amap-summary-card">
        <span class="amap-summary-icon blue">01</span>
        <div>
          <strong>地址搜索</strong>
          <p>商品发布和工作流地址输入会读取这里的 Key，统一调用高德 POI 能力。</p>
        </div>
      </article>
      <article class="amap-summary-card">
        <span class="amap-summary-icon green">02</span>
        <div>
          <strong>授权轮换</strong>
          <p>需要更换 Key 时直接覆盖保存，不需要重启前端，状态刷新后即可确认。</p>
        </div>
      </article>
      <article class="amap-summary-card">
        <span class="amap-summary-icon amber">03</span>
        <div>
          <strong>服务校验</strong>
          <p>保存后先看配置状态，再到商品发布页验证地址联想和 POI 返回。</p>
        </div>
      </article>
    </section>

    <div class="amap-workspace">
      <section class="amap-v9-card amap-config-panel">
        <div class="amap-card-head">
          <div>
            <span>AMap API Key</span>
            <h2>地图授权参数</h2>
          </div>
          <p>把 Web 服务 Key 填在这里，保存后前台发布商品与工作流地址搜索会使用最新配置。</p>
        </div>

        <div class="config-overview">
          <article class="overview-card">
            <span>推荐顺序</span>
            <strong>申请 Key → 选择 Web 服务 → 保存后立即验证</strong>
            <p>先拿到平台服务可用的 Web 服务 Key，再回到此页粘贴保存，避免拿错页面专用类型。</p>
          </article>
          <article class="overview-card">
            <span>影响范围</span>
            <strong>商品发布、工作流地址选择、POI 搜索</strong>
            <p>只要页面里有地图联想与地址选择能力，都会走这里的统一配置，不需要重复填写。</p>
          </article>
        </div>

        <div class="field-grid">
          <OpsConfigField
            label="AMap API Key"
            hint="直接粘贴高德控制台生成的 Key，保存后系统会自动切换到新的地图授权。"
            meta="不会在页面回显完整 Key；如需轮换，直接覆盖保存即可，无需重启服务。"
            badge="地址服务"
            required
          >
            <SecretInput
              v-model="form.amapApiKey"
              :placeholder="config.amapApiKeyConfigured ? '已保存，直接输入新值可覆盖' : '请输入高德地图 API Key'"
              autocomplete="off"
            />
          </OpsConfigField>
        </div>

        <div class="quick-links">
          <div class="quick-link">
            <strong>申请平台</strong>
            <span>https://lbs.amap.com</span>
          </div>
          <div class="quick-link">
            <strong>服务类型</strong>
            <span>创建 Key 时请选择「Web 服务」</span>
          </div>
          <div class="quick-link">
            <strong>服务校验</strong>
            <span>发布页地址搜索</span>
          </div>
        </div>
      </section>

      <aside class="amap-v9-card amap-guide-panel">
        <div class="amap-card-head compact">
          <div>
            <span>接入指南</span>
            <h2>使用说明</h2>
          </div>
          <p>如果是第一次配置地图服务，先确认 Key 类型，再保存并到发布页验证。</p>
        </div>

        <div class="guide-grid">
          <article class="guide-card">
            <div class="guide-icon">1</div>
            <div>
              <strong>先申请账号</strong>
              <p>访问高德开放平台并完成实名认证，个人与企业账号都可以使用。</p>
            </div>
          </article>
          <article class="guide-card">
            <div class="guide-icon">2</div>
            <div>
              <strong>确认服务平台</strong>
              <p>创建 Key 时请选择 Web 服务，否则 POI 地址搜索会直接鉴权失败。</p>
            </div>
          </article>
          <article class="guide-card">
            <div class="guide-icon">3</div>
            <div>
              <strong>保存后立即验证</strong>
              <p>保存配置并重新加载后，检查状态是否切换为已配置，再去商品发布页验证联想搜索。</p>
            </div>
          </article>
        </div>

        <ol class="hint-list ordered">
          <li><strong>申请高德开放平台账号</strong>：访问 <code>https://lbs.amap.com</code>，注册并完成实名认证（个人或企业均可）。</li>
          <li><strong>创建应用</strong>：进入“控制台 → 应用管理 → 我的应用 → 创建新应用”，应用名可填 <code>智鱼云</code>，类型选“Web端（JS API）”。</li>
          <li><strong>获取 Key</strong>：在应用下“添加 Key”，服务平台必须选 <strong>Web 服务</strong>（用于平台服务调用 POI 能力）。复制生成的 Key 粘贴到上方输入框。</li>
          <li><strong>计费说明</strong>：高德开放平台会按账号类型和套餐规则提供调用额度，普通商品发布场景通常消耗较低。</li>
          <li><strong>校验方法</strong>：保存后点击“重新加载”，确认“地图状态”变为“已配置”。若发布商品页仍无法搜索地址，请核对 Key 类型、额度与域名限制。</li>
          <li><strong>接入位置</strong>：发布商品页的地址搜索会读取这里的配置；常用地址历史暂未启用。</li>
        </ol>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, reactive } from 'vue'
import OpsConfigField from '../../components/OpsConfigField.vue'
import SecretInput from '../../components/SecretInput.vue'
import {
  cloneOpenSourceConfig,
  useOpenSourceSettings,
} from '../../composables/useOpenSourceSettings.js'

defineProps({ active: String })

const {
  loading,
  saving,
  error,
  success,
  config,
  runtimeStatus,
  configAvailable,
  runtimeStatusAvailable,
  loadBundle,
  refreshRuntimeStatus,
  saveConfig,
} = useOpenSourceSettings()

const form = reactive({
  amapApiKey: '',
})

onMounted(() => {
  window.addEventListener('xya-header-action', onHeaderAction)
  loadPage()
})

onBeforeUnmount(() => {
  window.removeEventListener('xya-header-action', onHeaderAction)
})

async function loadPage() {
  await loadBundle({ includeRuntimeStatus: true })
  if (configAvailable.value) form.amapApiKey = config.amapApiKey || ''
}

async function save() {
  if (!configAvailable.value) return
  const payload = cloneOpenSourceConfig(config)
  payload.amapApiKey = form.amapApiKey.trim()
  const saved = await saveConfig(payload, { successMessage: '高德地图配置已保存' })
  if (!saved) return
  form.amapApiKey = config.amapApiKey || ''
  await refreshRuntimeStatus()
}

function onHeaderAction(event) {
  if (event.detail === 'settings-save') save()
  if (event.detail === 'settings-reload') loadPage()
}
</script>

<style scoped>
.amap-v9-shell {
  --amap-primary: #2563eb;
  --amap-primary-dark: #1d4ed8;
  --amap-accent: #0f766e;
  --amap-warning: #f59e0b;
  --amap-text: #111827;
  --amap-muted: #64748b;
  --amap-line: #e5e7eb;
  --amap-panel: #ffffff;
  --amap-soft: #f8fafc;
  --amap-ease: cubic-bezier(0.23, 1, 0.32, 1);
  display: grid;
  gap: 16px;
  color: var(--amap-text);
}

.amap-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 16px;
  align-items: stretch;
}

.amap-hero-copy,
.amap-status-panel,
.amap-summary-card,
.amap-v9-card {
  border: 1px solid var(--amap-line);
  border-radius: 8px;
  background: var(--amap-panel);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05), 0 18px 42px rgba(15, 23, 42, 0.06);
}

.amap-hero-copy {
  position: relative;
  overflow: hidden;
  min-height: 236px;
  padding: 28px;
  background:
    linear-gradient(120deg, rgba(255, 255, 255, 0.98), rgba(248, 251, 255, 0.96)),
    repeating-linear-gradient(90deg, rgba(37, 99, 235, 0.06) 0 1px, transparent 1px 40px);
}

.amap-hero-copy::before {
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

.amap-hero-copy::after {
  content: '';
  position: absolute;
  right: 88px;
  bottom: 60px;
  width: 116px;
  height: 44px;
  border: 1px solid rgba(15, 118, 110, 0.18);
  border-radius: 999px;
  background: linear-gradient(90deg, rgba(37, 99, 235, 0.15), rgba(15, 118, 110, 0.16));
  opacity: 0.72;
}

.amap-kicker {
  position: relative;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  height: 28px;
  padding: 0 10px;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  background: #eff6ff;
  color: var(--amap-primary-dark);
  font-size: 11px;
  font-weight: 850;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.amap-hero-copy h1 {
  position: relative;
  z-index: 1;
  margin: 18px 0 10px;
  color: var(--amap-text);
  font-size: 34px;
  line-height: 1.12;
  font-weight: 900;
  letter-spacing: 0;
}

.amap-hero-copy p {
  position: relative;
  z-index: 1;
  max-width: 720px;
  margin: 0;
  color: var(--amap-muted);
  font-size: 14px;
  line-height: 1.8;
}

.amap-hero-actions {
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 22px;
}

.amap-save-btn,
.amap-reload-btn {
  min-height: 38px;
  padding: 0 15px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 850;
  cursor: pointer;
  transition:
    transform 140ms var(--amap-ease),
    box-shadow 160ms var(--amap-ease),
    border-color 160ms ease,
    background-color 160ms ease,
    color 160ms ease;
}

.amap-save-btn {
  border: 1px solid transparent;
  background: linear-gradient(135deg, var(--amap-primary), var(--amap-accent));
  color: #ffffff;
  box-shadow: 0 12px 22px rgba(37, 99, 235, 0.18);
}

.amap-reload-btn {
  border: 1px solid #bfdbfe;
  background: #ffffff;
  color: var(--amap-primary-dark);
}

.amap-save-btn:disabled,
.amap-reload-btn:disabled {
  cursor: not-allowed;
  opacity: 0.62;
}

.amap-status-panel {
  display: grid;
  align-content: space-between;
  gap: 14px;
  padding: 22px;
  background:
    linear-gradient(180deg, #ffffff 0%, #f8fafc 100%),
    repeating-linear-gradient(135deg, rgba(15, 118, 110, 0.06) 0 1px, transparent 1px 18px);
}

.amap-status-panel.orange {
  background:
    linear-gradient(180deg, #ffffff 0%, #fffbeb 100%),
    repeating-linear-gradient(135deg, rgba(245, 158, 11, 0.08) 0 1px, transparent 1px 18px);
}

.amap-status-panel span,
.amap-card-head span {
  color: var(--amap-muted);
  font-size: 12px;
  font-weight: 850;
}

.amap-status-panel strong {
  color: var(--amap-warning);
  font-size: 34px;
  line-height: 1.12;
  font-weight: 900;
  letter-spacing: 0;
}

.amap-status-panel.green strong {
  color: var(--amap-accent);
}

.amap-status-panel p {
  margin: 0;
  color: var(--amap-muted);
  font-size: 13px;
  line-height: 1.65;
}

.amap-status-meter {
  height: 8px;
  overflow: hidden;
  border-radius: 999px;
  background: #e5e7eb;
}

.amap-status-meter i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--amap-primary), var(--amap-accent));
  transition: width 220ms var(--amap-ease);
}

.amap-status-panel.orange .amap-status-meter i {
  background: linear-gradient(90deg, var(--amap-warning), var(--amap-accent));
}

.amap-summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.amap-summary-card {
  display: grid;
  grid-template-columns: 48px minmax(0, 1fr);
  gap: 12px;
  align-items: start;
  padding: 16px;
  transition:
    transform 180ms var(--amap-ease),
    border-color 180ms ease,
    box-shadow 180ms var(--amap-ease);
}

.amap-summary-icon {
  width: 48px;
  height: 48px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  color: var(--amap-primary);
  background: #eff6ff;
  font-family: 'SF Mono', 'JetBrains Mono', 'Cascadia Code', monospace;
  font-size: 13px;
  font-weight: 900;
}

.amap-summary-icon.green {
  color: var(--amap-accent);
  background: #f0fdfa;
}

.amap-summary-icon.amber {
  color: #b45309;
  background: #fffbeb;
}

.amap-summary-card strong,
.amap-card-head h2,
.overview-card strong,
.guide-card strong,
.quick-link strong {
  color: var(--amap-text);
  font-weight: 850;
}

.amap-summary-card p,
.amap-card-head p,
.overview-card p,
.guide-card p {
  margin: 6px 0 0;
  color: var(--amap-muted);
  font-size: 12px;
  line-height: 1.7;
}

.amap-workspace {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 16px;
  align-items: start;
}

.amap-v9-card {
  padding: 18px;
  transition:
    transform 180ms var(--amap-ease),
    border-color 180ms ease,
    box-shadow 180ms var(--amap-ease);
}

.amap-guide-panel {
  position: sticky;
  top: 12px;
}

.amap-card-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18px;
  margin-bottom: 16px;
}

.amap-card-head.compact {
  display: grid;
  gap: 8px;
}

.amap-card-head h2 {
  margin: 4px 0 0;
  font-size: 20px;
  line-height: 1.25;
  letter-spacing: 0;
}

.amap-card-head p {
  max-width: 420px;
  margin-top: 0;
}

.config-overview {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.overview-card {
  padding: 16px;
  border: 1px solid #dbe3ee;
  border-radius: 8px;
  background:
    linear-gradient(180deg, #ffffff 0%, #f8fbff 100%),
    repeating-linear-gradient(90deg, rgba(37, 99, 235, 0.04) 0 1px, transparent 1px 28px);
}

.overview-card span {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 8px;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  background: #eff6ff;
  color: var(--amap-primary-dark);
  font-size: 11px;
  font-weight: 850;
}

.overview-card strong {
  display: block;
  margin-top: 12px;
  font-size: 15px;
  line-height: 1.45;
}

.field-grid {
  display: grid;
  gap: 14px;
}

.amap-v9-shell :deep(.ops-config-field) {
  border-color: var(--amap-line);
  border-radius: 8px;
  background: var(--amap-soft);
  box-shadow: none;
  transition:
    transform 180ms var(--amap-ease),
    border-color 180ms ease,
    box-shadow 180ms var(--amap-ease);
}

.amap-v9-shell :deep(.ops-config-field:hover) {
  border-color: #bfdbfe;
  box-shadow: 0 16px 34px rgba(37, 99, 235, 0.08);
}

.amap-v9-shell :deep(.ops-config-field-label) {
  color: var(--amap-text);
  letter-spacing: 0;
}

.amap-v9-shell :deep(.ops-config-field-badge) {
  border-radius: 8px;
  background: #eff6ff;
  color: var(--amap-primary-dark);
}

.amap-v9-shell :deep(.ops-config-field-required) {
  border-radius: 8px;
}

.amap-v9-shell :deep(.ops-config-field-hint),
.amap-v9-shell :deep(.ops-config-field-meta) {
  color: var(--amap-muted);
}

.amap-v9-shell :deep(.secret-input) {
  border-color: #dbe3ee;
  border-radius: 8px;
  color: var(--amap-text);
  background: #ffffff;
}

.amap-v9-shell :deep(.secret-input:hover) {
  border-color: #bfdbfe;
}

.amap-v9-shell :deep(.secret-input:focus-within) {
  border-color: var(--amap-primary);
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.1);
}

.amap-v9-shell :deep(.secret-input-control) {
  color: var(--amap-text);
}

.amap-v9-shell :deep(.secret-input-toggle) {
  border-left-color: var(--amap-line);
  background: #f8fbff;
  color: var(--amap-primary-dark);
  transition:
    background-color 160ms ease,
    color 160ms ease;
}

.quick-links {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-top: 14px;
}

.quick-link {
  padding: 14px 16px;
  border: 1px dashed #bfdbfe;
  border-radius: 8px;
  background: #f8fbff;
}

.quick-link strong,
.quick-link span {
  display: block;
}

.quick-link strong {
  font-size: 13px;
}

.quick-link span {
  margin-top: 6px;
  color: var(--amap-muted);
  font-size: 12px;
  line-height: 1.6;
  word-break: break-all;
}

.guide-grid {
  display: grid;
  gap: 12px;
  margin-bottom: 16px;
}

.guide-card {
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr);
  gap: 12px;
  padding: 14px;
  border: 1px solid var(--amap-line);
  border-radius: 8px;
  background: var(--amap-soft);
}

.guide-icon {
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: #eff6ff;
  color: var(--amap-primary-dark);
  font-size: 13px;
  font-weight: 900;
}

.guide-card strong {
  display: block;
  font-size: 14px;
}

.hint-list {
  display: grid;
  gap: 8px;
  margin: 0;
  padding: 0;
  color: var(--amap-muted);
  font-size: 12px;
  line-height: 1.75;
}

.hint-list.ordered {
  padding-left: 18px;
  list-style: decimal;
}

.hint-list.ordered li {
  padding-left: 2px;
}

.hint-list.ordered code {
  padding: 1px 6px;
  border-radius: 6px;
  background: #eff6ff;
  color: var(--amap-primary-dark);
  font-size: 12px;
}

.hint-list.ordered strong {
  color: var(--amap-text);
}

@media (hover: hover) and (pointer: fine) {
  .amap-summary-card:hover,
  .amap-v9-card:hover {
    transform: translateY(-2px);
    border-color: #bfdbfe;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05), 0 24px 54px rgba(37, 99, 235, 0.11);
  }

  .amap-save-btn:hover:not(:disabled),
  .amap-reload-btn:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 12px 24px rgba(37, 99, 235, 0.1);
  }
}

.amap-save-btn:active,
.amap-reload-btn:active {
  transform: scale(0.98);
}

@media (max-width: 1220px) {
  .amap-hero,
  .amap-workspace {
    grid-template-columns: minmax(0, 1fr);
  }

  .amap-guide-panel {
    position: static;
  }
}

@media (max-width: 920px) {
  .amap-summary-grid,
  .config-overview,
  .quick-links {
    grid-template-columns: minmax(0, 1fr);
  }

  .amap-hero-copy {
    min-height: 0;
    padding: 22px;
  }

  .amap-hero-copy::before,
  .amap-hero-copy::after {
    display: none;
  }

  .amap-hero-copy h1 {
    font-size: 28px;
  }

  .amap-card-head {
    flex-direction: column;
  }
}

@media (max-width: 620px) {
  .amap-hero-actions,
  .amap-save-btn,
  .amap-reload-btn {
    width: 100%;
  }

  .amap-status-panel strong {
    font-size: 28px;
  }
}
</style>
