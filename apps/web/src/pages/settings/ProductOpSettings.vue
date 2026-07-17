<template>
  <div class="po-page">
    <div class="global-notice capability-notice" role="status">
      为避免库存误操作，库存归零自动下架暂未开放。请先完成库存核验和商品状态确认后，再进行手动下架。
    </div>
    <div class="po-grid">
      <div class="po-main">
        <n-card class="po-card" :bordered="false">
          <template #header>自动上下架策略</template>
          <template #header-extra><span class="po-card-desc">能力状态与上线前置条件</span></template>
          <div class="po-form">
            <div class="po-row po-row-toggle">
              <div>
                <strong>库存归零自动下架（当前不可用）</strong>
                <p>需先完成平台结果核验、异常人工复核与审计追踪后才能启用。</p>
              </div>
              <button type="button" class="po-switch" disabled aria-label="库存归零自动下架当前不可用">
                <span class="po-switch-knob" />
              </button>
            </div>
          </div>
        </n-card>

        <div class="po-actions">
          <button type="button" class="po-save-btn" disabled title="当前没有可生效的商品运营自动化配置">暂无可保存配置</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { NCard } from 'naive-ui'
</script>

<style scoped>
.po-page { padding: 4px; }
.po-card {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, .04);
}
.po-card :deep(.n-card__content) { padding: 16px; }
.po-card :deep(.n-card-header) { padding: 16px 16px 0; }
.po-card-desc { color: #64748b; font-size: 12px; }
.po-loading { padding: 40px; text-align: center; color: #6b7a90; }
.po-grid { display: grid; grid-template-columns: minmax(0, 1fr); gap: 16px; }

.po-form { display: grid; gap: 16px; padding: 4px 2px; }
.po-row { display: flex; flex-direction: column; gap: 6px; }
.po-row > label { font-size: 12px; color: #6b7a90; font-weight: 600; }
.po-row-toggle { flex-direction: row; align-items: center; justify-content: space-between; gap: 12px; }
.po-row-toggle > div { display: flex; flex-direction: column; gap: 4px; }
.po-row-toggle strong { font-size: 14px; color: #12233f; }
.po-row-toggle p { font-size: 12px; color: #6b7a90; margin: 0; }

.po-actions { display: flex; gap: 12px; margin-top: 16px; }
.po-save-btn {
  padding: 10px 20px; border-radius: 6px; border: 0; cursor: pointer;
  font-size: 13px; font-weight: 700;
  background: #2563eb; color: #fff;
  box-shadow: none;
}
.po-save-btn:hover:not(:disabled) { transform: translateY(-1px); }
.po-save-btn:disabled { opacity: .6; cursor: not-allowed; }

.po-switch {
  width: 44px; height: 24px; border-radius: 999px; border: 0;
  background: #cbd5e1; cursor: pointer; position: relative;
  transition: background .2s; flex-shrink: 0; padding: 0;
}
.po-switch.on { background: #22c55e; }
.po-switch-knob {
  position: absolute; top: 2px; left: 2px;
  width: 20px; height: 20px; border-radius: 50%;
  background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,.2);
  transition: left .2s;
}
.po-switch.on .po-switch-knob { left: 22px; }

@media (max-width: 900px) {
  .po-loading {
    padding: 20px;
  }

  .po-form {
    gap: 12px;
  }

  .po-row-toggle {
    gap: 10px;
  }

  .po-save-btn {
    width: 100%;
    padding: 12px 20px;
  }

  .po-actions {
    margin-top: 12px;
  }
}
</style>
