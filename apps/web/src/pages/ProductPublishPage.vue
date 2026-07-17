<template>
  <div class="publish-console">
    <div class="publish-notices">
      <div v-if="error" class="global-notice error">{{ error }}</div>
      <div v-if="warning" class="global-notice warning">{{ warning }}</div>
      <div v-if="success" class="global-notice success">{{ success }}</div>
      <div v-if="publishIntent.payload" class="global-notice warning publish-intent-notice" role="status">
        <b>当前是恢复中的发布任务</b>
        <span>本次操作固定使用下列数据和原安全凭证；页面表单的后续改动不会进入该恢复请求。</span>
        <pre>{{ persistedIntentSummary }}</pre>
      </div>
    </div>

    <section class="publish-command-center">
      <div class="publish-command-main">
        <div class="publish-command-kicker">
          <span>发布作业</span>
          <b>{{ accountsAvailable === true ? '账号可用' : '账号待确认' }}</b>
        </div>
        <h2>商品发布作业台</h2>
        <p>先确认账号、图片、分类、位置和履约口径，再提交到闲鱼；右侧会同步显示发布摘要和必填项核验。</p>
        <div class="publish-command-steps">
          <span>资料</span>
          <span>图片</span>
          <span>分类</span>
          <span>位置</span>
          <span>价格</span>
          <span>核验</span>
        </div>
      </div>
      <div class="publish-command-panel">
        <div class="publish-command-panel-head">
          <span>发布状态</span>
          <strong>{{ checks.filter(item => item.ok).length }}/{{ checks.length }} 项通过</strong>
        </div>
        <div class="publish-command-actions">
          <AppButton @click="handleCancel">取消</AppButton>
          <AppButton type="primary" :loading="submitting" :disabled="publishSubmitDisabled" @click="submit">{{ publishSubmitLabel }}</AppButton>
        </div>
      </div>
    </section>

    <section class="publish-workbench">
      <main class="publish-main">
        <section class="publish-panel publish-basic-panel">
          <header class="publish-panel-head">
            <div>
              <span>资料录入</span>
              <h3>宝贝基础信息</h3>
            </div>
            <b>{{ form.title.length }}/30</b>
          </header>
          <div class="publish-form-grid">
            <div class="publish-form-row">
              <label>闲鱼账号</label>
              <select v-model="form.accountId" :disabled="accountsAvailable !== true">
                <option value="">请选择账号</option>
                <option v-for="a in accounts" :key="a.id" :value="a.id">{{ accountName(a) }}</option>
              </select>
              <span v-if="accountsAvailable === false" class="field-error">账号列表暂不可用，当前禁止发布。</span>
            </div>
            <div class="publish-form-row">
              <label>宝贝标题</label>
              <input v-model="form.title" maxlength="30" placeholder="请填写宝贝标题，建议包含品牌、规格、成色等关键信息">
              <span class="char-count">{{ form.title.length }}/30</span>
            </div>
            <div class="publish-form-row publish-form-row-wide">
              <label>宝贝描述</label>
              <textarea v-model="form.description" rows="4" placeholder="请详细描述宝贝的成色、功能、使用感受等信息..."></textarea>
              <div class="chips">
                <button type="button" class="chip" :disabled="aiDescLoading" @click="aiDesc">{{ aiDescLoading ? 'AI 生成中...' : 'AI 生成描述' }}</button>
                <button type="button" class="chip" @click="insertPhrase">插入常用语</button>
              </div>
              <p v-if="!aiCategoryStatus.configured" class="ai-unconfigured-tip">
                {{ aiCategoryStatus.message || '未配置通用模型，AI 生成功能当前不可用。' }}
              </p>
            </div>
          </div>
        </section>

        <section class="publish-panel publish-media-panel">
          <header class="publish-panel-head">
            <div>
              <span>素材</span>
              <h3>宝贝图片</h3>
            </div>
            <b>{{ form.imageUrls.length }}/10 张</b>
          </header>
          <p class="publish-panel-desc">拖拽图片可调整顺序，第一张会作为封面参与自动分类。</p>
          <div class="image-strip">
          <div
            v-for="(img, idx) in form.imageUrls"
            :key="idx"
            class="img-card"
            draggable="true"
            @dragstart="onDragStart(idx, $event)"
            @dragover.prevent="onDragOver(idx, $event)"
            @drop="onDrop(idx, $event)"
          >
            <img :src="img" alt="">
            <button type="button" class="img-remove" :disabled="uploadingImages" :aria-label="`移除第 ${idx + 1} 张图片`" @click="removeImage(idx)">×</button>
          </div>
          <button
            v-if="form.imageUrls.length < 10"
            type="button"
            class="img-card add-card"
            :disabled="uploadingImages"
            @click="triggerUpload"
          >
            <span class="img-add-mark">{{ uploadingImages ? '…' : '＋' }}</span>
            <span class="img-add-text">{{ uploadingImages ? '上传中，请稍候' : '上传图片' }}</span>
          </button>
          <input
            ref="fileInput"
            type="file"
            accept="image/jpeg,image/png,image/gif,image/webp"
            multiple
            :disabled="uploadingImages"
            class="publish-file-input"
            @change="onFileSelect"
          >
          </div>
        </section>

        <section class="publish-panel">
          <header class="publish-panel-head">
            <div>
              <span>分类</span>
              <h3>商品分类</h3>
            </div>
            <b>{{ selectedCategoryName || '未选择' }}</b>
          </header>
          <div class="category-selector">
          <div class="auto-category-hint">
            <span class="hint-icon">i</span>
            <span>上传封面图之后自动获取分类</span>
            <span v-if="autoCategoryLoading" class="auto-category-spinner">检测中...</span>
          </div>
          <div v-if="autoCategoryMessage" :class="['auto-category-msg', autoCategoryMsgType]">
            {{ autoCategoryMessage }}
          </div>
          <div v-if="autoCategoryCandidates.length" class="auto-category-candidates">
            <span class="candidates-label">推荐分类：</span>
            <button
              v-for="(cat, idx) in autoCategoryCandidates"
              :key="cat.catId || idx"
              type="button"
              :class="['candidate-btn', { active: autoSelectedCatId === (cat.catId || cat.catName) }]"
              @click="applyAutoCategory(cat)"
            >
              {{ cat.catName || cat.catName }}
              <small v-if="cat.score">({{ (cat.score * 100).toFixed(1) }}%)</small>
            </button>
          </div>
          <div class="category-tools">
            <input v-model="categoryKeyword" class="category-search" placeholder="搜索分类，如 手机 / 图书 / 家居" />
            <button v-if="aiCategoryStatus.configured" type="button" class="category-ai-btn" :disabled="aiCategoryLoading || !form.title.trim()" @click="autoSelectCategory">{{ aiCategoryLoading ? 'AI选择中...' : 'AI自动选择' }}</button>
            <button v-if="categoryKeyword" type="button" class="category-clear" @click="categoryKeyword = ''">清空</button>
          </div>
          <p v-if="!aiCategoryStatus.configured" class="ai-unconfigured-tip">
            {{ aiCategoryStatus.message || '未配置通用模型，AI 自动选分类当前不可用。' }}
          </p>
          <button
            v-if="!aiCategoryStatus.configured"
            type="button"
            class="category-ai-btn category-ai-btn-blocked"
            :disabled="aiCategoryLoading || !form.title.trim()"
            @click="autoSelectCategory"
          >
            AI 自动选择
          </button>
          <div v-if="categoryKeyword" class="category-search-results">
            <div
              v-for="item in categorySearchResults"
              :key="item.pathIds.join('-')"
              class="category-result"
              @click="selectCategoryByPath(item)"
            >
              <strong>{{ item.name }}</strong>
              <span>{{ item.path }}</span>
            </div>
            <div v-if="!categorySearchResults.length" class="category-result muted">未找到匹配分类</div>
          </div>
          <div v-if="favoriteCategories.length" class="recent-categories favorite-categories">
            <span>收藏分类：</span>
            <button v-for="item in favoriteCategories" :key="item.path" type="button" @click="selectCategoryByPath(item)">{{ item.name }}</button>
          </div>
          <div v-if="recentCategories.length" class="recent-categories">
            <span>最近使用：</span>
            <button v-for="item in recentCategories" :key="item.path" type="button" @click="selectCategoryByPath(item)">{{ item.name }}</button>
            <button type="button" class="category-link" @click="clearRecentCategories">清除</button>
          </div>
          <div v-if="selectedCategoryPath" class="category-actions">
            <button type="button" @click="toggleFavoriteCategory">{{ isFavoriteCategory ? '取消收藏当前分类' : '收藏当前分类' }}</button>
          </div>
          <div class="cascader-levels">
            <div class="cascader-col">
              <div v-if="categoriesLoading" class="cascader-item muted">分类加载中...</div>
              <div v-else-if="!categories.length" class="cascader-item muted">暂无分类</div>
              <div
                v-for="cat in filteredCategories"
                :key="cat.id"
                :class="['cascader-item', { active: level1Id === cat.id }]"
                @click="selectLevel1(cat)"
              >
{{ cat.label || cat.title }}
</div>
            </div>
            <div v-if="level2List.length" class="cascader-col">
              <div
                v-for="cat in level2List"
                :key="cat.id"
                :class="['cascader-item', { active: level2Id === cat.id }]"
                @click="selectLevel2(cat)"
              >
{{ cat.label || cat.title }}
</div>
            </div>
            <div v-if="level3List.length" class="cascader-col">
              <div
                v-for="cat in level3List"
                :key="cat.id"
                :class="['cascader-item', { active: level3Id === cat.id }]"
                @click="selectLevel3(cat)"
              >
{{ cat.label || cat.title }}
</div>
            </div>
          </div>
          <p class="selected-category-line">
            已选分类：{{ selectedCategoryPath || '请选择分类' }}
            <span v-if="aiCategoryMessage" class="ai-category-tip">{{ aiCategoryMessage }}</span>
          </p>
        </div>
        </section>

        <section class="publish-panel">
          <header class="publish-panel-head">
            <div>
              <span>位置</span>
              <h3>商品位置</h3>
            </div>
            <b>{{ selectedPoi?.name || '未选择' }}</b>
          </header>
          <div class="location-search">
          <div class="location-input-wrap">
            <input
              v-model="locationKeyword"
              placeholder="搜索小区/学校/商圈/商场等"
              class="location-input"
              @input="onLocationInput"
              @focus="onLocationFocus"
              @blur="onLocationBlur"
            />
            <div v-if="locationKeyword && showPoiDropdown" class="poi-dropdown">
              <div
                v-for="poi in poiList"
                :key="poi.id"
                class="poi-item"
                @mousedown.prevent="selectPoi(poi)"
              >
                <div class="poi-name">{{ poi.name }}</div>
                <div class="poi-addr">{{ poi.address || poi.district || '' }}</div>
              </div>
              <div v-if="!poiList.length && locationKeyword" class="poi-empty" :class="{ 'poi-empty-error': poiError }">
                <span v-if="poiLoading">搜索中...</span>
                <span v-else>{{ poiError || '未找到相关位置' }}</span>
              </div>
            </div>
          </div>
          <div v-if="selectedPoi" class="selected-poi">
            <div class="poi-badge">
              <span class="poi-badge-name">{{ selectedPoi.name }}</span>
              <span class="poi-badge-addr">{{ selectedPoi.address || selectedPoi.district || '' }}</span>
              <button type="button" class="poi-badge-remove" aria-label="清除已选位置" @click="clearPoi">×</button>
            </div>
            <div class="poi-detail">
              <span>经度：{{ selectedPoi.lng }}</span>
              <span>纬度：{{ selectedPoi.lat }}</span>
              <span>区域：{{ selectedPoi.pname }}{{ selectedPoi.cityname }}{{ selectedPoi.adname }}</span>
            </div>
          </div>
        </div>
        </section>

        <section class="publish-commerce-grid">
          <div class="publish-panel">
            <header class="publish-panel-head">
              <div>
                <span>交易</span>
                <h3>价格与规格</h3>
              </div>
              <b>单规格</b>
            </header>
            <div class="publish-form-grid compact">
              <div class="publish-form-row">
                <label>售价（元）</label>
                <input v-model="form.price" type="number" step="0.01" min="0" placeholder="0.00">
              </div>
              <div class="publish-form-row">
                <label>库存</label>
                <input v-model="form.stock" type="number" placeholder="1">
              </div>
            </div>
            <div class="publish-option-line unavailable-option" title="当前发布接口尚未支持规格组合的完整提交与回读核验">
              <span>多规格 <em>当前不可用，仅支持单规格发布</em></span>
              <ToggleSwitch :on="false" />
            </div>
          </div>

          <div class="publish-panel">
            <header class="publish-panel-head">
              <div>
                <span>履约</span>
                <h3>发货设置</h3>
              </div>
              <b>包邮</b>
            </header>
            <div class="shipping-grid">
              <div class="shipping-item">
                <span>包邮</span>
                <ToggleSwitch :on="true" />
              </div>
              <div class="shipping-item unavailable-option" title="固定运费尚未完成平台发布与回读核验">
                <span>一口价 / 运费（当前不可用）</span>
                <ToggleSwitch :on="false" />
              </div>
              <div class="shipping-item unavailable-option" title="无需邮寄模式尚未完成平台发布与回读核验">
                <span>无需邮寄（当前不可用）</span>
                <ToggleSwitch :on="false" />
              </div>
              <div class="shipping-item">
                <span>支持自提</span>
                <ToggleSwitch :on="form.supportSelfPick" @click="form.supportSelfPick = !form.supportSelfPick" />
              </div>
            </div>
          </div>
        </section>
      </main>

      <aside class="publish-side">
        <section class="publish-panel publish-preview-panel">
          <header class="publish-panel-head">
            <div>
              <span>预览</span>
              <h3>商品卡片</h3>
            </div>
            <b>¥{{ displayPrice }}</b>
          </header>
          <div class="publish-preview-card">
            <div class="publish-preview-thumb">
              <img v-if="form.imageUrls.length > 0" :src="form.imageUrls[0]" alt="">
              <span v-else>暂无图片</span>
            </div>
            <div>
              <h4>{{ form.title || '商品标题' }}</h4>
              <strong>¥{{ displayPrice }}</strong>
              <p>{{ selectedPoi?.name || runtime.defaultAddress || '未选择位置' }}</p>
            </div>
          </div>
        </section>

        <section class="publish-panel">
          <header class="publish-panel-head">
            <div>
              <span>摘要</span>
              <h3>发布摘要</h3>
            </div>
            <b>{{ totalStock }} 件</b>
          </header>
          <div class="publish-summary-list">
            <div><span>闲鱼账号</span><b>{{ selectedAccount || '未选择' }}</b></div>
            <div><span>商品分类</span><b>{{ selectedCategoryPath || '未选择' }}</b></div>
            <div><span>商品位置</span><b>{{ selectedPoi?.name || '未选择' }}</b></div>
            <div><span>规格能力</span><b>单规格</b></div>
            <div><span>总库存</span><b>{{ totalStock }}件</b></div>
            <div><span>运费模式</span><b>包邮</b></div>
          </div>
        </section>

        <section class="publish-panel">
          <header class="publish-panel-head">
            <div>
              <span>核验</span>
              <h3>发布检查</h3>
            </div>
            <b>{{ checks.filter(item => item.ok).length }}/{{ checks.length }}</b>
          </header>
          <div class="publish-check-list">
            <div v-for="i in checks" :key="i.text" class="publish-check-row" :class="{ ok: i.ok }">
              <span><i></i>{{ i.text }}</span>
              <b>{{ i.ok ? '通过' : '待完善' }}</b>
            </div>
          </div>
        </section>
      </aside>
    </section>

    <div class="publish-bottom-actions">
      <AppButton @click="handleCancel">取消</AppButton>
      <AppButton type="primary" :loading="submitting" :disabled="publishSubmitDisabled" @click="submit">{{ publishSubmitLabel }}</AppButton>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import AppButton from '../components/AppButton.vue'
