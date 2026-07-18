<template>
  <div class="card-warehouse-page warehouse-v14-shell">
    <div class="card-warehouse-notices">
      <div v-if="error" class="global-notice error">{{ error }}</div>
      <div v-if="groupsWarning" class="global-notice warning" role="status">{{ groupsWarning }}</div>
      <div v-if="success" class="global-notice success">{{ success }}</div>
    </div>

    <section class="warehouse-command-center">
      <div class="warehouse-command-main">
        <div class="warehouse-command-kicker">
          <span>卡密库存</span>
          <b>{{ selected?.groupName || '未选择分组' }}</b>
        </div>
        <h2>卡密库存控制台</h2>
        <p>集中管理卡密分组、库存明细、使用记录、导入和导出，自动发货会从这里领取库存。</p>
        <div class="warehouse-command-meta">
          <span>{{ groupsLoading ? '库存刷新中' : `当前 ${groupsMetric(groups.length)} 个分组` }}</span>
          <span>可用 {{ groupsMetric(stockStats.remain) }}</span>
          <span>低库存 {{ groupsMetric(lowStockCount) }}</span>
        </div>
      </div>
      <div class="warehouse-command-panel">
        <div class="warehouse-command-panel-head">
          <span>库存动作</span>
          <strong>{{ selected ? '分组已选' : '全局操作' }}</strong>
        </div>
        <div class="warehouse-command-buttons">
          <n-button :title="warehouseActionHint" :loading="groupsLoading" @click="load">刷新库存</n-button>
          <n-button type="primary" :title="warehouseActionHint" :disabled="saving || importing" @click="openCreateDialog">新建卡密组</n-button>
        </div>
        <p class="warehouse-action-hint">{{ warehouseActionHint }}</p>
      </div>
    </section>

    <section class="warehouse-metric-rail">
      <article
        v-for="item in warehouseStatCards"
        :key="item.key"
        class="warehouse-metric-card"
        :class="item.tone"
      >
        <span class="warehouse-metric-icon">{{ item.symbol }}</span>
        <n-statistic :label="item.title" :value="item.value" />
        <small>{{ item.change }}</small>
      </article>
    </section>

    <div class="card-warehouse-workspace">
      <div class="card-warehouse-left">
      <section class="warehouse-panel warehouse-group-panel">
        <header class="warehouse-panel-head">
          <div>
            <span>分组管理</span>
            <h3>卡密分组</h3>
          </div>
          <b>共 {{ groupsAvailable === true ? groups.length : '—' }} 组</b>
        </header>
        <div class="warehouse-toolbar">
          <n-input v-model:value="query.keyword" clearable placeholder="搜索卡密组名称" @keyup.enter="load" />
          <n-button :loading="groupsLoading" @click="load">搜索</n-button>
          <n-button type="primary" @click="openCreateDialog">新建卡密组</n-button>
        </div>
        <div v-if="groupsRefreshing" class="refresh-status" role="status" aria-live="polite">
          正在刷新卡密分组，现有数据仍可查看。
        </div>
        <EmptyState v-if="groupsLoading && groupsAvailable !== true" icon="⏳" title="卡密分组加载中" description="正在读取分组与库存摘要。" />
        <EmptyState v-else-if="groupsAvailable === false" icon="⚠️" title="卡密分组暂不可用" description="当前无法确认分组和库存，请恢复服务后重试。">
          <template #actions><AppButton @click="load">重新加载</AppButton></template>
        </EmptyState>
        <BaseTable v-else-if="groupsAvailable === true" :columns="groupCols" :rows="groupRows">
          <template #name="{row}">
            <div class="group-name-cell">
              <strong>{{ row.groupName }}</strong>
              <em v-if="row.remark" class="subtle group-remark">{{ row.remark }}</em>
            </div>
          </template>
          <template #cardType="{row}">
            <Badge>{{ cardTypeLabel(row.cardType) }}</Badge>
          </template>
          <template #remain="{row}">
            <b :class="['remain-count', remainToneClass(row)]">{{ row.remainCount }}</b>
          </template>
          <template #status="{row}">
            <Badge :type="row.status === 1 ? 'green' : 'orange'">{{ row.status === 1 ? '启用' : '禁用' }}</Badge>
          </template>
          <template #op="{row}">
            <button class="link" @click="selectGroup(row.raw)">查看</button>
            <button class="link" @click="openEditDialog(row.raw)">编辑</button>
            <button class="link" @click="exportGroup(row.raw)">导出</button>
            <button class="link danger-text" @click="removeGroup(row.raw.id)">删除</button>
          </template>
          <template #empty>
            <EmptyState icon="🔑" title="还没有卡密组" description="先创建卡密组，再批量导入卡密；自动发货规则会从这里安全领取库存。">
              <template #actions><AppButton type="primary" @click="openCreateDialog">新建卡密组</AppButton></template>
            </EmptyState>
          </template>
        </BaseTable>
      </section>
      <section class="warehouse-panel warehouse-import-panel">
        <header class="warehouse-panel-head">
          <div>
            <span>库存入库</span>
            <h3>导入卡密</h3>
          </div>
        </header>
        <div class="form-grid">
          <div class="form-row">
            <label>目标分组</label>
            <select v-model="importGroupId" class="input">
              <option value="">请选择分组</option>
              <option v-for="g in groups" :key="g.id" :value="g.id">{{ g.groupName }}（余 {{ g.remainCount || 0 }}）</option>
            </select>
          </div>
          <div class="form-row">
            <label>导入方式</label>
            <div class="import-tabs">
              <button :class="['import-tab', { active: importMode === 'paste' }]" @click="importMode = 'paste'">粘贴导入</button>
              <button :class="['import-tab', { active: importMode === 'file' }]" @click="importMode = 'file'">文件导入</button>
            </div>
          </div>
          <div v-if="importMode === 'paste'" class="form-row">
            <label>每行一条卡密</label>
            <textarea v-model="bulkText" class="input" rows="6" placeholder="CARD-AAAA-BBBB&#10;CARD-CCCC-DDDD&#10;支持格式：卡密内容&#10;卡号----密码（卡号+密码类型）"></textarea>
            <span class="subtle bulk-count-note">{{ bulkCount }} 条</span>
          </div>
          <div v-if="importMode === 'file'" class="form-row">
            <label>选择文件（TXT / CSV）</label>
            <input ref="fileInputRef" type="file" accept=".txt,.csv" class="file-input-hidden" @change="handleFileSelect">
            <button type="button" class="file-drop-zone" @click="triggerFileInput" @dragover.prevent @drop.prevent="handleFileDrop">
              <span v-if="!importFileName">点击或拖拽 TXT/CSV 文件到此处</span>
              <span v-else class="file-name">{{ importFileName }}</span>
            </button>
            <span class="subtle file-format-note">文件每行一条卡密，支持逗号/制表符/----分隔卡号和密码</span>
          </div>
          <div class="form-row import-action-row">
            <AppButton type="primary" :disabled="importing || !importGroupId" @click="submitImport">
              {{ importing ? '导入中...' : '确认导入' }}
            </AppButton>
            <span v-if="importResult" class="import-result">
              <span class="import-success">✓ 成功 {{ importResult.success }}</span>
              <span v-if="importResult.duplicate" class="import-duplicate">重复 {{ importResult.duplicate }}</span>
              <span v-if="importResult.fail" class="import-fail">失败 {{ importResult.fail }}</span>
            </span>
          </div>
        </div>
      </section>
    </div>
    <!-- Right -->
    <div class="card-warehouse-right">
      <section class="warehouse-panel warehouse-detail-panel">
        <header class="warehouse-panel-head">
          <div>
            <span>库存明细</span>
            <h3>{{ selected ? selected.groupName : '卡密详情' }}</h3>
          </div>
        </header>
        <EmptyState v-if="!selected" icon="👈" title="请选择卡密分组" description="从左侧列表选择一个卡密组，查看卡密明细、使用记录和导入历史。" class="detail-empty-state" />
        <template v-else>
          <div class="tab-bar">
            <button v-for="t in tabs" :key="t.key" :class="['tab-btn', { active: activeTab === t.key }]" @click="switchTab(t.key)">{{ t.label }}</button>
          </div>
          <!-- 卡密明细 -->
          <div v-show="activeTab === 'items'">
            <div v-if="itemsWarning" class="inline-warning" role="status">{{ itemsWarning }}</div>
            <div v-if="itemsRefreshing" class="refresh-status" role="status" aria-live="polite">
              正在刷新卡密明细，现有数据仍可查看。
            </div>
            <div class="toolbar detail-toolbar">
              <span class="table-info">共 <b>{{ itemsAvailable === false ? '—' : itemTotal }}</b> 条卡密</span>
              <select v-model="itemStatusFilter" class="input item-status-select" @change="filterItems">
                <option value="">全部状态</option>
                <option value="0">未使用</option>
                <option value="1">已锁定</option>
                <option value="2">已使用</option>
                <option value="3">已作废</option>
                <option value="4">异常</option>
              </select>
            </div>
            <EmptyState v-if="itemsLoading && itemsAvailable !== true" icon="⏳" title="卡密明细加载中" description="正在读取当前分组的卡密数据。" />
            <EmptyState v-else-if="itemsAvailable === false" icon="⚠️" title="卡密明细暂不可用" description="当前无法确认该分组是否有卡密。">
              <template #actions><AppButton @click="loadItems">重新加载</AppButton></template>
            </EmptyState>
            <BaseTable v-else-if="itemsAvailable === true" :columns="itemCols" :rows="cardItems">
              <template #content="{row}">
                <code class="card-content-text">{{ row.cardContent || row.content || '-' }}</code>
              </template>
              <template #status="{row}">
                <Badge :type="itemStatusBadge(row.status)">{{ itemStatusLabel(row.status) }}</Badge>
              </template>
              <template #usedOrderId="{row}">{{ row.usedOrderId || '-' }}</template>
              <template #usedTime="{row}">{{ row.usedTime ? dateTime(row.usedTime) : '-' }}</template>
              <template #op="{row}">
                <button v-if="row.status === 0" class="link" @click="lockItem(row)">锁定</button>
                <button v-if="row.status === 1" class="link" @click="resetItem(row)">解锁</button>
                <button v-if="row.status === 2" class="link" @click="resetItem(row)">重置</button>
                <button v-if="row.status !== 3" class="link danger-text" @click="markInvalid(row)">作废</button>
                <button class="link danger-text" @click="removeItem(row)">删除</button>
              </template>
              <template #empty>
                <EmptyState icon="📦" title="当前分组暂无卡密" description="在左侧选择分组并粘贴或上传文件导入卡密。" />
              </template>
            </BaseTable>
            <div v-if="itemTotal > pageSize" class="pagination">
              <span class="page-info">第 {{ itemPage }} / {{ itemPages }} 页</span>
              <button class="page-no" :disabled="itemPage <= 1" @click="itemPage--; loadItems()">‹</button>
              <button class="page-no" :disabled="itemPage >= itemPages" @click="itemPage++; loadItems()">›</button>
            </div>
          </div>
          <!-- 使用记录 -->
          <div v-show="activeTab === 'usage'">
            <div v-if="usageWarning" class="inline-warning" role="status">{{ usageWarning }}</div>
            <div v-if="usageRefreshing" class="refresh-status" role="status" aria-live="polite">
              正在刷新使用记录，现有数据仍可查看。
            </div>
            <div class="toolbar detail-toolbar">
              <span class="table-info">共 <b>{{ usageAvailable === false ? '—' : usageTotal }}</b> 条使用记录</span>
            </div>
            <EmptyState v-if="usageLoading && usageAvailable !== true" icon="⏳" title="使用记录加载中" description="正在读取当前分组的卡密使用记录。" />
            <EmptyState v-else-if="usageAvailable === false" icon="⚠️" title="使用记录暂不可用" description="当前无法确认是否存在卡密使用记录。">
              <template #actions><AppButton @click="loadUsageRecords">重新加载</AppButton></template>
            </EmptyState>
            <BaseTable v-else-if="usageAvailable === true" :columns="usageCols" :rows="usageRecords">
              <template #content="{row}">
                <code class="card-content-text">{{ row.cardContent || row.content || '-' }}</code>
              </template>
              <template #orderInfo="{row}">
                <span>{{ row.usedOrderId || row.orderId || '-' }}</span>
              </template>
              <template #usedTime="{row}">{{ row.usedTime ? dateTime(row.usedTime) : '-' }}</template>
              <template #empty>
                <EmptyState icon="📋" title="暂无使用记录" description="卡密被使用后，记录会出现在这里。" />
              </template>
            </BaseTable>
            <div v-if="usageTotal > usagePageSize" class="pagination">
              <span class="page-info">第 {{ usagePage }} / {{ usagePages }} 页</span>
              <button class="page-no" :disabled="usagePage <= 1" @click="usagePage--; loadUsageRecords()">‹</button>
              <button class="page-no" :disabled="usagePage >= usagePages" @click="usagePage++; loadUsageRecords()">›</button>
            </div>
          </div>
          <!-- 库存统计 -->
          <div v-show="activeTab === 'stats'">
            <div v-if="stockWarning" class="inline-warning" role="status">{{ stockWarning }}</div>
            <div v-if="stockRefreshing" class="refresh-status" role="status" aria-live="polite">
              正在刷新库存统计，现有数据仍可查看。
            </div>
            <EmptyState v-if="stockLoading && stockAvailable !== true" icon="⏳" title="库存统计加载中" description="正在读取当前分组的库存统计。" />
            <EmptyState v-else-if="stockAvailable === false" icon="⚠️" title="库存统计暂不可用" description="当前不会用全零数据代替查询失败。">
              <template #actions><AppButton @click="loadStockStats">重新加载</AppButton></template>
            </EmptyState>
            <div v-else-if="stockAvailable === true" class="stock-stats">
              <div class="stat-item">
                <span class="stat-label">总数量</span>
                <strong class="stat-value">{{ stockDetail.totalCount ?? 0 }}</strong>
              </div>
              <div class="stat-item green">
                <span class="stat-label">未使用</span>
                <strong class="stat-value">{{ stockDetail.remainCount ?? 0 }}</strong>
              </div>
              <div class="stat-item orange">
                <span class="stat-label">已锁定</span>
                <strong class="stat-value">{{ stockDetail.lockedCount ?? 0 }}</strong>
              </div>
              <div class="stat-item gray">
                <span class="stat-label">已使用</span>
                <strong class="stat-value">{{ stockDetail.usedCount ?? 0 }}</strong>
              </div>
              <div class="stat-item red">
                <span class="stat-label">已作废</span>
                <strong class="stat-value">{{ stockDetail.invalidCount ?? 0 }}</strong>
              </div>
              <div class="stat-item red">
                <span class="stat-label">异常</span>
                <strong class="stat-value">{{ stockDetail.errorCount ?? 0 }}</strong>
              </div>
            </div>
          </div>
        </template>
      </section>
    </div>
    </div>
    <!-- Edit / Create Dialog -->
    <div v-if="editDialogVisible" class="modal-overlay" @click.self="closeEditDialog">
      <div class="modal-content warehouse-edit-modal">
        <h3>{{ editForm.id ? '编辑卡密分组' : '新建卡密分组' }}</h3>
        <div class="form-grid">
          <div class="form-row">
            <label>分组名称 <span class="required">*</span></label>
            <input v-model="editForm.groupName" class="input" placeholder="例如：月卡VIP" />
          </div>
          <div class="form-row">
            <label>卡密类型</label>
            <select v-model="editForm.cardType" class="input">
              <option value="unique">唯一卡密</option>
              <option value="card_password">卡号+密码</option>
              <option value="link_code">链接+提取码</option>
              <option value="account_password">账号+密码</option>
              <option value="custom">自定义文本</option>
            </select>
          </div>
          <div class="form-row">
            <label>卡号前缀（可选）</label>
            <input v-model="editForm.cardPrefix" class="input" placeholder="例如：VIP-" />
          </div>
          <div class="form-row">
            <label>密码前缀（可选）</label>
            <input v-model="editForm.passwordPrefix" class="input" placeholder="例如：PWD-" />
          </div>
          <div class="form-row">
            <label>成本单价</label>
            <input v-model.number="editForm.costPrice" type="number" step="0.01" min="0" class="input" placeholder="0.00" />
          </div>
          <div class="form-row">
            <label>售价建议</label>
            <input v-model.number="editForm.suggestedPrice" type="number" step="0.01" min="0" class="input" placeholder="0.00" />
          </div>
          <div class="form-row">
            <label>库存预警阈值</label>
            <input v-model.number="editForm.alertThreshold" type="number" min="0" class="input" placeholder="10" />
          </div>
          <div class="form-row">
            <label>状态</label>
            <select v-model.number="editForm.status" class="input">
              <option :value="1">启用</option>
              <option :value="0">禁用</option>
            </select>
          </div>
          <div class="form-row edit-remark-row">
            <label>备注</label>
            <textarea v-model="editForm.remark" class="input" rows="3" placeholder="可选备注信息"></textarea>
          </div>
        </div>
        <div class="toolbar modal-actions-row">
          <AppButton @click="closeEditDialog">取消</AppButton>
          <AppButton type="primary" :loading="saving" @click="saveGroup">{{ editForm.id ? '保存' : '创建' }}</AppButton>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { NButton, NInput, NStatistic } from 'naive-ui'