import ToggleSwitch from '../components/ToggleSwitch.vue'
import { getAccounts } from '../api/accounts.js'
import { publishItem, autoCategory } from '../api/items.js'
import { uploadImage, amapInputTips } from '../api/misc.js'
import { runtimeConfig } from '../api/system.js'
import { accountName } from '../utils/format.js'
import { recordsOf } from '../utils/apiData.js'
import { confirmAction } from '../utils/confirmAction.js'
import { getAiProviderStatus, suggestCategoryByAi } from '../api/aiProvider.js'
import { fetchCategories } from '../api/categories.js'
import { aiRewriteGoods } from '../api/workflow.js'
import {
  buildPublishIntentSummary,
  canSubmitPublishIntent,
  captureProductAsyncContext,
  isProductAsyncRequestCurrent,
  markPendingProductSync,
} from '../utils/productPublishState.js'

const emit = defineEmits(['navigate'])
const accounts = ref([])
const error = ref('')
const warning = ref('')
const success = ref('')
const submitting = ref(false)
const publishOutcome = ref(null)
const publishIntent = reactive({ idempotencyKey: '', payload: null })
const PUBLISH_INTENT_KEY = 'xianyu_publish_intent_v1'
const unsafePublishFailure = computed(() => {
  const outcome = publishOutcome.value
  return outcome?.status === 'failed' && outcome?.retrySafe !== true
})
const publishSubmitDisabled = computed(() => !canSubmitPublishIntent({
  accountsAvailable: accountsAvailable.value,
  submitting: submitting.value,
  hasIntent: Boolean(publishIntent.payload),
  outcome: publishOutcome.value,
}))
const publishSubmitLabel = computed(() => {
  if (publishOutcome.value?.status === 'remote_confirmed') return '仅修复系统状态'
  if (publishOutcome.value?.status === 'unknown') return '结果未知，禁止重试'
  if (publishOutcome.value?.status === 'in_progress') return '发布执行中'
  if (unsafePublishFailure.value) return '失败不可安全重试'
  if (publishOutcome.value?.status === 'failed' && publishOutcome.value?.retrySafe) return '使用原任务重试'
  return '立即发布'
})
const fileInput = ref(null)
const uploadingImages = ref(false)
let uploadRequestVersion = 0
const accountsAvailable = ref(null)
const runtime = reactive({ defaultCity: '', defaultAddress: '' })
const dragIndex = ref(-1)

// ---- 分类级联 ----
const categories = ref([])
const categoriesLoading = ref(false)
const level1Id = ref(null)
const level2Id = ref(null)
const level3Id = ref(null)
const level2List = ref([])
const level3List = ref([])
const categoryKeyword = ref('')
const recentCategories = ref([])
const favoriteCategories = ref([])
const selectedCategoryPath = ref('')
const selectedCategoryName = ref('')
const aiCategoryStatus = ref({ configured: false, message: '' })
const aiCategoryLoading = ref(false)
const aiCategoryMessage = ref('')

// ---- 自动分类（闲鱼接口） ----
const autoCategoryLoading = ref(false)
const autoCategoryMessage = ref('')
const autoCategoryMsgType = ref('info')
const autoCategoryCandidates = ref([])
const autoSelectedCatId = ref('')
const autoCategorySource = ref(null) // 'xianyu_auto' | 'local_category' | null
const userManuallySelectedCategory = ref(false) // 用户是否手动改过分类
let categoryRevision = 0
let aiCategoryRequestVersion = 0
let autoCategoryRequestVersion = 0

function productAsyncContext() {
  return captureProductAsyncContext({
    accountId: form.accountId,
    title: form.title,
    description: form.description,
    coverImageUrl: form.imageUrls[0],
    categoryRevision,
  })
}

function markManualCategorySelection() {
  categoryRevision += 1
  userManuallySelectedCategory.value = true
  aiCategoryRequestVersion += 1
  autoCategoryRequestVersion += 1
  aiCategoryLoading.value = false
  autoCategoryLoading.value = false
}

function selectLevel1(cat, { manual = true } = {}) {
  if (manual) markManualCategorySelection()
  level1Id.value = cat.id
  level2Id.value = null
  level3Id.value = null
  level2List.value = cat.children || []
  level3List.value = []
  selectedCategoryName.value = cat.label || cat.title
  selectedCategoryPath.value = cat.label || cat.title
  if (!level2List.value.length) rememberCategory({ name: selectedCategoryName.value, path: selectedCategoryPath.value, pathIds: [cat.id] })
}

function selectLevel2(cat, { manual = true } = {}) {
  if (manual) markManualCategorySelection()
  level2Id.value = cat.id
  level3Id.value = null
  level3List.value = cat.children || []
  const l1 = categories.value.find(c => c.id === level1Id.value)
  const path = (l1?.label || l1?.title) + ' ＞ ' + (cat.label || cat.title)
  selectedCategoryName.value = cat.label || cat.title
  selectedCategoryPath.value = path
  if (!level3List.value.length) rememberCategory({ name: selectedCategoryName.value, path, pathIds: [l1?.id, cat.id].filter(Boolean) })
}

function selectLevel3(cat, { manual = true } = {}) {
  if (manual) markManualCategorySelection()
  level3Id.value = cat.id
  const l1 = categories.value.find(c => c.id === level1Id.value)
  const l2 = level2List.value.find(c => c.id === level2Id.value)
  const path = (l1?.label || l1?.title) + ' ＞ ' + (l2?.label || l2?.title) + ' ＞ ' + (cat.label || cat.title)
  selectedCategoryName.value = cat.label || cat.title
  selectedCategoryPath.value = path
  rememberCategory({ name: selectedCategoryName.value, path, pathIds: [l1?.id, l2?.id, cat.id].filter(Boolean) })
}


const filteredCategories = computed(() => {
  if (!categoryKeyword.value.trim()) return categories.value
  const kw = categoryKeyword.value.trim().toLowerCase()
  return categories.value.filter(cat => String(cat.label || cat.title || '').toLowerCase().includes(kw) || (cat.children || []).some(child => String(child.label || child.title || '').toLowerCase().includes(kw)))
})

const isFavoriteCategory = computed(() => favoriteCategories.value.some(item => item.path === selectedCategoryPath.value))

const categorySearchResults = computed(() => {
  const kw = categoryKeyword.value.trim().toLowerCase()
  if (!kw) return []
  const res = []
  const walk = (nodes, parents = [], parentIds = []) => {
    for (const node of nodes || []) {
      const name = node.label || node.title || ''
      const pathParts = [...parents, name]
      const pathIds = [...parentIds, node.id]
      if (String(name).toLowerCase().includes(kw)) {
        res.push({ name, path: pathParts.join(' ＞ '), pathIds })
      }
      if (res.length < 20) walk(node.children || [], pathParts, pathIds)
      if (res.length >= 20) return
    }
  }
  walk(categories.value)
  return res.slice(0, 20)
})

function flatCategoryOptions(limit = 5000) {
  const res = []
  const walk = (nodes, parents = [], parentIds = []) => {
    for (const node of nodes || []) {
      if (res.length >= limit) return
      const name = node.label || node.title || ''
      const pathParts = [...parents, name]
      const pathIds = [...parentIds, node.id]
      const children = node.children || []
      if (!children.length) {
        res.push({ id: node.id, name, path: pathParts.join(' ＞ '), pathIds })
      } else {
        walk(children, pathParts, pathIds)
      }
    }
  }
  walk(categories.value)
  return res
}

function findCategoryOption(category) {
  if (!category) return null
  const options = flatCategoryOptions(5000)
  const id = String(category.id || category.categoryId || '')
  const path = String(category.path || category.categoryPath || '')
  const name = String(category.name || category.categoryName || '')
  return options.find(item =>
    (id && String(item.id) === id) ||
    (path && item.path === path) ||
    (name && (item.name === name || item.path.endsWith(name)))
  ) || null
}

async function loadAiCategoryStatus() {
  try {
    const res = await getAiProviderStatus()
    aiCategoryStatus.value = res?.data || { configured: false, message: '' }
  } catch {
    if (import.meta.env.DEV) console.warn('[loadAiCategoryStatus] failed')
    aiCategoryStatus.value = {
      configured: false,
      message: '未能读取 AI 模型配置状态，请稍后重试。'
    }
  }
}

function aiStatusMessage(defaultMessage = '未配置通用模型，请先前往系统设置中的“模型配置”完成配置。') {
  return aiCategoryStatus.value?.message || defaultMessage
}

async function autoSelectCategory() {
  if (aiCategoryLoading.value) return
  if (!aiCategoryStatus.value.configured) {
    error.value = aiStatusMessage('未配置通用模型，暂时无法使用 AI 自动选分类。')
    aiCategoryMessage.value = error.value
    return
  }
  if (!form.title.trim()) { error.value = '请先填写宝贝标题，AI才能判断分类'; return }
  const options = flatCategoryOptions(5000)
  if (!options.length) { error.value = '分类数据尚未加载完成'; return }
  const requestVersion = ++aiCategoryRequestVersion
  const requestContext = productAsyncContext()
  aiCategoryLoading.value = true
  aiCategoryMessage.value = ''
  error.value = ''
  try {
    const res = await suggestCategoryByAi({
      title: requestContext.title,
      description: requestContext.description,
      categories: options,
    })
    if (!isProductAsyncRequestCurrent({
      requestVersion,
      currentVersion: aiCategoryRequestVersion,
      snapshot: requestContext,
      current: productAsyncContext(),
      fields: ['title', 'description', 'categoryRevision'],
    })) return
    const data = res?.data || {}
    if (data.enabled === false || data.configured === false) {
      aiCategoryStatus.value = {
        configured: false,
        message: data.message || data.reason || aiStatusMessage()
      }
      error.value = aiCategoryStatus.value.message
      return
    }
    if (!data.matched) {
      error.value = data.error || data.message || 'AI未能匹配到合适分类，请手动选择'
      return
    }
    const matched = findCategoryOption(data.category) || data.category
    selectCategoryByPath(matched, { manual: false })
    aiCategoryMessage.value = data.reason ? `AI已选择：${data.reason}` : 'AI已自动选择分类'
  } catch (e) {
    if (requestVersion === aiCategoryRequestVersion) error.value = e.message || 'AI自动选择分类失败'
  } finally {
    if (requestVersion === aiCategoryRequestVersion) aiCategoryLoading.value = false
  }
}