import BaseTable from '../components/BaseTable.vue'
import Badge from '../components/Badge.vue'
import AppButton from '../components/AppButton.vue'
import EmptyState from '../components/EmptyState.vue'
import { confirmDelete, confirmAction } from '../utils/confirmAction.js'
import {
  getCards,
  createCard,
  updateCard,
  deleteCard,
  getCardItems,
  batchCreateCardItems,
  deleteCardItem,
  resetCardItem,
  markCardItemInvalid,
  getCardStockStats,
  getCardUsageRecords,
  exportCardItems
} from '../api/cards.js'
import { recordsOf, totalOf, dateTime } from '../utils/apiData.js'
import { createLatestRequestGuard, listRefreshRequestConfig } from '../utils/latestRequest.js'

// ─── State ───
const error = ref('')
const success = ref('')
const groupsWarning = ref('')
const itemsWarning = ref('')
const usageWarning = ref('')
const stockWarning = ref('')
const groups = ref([])
const selected = ref(null)
const cardItems = ref([])
const usageRecords = ref([])
const stockDetail = ref({})
const groupsAvailable = ref(null)
const itemsAvailable = ref(null)
const usageAvailable = ref(null)
const stockAvailable = ref(null)
const groupsLoading = ref(true)
const itemsLoading = ref(false)
const usageLoading = ref(false)
const stockLoading = ref(false)
const query = reactive({ keyword: '' })
const groupsRequestGuard = createLatestRequestGuard()
const itemsRequestGuard = createLatestRequestGuard()
const usageRequestGuard = createLatestRequestGuard()
const stockRequestGuard = createLatestRequestGuard()