// ---- 自动分类（上传封面图后触发） ----
async function triggerAutoCategory() {
  if (!form.accountId) {
    autoCategoryMessage.value = '请先选择闲鱼账号'
    autoCategoryMsgType.value = 'warn'
    return
  }
  if (!form.imageUrls.length) {
    return
  }
  // 如果用户已手动选择分类，不要覆盖
  if (userManuallySelectedCategory.value) {
    autoCategoryMessage.value = '已手动选择分类，重新上传封面图可再次自动识别'
    autoCategoryMsgType.value = 'info'
    return
  }
  const coverImageUrl = form.imageUrls[0]
  const requestAccountId = form.accountId
  const requestVersion = ++autoCategoryRequestVersion
  const requestContext = productAsyncContext()
  autoCategoryLoading.value = true
  autoCategoryMessage.value = '正在识别商品分类...'
  autoCategoryMsgType.value = 'info'
  autoCategoryCandidates.value = []
  autoSelectedCatId.value = ''
  try {
    const res = await autoCategory(requestAccountId, {
      coverImageUrl,
      title: requestContext.title || undefined,
      description: requestContext.description || undefined,
    })
    if (!isProductAsyncRequestCurrent({
      requestVersion,
      currentVersion: autoCategoryRequestVersion,
      snapshot: requestContext,
      current: productAsyncContext(),
      fields: ['accountId', 'title', 'description', 'coverImageUrl', 'categoryRevision'],
    })) return
    const data = res?.data || {}
    if (!data.success) {
      // 自动分类失败，如果是 cookie 问题提示重新登录
      if (data.fallbackReason === 'COOKIE_EXPIRED' || data.fallbackReason === 'COOKIE_MISSING_M_H5_TK') {
        autoCategoryMessage.value = '账号登录凭证已失效，请重新登录后再试'
        autoCategoryMsgType.value = 'error'
      } else if (data.fallbackReason && data.fallbackReason.includes('LOW_CONFIDENCE')) {
        autoCategoryMessage.value = '封面图自动识别置信度不足，已切换到备用分类'
        autoCategoryMsgType.value = 'warn'
        // 展示能检测到的候选
        if (data.candidates && data.candidates.length) {
          autoCategoryCandidates.value = data.candidates
        }
      } else {
        const reason = data.fallbackReason ? `（${data.fallbackReason}）` : ''
        autoCategoryMessage.value = `封面图自动识别失败，请手动选择分类${reason}`
        autoCategoryMsgType.value = 'warn'
        // 展示能检测到的候选
        if (data.candidates && data.candidates.length) {
          autoCategoryCandidates.value = data.candidates
        }
      }
      autoCategorySource.value = data.source || null
      return
    }
    // 自动分类成功
    autoCategorySource.value = 'xianyu_auto'
    const selected = data.selectedCategory
    const candidates = data.candidates || []
    autoCategoryCandidates.value = candidates
    if (selected) {
      // 尝试在本地分类树中找到匹配项
      const option = findCategoryOption(selected)
      if (option) {
        selectCategoryByPath(option, { manual: false })
        autoSelectedCatId.value = selected.catId || selected.catName || ''
        autoCategoryMessage.value = '已根据封面图自动识别分类'
        autoCategoryMsgType.value = 'success'
      } else if (candidates.length) {
        // 未匹配到本地分类树，展示候选分类让用户手动点选
        autoCategoryMessage.value = '已识别候选分类，请点击选择'
        autoCategoryMsgType.value = 'info'
        autoSelectedCatId.value = selected.catId || ''
      } else {
        autoCategoryMessage.value = '已根据封面图自动识别分类'
        autoCategoryMsgType.value = 'success'
      }
    } else {
      autoCategoryMessage.value = '已识别候选分类，请点击选择'
      autoCategoryMsgType.value = 'info'
    }
  } catch (e) {
    if (requestVersion === autoCategoryRequestVersion) {
      autoCategoryMessage.value = '自动分类请求失败：' + (e.message || '网络异常')
      autoCategoryMsgType.value = 'error'
      autoCategoryCandidates.value = []
      autoCategorySource.value = null
    }
  } finally {
    if (requestVersion === autoCategoryRequestVersion) {
      autoCategoryLoading.value = false
      // 后台刷新分类树，让新增的分类在前端级联选择器中可见
      refreshCategoriesInBackground()
    }
  }
}

async function refreshCategoriesInBackground() {
  try {
    const res = await fetchCategories()
    const newTree = res?.data?.cation || []
    if (newTree.length) {
      categories.value = newTree
    }
  } catch {
    if (import.meta.env.DEV) console.warn('[refreshCategoriesInBackground] failed')
  }
}

function applyAutoCategory(cat) {
  if (!cat) return
  markManualCategorySelection()
  // 用候选分类的名称匹配本地分类树
  const matchName = cat.catName || cat.name || ''
  if (matchName) {
    const options = flatCategoryOptions(5000)
    const matched = options.find(item =>
      item.name === matchName || item.path.endsWith(matchName)
    )
    if (matched) {
      selectCategoryByPath(matched, { manual: false })
      autoSelectedCatId.value = cat.catId || cat.catName || ''
      autoCategoryMessage.value = `已选择分类：${matchName}`
      autoCategoryMsgType.value = 'success'
      return
    }
  }
  // 未匹配到本地分类树时，直接设置分类名称
  selectedCategoryName.value = matchName
  selectedCategoryPath.value = matchName
  autoSelectedCatId.value = cat.catId || cat.catName || ''
  autoCategoryMessage.value = `已选择分类：${matchName}`
  autoCategoryMsgType.value = 'success'
}

function selectCategoryByPath(item, { manual = true } = {}) {
  const ids = item.pathIds || []
  const l1 = categories.value.find(c => String(c.id) === String(ids[0]))
  if (!l1) return
  if (manual) markManualCategorySelection()
  selectLevel1(l1, { manual: false })
  if (ids[1]) {
    const l2 = (l1.children || []).find(c => String(c.id) === String(ids[1]))
    if (l2) selectLevel2(l2, { manual: false })
    if (ids[2]) {
      const l3 = (l2?.children || []).find(c => String(c.id) === String(ids[2]))
      if (l3) selectLevel3(l3, { manual: false })
    }
  }
  categoryKeyword.value = ''
  rememberCategory(item)
}

function rememberCategory(item) {
  if (!item?.path) return
  const normalized = { name: item.name, path: item.path, pathIds: item.pathIds || [] }
  recentCategories.value = [normalized, ...recentCategories.value.filter(i => i.path !== normalized.path)].slice(0, 6)
  try { localStorage.setItem('xianyu_recent_categories', JSON.stringify(recentCategories.value)) } catch { /* Recent categories are optional. */ }
}

function loadRecentCategories() {
  try {
    const list = JSON.parse(localStorage.getItem('xianyu_recent_categories') || '[]')
    recentCategories.value = Array.isArray(list) ? list.slice(0, 6) : []
  } catch {
    recentCategories.value = []
  }
  try {
    const list = JSON.parse(localStorage.getItem('xianyu_favorite_categories') || '[]')
    favoriteCategories.value = Array.isArray(list) ? list.slice(0, 12) : []
  } catch {
    favoriteCategories.value = []
  }
}

function clearRecentCategories() {
  recentCategories.value = []
  try { localStorage.removeItem('xianyu_recent_categories') } catch { /* Storage may be unavailable. */ }
}

function toggleFavoriteCategory() {
  if (!selectedCategoryPath.value) return
  const item = { name: selectedCategoryName.value, path: selectedCategoryPath.value, pathIds: [level1Id.value, level2Id.value, level3Id.value].filter(Boolean) }
  if (isFavoriteCategory.value) {
    favoriteCategories.value = favoriteCategories.value.filter(i => i.path !== item.path)
  } else {
    favoriteCategories.value = [item, ...favoriteCategories.value.filter(i => i.path !== item.path)].slice(0, 12)
  }
  try { localStorage.setItem('xianyu_favorite_categories', JSON.stringify(favoriteCategories.value)) } catch { /* Favorites remain available for this session. */ }
}

// ---- 表单（清除草稿，初始为空） ----
const form = reactive({
  accountId: '',
  title: '',
  description: '',
  imageUrls: [],
  price: '',
  stock: '',
  supportSelfPick: false,
})

watch(() => form.accountId, (nextAccountId, previousAccountId) => {
  if (String(nextAccountId ?? '') === String(previousAccountId ?? '')) return
  const discardedUpload = uploadingImages.value
  uploadRequestVersion += 1
  autoCategoryRequestVersion += 1
  aiCategoryRequestVersion += 1
  uploadingImages.value = false
  autoCategoryLoading.value = false
  aiCategoryLoading.value = false
  if (discardedUpload && previousAccountId) {
    warning.value = '账号已切换，旧账号尚未完成的图片上传结果已忽略。'
  }
})

async function handleCancel() {
  const ok = await confirmAction({
    title: '确认离开？',
    description: '未保存的更改将丢失，确定要离开吗？',
    confirmText: '离开',
    dangerous: true
  })
  if (ok) emit('navigate', 'products')
}

// ---- POI 位置搜索 ----
const locationKeyword = ref('')
const poiList = ref([])
const poiLoading = ref(false)
const showPoiDropdown = ref(false)
const selectedPoi = ref(null)
const poiError = ref('')
let searchTimer = null
let inhibitPoiClear = false
// Each input owns one search version. A slow response for an older keyword
// must never replace (or hide) the dropdown for the keyword now on screen.
let poiSearchVersion = 0
// 搜索结果缓存（避免相同关键词重复请求，触发高德 QPS 限制）
const poiCache = new Map()
// 上次请求时间戳，用于请求节流（高德免费 API QPS 限制约 3 次/秒）
let lastPoiRequestTime = 0

// 将高德 API 错误码翻译成中文友好提示
function friendlyAmapError(error) {
  if (!error) return ''
  if (error.includes('CUQPS_HAS_EXCEEDED_THE_LIMIT')) {
    return '搜索过于频繁，请稍等 2 秒后重试'
  }
  if (error.includes('INVALID_USER_KEY')) {
    return '高德 API Key 无效，请检查系统设置中的配置'
  }
  if (error.includes('DAILY_QUERY_OVER_LIMIT')) {
    return '高德 API 日调用次数已超限，请明天重试或升级配额'
  }
  return error
}

function onLocationInput() {
  const searchVersion = ++poiSearchVersion
  // 用户重新输入时清除已选 POI
  if (inhibitPoiClear) { inhibitPoiClear = false; return }
  selectedPoi.value = null
  showPoiDropdown.value = true
  if (searchTimer) clearTimeout(searchTimer)
  if (!locationKeyword.value.trim()) {
    poiList.value = []
    poiError.value = ''
    poiLoading.value = false
    showPoiDropdown.value = false
    return
  }
  poiLoading.value = true
  poiError.value = ''
  // 短防抖让输入后立即出现“搜索中”提示，同时仍通过请求节流避免高德 QPS 限制。
  searchTimer = setTimeout(async () => {
    const kw = locationKeyword.value.trim()
    if (!kw || searchVersion !== poiSearchVersion) return

    // 命中缓存直接返回（缓存 30 秒）
    const cacheKey = kw + (runtime.defaultCity || '')
    const cached = poiCache.get(cacheKey)
    if (cached && Date.now() - cached.time < 30000) {
      if (searchVersion === poiSearchVersion) {
        poiList.value = cached.list
        poiError.value = ''
        poiLoading.value = false
        showPoiDropdown.value = true
      }
      return
    }

    // 请求节流：距上次请求不足 1 秒则再等
    const now = Date.now()
    const wait = now - lastPoiRequestTime < 1000 ? (1000 - (now - lastPoiRequestTime)) : 0
    if (wait > 0) {
      await new Promise(r => setTimeout(r, wait))
    }
    if (searchVersion !== poiSearchVersion || kw !== locationKeyword.value.trim()) return
    lastPoiRequestTime = Date.now()

    try {
      const params = { keywords: kw }
      // 如果配置了默认城市，则限定城市范围，提高搜索精度
      if (runtime.defaultCity) {
        params.city = runtime.defaultCity
      }
      const res = await amapInputTips(params)
      if (searchVersion !== poiSearchVersion || kw !== locationKeyword.value.trim()) return
      const data = res?.data
      // 兼容新旧响应格式：旧格式 data 为数组，新格式 data 为 { pois, error }
      poiList.value = Array.isArray(data) ? data : (data?.pois || [])
      const rawError = (!Array.isArray(data) && data?.error) ? data.error : ''
      poiError.value = friendlyAmapError(rawError)
      // 仅在成功获取到结果时缓存
      if (poiList.value.length > 0) {
        poiCache.set(cacheKey, { list: poiList.value, time: Date.now() })
      }
      showPoiDropdown.value = true
    } catch {
      if (searchVersion !== poiSearchVersion) return
      if (import.meta.env.DEV) console.warn('[poiSearch] failed')
      poiList.value = []
      poiError.value = '位置搜索请求失败，请检查网络或联系平台支持'
    } finally {
      if (searchVersion === poiSearchVersion) poiLoading.value = false
    }
  }, 250)
}

function onLocationFocus() {
  if (selectedPoi.value) {
    // 已选中 POI 时聚焦不清除
    return
  }
  if (locationKeyword.value.trim()) {
    showPoiDropdown.value = true
  }
}

function onLocationBlur() {
  // 延迟隐藏，让点击事件先触发
  setTimeout(() => { showPoiDropdown.value = false }, 200)
}

function selectPoi(poi) {
  // 解析 location
  let lng = '', lat = ''
  if (poi.location) {
    const parts = poi.location.split(',')
    lng = parts[0] || ''
    lat = parts[1] || ''
  }
  selectedPoi.value = {
    id: poi.id,
    name: poi.name,
    address: poi.address || '',
    district: poi.district || '',
    adcode: poi.adcode || '',
    lng,
    lat,
    location: poi.location || '',
    pname: poi.pname || '',
    cityname: poi.cityname || '',
    adname: poi.adname || '',
    typecode: poi.typecode || '',
  }
  locationKeyword.value = poi.name
  showPoiDropdown.value = false
  // 阻止 v-model 触发的 onLocationInput 清除 selectedPoi
  inhibitPoiClear = true
}

function clearPoi() {
  selectedPoi.value = null
  locationKeyword.value = ''
  poiList.value = []
}

// ---- 请求封装 ----
// 已改用 amapInputTips 统一请求，不再需要本地 request 封装

const selectedAccount = computed(() => accountName(accounts.value.find(a => String(a.id) === String(form.accountId)) || {}))
const displayPrice = computed(() => form.price || '0.00')
const totalStock = computed(() => Number(form.stock) || 0)
const confirmationPayload = computed(() => publishIntent.payload || {
  xianyuAccountId: Number(form.accountId),
  title: form.title,
  category: selectedCategoryName.value,
  price: form.price,
  stock: Number(form.stock) || 0,
})
function resolveIntentAccountName(accountId) {
  const account = accounts.value.find(item => String(item.id) === String(accountId))
  return account ? accountName(account) : ''
}
const persistedIntentSummary = computed(() => (
  publishIntent.payload
    ? buildPublishIntentSummary(publishIntent.payload, resolveIntentAccountName)
    : ''
))
const checks = computed(() => [
  { text: '已选择闲鱼账号', ok: !!form.accountId },
  { text: '标题已填写', ok: form.title.trim().length > 0 },
  { text: '商品描述已填写', ok: form.description.trim().length > 0 },
  { text: '已上传商品图片', ok: form.imageUrls.length > 0 },
  { text: '分类已选择', ok: !!selectedCategoryName.value },
  { text: '商品位置已确认', ok: !!selectedPoi.value },
  { text: '价格已填写', ok: Number(form.price) > 0 },
  { text: '库存数大于 0', ok: totalStock.value > 0 },
])

// 触发文件选择
function triggerUpload() {
  if (uploadingImages.value) {
    warning.value = '图片正在上传，请等待当前批次完成后再选择。'
    return
  }
  if (accountsAvailable.value !== true) {
    error.value = '账号列表暂不可用，无法安全上传商品图片。'
    return
  }
  if (!form.accountId) {
    error.value = '请先选择闲鱼账号，再上传商品图片。'
    return
  }
  fileInput.value?.click()
}

async function onFileSelect(e) {
  const input = e.target
  const files = input.files
  if (!files || files.length === 0) return
  if (uploadingImages.value) {
    input.value = ''
    return
  }
  const requestVersion = ++uploadRequestVersion
  const requestContext = productAsyncContext()
  const uploadAccountId = form.accountId
  const remaining = 10 - form.imageUrls.length
  const toUpload = Array.from(files).slice(0, remaining)
  const hadNoImages = form.imageUrls.length === 0
  const uploadedUrls = []
  let uploadError = ''
  uploadingImages.value = true
  warning.value = ''
  try {
    for (const file of toUpload) {
      try {
        const res = await uploadImage(uploadAccountId || 0, file)
        if (!isProductAsyncRequestCurrent({
          requestVersion,
          currentVersion: uploadRequestVersion,
          snapshot: requestContext,
          current: productAsyncContext(),
          fields: ['accountId'],
        })) return
        if (res.code === 200 && res.data?.url) {
          uploadedUrls.push(res.data.url)
        } else {
          uploadError = res.msg || '图片上传失败'
        }
      } catch (err) {
        if (requestVersion !== uploadRequestVersion) return
        uploadError = err.message || '图片上传失败'
      }
    }
    if (!isProductAsyncRequestCurrent({
      requestVersion,
      currentVersion: uploadRequestVersion,
      snapshot: requestContext,
      current: productAsyncContext(),
      fields: ['accountId'],
    })) return
    form.imageUrls.push(...uploadedUrls.slice(0, 10 - form.imageUrls.length))
    if (uploadError) error.value = uploadError
    uploadingImages.value = false
    // 上传完成后，如果是第一次上传图片（刚有了封面图），触发自动分类
    if (hadNoImages && uploadedUrls.length > 0) await triggerAutoCategory()
  } finally {
    input.value = ''
    if (requestVersion === uploadRequestVersion) uploadingImages.value = false
  }
}

function removeImage(idx) {
  form.imageUrls.splice(idx, 1)
}

function onDragStart(idx, e) {
  dragIndex.value = idx
  e.dataTransfer.effectAllowed = 'move'
}
function onDragOver(idx, e) {
  e.dataTransfer.dropEffect = 'move'
}
function onDrop(idx) {
  const from = dragIndex.value
  if (from === idx) return
  const item = form.imageUrls.splice(from, 1)[0]
  form.imageUrls.splice(idx, 0, item)
  dragIndex.value = -1
}