// ─── Import ───
const importGroupId = ref('')
const importMode = ref('paste')
const bulkText = ref('')
const importing = ref(false)
const importResult = ref(null)
const fileInputRef = ref(null)
const importFileName = ref('')

// ─── Items pagination ───
const itemPage = ref(1)
const itemTotal = ref(0)
const pageSize = 50
const itemStatusFilter = ref('')

// ─── Usage pagination ───
const usagePage = ref(1)
const usageTotal = ref(0)
const usagePageSize = 20

// ─── Tab ───
const activeTab = ref('items')
const tabs = [
  { key: 'items', label: '卡密明细' },
  { key: 'usage', label: '使用记录' },
  { key: 'stats', label: '库存统计' }
]

// ─── Edit Dialog ───
const editDialogVisible = ref(false)
const saving = ref(false)
const editForm = reactive({
  id: null,
  groupName: '',
  cardType: 'unique',
  cardPrefix: '',
  passwordPrefix: '',
  costPrice: 0,
  suggestedPrice: 0,
  alertThreshold: 10,
  remark: '',
  status: 1
})

// ─── Card Type Labels ───
const cardTypeMap = {
  unique: '唯一卡密',
  card_password: '卡号+密码',
  link_code: '链接+提取码',
  account_password: '账号+密码',
  custom: '自定义文本'
}
function cardTypeLabel(type) {
  return cardTypeMap[type] || type || '-'
}