async function loadCategories() {
  if (categories.value.length || categoriesLoading.value) return
  categoriesLoading.value = true
  try {
    // 优先从静态 JSON 文件加载（零网络延迟）
    const module = await import('../assets/data/categories.json')
    categories.value = module.default?.cation || module.cation || []
    // 静默拉取最新分类树（含自动分类新增的分类）
    // 自动分类服务已将新分类写入 categories.json
    refreshCategoriesInBackground()
  } catch (e) {
    error.value = e?.message || '商品分类加载失败'
    categories.value = []
  } finally {
    categoriesLoading.value = false
  }
}

async function load() {
  restorePublishIntent()
  loadRecentCategories()
  await Promise.allSettled([loadCategories(), loadAiCategoryStatus()])
  const [accountResult, configResult] = await Promise.allSettled([
    loadAllAccounts(),
    runtimeConfig()
  ])
  if (accountResult.status === 'fulfilled') {
    accounts.value = accountResult.value
    accountsAvailable.value = true
    if (!form.accountId && accounts.value[0]) form.accountId = accounts.value[0].id
  } else {
    accounts.value = []
    accountsAvailable.value = false
    error.value = accountResult.reason?.message || '账号列表暂不可用，当前禁止发布。'
  }
  if (configResult.status === 'fulfilled') {
    const cfg = configResult.value?.data || {}
    runtime.defaultCity = cfg.map?.defaultCity || cfg.defaultCity || ''
    runtime.defaultAddress = cfg.map?.defaultAddress || cfg.defaultAddress || ''
  } else {
    warning.value = warning.value || '默认位置配置暂不可用，请手动选择并确认商品位置。'
  }
}

async function loadAllAccounts() {
  const result = []
  const pageSize = 200
  let current = 1
  let total
  let hasMore = true
  while (hasMore) {
    const response = await getAccounts({ current, size: pageSize })
    const pageRecords = recordsOf(response?.data)
    total = Number(response?.data?.total ?? pageRecords.length) || 0
    result.push(...pageRecords)
    hasMore = pageRecords.length === pageSize && result.length < total
    if (hasMore) current += 1
  }
  return result
}

const aiDescLoading = ref(false)
let aiDescriptionRequestVersion = 0
async function aiDesc() {
  if (aiDescLoading.value) return
  if (!form.title && !form.description) {
    error.value = '请先填写商品标题或基础描述'
    return
  }
  if (!aiCategoryStatus.value.configured) {
    error.value = aiStatusMessage('未配置通用模型，暂时无法使用 AI 生成描述。')
    return
  }
  const requestVersion = ++aiDescriptionRequestVersion
  const requestContext = productAsyncContext()
  aiDescLoading.value = true
  error.value = ''
  try {
    const res = await aiRewriteGoods({
      title: requestContext.title,
      description: requestContext.description
    })
    if (!isProductAsyncRequestCurrent({
      requestVersion,
      currentVersion: aiDescriptionRequestVersion,
      snapshot: requestContext,
      current: productAsyncContext(),
      fields: ['title', 'description'],
    })) {
      warning.value = 'AI 描述已生成，但您已继续编辑，因此未覆盖当前内容。'
      return
    }
    const data = res?.data || {}
    if (data.configured === false || data.ok === false) {
      error.value = data.message || aiStatusMessage('未配置通用模型，暂时无法使用 AI 生成描述。')
      return
    }
    form.description = data.content || data.description || (typeof data === 'string' ? data : '') || ''
  } catch (e) {
    if (requestVersion === aiDescriptionRequestVersion) error.value = e.message || 'AI 描述生成失败'
  } finally {
    if (requestVersion === aiDescriptionRequestVersion) aiDescLoading.value = false
  }
}
function insertPhrase() {
  form.description += (form.description ? '\n' : '') + '下单前请先确认库存，售出不退不换。'
}

function validate() {
  if (accountsAvailable.value !== true) {
    error.value = '账号列表状态未知，重新加载成功前禁止发布。'
    return false
  }
  const miss = checks.value.find(i => !i.ok)
  if (miss) { error.value = `"${miss.text}" 检查未通过，请完善后再提交`; return false }
  return true
}

function createPublishIntentKey() {
  if (typeof globalThis.crypto?.randomUUID === 'function') {
    return `publish-${globalThis.crypto.randomUUID()}`
  }
  return `publish-${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`
}

function savePublishIntent() {
  try {
    sessionStorage.setItem(PUBLISH_INTENT_KEY, JSON.stringify({
      idempotencyKey: publishIntent.idempotencyKey,
      payload: publishIntent.payload,
      outcome: publishOutcome.value,
    }))
  } catch { /* Session recovery is best-effort. */ }
}

function restorePublishIntent() {
  try {
    const saved = JSON.parse(sessionStorage.getItem(PUBLISH_INTENT_KEY) || 'null')
    if (saved?.idempotencyKey && saved?.payload) {
      const hasUnsupportedSku = Array.isArray(saved.payload.skus) && saved.payload.skus.length > 0
      const hasUnsupportedShipping = saved.payload.shippingMode && saved.payload.shippingMode !== 'free'
      if (hasUnsupportedSku || hasUnsupportedShipping || saved.payload.freeShipping === false) {
        clearPublishIntent()
        warning.value = '检测到旧版多规格或非包邮发布任务。当前无法安全恢复，请按单规格、包邮重新确认后提交。'
        return
      }
      publishIntent.idempotencyKey = String(saved.idempotencyKey)
      publishIntent.payload = saved.payload
      publishOutcome.value = saved.outcome || { status: 'failed', retrySafe: true, retryScope: 'resume' }
      if (publishOutcome.value.status === 'unknown') {
        warning.value = '检测到结果未知的发布任务。请先同步商品或到闲鱼 App 核对，当前禁止重试。'
      } else if (publishOutcome.value.status === 'remote_confirmed') {
        warning.value = '闲鱼平台已确认发布；继续操作只会修复系统商品状态。'
      } else {
        warning.value = '检测到未完成的发布任务。继续操作只会恢复该任务；系统会阻止重复发布。'
      }
    }
  } catch { /* Ignore invalid session state. */ }
}

function clearPublishIntent() {
  publishIntent.idempotencyKey = ''
  publishIntent.payload = null
  publishOutcome.value = null
  try { sessionStorage.removeItem(PUBLISH_INTENT_KEY) } catch { /* Optional storage. */ }
}