// ─── Item Status ───
const itemStatusMap = {
  0: { label: '未使用', badge: 'green' },
  1: { label: '已锁定', badge: 'orange' },
  2: { label: '已使用', badge: 'gray' },
  3: { label: '已作废', badge: 'red' },
  4: { label: '异常', badge: 'red' }
}
function itemStatusLabel(status) {
  return itemStatusMap[status]?.label || '未知'
}
function itemStatusBadge(status) {
  return itemStatusMap[status]?.badge || 'gray'
}

// ─── Computed ───
const groupRows = computed(() => groups.value.map(g => ({ ...g, raw: g })))

const groupCols = [
  { key: 'name', title: '分组名称' },
  { key: 'cardType', title: '类型' },
  { key: 'totalCount', title: '总量' },
  { key: 'remain', title: '可用' },
  { key: 'usedCount', title: '已使用' },
  { key: 'status', title: '状态' },
  { key: 'op', title: '操作' }
]

const itemCols = [
  { key: 'content', title: '卡密内容' },
  { key: 'status', title: '状态' },
  { key: 'usedOrderId', title: '订单ID' },
  { key: 'usedTime', title: '使用时间' },
  { key: 'op', title: '操作' }
]

const usageCols = [
  { key: 'content', title: '卡密内容' },
  { key: 'orderInfo', title: '关联订单' },
  { key: 'usedTime', title: '使用时间' }
]

const stockStats = computed(() => {
  return groups.value.reduce((a, g) => ({
    total: a.total + Number(g.totalCount || 0),
    remain: a.remain + Number(g.remainCount || 0),
    used: a.used + Number(g.usedCount || 0),
    invalid: a.invalid + Number(g.invalidCount || 0) + Number(g.errorCount || 0)
  }), { total: 0, remain: 0, used: 0, invalid: 0 })
})

const lowStockCount = computed(() => {
  return groups.value.filter(g => Number(g.remainCount || 0) < (g.alertThreshold || 10)).length
})

function remainToneClass(row) {
  return Number(row.remainCount || 0) < (row.alertThreshold || 10) ? 'is-low' : 'is-healthy'
}

function groupsMetric(value) {
  return groupsAvailable.value === true ? value : '—'
}

const warehouseStatCards = computed(() => [
  { key: 'groups', title: '卡密组', value: groupsMetric(groups.value.length), change: '总分组数', symbol: '组', tone: 'tone-blue' },
  { key: 'total', title: '卡密总量', value: groupsMetric(stockStats.value.total), change: '全部卡密', symbol: '总', tone: 'tone-cyan' },
  { key: 'remain', title: '未使用', value: groupsMetric(stockStats.value.remain), change: '可用库存', symbol: '余', tone: 'tone-green' },
  { key: 'used', title: '已使用', value: groupsMetric(stockStats.value.used), change: '已消耗', symbol: '用', tone: 'tone-gray' },
  { key: 'invalid', title: '异常/作废', value: groupsMetric(stockStats.value.invalid), change: '需关注', symbol: '异', tone: 'tone-orange' },
  { key: 'low', title: '低库存', value: groupsMetric(lowStockCount.value), change: '低于预警阈值', symbol: '低', tone: 'tone-red' }
])

const bulkCount = computed(() => {
  return bulkText.value.split(/\n+/).map(s => s.trim()).filter(Boolean).length
})

const itemPages = computed(() => Math.max(1, Math.ceil(itemTotal.value / pageSize)))
const usagePages = computed(() => Math.max(1, Math.ceil(usageTotal.value / usagePageSize)))
const groupsRefreshing = computed(() => groupsLoading.value && groupsAvailable.value === true)
const itemsRefreshing = computed(() => itemsLoading.value && itemsAvailable.value === true)
const usageRefreshing = computed(() => usageLoading.value && usageAvailable.value === true)
const stockRefreshing = computed(() => stockLoading.value && stockAvailable.value === true)
const warehouseActionHint = computed(() => {
  if (saving.value) return '正在保存卡密分组，完成前请不要重复提交。'
  if (importing.value) return '正在导入卡密，导入完成后会自动刷新库存。'
  if (groupsLoading.value && groupsAvailable.value !== true) return '正在读取卡密分组和库存摘要。'
  if (groupsRefreshing.value) return '正在后台刷新库存，当前列表仍可查看。'
  if (groupsAvailable.value === false) return '卡密分组暂不可用，请先恢复服务后再新增或导入。'
  if (!groups.value.length) return '还没有卡密组，请先创建分组再导入库存。'
  if (!selected.value) return '请选择一个卡密分组查看明细和使用记录。'
  if (lowStockCount.value > 0) return `有 ${lowStockCount.value} 个分组低于预警阈值，建议补充库存。`
  return `当前选中「${selected.value.groupName || '卡密分组'}」，可查看明细或导入库存。`
})

function resetSelectedGroupData() {
  itemsRequestGuard.invalidate()
  usageRequestGuard.invalidate()
  stockRequestGuard.invalidate()
  itemsLoading.value = false
  usageLoading.value = false
  stockLoading.value = false
  itemsAvailable.value = null
  usageAvailable.value = null
  stockAvailable.value = null
  itemsWarning.value = ''
  usageWarning.value = ''
  stockWarning.value = ''
  cardItems.value = []
  itemTotal.value = 0
  usageRecords.value = []
  usageTotal.value = 0
  stockDetail.value = {}
}

// ─── Group CRUD ───
async function load() {
  const request = groupsRequestGuard.begin()
  const hadSnapshot = groupsAvailable.value === true
  groupsLoading.value = true
  error.value = ''
  success.value = ''
  groupsWarning.value = ''
  try {
    const res = await getCards(query, listRefreshRequestConfig(hadSnapshot))
    if (!request.isCurrent()) return
    groups.value = recordsOf(res.data)
    groupsAvailable.value = true
    if (selected.value) {
      const current = groups.value.find(g => String(g.id) === String(selected.value.id))
      if (current) selected.value = current
      else {
        selected.value = null
        importGroupId.value = ''
        resetSelectedGroupData()
      }
    }
    if (!selected.value && groups.value[0]) {
      await selectGroup(groups.value[0])
    }
  } catch (e) {
    if (!request.isCurrent()) return
    if (hadSnapshot) {
      groupsWarning.value = `卡密分组刷新失败，继续显示上次成功加载的分组数据。${e.message ? ` ${e.message}` : ''}`
    } else {
      groupsAvailable.value = false
      groups.value = []
      selected.value = null
      importGroupId.value = ''
      resetSelectedGroupData()
      error.value = e.message || '卡密分组加载失败'
    }
  } finally {
    if (request.isCurrent()) groupsLoading.value = false
  }
}

async function selectGroup(g) {
  resetSelectedGroupData()
  selected.value = g
  importGroupId.value = g.id
  activeTab.value = 'items'
  itemPage.value = 1
  itemStatusFilter.value = ''
  await loadItems()
}

function openCreateDialog() {
  editForm.id = null
  editForm.groupName = ''
  editForm.cardType = 'unique'
  editForm.cardPrefix = ''
  editForm.passwordPrefix = ''
  editForm.costPrice = 0
  editForm.suggestedPrice = 0
  editForm.alertThreshold = 10
  editForm.remark = ''
  editForm.status = 1
  editDialogVisible.value = true
}

function openEditDialog(group) {
  editForm.id = group.id
  editForm.groupName = group.groupName || ''
  editForm.cardType = group.cardType || 'unique'
  editForm.cardPrefix = group.cardPrefix || ''
  editForm.passwordPrefix = group.passwordPrefix || ''
  editForm.costPrice = Number(group.costPrice || 0)
  editForm.suggestedPrice = Number(group.suggestedPrice || 0)
  editForm.alertThreshold = Number(group.alertThreshold || 10)
  editForm.remark = group.remark || ''
  editForm.status = group.status !== undefined ? group.status : 1
  editDialogVisible.value = true
}

function closeEditDialog() {
  editDialogVisible.value = false
}

async function saveGroup() {
  if (!editForm.groupName.trim()) {
    error.value = '请输入分组名称'
    return
  }
  saving.value = true
  error.value = ''
  success.value = ''
  try {
    const data = { ...editForm }
    if (editForm.id) {
      await updateCard(editForm.id, data)
      success.value = '卡密分组已更新'
    } else {
      await createCard(data)
      success.value = '卡密分组已创建'
    }
    editDialogVisible.value = false
    await load()
  } catch (e) {
    error.value = e.message || '保存失败'
  } finally {
    saving.value = false
  }
}

async function removeGroup(id) {
  if (!await confirmAction({ title: '确认删除卡密分组？', description: '该操作会影响自动发货库存，请确认没有正在使用的发货规则。', dangerous: true, confirmText: '删除' })) return
  try {
    await deleteCard(id)
    success.value = '卡密分组已删除'
    if (selected.value && String(selected.value.id) === String(id)) {
      selected.value = null
    }
    await load()
  } catch (e) {
    error.value = e.message
  }
}

// ─── Import ───
async function submitImport() {
  if (importing.value) return
  if (!importGroupId.value) {
    error.value = '请选择目标分组'
    return
  }
  let lines = []
  if (importMode.value === 'paste') {
    lines = bulkText.value.split(/\n+/).map(s => s.trim()).filter(Boolean)
  } else if (importFileName.value) {
    // lines already populated from file read
    lines = parsedFileLines.value
  }
  if (!lines.length) {
    error.value = importMode.value === 'paste' ? '请粘贴卡密内容' : '请选择文件'
    return
  }
  importing.value = true
  error.value = ''
  success.value = ''
  importResult.value = null
  try {
    const payload = lines.map(line => {
      // Support "----" separator for card+password types
      const sepIdx = line.indexOf('----')
      if (sepIdx > 0) {
        return { content: line, cardContent: line.slice(0, sepIdx), password: line.slice(sepIdx + 4) }
      }
      // Support comma/tab separator
      const commaIdx = line.indexOf(',')
      if (commaIdx > 0) {
        return { content: line, cardContent: line.slice(0, commaIdx), password: line.slice(commaIdx + 1) }
      }
      const tabIdx = line.indexOf('\t')
      if (tabIdx > 0) {
        return { content: line, cardContent: line.slice(0, tabIdx), password: line.slice(tabIdx + 1) }
      }
      return { content: line }
    })
    const res = await batchCreateCardItems(importGroupId.value, { items: payload })
    const resultData = res?.data || {}
    importResult.value = {
      success: resultData.successCount ?? resultData.success ?? payload.length,
      duplicate: resultData.duplicateCount ?? resultData.duplicate ?? 0,
      fail: resultData.failCount ?? resultData.fail ?? 0
    }
    success.value = `成功导入 ${importResult.value.success} 条卡密`
    bulkText.value = ''
    importFileName.value = ''
    parsedFileLines.value = []
    await load()
    const g = groups.value.find(x => String(x.id) === String(importGroupId.value))
    if (g) {
      selected.value = g
      await loadItems()
    }
  } catch (e) {
    error.value = e.message || '导入失败'
    importResult.value = { success: 0, duplicate: 0, fail: 1 }
  } finally {
    importing.value = false
  }
}

const parsedFileLines = ref([])

function triggerFileInput() {
  fileInputRef.value?.click()
}

function handleFileSelect(e) {
  const file = e.target.files?.[0]
  if (file) readImportFile(file)
}

function handleFileDrop(e) {
  const file = e.dataTransfer?.files?.[0]
  if (file) readImportFile(file)
}

function readImportFile(file) {
  importFileName.value = file.name
  parsedFileLines.value = []
  const reader = new FileReader()
  reader.onload = (ev) => {
    const text = ev.target?.result || ''
    const lines = text.split(/\r?\n/).map(s => s.trim()).filter(Boolean)
    parsedFileLines.value = lines
  }
  reader.onerror = () => {
    error.value = '文件读取失败'
  }
  reader.readAsText(file)
}