async function submit() {
  error.value = ''
  warning.value = ''
  success.value = ''
  if (!publishIntent.payload && !validate()) return
  const onlyRepairLocal = publishOutcome.value?.status === 'remote_confirmed'
  const confirmationSummary = buildPublishIntentSummary(confirmationPayload.value, resolveIntentAccountName)
  const ok = await confirmAction({
    title: onlyRepairLocal ? '确认仅修复系统商品状态？' : '确认立即发布到闲鱼？',
    description: onlyRepairLocal
      ? `平台已经确认发布。本次仅补全系统商品库，不会再次向闲鱼提交发布。\n\n${confirmationSummary}`
      : `${confirmationSummary}\n发布成功后会同步保存到系统商品库。`,
    dangerous: true
  })
  if (!ok) return
  submitting.value = true
  try {
    const finalPrice = form.price
    const finalStock = Number(form.stock) || 1

    // 构建位置数据
    const locationData = selectedPoi.value ? {
      prov: selectedPoi.value.pname || '',
      city: selectedPoi.value.cityname || '',
      area: selectedPoi.value.adname || '',
      divisionId: selectedPoi.value.adcode || '',
      gps: selectedPoi.value.location || '',
      poiId: selectedPoi.value.id || '',
      poiName: selectedPoi.value.name || '',
    } : {
      prov: '',
      city: '',
      area: '',
      divisionId: '',
      gps: '',
      poiId: '',
      poiName: runtime.defaultAddress || '',
    }

    // 先发布到闲鱼，成功后再保存到系统记录，避免发布失败时系统内却显示商品
    if (!publishIntent.payload) {
      publishIntent.idempotencyKey = createPublishIntentKey()
      publishIntent.payload = {
        xianyuAccountId: Number(form.accountId),
        title: form.title.slice(0, 30),
        description: form.description,
        imageUrls: [...form.imageUrls],
        price: finalPrice,
        stock: finalStock,
        category: selectedCategoryName.value,
        shippingMode: 'free',
        postFee: 0,
        freeShipping: true,
        supportSelfPick: form.supportSelfPick,
        location: locationData,
      }
      savePublishIntent()
    }
    const publishRes = await publishItem({
      ...publishIntent.payload,
      idempotencyKey: publishIntent.idempotencyKey,
    })

    if (publishRes.code === 200) {
      success.value = '发布成功，平台与系统商品库均已确认。'
      clearPublishIntent()
      // 浏览器中的待同步标记只是可选的后续 UX，失败不得改写已确认的平台发布结果。
      const pendingSync = markPendingProductSync()
      if (!pendingSync.stored) {
        warning.value = '发布已确认成功，但浏览器未能记录自动同步标记。请进入商品管理手动同步；该提示不影响发布结果。'
      }
      setTimeout(() => emit('navigate', 'products'), 1000)
    } else {
      error.value = publishRes.msg || '发布到闲鱼失败'
    }
  } catch (e) {
    const state = String(e?.data?.status || 'unknown')
    publishOutcome.value = {
      status: state,
      retrySafe: e?.data?.retrySafe === true,
      retryScope: e?.data?.retryScope || null,
    }
    savePublishIntent()
    if (state === 'remote_confirmed') {
      warning.value = '闲鱼平台已确认发布，但系统商品库尚未完成。可点击“仅修复系统状态”，系统绝不会重复发布。'
    } else if (state === 'unknown') {
      error.value = '发布结果未知。请先同步商品或到闲鱼 App 核对；为避免重复发布，当前禁止重试。'
    } else if (state === 'in_progress') {
      warning.value = '同一发布任务正在执行，请勿重复提交。'
    } else if (state === 'failed' && publishOutcome.value.retrySafe !== true) {
      error.value = `${e.message || '发布失败'}。系统未确认可安全重试，当前任务已锁定。`
    } else {
      error.value = e.message || '发布失败'
    }
  } finally {
    submitting.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.publish-console {
  display: grid;
  gap: 18px;
  min-width: 0;
}

.publish-notices {
  display: grid;
  gap: 10px;
}

.publish-command-center {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 330px;
  gap: 18px;
  padding: 22px;
  border: 1px solid #dbe3ef;
  border-radius: 8px;
  background:
    linear-gradient(135deg, rgba(15, 118, 110, .08), rgba(37, 99, 235, .06) 44%, rgba(245, 158, 11, .08)),
    #ffffff;
  box-shadow: 0 16px 38px rgba(15, 23, 42, .07);
}

.publish-command-main {
  min-width: 0;
}

.publish-command-kicker,
.publish-command-panel-head,
.publish-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.publish-command-kicker {
  justify-content: flex-start;
}

.publish-command-kicker span,
.publish-command-panel-head span,
.publish-panel-head span {
  color: #0f766e;
  font-size: 12px;
  font-weight: 750;
}

.publish-command-kicker b,
.publish-command-panel-head strong,
.publish-panel-head b {
  color: #475569;
  font-size: 12px;
  font-weight: 700;
}

.publish-command-main h2 {
  margin: 12px 0 6px;
  color: #0f172a;
  font-size: 26px;
  font-weight: 780;
  line-height: 1.2;
}

.publish-command-main p {
  max-width: 780px;
  margin: 0;
  color: #475569;
  font-size: 14px;
  line-height: 1.8;
}

.publish-command-steps {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}

.publish-command-steps span {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 11px;
  border: 1px solid #dbeafe;
  border-radius: 8px;
  background: rgba(255, 255, 255, .82);
  color: #2563eb;
  font-size: 12px;
  font-weight: 750;
}

.publish-command-panel {
  display: grid;
  align-content: start;
  gap: 14px;
  padding: 16px;
  border: 1px solid rgba(148, 163, 184, .32);
  border-radius: 8px;
  background: rgba(255, 255, 255, .78);
}

.publish-command-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.publish-workbench {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 16px;
  align-items: start;
}

.publish-main {
  display: grid;
  gap: 16px;
  min-width: 0;
}

.publish-panel {
  min-width: 0;
  padding: 16px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 10px 26px rgba(15, 23, 42, .05);
}

.publish-panel-head {
  align-items: flex-start;
  margin-bottom: 14px;
}

.publish-panel-head h3 {
  margin: 4px 0 0;
  color: #0f172a;
  font-size: 17px;
  font-weight: 760;
  line-height: 1.25;
}

.publish-panel-desc {
  margin: -4px 0 14px;
  color: #64748b;
  font-size: 13px;
  line-height: 1.6;
}

.publish-form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.publish-form-grid.compact {
  gap: 12px;
}

.publish-form-row {
  display: grid;
  gap: 7px;
  min-width: 0;
}

.publish-form-row-wide {
  grid-column: 1 / -1;
}

.publish-form-row label {
  color: #334155;
  font-size: 13px;
  font-weight: 700;
}

.publish-form-row input,
.publish-form-row textarea,
.publish-form-row select {
  width: 100%;
  min-width: 0;
  border: 1px solid #dbe3ef;
  border-radius: 8px;
  background: #ffffff;
  color: #0f172a;
  font-size: 14px;
  box-sizing: border-box;
}

.publish-form-row input,
.publish-form-row select {
  height: 38px;
  padding: 0 12px;
}

.publish-form-row textarea {
  resize: vertical;
  padding: 10px 12px;
  line-height: 1.6;
}

.publish-form-row input:focus,
.publish-form-row textarea:focus,
.publish-form-row select:focus {
  border-color: #0f766e;
  outline: none;
  box-shadow: 0 0 0 3px rgba(15, 118, 110, .12);
}

.publish-media-panel .image-strip {
  margin-top: 0;
}

.publish-commerce-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.publish-side {
  position: sticky;
  top: 16px;
  display: grid;
  gap: 16px;
  min-width: 0;
}

.publish-preview-card {
  display: grid;
  grid-template-columns: 126px minmax(0, 1fr);
  gap: 12px;
  align-items: center;
}

.publish-preview-thumb {
  width: 126px;
  height: 96px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f8fafc;
  overflow: hidden;
}

.publish-preview-thumb img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
}

.publish-preview-thumb span {
  width: 100%;
  height: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  font-size: 12px;
}

.publish-preview-card h4 {
  margin: 0 0 8px;
  color: #0f172a;
  font-size: 15px;
  font-weight: 760;
  line-height: 1.35;
}

.publish-preview-card strong {
  color: #dc2626;
  font-size: 22px;
  font-weight: 800;
}

.publish-preview-card p {
  margin: 8px 0 0;
  color: #64748b;
  font-size: 12px;
}

.publish-summary-list,
.publish-check-list {
  display: grid;
  gap: 9px;
}

.publish-summary-list div,
.publish-check-row,
.publish-option-line {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  padding: 11px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f8fafc;
}

.publish-summary-list span,
.publish-check-row span,
.publish-option-line span {
  color: #64748b;
  font-size: 12px;
  line-height: 1.5;
}

.publish-summary-list b,
.publish-check-row b,
.publish-option-line b {
  color: #0f172a;
  font-size: 12px;
  text-align: right;
  word-break: break-word;
}

.publish-check-row span {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.publish-check-row i {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #f59e0b;
}

.publish-check-row.ok i {
  background: #16a34a;
}

.publish-check-row.ok b {
  color: #047857;
}

.publish-check-row:not(.ok) b {
  color: #b45309;
}

.publish-bottom-actions {
  position: sticky;
  bottom: 0;
  z-index: 10;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 12px 0 0;
  background: linear-gradient(180deg, rgba(248, 250, 252, 0), #f8fafc 36%);
}

.unavailable-option {
  opacity: 0.72;
  cursor: not-allowed;
}

.unavailable-option em {
  margin-left: 8px;
  color: #a05b00;
  font-size: 12px;
  font-style: normal;
}

.field-error {
  color: #b42318;
  font-size: 12px;
}

.img-card {
  position: relative;
  width: 100px;
  height: 100px;
  border: 2px solid #e8e8e8;
  border-radius: 12px;
  overflow: hidden;
  flex-shrink: 0;
  cursor: grab;
  transition: border-color 0.2s;
}
.img-card:hover {
  border-color: var(--primary, #0f766e);
}
.img-card.add-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #FFFFFF;
  border-style: dashed;
  cursor: pointer;
  color: inherit;
  font: inherit;
}
.img-card.add-card:hover:not(:disabled) {
  border-color: var(--primary, #0f766e);
  background: #f0f5ff;
}
.img-card.add-card:disabled { cursor: wait; opacity: .72; }
.img-card.add-card:focus-visible,
.img-remove:focus-visible { outline: 3px solid rgba(24, 160, 88,.35); outline-offset: 2px; }
.img-card img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
}
.img-add-mark {
  color: #94a3b8;
  font-size: 28px;
  line-height: 1;
}
.img-add-text {
  margin-top: 4px;
  color: #64748b;
  font-size: 12px;
}
.img-remove {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 20px;
  height: 20px;
  background: rgba(0,0,0,0.5);
  border: 0;
  padding: 0;
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  cursor: pointer;
  z-index: 2;
}
.img-remove:hover:not(:disabled) {
  background: rgba(255,0,0,0.7);
}
.img-remove:disabled { cursor: wait; opacity: .7; }
.image-strip {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.publish-file-input {
  display: none;
}
/* ---- 分类级联选择器 ---- */
.category-selector {
  min-height: 60px;
}
.category-tools { display: flex; gap: 8px; margin-bottom: 10px; }
.category-search { flex: 1; padding: 10px 12px; border: 1px solid #e5e7eb; border-radius: 10px; outline: none; }
.category-search:focus { border-color: var(--primary, #0f766e); }
.category-clear { border: 1px solid #efe1db; background: #fff; border-radius: 10px; padding: 0 12px; cursor: pointer; }
.category-ai-btn { border: 1px solid #99f6e4; background: #F6F6F6; color: #0f766e; border-radius: 10px; padding: 0 12px; cursor: pointer; font-weight: 700; }
.category-ai-btn-blocked { margin-bottom: 10px; }
.category-ai-btn:disabled { cursor: not-allowed; opacity: .55; }
.ai-unconfigured-tip { margin: 8px 0 0; color: #b45309; font-size: 12px; line-height: 1.6; }
.ai-category-tip { margin-left: 10px; color: #16bf78; font-weight: 700; }
.category-search-results { display: grid; gap: 6px; max-height: 220px; overflow: auto; margin-bottom: 10px; padding: 8px; border: 1px solid #e8edf5; border-radius: 12px; background: #FFFFFF; }
.category-result { display: grid; gap: 2px; padding: 8px 10px; border-radius: 9px; cursor: pointer; }
.category-result:hover { background: #eef5ff; }
.category-result strong { color: #111827; font-size: 13px; }
.category-result span { color: #64748b; font-size: 12px; }
.recent-categories { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 10px; color: #64748b; font-size: 12px; }
.recent-categories button { border: 1px solid #dbeafe; background: #eff6ff; color: #0f766e; border-radius: 999px; padding: 5px 10px; cursor: pointer; }
.favorite-categories span { color: #92400e; }
.favorite-categories button { border-color: #fed7aa; background: #fff7ed; color: #0f766e; }
.category-actions { margin-bottom: 10px; }
.category-actions button, .category-link { border: 1px solid #efe1db; background: #fff; border-radius: 999px; padding: 5px 10px; cursor: pointer; font-size: 12px; color: #0f766e; }
.cascader-levels {
  display: flex;
  gap: 8px;
  border: 1px solid #e8e8e8;
  border-radius: 10px;
  overflow: hidden;
}
.cascader-col {
  flex: 1;
  min-width: 120px;
  max-height: 220px;
  overflow-y: auto;
  border-right: 1px solid #e8e8e8;
  background: #fafafa;
}
.cascader-col:last-child {
  border-right: none;
}
.cascader-item {
  padding: 8px 12px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.cascader-item:hover {
  background: #e6f0ff;
}
.cascader-item.active {
  background: var(--primary, #0f766e);
  color: #fff;
  font-weight: 500;
}
/* ---- 发货设置 ---- */
.shipping-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.shipping-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}
.shipping-item:not(:last-child) {
  border-bottom: 1px solid #f0f0f0;
}
/* ---- 位置搜索 ---- */
.location-search {
  position: relative;
}
.location-input-wrap {
  position: relative;
}
.location-input {
  width: 100%;
  padding: 10px 14px;
  border: 2px solid #e8e8e8;
  border-radius: 10px;
  font-size: 14px;
  outline: none;
  box-sizing: border-box;
  transition: border-color 0.2s;
}
.location-input:focus {
  border-color: var(--primary, #0f766e);
}
.poi-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 10px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
  max-height: 260px;
  overflow-y: auto;
  z-index: 100;
  margin-top: 4px;
}
.poi-item {
  padding: 10px 14px;
  cursor: pointer;
  border-bottom: 1px solid #f5f5f5;
  transition: background 0.15s;
}
.poi-item:last-child {
  border-bottom: none;
}
.poi-item:hover {
  background: #f0f5ff;
}
.poi-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}
.poi-addr {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}
.poi-empty {
  padding: 20px 14px;
  text-align: center;
  color: #999;
  font-size: 13px;
}
.poi-empty-error {
  color: #dc2626;
}
.selected-poi {
  margin-top: 10px;
}
.poi-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: #e6f0ff;
  border: 1px solid #99f6e4;
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 13px;
}
.poi-badge-name {
  font-weight: 500;
  color: var(--primary, #0f766e);
}
.poi-badge-addr {
  color: #666;
  font-size: 12px;
}
.poi-badge-remove {
  cursor: pointer;
  color: #999;
  font-size: 16px;
  line-height: 1;
  margin-left: 4px;
  padding: 0;
  border: 0;
  background: transparent;
}
.poi-badge-remove:hover {
  color: #ef4444;
}
.poi-detail {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  margin-top: 6px;
  font-size: 12px;
  color: #888;
}
.char-count {
  font-size: 12px;
  color: #999;
  margin-left: 8px;
  white-space: nowrap;
}

/* ---- 自动分类 ---- */
.auto-category-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
  padding: 8px 12px;
  background: #f0f7ff;
  border: 1px solid #ffe1d4;
  border-radius: 10px;
  color: #0f766e;
  font-size: 13px;
}
.auto-category-hint .hint-icon {
  font-size: 16px;
}
.auto-category-spinner {
  margin-left: auto;
  color: #0f766e;
  font-weight: 700;
  animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
.auto-category-msg {
  margin-bottom: 10px;
  padding: 8px 12px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
}
.auto-category-msg.success {
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  color: #059669;
}
.auto-category-msg.warn {
  background: #fffbeb;
  border: 1px solid #fde68a;
  color: #b45309;
}
.auto-category-msg.error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
}
.auto-category-msg.info {
  background: #eff6ff;
  border: 1px solid #99f6e4;
  color: #0f766e;
}
.auto-category-candidates {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 10px;
  padding: 8px 12px;
  border: 1px solid #e4eaf2;
  border-radius: 10px;
  background: #fafcff;
}
.candidates-label {
  font-size: 12px;
  color: #64748b;
  font-weight: 600;
  white-space: nowrap;
}
.candidate-btn {
  border: 1px solid #dbeafe;
  background: #eff6ff;
  color: #0f766e;
  border-radius: 999px;
  padding: 5px 12px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.15s;
}
.candidate-btn:hover {
  background: #dbeafe;
  border-color: #5eead4;
}
.candidate-btn.active {
  background: #0f766e;
  border-color: #0f766e;
  color: #fff;
}
.candidate-btn small {
  font-weight: 400;
  opacity: 0.8;
}

.cascader-item.active,
.candidate-btn.active {
  background: #2563eb;
  border-color: #2563eb;
  color: #fff;
}

/* === 移动端适配 (max-width: 900px) === */
@media (max-width: 900px) {
  .publish-console {
    gap: 12px;
  }

  .publish-command-center,
  .publish-workbench,
  .publish-form-grid,
  .publish-commerce-grid,
  .publish-command-actions,
  .publish-preview-card {
    grid-template-columns: minmax(0, 1fr);
  }

  .publish-command-center {
    padding: 16px;
  }

  .publish-side {
    position: static;
  }

  .publish-panel {
    padding: 14px;
  }

  /* 图片上传卡片：移动端缩小尺寸，更多列数 */
  .img-card {
    width: 78px;
    height: 78px;
    border-radius: 10px;
  }
  .image-strip {
    gap: 8px;
  }
  /* 分类级联选择器：移动端纵向堆叠三列，避免横向挤压 */
  .cascader-levels {
    flex-direction: column;
    gap: 6px;
    border-radius: 10px;
  }
  .cascader-col {
    min-width: 0;
    width: 100%;
    max-height: 180px;
    border-right: none;
    border-bottom: 1px solid #e8e8e8;
  }
  .cascader-col:last-child {
    border-bottom: none;
  }
  .cascader-item {
    padding: 8px 10px;
    font-size: 12px;
  }
  /* 分类工具栏允许换行 */
  .category-tools {
    flex-wrap: wrap;
    gap: 6px;
  }
  .category-search {
    flex: 1 1 100%;
    padding: 8px 10px;
  }
  .category-ai-btn,
  .category-clear {
    padding: 6px 10px;
    font-size: 12px;
  }
  .category-search-results {
    max-height: 180px;
    padding: 6px;
  }
  .recent-categories {
    gap: 6px;
  }
  .recent-categories button {
    padding: 4px 8px;
    font-size: 11px;
  }
  /* 位置搜索输入框 */
  .location-input {
    padding: 8px 12px;
    font-size: 13px;
  }
  .poi-dropdown {
    max-height: 220px;
  }
  .poi-item {
    padding: 8px 12px;
  }
  .poi-name {
    font-size: 13px;
  }
  .poi-addr {
    font-size: 11px;
  }
  .poi-detail {
    flex-direction: column;
    gap: 4px;
    font-size: 11px;
  }
  .poi-badge {
    flex-wrap: wrap;
    padding: 6px 10px;
    font-size: 12px;
  }
  /* 自动分类提示与候选 */
  .auto-category-hint {
    flex-wrap: wrap;
    padding: 6px 10px;
    font-size: 12px;
  }
  .auto-category-candidates {
    flex-wrap: wrap;
    gap: 6px;
    padding: 6px 10px;
  }
  .candidate-btn {
    padding: 4px 10px;
    font-size: 11px;
  }
  /* 发货设置 */
  .shipping-grid {
    gap: 8px;
  }
  .shipping-item {
    padding: 6px 0;
  }
  /* SKU 表格横向滚动 */
  .sku-table,
  :deep(.base-table) {
    display: block;
    overflow-x: auto;
    white-space: nowrap;
    -webkit-overflow-scrolling: touch;
  }
  /* 字符计数 */
  .char-count {
    font-size: 11px;
  }
}
</style>