// ─── Export ───
async function exportGroup(group) {
  try {
    const res = await exportCardItems(group.id, {})
    const blob = new Blob([res], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${group.groupName}_卡密导出.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    success.value = `「${group.groupName}」卡密已导出`
  } catch (e) {
    error.value = e.message || '导出失败'
  }
}

// ─── Items ───
async function loadItems() {
  if (!selected.value) return
  const request = itemsRequestGuard.begin()
  const hadSnapshot = itemsAvailable.value === true
  const groupId = selected.value.id
  itemsLoading.value = true
  itemsWarning.value = ''
  error.value = ''
  try {
    const params = { current: itemPage.value, size: pageSize }
    if (itemStatusFilter.value !== '') {
      params.status = itemStatusFilter.value
    }
    const res = await getCardItems(groupId, params, listRefreshRequestConfig(hadSnapshot))
    if (!request.isCurrent()) return
    const pageData = recordsOf(res.data)
    cardItems.value = Array.isArray(pageData) ? pageData : []
    itemTotal.value = totalOf(res.data, cardItems.value.length)
    itemsAvailable.value = true
  } catch (requestError) {
    if (!request.isCurrent()) return
    if (hadSnapshot) {
      itemsWarning.value = `卡密明细刷新失败，继续显示上次成功加载的卡密数据。${requestError.message ? ` ${requestError.message}` : ''}`
    } else {
      cardItems.value = []
      itemTotal.value = 0
      itemsAvailable.value = false
      error.value = '卡密明细暂不可用，当前不会把查询失败显示为空库存。'
    }
  } finally {
    if (request.isCurrent()) itemsLoading.value = false
  }
}

function filterItems() {
  itemPage.value = 1
  loadItems()
}

async function removeItem(item) {
  if (!selected.value || !await confirmDelete('该卡密')) return
  try {
    await deleteCardItem(selected.value.id, item.id)
    success.value = '卡密已删除'
    await loadItems()
    await load()
  } catch (e) {
    error.value = e.message
  }
}

async function resetItem(item) {
  if (!selected.value) return
  try {
    await resetCardItem(selected.value.id, item.id)
    success.value = '卡密已重置'
    await loadItems()
    await load()
  } catch (e) {
    error.value = e.message
  }
}

async function lockItem(item) {
  if (!selected.value) return
  try {
    const { lockCardItem } = await import('../api/cards.js')
    await lockCardItem(selected.value.id, item.id)
    success.value = '卡密已锁定'
    await loadItems()
    await load()
  } catch (e) {
    error.value = e.message || '锁定失败'
  }
}

async function markInvalid(item) {
  if (!selected.value) return
  if (!await confirmAction({ title: '确认作废该卡密？', dangerous: true })) return
  try {
    await markCardItemInvalid(selected.value.id, item.id)
    success.value = '卡密已作废'
    await loadItems()
    await load()
  } catch (e) {
    error.value = e.message
  }
}

// ─── Usage Records ───
async function loadUsageRecords() {
  if (!selected.value) return
  const request = usageRequestGuard.begin()
  const hadSnapshot = usageAvailable.value === true
  const groupId = selected.value.id
  usageLoading.value = true
  usageWarning.value = ''
  error.value = ''
  try {
    const params = { current: usagePage.value, size: usagePageSize }
    const res = await getCardUsageRecords(groupId, params, listRefreshRequestConfig(hadSnapshot))
    if (!request.isCurrent()) return
    const pageData = recordsOf(res.data)
    usageRecords.value = Array.isArray(pageData) ? pageData : []
    usageTotal.value = totalOf(res.data, usageRecords.value.length)
    usageAvailable.value = true
  } catch (requestError) {
    if (!request.isCurrent()) return
    if (hadSnapshot) {
      usageWarning.value = `使用记录刷新失败，继续显示上次成功加载的记录。${requestError.message ? ` ${requestError.message}` : ''}`
    } else {
      usageRecords.value = []
      usageTotal.value = 0
      usageAvailable.value = false
      error.value = '卡密使用记录暂不可用，当前无法确认是否存在使用记录。'
    }
  } finally {
    if (request.isCurrent()) usageLoading.value = false
  }
}

// ─── Stock Stats ───
async function loadStockStats() {
  if (!selected.value) return
  const request = stockRequestGuard.begin()
  const hadSnapshot = stockAvailable.value === true
  const groupId = selected.value.id
  stockLoading.value = true
  stockWarning.value = ''
  error.value = ''
  try {
    const res = await getCardStockStats(groupId, listRefreshRequestConfig(hadSnapshot))
    if (!request.isCurrent()) return
    stockDetail.value = res?.data || {}
    stockAvailable.value = true
  } catch (requestError) {
    if (!request.isCurrent()) return
    if (hadSnapshot) {
      stockWarning.value = `库存统计刷新失败，继续显示上次成功加载的统计。${requestError.message ? ` ${requestError.message}` : ''}`
    } else {
      stockDetail.value = {}
      stockAvailable.value = false
      error.value = '卡密库存统计暂不可用，当前不会用全零数据代替查询失败。'
    }
  } finally {
    if (request.isCurrent()) stockLoading.value = false
  }
}

// ─── Tab Switching ───
function switchTab(key) {
  activeTab.value = key
  if (key === 'items') {
    itemPage.value = 1
    loadItems()
  } else if (key === 'usage') {
    usagePage.value = 1
    loadUsageRecords()
  } else if (key === 'stats') {
    loadStockStats()
  }
}

function onHeaderAction(event) {
  if (event.detail === 'cards-create-group') openCreateDialog()
  if (event.detail === 'cards-export-current' && selected.value) exportGroup(selected.value)
  if (event.detail === 'cards-refresh') load()
}

onMounted(() => {
  window.addEventListener('xya-header-action', onHeaderAction)
  load()
})

onBeforeUnmount(() => {
  groupsRequestGuard.invalidate()
  itemsRequestGuard.invalidate()
  usageRequestGuard.invalidate()
  stockRequestGuard.invalidate()
  window.removeEventListener('xya-header-action', onHeaderAction)
})
</script>

<style scoped>
.card-warehouse-page {
  --warehouse-text: #101828;
  --warehouse-muted: #64748b;
  --warehouse-line: #e5eaf0;
  --warehouse-soft: #f8fafc;
  --warehouse-primary: #1d4ed8;
  --warehouse-primary-soft: #eff6ff;
  --warehouse-danger: #dc2626;
  --warehouse-success: #059669;
  --warehouse-ease: cubic-bezier(0.23, 1, 0.32, 1);
  display: grid;
  gap: 18px;
  min-width: 0;
  color: var(--warehouse-text);
}

.card-warehouse-page * {
  box-sizing: border-box;
}

.card-warehouse-notices {
  display: grid;
  gap: 8px;
}

.warehouse-command-center {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(280px, 340px);
  gap: 16px;
  min-width: 0;
  padding: 18px;
  border: 1px solid #dbe4ef;
  border-left: 5px solid #0f766e;
  border-radius: 8px;
  background:
    linear-gradient(135deg, rgba(15, 118, 110, .08), rgba(37, 99, 235, .04) 44%, rgba(255, 255, 255, .96)),
    #fff;
  box-shadow: 0 16px 42px rgba(15, 23, 42, .08);
}

.warehouse-command-main {
  min-width: 0;
  display: grid;
  align-content: start;
  gap: 10px;
}

.warehouse-command-kicker {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  color: #0f766e;
  font-size: 12px;
  font-weight: 700;
}

.warehouse-command-kicker span,
.warehouse-command-kicker b {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 9px;
  border-radius: 999px;
  background: rgba(15, 118, 110, .1);
}

.warehouse-command-kicker b {
  max-width: min(420px, 100%);
  overflow: hidden;
  color: #1f2937;
  text-overflow: ellipsis;
  white-space: nowrap;
  background: rgba(255, 255, 255, .82);
}

.warehouse-command-main h2 {
  margin: 0;
  color: #0f172a;
  font-size: 26px;
  font-weight: 750;
  line-height: 1.22;
}

.warehouse-command-main p {
  max-width: 720px;
  margin: 0;
  color: #526079;
  font-size: 13px;
  line-height: 1.7;
}

.warehouse-command-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 2px;
}

.warehouse-command-meta span {
  min-height: 28px;
  display: inline-flex;
  align-items: center;
  padding: 0 10px;
  border: 1px solid rgba(148, 163, 184, .26);
  border-radius: 6px;
  background: rgba(255, 255, 255, .78);
  color: #334155;
  font-size: 12px;
  font-weight: 650;
}

.warehouse-command-panel {
  align-self: stretch;
  min-width: 0;
  display: grid;
  gap: 14px;
  padding: 14px;
  border: 1px solid rgba(148, 163, 184, .25);
  border-radius: 8px;
  background: rgba(255, 255, 255, .9);
}

.warehouse-command-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  color: #64748b;
  font-size: 12px;
}

.warehouse-command-panel-head strong {
  color: #0f766e;
  font-size: 13px;
}

.warehouse-command-buttons {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.warehouse-command-buttons :deep(.n-button) {
  min-width: 0;
  transition:
    transform 150ms var(--warehouse-ease),
    box-shadow 150ms var(--warehouse-ease),
    border-color 150ms var(--warehouse-ease),
    background-color 150ms var(--warehouse-ease);
}

.warehouse-command-buttons :deep(.n-button:not(.n-button--disabled):active) {
  transform: scale(.97);
}

.warehouse-action-hint {
  margin: 0;
  color: var(--warehouse-muted);
  font-size: 12px;
  line-height: 1.55;
}

.warehouse-metric-rail {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
}

.warehouse-metric-card {
  min-width: 0;
  min-height: 136px;
  display: grid;
  grid-template-rows: auto 1fr auto;
  gap: 8px;
  padding: 14px;
  border: 1px solid #e4ebf5;
  border-top: 3px solid #64748b;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 10px 28px rgba(15, 23, 42, .06);
}

.warehouse-metric-icon {
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  color: #fff;
  background: #64748b;
  font-size: 12px;
  font-weight: 750;
}

.warehouse-metric-card.tone-blue { border-top-color: #2563eb; }
.warehouse-metric-card.tone-blue .warehouse-metric-icon { background: #2563eb; }
.warehouse-metric-card.tone-cyan { border-top-color: #0891b2; }
.warehouse-metric-card.tone-cyan .warehouse-metric-icon { background: #0891b2; }
.warehouse-metric-card.tone-green { border-top-color: #059669; }
.warehouse-metric-card.tone-green .warehouse-metric-icon { background: #059669; }
.warehouse-metric-card.tone-gray { border-top-color: #64748b; }
.warehouse-metric-card.tone-gray .warehouse-metric-icon { background: #64748b; }
.warehouse-metric-card.tone-orange { border-top-color: #ea580c; }
.warehouse-metric-card.tone-orange .warehouse-metric-icon { background: #ea580c; }
.warehouse-metric-card.tone-red { border-top-color: #dc2626; }
.warehouse-metric-card.tone-red .warehouse-metric-icon { background: #dc2626; }

.warehouse-metric-card :deep(.n-statistic .n-statistic-label) {
  color: #64748b;
  font-size: 12px;
}

.warehouse-metric-card :deep(.n-statistic .n-statistic-value) {
  color: #111827;
  font-size: 24px;
  font-weight: 760;
}

.warehouse-metric-card small {
  color: #64748b;
  font-size: 12px;
  line-height: 1.45;
}

.card-warehouse-workspace {
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(380px, .62fr);
  gap: 16px;
  align-items: start;
}

.card-warehouse-left,
.card-warehouse-right {
  min-width: 0;
  display: grid;
  gap: 16px;
}

.warehouse-panel {
  min-width: 0;
  padding: 16px;
  border: 1px solid #e4ebf5;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 10px 28px rgba(15, 23, 42, .05);
}

.warehouse-panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid #eef2f7;
}

.warehouse-panel-head span {
  color: #0f766e;
  font-size: 12px;
  font-weight: 760;
}

.warehouse-panel-head h3 {
  margin: 4px 0 0;
  color: #111827;
  font-size: 17px;
  font-weight: 730;
  line-height: 1.35;
}

.warehouse-panel-head b {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: #f1f5f9;
  color: #475569;
  font-size: 12px;
}

.warehouse-toolbar {
  display: grid;
  grid-template-columns: minmax(240px, 1fr) auto auto;
  gap: 10px;
  align-items: center;
  margin-bottom: 12px;
}

.warehouse-detail-panel {
  position: sticky;
  top: 118px;
}

.group-name-cell {
  min-width: 0;
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 6px;
}

.group-name-cell strong {
  min-width: 0;
  color: var(--warehouse-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.group-remark {
  font-style: normal;
}

.remain-count {
  font-weight: 760;
}

.remain-count.is-healthy {
  color: var(--warehouse-success);
}

.remain-count.is-low {
  color: var(--warehouse-danger);
}

.warehouse-v14-shell .toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.warehouse-import-panel .form-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.warehouse-edit-modal .form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.form-row {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-row > label:first-child {
  color: var(--warehouse-text);
  font-size: 13px;
  font-weight: 700;
}

.warehouse-v14-shell .input {
  box-sizing: border-box;
  width: 100%;
  min-height: 36px;
  padding: 0 11px;
  border: 1px solid var(--warehouse-line);
  border-radius: 8px;
  background: #fff;
  color: var(--warehouse-text);
  font: inherit;
  transition:
    border-color 150ms var(--warehouse-ease),
    box-shadow 150ms var(--warehouse-ease),
    background-color 150ms var(--warehouse-ease);
}

textarea.input {
  min-height: 96px;
  padding: 9px 11px;
  resize: vertical;
}

.warehouse-v14-shell .input:focus {
  outline: none;
  border-color: var(--warehouse-primary);
  box-shadow: 0 0 0 3px rgba(29, 78, 216, .12);
}

.warehouse-v14-shell .input:disabled {
  cursor: not-allowed;
  background: var(--warehouse-soft);
  color: #94a3b8;
}

.bulk-count-note,
.file-format-note {
  margin-top: 4px;
  line-height: 1.5;
}

.file-input-hidden {
  display: none;
}

.import-action-row {
  flex-direction: row;
  align-items: center;
  gap: 12px;
}

.detail-empty-state {
  padding: 40px 0;
}

.detail-toolbar {
  margin-bottom: 8px;
}

.item-status-select {
  max-width: 140px;
  margin-left: auto;
}

.edit-remark-row {
  grid-column: 1 / -1;
}

.modal-actions-row {
  justify-content: flex-end;
  margin-top: 20px;
}

.success { background: #ecfdf3; color: #067647; border-color: #abefc6; }
.warning,
.inline-warning {
  background: #fff8e8;
  color: #8a4b08;
  border-color: #f7c97a;
}

.inline-warning {
  margin-bottom: 10px;
  padding: 9px 11px;
  border: 1px solid #f7c97a;
  border-radius: 8px;
  font-size: 13px;
}

.refresh-status {
  margin-bottom: 10px;
  color: #526079;
  font-size: 13px;
}

.import-tabs {
  display: flex;
  gap: 4px;
  background: #f5f6fa;
  border-radius: 8px;
  padding: 3px;
}
.import-tab {
  flex: 1;
  padding: 7px 12px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: #526079;
  font-size: 13px;
  cursor: pointer;
  font-weight: 500;
  transition:
    transform 150ms var(--warehouse-ease),
    background-color 150ms var(--warehouse-ease),
    color 150ms var(--warehouse-ease),
    box-shadow 150ms var(--warehouse-ease);
}
.import-tab.active {
  background: #fff;
  color: var(--warehouse-primary);
  box-shadow: 0 1px 3px rgba(0,0,0,.08);
}
.import-tab:active { transform: scale(.98); }
.import-tab:hover:not(.active) { color: var(--warehouse-primary); }

.file-drop-zone {
  border: 1px dashed #cbd5e1;
  border-radius: 8px;
  background: #FFFFFF;
  padding: 24px 16px;
  text-align: center;
  color: #0f766e;
  font-weight: 600;
  cursor: pointer;
  transition:
    transform 150ms var(--warehouse-ease),
    border-color 150ms var(--warehouse-ease),
    background-color 150ms var(--warehouse-ease),
    color 150ms var(--warehouse-ease);
  width: 100%;
  color: inherit;
  font: inherit;
}

@media (hover: hover) and (pointer: fine) {
  .file-drop-zone:hover {
    border-color: var(--warehouse-primary);
    background: var(--warehouse-primary-soft);
    color: var(--warehouse-primary);
  }
}

.file-drop-zone:active {
  transform: scale(.99);
}

.file-drop-zone .file-name {
  color: var(--warehouse-text);
  font-weight: 600;
}

.import-result {
  display: inline-flex;
  gap: 12px;
  font-size: 13px;
  font-weight: 600;
}
.import-success { color: #16bf78; }
.import-duplicate { color: #f59e0b; }
.import-fail { color: #ef4444; }

.tab-bar {
  display: flex;
  gap: 4px;
  margin-bottom: 14px;
  background: #f5f6fa;
  border-radius: 8px;
  padding: 3px;
}
.tab-btn {
  flex: 1;
  padding: 8px 12px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: #526079;
  font-size: 13px;
  cursor: pointer;
  font-weight: 500;
  transition:
    transform 150ms var(--warehouse-ease),
    background-color 150ms var(--warehouse-ease),
    color 150ms var(--warehouse-ease),
    box-shadow 150ms var(--warehouse-ease);
}
.tab-btn.active {
  background: #fff;
  color: var(--warehouse-primary);
  box-shadow: 0 1px 3px rgba(0,0,0,.08);
}
.tab-btn:active { transform: scale(.98); }
.tab-btn:hover:not(.active) { color: var(--warehouse-primary); }

.table-info {
  font-size: 14px;
  color: #526079;
}

.card-content-text {
  max-width: 280px;
  display: inline-block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: middle;
}

/* Stock Stats */
.stock-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  padding: 4px 0;
}
.stat-item {
  background: #f8faff;
  border: 1px solid #F0F0F0;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}
.stat-item .stat-label {
  display: block;
  font-size: 13px;
  color: #667085;
  margin-bottom: 6px;
}
.stat-item .stat-value {
  font-size: 22px;
  color: #16213e;
}
.stat-item.green .stat-value { color: #16bf78; }
.stat-item.orange .stat-value { color: #f59e0b; }
.stat-item.gray .stat-value { color: #667085; }
.stat-item.red .stat-value { color: #ef4444; }

/* Pagination */
.pagination {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 0 4px;
  font-size: 13px;
  color: #667085;
}
.page-info {
  margin-right: 8px;
}
.page-no {
  min-width: 32px;
  height: 32px;
  border: 1px solid #e4ebf5;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  cursor: pointer;
  font-size: 15px;
  color: #526079;
  transition:
    transform 150ms var(--warehouse-ease),
    border-color 150ms var(--warehouse-ease),
    color 150ms var(--warehouse-ease),
    background-color 150ms var(--warehouse-ease);
}
.page-no:hover:not(:disabled) {
  border-color: var(--warehouse-primary);
  color: var(--warehouse-primary);
  background: var(--warehouse-primary-soft);
}
.page-no:active:not(:disabled) {
  transform: scale(.97);
}
.page-no:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.warehouse-v14-shell .link {
  transition:
    color 150ms var(--warehouse-ease),
    opacity 150ms var(--warehouse-ease),
    transform 150ms var(--warehouse-ease);
}

.warehouse-v14-shell .link:active:not(:disabled) {
  transform: scale(.97);
}

.warehouse-v14-shell .link:disabled {
  cursor: not-allowed;
  opacity: .45;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.35);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal-content {
  background: #fff;
  border-radius: 8px;
  padding: 28px;
  max-width: 540px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0,0,0,.2);
}
.modal-content h3 {
  margin: 0 0 16px;
  font-size: 18px;
  color: #16213e;
}

.required { color: #ef4444; }

.subtle { color: #98a2b3; font-size: 13px; }

@media (max-width: 900px) {
  .card-warehouse-page {
    gap: 12px;
  }

  .warehouse-command-center,
  .card-warehouse-workspace,
  .warehouse-toolbar {
    grid-template-columns: minmax(0, 1fr);
  }

  .warehouse-command-center,
  .warehouse-panel {
    padding: 14px;
  }

  .warehouse-command-main h2 {
    font-size: 22px;
  }

  .warehouse-command-buttons {
    grid-template-columns: minmax(0, 1fr);
  }

  .warehouse-metric-rail {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }

  .warehouse-metric-card {
    min-height: 126px;
    padding: 12px;
  }

  .warehouse-detail-panel {
    position: static;
  }

  .warehouse-panel-head {
    gap: 10px;
    margin-bottom: 12px;
  }

  .import-tabs {
    gap: 4px;
    padding: 3px;
  }
  .import-tab {
    padding: 8px 10px;
    font-size: 13px;
  }

  .file-drop-zone {
    padding: 16px 12px;
    font-size: 13px;
  }

  .import-result {
    flex-wrap: wrap;
    gap: 8px;
    font-size: 13px;
  }

  .tab-bar {
    gap: 4px;
    padding: 3px;
    margin-bottom: 10px;
  }
  .tab-btn {
    padding: 8px 6px;
    font-size: 13px;
  }

  .table-info {
    font-size: 13px;
  }

  /* 卡密内容文本收窄 */
  .card-content-text {
    max-width: 160px;
  }

  .stock-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }
  .stock-stats > * {
    min-width: 0;
  }
  .stat-item {
    padding: 12px;
  }
  .stat-item .stat-label {
    font-size: 12px;
    margin-bottom: 4px;
  }
  .stat-item .stat-value {
    font-size: 18px;
  }

  .pagination {
    gap: 6px;
    padding: 10px 0 4px;
    font-size: 13px;
  }
  .page-info {
    margin-right: 4px;
  }
  .page-no {
    min-width: 36px;
    height: 36px;
    font-size: 15px;
  }

  .modal-overlay {
    align-items: flex-end;
  }
  .modal-content {
    width: 100vw;
    max-width: 100vw;
    max-height: 90vh;
    border-radius: 8px 8px 0 0;
    padding: 16px 14px;
    overflow-y: auto;
    -webkit-overflow-scrolling: touch;
  }
  .modal-content h3 {
    margin: 0 0 12px;
    font-size: 18px;
  }

  .warehouse-edit-modal .form-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .import-action-row {
    align-items: flex-start;
    flex-direction: column;
  }

  .item-status-select {
    max-width: none;
    margin-left: 0;
  }
}
</style>
