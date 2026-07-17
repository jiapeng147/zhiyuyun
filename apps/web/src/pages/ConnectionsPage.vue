<template>
  <div class="connections-console">
    <div class="connections-notices">
      <div v-if="error" class="global-notice error">{{ error }}</div>
      <div v-if="notice" class="global-notice success">{{ notice }}</div>
    </div>

    <section class="connections-command-center">
      <div class="connections-command-main">
        <div class="connections-command-kicker">
          <span>连接中心</span>
          <b>{{ dataAvailable === true ? '状态已同步' : '状态待确认' }}</b>
        </div>
        <h2>账号连接运维台</h2>
        <p>统一监控闲鱼账号登录凭证、消息通道和实时连接状态，异常账号可从右侧详情完成刷新、检查和断开处理。</p>
        <div class="connections-command-meta">
          <span>{{ loading ? '正在刷新连接' : '连接刷新就绪' }}</span>
          <span>当前页 {{ rows.length }} 个账号</span>
          <span>{{ selected ? `已选 ${selected.name}` : '未选择账号' }}</span>
        </div>
      </div>
      <div class="connections-command-panel">
        <div class="connections-command-panel-head">
          <span>批量操作</span>
          <strong>{{ filteredRows.length }} 个可见账号</strong>
        </div>
        <div class="connections-command-buttons">
          <button class="connections-action-btn" type="button" :disabled="loading" @click="load">
            {{ loading ? '刷新中...' : '刷新连接' }}
          </button>
          <button class="connections-action-btn primary" type="button" @click="batchStart">批量启动</button>
          <button class="connections-action-btn warn" type="button" @click="batchStop">批量断开</button>
        </div>
      </div>
    </section>

    <section class="connections-metric-rail">
      <article
        v-for="item in connectionStatCards"
        :key="item.key"
        class="connections-metric-card"
        :class="item.tone"
      >
        <span class="connections-metric-icon">{{ item.symbol }}</span>
        <div>
          <p>{{ item.title }}</p>
          <strong>{{ item.value }}</strong>
          <small>{{ item.change }}</small>
        </div>
      </article>
    </section>

    <section class="connections-workbench">
      <main class="connections-main">
        <section class="connections-panel connections-list-panel">
          <header class="connections-panel-head">
            <div>
              <span>连接列表</span>
              <h3>账号连接队列</h3>
            </div>
            <b>{{ dataAvailable === true ? `共 ${total} 个` : '列表不可用' }}</b>
          </header>
          <div class="connections-filter-bar">
            <select v-model="statusFilter" class="input connections-filter-select">
              <option value="all">全部状态</option>
              <option value="online">仅在线</option>
              <option value="offline">仅离线</option>
              <option value="unknown">状态未知</option>
              <option value="warning">登录/验证异常</option>
            </select>
            <input v-model="keyword" class="input connections-search-input" placeholder="搜索账号昵称/用户名">
            <AppButton :disabled="loading" @click="load">{{ loading ? '刷新中...' : '刷新' }}</AppButton>
          </div>
          <EmptyState v-if="dataAvailable === false" icon="!" title="连接列表暂不可用" description="当前无法确认账号与连接状态，不会把失败显示为离线。">
            <template #actions><AppButton @click="load">重新加载</AppButton></template>
          </EmptyState>
          <BaseTable v-else :columns="cols" :rows="filteredRows">
            <template #info="{row}">
              <div class="connection-account-cell">
                <img v-if="row.avatar" :src="row.avatar" class="connection-avatar small" alt="">
                <div v-else class="connection-avatar small"></div>
                <div>
                  <strong>{{ row.name }}</strong>
                  <em>{{ row.user }}</em>
                </div>
              </div>
            </template>
            <template #cookie="{row}">
              <Badge :type="row.authState === true ? 'green' : (row.authState === false ? 'red' : 'gray')">{{ row.cookie }}</Badge>
            </template>
            <template #ws="{row}">
              <div class="connection-state-cell">
                <Badge :type="row.connected === true ? 'green' : (row.connected === false ? 'red' : 'orange')">{{ row.ws }}</Badge>
                <p v-if="row.retrying" class="retrying">第 {{ row.retryAttempt }}/{{ row.retryMax }} 次尝试</p>
                <p v-else-if="row.refreshError" class="danger">{{ row.refreshError }}</p>
                <p v-else-if="row.phase || row.lastError">{{ row.lastError || row.phase }}</p>
              </div>
            </template>
            <template #latency="{row}">
              <b class="latency-text" :class="{ online: row.connected === true, offline: row.connected === false, unknown: row.connected == null }">{{ row.latency }}</b>
            </template>
            <template #op="{row}">
              <div class="connections-row-actions">
                <button class="link" :disabled="isBusy(row.id) || row.isRefreshing || row.connected == null || row.operationPending" @click="toggle(row)">{{ isBusy(row.id) ? (row.retrying ? '确认中...' : '处理中...') : (row.operationPending ? '启动中' : (row.connected === true ? '断开' : (row.connected === false ? '启动' : '状态未知'))) }}</button>
                <button class="link" :disabled="isBusy(row.id) || row.isRefreshing" @click="refresh(row)"><span :class="{ spinning: row.isRefreshing }">↻</span></button>
                <button class="link" @click="select(row)">详情</button>
              </div>
            </template>
          </BaseTable>
          <Pagination v-if="dataAvailable === true" :total="total" :current="current" :page-size="pageSize" @page-change="goPage" />
        </section>

        <div class="connections-secondary-grid">
          <section class="connections-panel">
            <header class="connections-panel-head compact">
              <div>
                <span>操作流水</span>
                <h3>本次操作记录</h3>
              </div>
              <b>{{ logs.length }} 条</b>
            </header>
            <EmptyState v-if="logs.length===0" icon="·" title="暂无本次操作记录" description="本页执行的连接、断开、重连操作会显示在这里。" />
            <div v-else class="connections-event-list">
              <div v-for="l in logs" :key="l.text+l.time" class="connections-event-row">
                <span>{{ l.text }}</span>
                <time>{{ l.time }}</time>
              </div>
            </div>
          </section>

          <section class="connections-panel">
            <header class="connections-panel-head compact">
              <div>
                <span>风险告警</span>
                <h3>异常告警列表</h3>
              </div>
              <b>{{ alerts.length }} 条</b>
            </header>
            <EmptyState v-if="dataAvailable === false" icon="!" title="告警状态不可用" description="账号列表加载失败，当前无法确认是否有连接或登录凭证异常。" />
            <EmptyState v-else-if="alerts.length===0" icon="✓" title="暂无已确认异常" description="当前已加载并确认的账号中没有发现连接或登录凭证异常。" />
            <div v-else class="connections-alert-list">
              <div v-for="e in alerts" :key="e.id" class="connections-alert-row">
                <span>{{ e.text }}</span>
                <AppButton @click="handleAlert(e)">查看</AppButton>
              </div>
            </div>
          </section>
        </div>
      </main>

      <aside class="connection-detail-panel">
        <header class="connections-panel-head detail-head">
          <div>
            <span>账号详情</span>
            <h3>连接诊断</h3>
          </div>
          <button class="link" type="button" @click="selected = null">关闭</button>
        </header>
        <template v-if="selected">
          <div class="connection-detail-identity">
            <img v-if="selected.avatar" :src="selected.avatar" class="connection-avatar" alt="">
            <div v-else class="connection-avatar"></div>
            <div>
              <strong>{{ selected.name }} <Badge type="blue">账号</Badge></strong>
              <p>{{ selected.user }}</p>
            </div>
            <b :class="{ online: selected.connected === true, offline: selected.connected === false }">{{ selected.ws }}</b>
          </div>

          <section class="connection-status-summary">
            <span>实时状态</span>
            <p>{{ selectedStatusSummary }}</p>
          </section>

          <section class="connection-health-list">
            <div>
              <i :class="{ online: selected.connected === true, offline: selected.connected === false }"></i>
              <span>实时连接</span>
              <b>{{ selected.ws }}</b>
            </div>
            <div>
              <i :class="{ online: selected.connected === true }"></i>
              <span>消息通道</span>
              <b>{{ selected.heartbeat }}</b>
            </div>
            <div>
              <i :class="{ online: selected.authState === true, offline: selected.authState === false }"></i>
              <span>登录凭证</span>
              <b>{{ selected.cookie }}</b>
            </div>
            <div>
              <i :class="{ offline: selected.lastError }"></i>
              <span>最近状态</span>
              <b>{{ selected.lastError || selected.status || selected.phase || '-' }}</b>
            </div>
          </section>

          <section class="connection-detail-block">
            <header>连接详情</header>
            <div class="connection-info-row"><span>账号编号</span><b>{{ selected.id }}</b></div>
            <div class="connection-info-row"><span>登录凭证状态</span><b>{{ selected.cookie }}</b></div>
            <div class="connection-info-row"><span>连接进度</span><b>{{ selected.phase || '-' }}</b></div>
            <div class="connection-info-row"><span>最近提示</span><b v-if="selected.refreshError" class="danger">{{ selected.refreshError }}</b><b v-else>{{ selected.lastError || '-' }}</b></div>
            <div class="connection-info-row"><span>连接凭证状态</span><b>{{ selected.wsTokenStatus || '-' }}</b></div>
            <div class="connection-info-row"><span>最近消息</span><b>{{ selected.last }}</b></div>
            <div v-if="selected.refreshError" class="connection-info-row"><span>操作</span><AppButton size="small" @click="refresh(selected)">重新刷新状态</AppButton></div>
          </section>

          <div class="connection-detail-actions">
            <AppButton type="primary" :disabled="isBusy(selected.id) || selected.connected == null || selected.operationPending" @click="toggle(selected)">{{ selected.operationPending ? '启动中' : '启动/断开' }}</AppButton>
            <AppButton type="danger" :disabled="isBusy(selected.id) || selected.connected !== true" @click="stop(selected)">断开连接</AppButton>
            <AppButton :disabled="isBusy(selected.id)" @click="refreshCookieAction(selected)">刷新登录凭证</AppButton>
            <AppButton :disabled="isBusy(selected.id)" @click="checkLoginAction(selected)">检查登录</AppButton>
          </div>

          <section class="connection-detail-block">
            <header>连接操作</header>
            <div class="connection-info-row"><span>操作方式</span><Badge>手动控制</Badge></div>
            <div class="connection-info-row"><span>安全验证</span><b>{{ selected.captcha || '-' }}</b></div>
            <div class="connection-info-row"><span>服务状态</span><b>{{ selected.status || '-' }}</b></div>
          </section>
        </template>
        <EmptyState v-else icon=">" title="请选择一个连接" description="从左侧列表选择账号，查看连接详情、重连策略和实时状态。" />
      </aside>
    </section>
  </div>
</template>
<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import BaseTable from '../components/BaseTable.vue'
import Badge from '../components/Badge.vue'
import AppButton from '../components/AppButton.vue'
import Pagination from '../components/Pagination.vue'
import EmptyState from '../components/EmptyState.vue'
import { getAccounts } from '../api/accounts.js'
import { recordsOf } from '../utils/apiData.js'
import { globalConfirm } from '../composables/confirmState.js'
import { useDebouncedRef } from '../composables/useDebouncedRef.js'
import { checkLogin, refreshCookie, startWebSocket, stopWebSocket, websocketStatus } from '../api/websocket.js'
import { accountAuthState, accountCookieLabel, accountWsConnected } from '../utils/accountAuth.js'
import { accountName } from '../utils/format.js'
const cols=[{key:'info',title:'账号信息'},{key:'cookie',title:'登录凭证'},{key:'ws',title:'实时连接'},{key:'heartbeat',title:'消息通道'},{key:'latency',title:'在线状态'},{key:'last',title:'最近消息时间'},{key:'proxy',title:'代理'},{key:'op',title:'操作'}]
const accounts = ref([])
const statusMap = ref({})
const selected = ref(null)
const keyword = ref('')
const debouncedKeyword = useDebouncedRef(keyword, 300)
const statusFilter = ref('all')
const error = ref('')
const current = ref(1)
const pageSize = ref(20)
const total = ref(0)
const notice = ref('')
const loading = ref(false)
const dataAvailable = ref(null)
const logs = ref([])
const busyMap = ref({})

// 连接重试状态追踪
const retryMap = ref({})  // { [id]: { attempt, max, phase, message } }
// 刷新状态追踪
const refreshingMap = ref({})  // { [id]: true/false }
// 刷新错误追踪
const refreshErrorMap = ref({})  // { [id]: errorMessage }
// 启动命令只提交一次，随后仅轮询状态，避免重复启动产生副作用。
const STARTUP_PHASES = new Set(['starting', 'refresh_token', 'connecting', 'registering', 'syncing', 'accepted', 'pending'])
const rows = computed(() => accounts.value.map(a => {
  const s = statusMap.value[a.id] || {}
  const phase = s.phase || s.status || ''
  const lastError = s.lastError || s.error || ''
  const retry = retryMap.value[a.id]
  const isRefreshing = !!refreshingMap.value[a.id]
  const refreshErr = refreshErrorMap.value[a.id]
  const statusAvailable = Object.prototype.hasOwnProperty.call(statusMap.value, a.id) && s.statusUnavailable !== true
  const connected = statusAvailable ? accountWsConnected(a, s) : null
  const operationPending = connected !== true && STARTUP_PHASES.has(String(phase).toLowerCase())
  const cookieText = accountCookieLabel(a)
  const authState = accountAuthState(a)

  // 判断 WS 状态文本
  let wsText
  if (isRefreshing) {
    wsText = '刷新中...'
  } else if (retry?.phase === 'retrying') {
    wsText = `连接中 (${retry.attempt}/${retry.max})`
  } else if (!statusAvailable) {
    wsText = '状态未知'
  } else if (connected === true) {
    wsText = '已连接'
  } else if (lastError) {
    wsText = '异常'
  } else if (operationPending) {
    wsText = '启动中'
  } else {
    wsText = '断开'
  }

  return { id:a.id, raw:a, avatar:a.avatarUrl || a.avatar, name:accountName(a), user:a.externalUid || a.unb || `account_${a.id}`, cookie:cookieText, authState, connected, operationPending, ws:wsText, heartbeat:connected === true ? '正常' : (connected === false ? '停止' : '未知'), latency:connected === true ? '在线' : (connected === false ? '-' : '未知'), last:s.lastMessageTime || s.last || '-', proxy:a.proxyHost || '-', status:s.status, phase, lastError, captcha:s.captchaStatus, wsTokenStatus:s.wsTokenStatus, isRefreshing, refreshError: refreshErr, retrying: retry?.phase === 'retrying', retryAttempt: retry?.attempt || 0, retryMax: retry?.max || 0 }
}))
const selectedStatusSummary = computed(() => {
  if (!selected.value) return '未选择账号'
  if (selected.value.authState === false) return '登录凭证不可用，请重新登录'
  if (selected.value.authState == null) return '登录状态尚未验证'
  if (selected.value.connected == null) return '连接状态暂不可用，请先刷新状态'
  if (selected.value.operationPending) return '启动命令已提交，正在等待平台确认连接'
  if (selected.value.lastError) return `连接异常：${selected.value.lastError}`
  if (selected.value.connected) return '实时连接与消息通道正常'
  return '登录凭证可用，实时连接当前未启动'
})
const filteredRows = computed(() => rows.value.filter(r => {
  const kw = debouncedKeyword.value.trim().toLowerCase()
  if (kw && !JSON.stringify(r).toLowerCase().includes(kw)) return false
  if (statusFilter.value === 'online') return r.connected === true
  if (statusFilter.value === 'offline') return r.connected === false
  if (statusFilter.value === 'unknown') return r.connected == null
  if (statusFilter.value === 'warning') return r.authState === false || String(r.status || '').includes('验证')
  return true
}))
const onlineCount = computed(() => rows.value.filter(r => r.connected === true).length)
const offlineCount = computed(() => rows.value.filter(r => r.connected === false).length)
const unknownCount = computed(() => rows.value.filter(r => r.connected == null).length)
const cookieOkCount = computed(() => accounts.value.filter(a => accountAuthState(a) === true).length)
const errorCount = computed(() => accounts.value.filter(a => accountAuthState(a) === false).length)
const connectionStatCards = computed(() => [
  { key: 'total', title: '账号总数', value: connectionMetric(total.value), change: '全部记录', symbol: '账', tone: 'tone-blue' },
  { key: 'online', title: '在线连接数', value: connectionMetric(onlineCount.value), change: '当前页已确认', symbol: '连', tone: 'tone-green' },
  { key: 'offline', title: '离线连接数', value: connectionMetric(offlineCount.value), change: '当前页已确认', symbol: '断', tone: 'tone-orange' },
  { key: 'unknown', title: '状态未知', value: connectionMetric(unknownCount.value), change: '当前页需刷新', symbol: '未', tone: 'tone-purple' },
  { key: 'cookie', title: '凭证正常', value: connectionMetric(cookieOkCount.value), change: '当前页实际状态', symbol: '凭', tone: 'tone-cyan' },
  { key: 'error', title: '认证异常', value: connectionMetric(errorCount.value), change: '当前页实际状态', symbol: '异', tone: 'tone-red' }
])
const alerts = computed(() => rows.value
  .filter(r => (r.connected === false && !r.operationPending) || r.authState === false)
  .map(r => ({
    id: r.id,
    row: r,
    text: `${r.name}：${r.authState === false ? '账号登录异常' : '实时连接断开'}`
  }))
  .slice(0, 5))
function connectionMetric(value) { return dataAvailable.value === true ? value : '—' }
function log(text){ logs.value.unshift({text,time:new Date().toLocaleTimeString('zh-CN',{hour12:false})}); logs.value=logs.value.slice(0,12) }
function showNotice(text){ notice.value=text; setTimeout(()=>{ if(notice.value===text) notice.value='' }, 3500) }
function setBusy(id, busy){ busyMap.value = { ...busyMap.value, [id]: busy } }
function isBusy(id){ return !!busyMap.value[id] }
function syncSelected(accountId){ const latest = rows.value.find(r=>r.id===accountId); if(latest) selected.value = latest }
function patchAccountAuth(accountId, patch = {}) {
  if (!accountId) return
  const account = accounts.value.find(item => item.id === accountId)
  if (!account) return
  Object.assign(account, patch)
  syncSelected(accountId)
}
async function load(){
  loading.value = true
  error.value=''
  try {
    const res=await getAccounts({ current: current.value, size: pageSize.value })
    accounts.value=recordsOf(res)
    total.value = Number(res.data?.total ?? res.data?.totalCount ?? res.data?.count ?? accounts.value.length) || 0
    await Promise.allSettled(accounts.value.map(a=>refresh({id:a.id,name:accountName(a)}, { silent: true, skipRefreshState: true })))
    dataAvailable.value = true
    if(!selected.value && rows.value.length) selected.value=rows.value[0]
    else if (selected.value) syncSelected(selected.value.id)
  } catch(e){
    accounts.value = []
    statusMap.value = {}
    selected.value = null
    total.value = 0
    dataAvailable.value = false
    error.value=e.message||'加载失败'
  }
  finally { loading.value = false }
}
function goPage(p) {
  current.value = p
  load()
}
async function refresh(row, { silent = false, skipRefreshState = false } = {}){
  const id = typeof row === 'object' ? row.id : row
  const name = typeof row === 'object' ? (row.name || row.id) : id

  // 批量加载时不显示"刷新中"状态（由 loading 状态统一指示）
  if (!skipRefreshState) {
    refreshingMap.value = { ...refreshingMap.value, [id]: true }
  }
  // 清除之前的刷新错误
  delete refreshErrorMap.value[id]
  refreshErrorMap.value = { ...refreshErrorMap.value }

  try {
    const res = await websocketStatus(id)
    const data = res.data || {}
    if (typeof data.connected !== 'boolean') throw new Error('连接状态响应无法确认')
    statusMap.value = { ...statusMap.value, [id]: data }
    if (!silent) {
      log(`${name} 状态刷新完成：${data.lastError || data.phase || (data.connected ? 'connected' : 'offline')}`)
    }
    // 刷新成功，清除错误
    delete refreshErrorMap.value[id]
    refreshErrorMap.value = { ...refreshErrorMap.value }
    return data
  } catch(e) {
    statusMap.value = { ...statusMap.value, [id]: { connected: null, statusUnavailable: true, status: '状态未知', lastError: '' } }
    refreshErrorMap.value = { ...refreshErrorMap.value, [id]: e.message || '状态刷新失败' }
    if (!silent) {
      log(`${name} 状态刷新失败：${e.message}`)
    }
    throw e
  } finally {
    if (!skipRefreshState) {
      refreshingMap.value = { ...refreshingMap.value, [id]: false }
    }
  }
}
function select(row){ selected.value=row }
async function toggle(row){
  if (!row?.id || isBusy(row.id)) return
  if (row.connected == null) {
    error.value = '连接状态未知，请先刷新状态后再操作。'
    return
  }
  if (row.operationPending) {
    error.value = '该账号的启动命令仍在处理中，请先刷新状态，系统不会重复提交启动命令。'
    return
  }
  if (row.connected === true) {
    await stop(row)
    return
  }

  setBusy(row.id, true); error.value=''
  try {
    const startRes = await startWebSocket(row.id)
    const startData = startRes?.data || {}
    statusMap.value = { ...statusMap.value, [row.id]: { ...(statusMap.value[row.id] || {}), ...startData } }
    if (typeof startData.connected !== 'boolean') throw new Error('实时连接启动响应缺少连接状态')

    if (startData.connected === true) {
      showNotice(startData.optimistic
        ? `${row.name}：实时连接已提交，未检测到滑块/验证`
        : `${row.name}：实时连接已确认就绪`)
      log(startData.optimistic
        ? `${row.name} 连接已提交（乐观确认），未检测到验证`
        : `${row.name} 连接成功（状态已确认）`)
    } else {
      showNotice(startData.message || `${row.name}：连接请求返回未连接状态`)
      log(`${row.name} 启动返回：${startData.message || startData.status || '未连接'}`)
    }

    if (startData.optimistic) {
      // 乐观确认：系统 12 秒内未检测到验证失败，8 秒后刷新实际状态
      setTimeout(() => {
        refresh(row, { silent: true, skipRefreshState: true }).catch(() => {})
      }, 8000)
    } else {
      // 已确认连接/恢复中：短暂等待后刷新状态
      await new Promise(resolve => setTimeout(resolve, 1200))
      await refresh(row, { silent: true, skipRefreshState: true }).catch(() => {})
    }
    syncSelected(row.id)
    // 连接成功后刷新账号列表，同步 Cookie 状态
    load()
  } catch(e){
    error.value = e.message || '启动命令提交失败'
    log(`${row.name} 启动命令未能提交：${error.value}`)
  }
  finally {
    retryMap.value = { ...retryMap.value, [row.id]: undefined }
    setBusy(row.id, false)
  }
}
async function stop(row){
  if (!row?.id || isBusy(row.id)) return
  if (row.connected !== true) {
    error.value = row.connected == null ? '连接状态未知，请先刷新。' : '该账号当前未确认在线，无需断开。'
    return
  }
  setBusy(row.id, true)
  error.value = ''
  try {
    log(`${row.name} 正在断开连接...`)
    await stopWebSocket(row.id)
    // 等待短暂时间确保系统处理完成
    await new Promise(r => setTimeout(r, 500))
    await refresh(row, { silent: true })
    syncSelected(row.id)
    showNotice(`${row.name} 已断开`)
    log(`${row.name} 断开成功，状态已更新`)
  } catch(e){
    const errMsg = e.message || '断开连接失败'
    error.value = errMsg
    log(`${row.name} 断开失败：${errMsg}`)
    // 即使失败也刷新状态
    try { await refresh(row, { silent: true }) } catch { /* Preserve the disconnect error. */ }
  }
  finally { setBusy(row.id, false) }
}
async function refreshCookieAction(row){
  if (!row?.id || isBusy(row.id)) return
  setBusy(row.id, true)
  try {
    await refreshCookie(row.id)
    await load()
    await refresh(row, { silent: true })
    syncSelected(row.id)
    log(`${row.name} 登录凭证刷新完成`)
    showNotice('登录凭证刷新完成')
  } catch(e){ error.value=e.message }
  finally { setBusy(row.id, false) }
}
async function checkLoginAction(row){
  if (!row?.id || isBusy(row.id)) return
  setBusy(row.id, true)
  try {
    const res = await checkLogin(row.id)
    const auth = res.data?.status || {}
    patchAccountAuth(row.id, {
      cookieStatus: auth.cookieStatus,
      authUsable: auth.usable,
      loginStatusCode: auth.loginStatusCode,
      loginStatusMessage: auth.loginStatusMessage,
      loginCheckTime: auth.checkedAt,
    })
    await load()
    await refresh(row, { silent: true })
    syncSelected(row.id)
    showNotice(auth.loginStatusMessage || res.data?.message || '检查完成')
  } catch(e){ error.value=e.message }
  finally { setBusy(row.id, false) }
}
async function batchStart(){
  const targets = filteredRows.value.filter(r => r.connected === false && !r.operationPending)
  if(!targets.length) return showNotice('当前没有需要启动的离线连接')
  if(!await globalConfirm.confirm(`确认批量启动 ${targets.length} 个连接？`)) return
  for (const row of targets) await toggle(row)
}
async function batchStop(){
  const targets = filteredRows.value.filter(r => r.connected === true)
  if(!targets.length) return showNotice('当前没有在线连接')
  if(!await globalConfirm.confirm(`确认批量断开 ${targets.length} 个连接？`)) return
  for (const row of targets) await stop(row)
}
function handleAlert(alert){
  select(alert.row)
  showNotice(alert.row.authState === true
    ? '已打开连接详情，请核对状态后手动处理。'
    : '登录凭证或登录状态异常，请先到账号管理更新授权信息。')
}
function onHeader(e){
  if(e.detail === 'connections-batch-start') batchStart()
  if(e.detail === 'connections-batch-stop') batchStop()
}
function onSseEvent(e) {
  const event = e.detail
  if (!event || !event.type) return
  if (event.type === 'cookie_status_changed') {
    const accountId = event.accountId
    if (!accountId) return
    const cookieStatus = Number(event.cookieStatus)
    const invalid = cookieStatus !== 1
    patchAccountAuth(accountId, {
      cookieStatus,
      authUsable: !invalid,
      loginStatusMessage: event.reason || (invalid ? '登录凭证已失效，请重新登录闲鱼账号' : '账号登录状态正常'),
      loginStatusCode: invalid ? 'COOKIE_EXPIRED' : 'OK',
    })
    if (invalid) {
      statusMap.value = {
        ...statusMap.value,
        [accountId]: {
          ...(statusMap.value[accountId] || {}),
          connected: false,
          lastError: event.reason || '登录凭证已失效',
          phase: 'cookie_expired',
          status: '登录凭证失效',
        }
      }
      log(`账号 ${accountId} 登录凭证已失效，连接已断开`)
    } else {
      log(`账号 ${accountId} 登录凭证状态已恢复正常`)
    }
  }
}
onMounted(()=>{ window.addEventListener('xya-header-action', onHeader); window.addEventListener('xya-sse-event', onSseEvent); load() })
onBeforeUnmount(()=>{ window.removeEventListener('xya-header-action', onHeader); window.removeEventListener('xya-sse-event', onSseEvent) })
</script>

<style scoped>
.connections-console {
  display: grid;
  gap: 18px;
  min-width: 0;
}

.connections-notices {
  display: grid;
  gap: 10px;
}

.connections-command-center {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 18px;
  padding: 22px;
  border: 1px solid #dbe3ef;
  border-radius: 8px;
  background:
    linear-gradient(135deg, rgba(29, 78, 216, .08), rgba(14, 165, 233, .05) 45%, rgba(16, 185, 129, .08)),
    #ffffff;
  box-shadow: 0 16px 38px rgba(15, 23, 42, .07);
}

.connections-command-main {
  min-width: 0;
}

.connections-command-kicker,
.connections-command-meta,
.connections-command-panel-head,
.connections-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.connections-command-kicker {
  justify-content: flex-start;
}

.connections-command-kicker span,
.connections-command-panel-head span,
.connections-panel-head span {
  color: #0369a1;
  font-size: 12px;
  font-weight: 750;
}

.connections-command-kicker b,
.connections-command-panel-head strong,
.connections-panel-head b {
  color: #475569;
  font-size: 12px;
  font-weight: 700;
}

.connections-command-main h2 {
  margin: 12px 0 8px;
  color: #0f172a;
  font-size: 26px;
  font-weight: 780;
  line-height: 1.2;
}

.connections-command-main p {
  max-width: 760px;
  margin: 0;
  color: #475569;
  font-size: 14px;
  line-height: 1.8;
}

.connections-command-meta {
  justify-content: flex-start;
  flex-wrap: wrap;
  margin-top: 18px;
}

.connections-command-meta span,
.connections-command-panel {
  border: 1px solid rgba(148, 163, 184, .32);
  border-radius: 8px;
  background: rgba(255, 255, 255, .78);
}

.connections-command-meta span {
  padding: 7px 10px;
  color: #334155;
  font-size: 12px;
}

.connections-command-panel {
  display: grid;
  align-content: start;
  gap: 12px;
  padding: 16px;
}

.connections-command-buttons {
  display: grid;
  gap: 10px;
}

.connections-action-btn {
  min-height: 38px;
  border: 1px solid #dbe3ef;
  border-radius: 8px;
  background: #ffffff;
  color: #0f172a;
  font-size: 13px;
  font-weight: 750;
  cursor: pointer;
}

.connections-action-btn.primary {
  border-color: #2563eb;
  background: #2563eb;
  color: #ffffff;
}

.connections-action-btn.warn {
  border-color: #f59e0b;
  background: #fff7ed;
  color: #b45309;
}

.connections-action-btn:disabled {
  cursor: wait;
  opacity: .65;
}

.connections-metric-rail {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
}

.connections-metric-card {
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr);
  gap: 12px;
  min-width: 0;
  padding: 15px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 10px 24px rgba(15, 23, 42, .05);
}

.connections-metric-icon {
  width: 38px;
  height: 38px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 800;
}

.connections-metric-card p {
  margin: 0;
  color: #64748b;
  font-size: 12px;
}

.connections-metric-card strong {
  display: block;
  margin-top: 3px;
  color: #0f172a;
  font-size: 24px;
  font-weight: 800;
  line-height: 1.2;
}

.connections-metric-card small {
  display: block;
  margin-top: 6px;
  color: #64748b;
  font-size: 12px;
  line-height: 1.4;
}

.connections-metric-card.tone-blue .connections-metric-icon { background: #dbeafe; color: #1d4ed8; }
.connections-metric-card.tone-green .connections-metric-icon { background: #dcfce7; color: #15803d; }
.connections-metric-card.tone-orange .connections-metric-icon { background: #ffedd5; color: #c2410c; }
.connections-metric-card.tone-purple .connections-metric-icon { background: #ede9fe; color: #6d28d9; }
.connections-metric-card.tone-cyan .connections-metric-icon { background: #ccfbf1; color: #0f766e; }
.connections-metric-card.tone-red .connections-metric-icon { background: #fee2e2; color: #dc2626; }

.connections-workbench {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 380px;
  gap: 16px;
  align-items: start;
}

.connections-main {
  display: grid;
  gap: 16px;
  min-width: 0;
}

.connections-panel,
.connection-detail-panel {
  min-width: 0;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 10px 26px rgba(15, 23, 42, .05);
}

.connections-panel {
  padding: 16px;
}

.connections-list-panel {
  overflow: hidden;
}

.connections-panel-head {
  align-items: flex-start;
  margin-bottom: 14px;
}

.connections-panel-head.compact {
  margin-bottom: 12px;
}

.connections-panel-head h3 {
  margin: 4px 0 0;
  color: #0f172a;
  font-size: 17px;
  font-weight: 760;
  line-height: 1.25;
}

.connections-filter-bar {
  display: grid;
  grid-template-columns: 170px minmax(220px, 1fr) auto;
  gap: 10px;
  align-items: center;
  margin-bottom: 14px;
}

.connections-filter-select,
.connections-search-input {
  min-width: 0;
}

.connections-list-panel :deep(.base-table-wrap) {
  border-radius: 8px;
}

.connection-account-cell {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 190px;
}

.connection-account-cell strong,
.connection-detail-identity strong {
  color: #0f172a;
  font-size: 13px;
  font-weight: 760;
}

.connection-account-cell em {
  display: block;
  margin-top: 3px;
  color: #64748b;
  font-size: 12px;
  font-style: normal;
}

.connection-avatar {
  width: 44px;
  height: 44px;
  flex: 0 0 auto;
  border-radius: 8px;
  background: linear-gradient(135deg, #dbeafe, #ccfbf1);
  object-fit: cover;
}

.connection-avatar.small {
  width: 34px;
  height: 34px;
}

.connection-state-cell {
  display: grid;
  gap: 5px;
  max-width: 210px;
}

.connection-state-cell p {
  margin: 0;
  color: #64748b;
  font-size: 12px;
  line-height: 1.45;
  white-space: normal;
  word-break: break-word;
}

.connection-state-cell .retrying {
  color: #2563eb;
}

.connection-state-cell .danger,
.connection-info-row .danger {
  color: #dc2626;
}

.latency-text {
  color: #8c98ae;
}

.latency-text.online {
  color: #16bf78;
}

.latency-text.offline {
  color: #f59e0b;
}

.connections-row-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.connections-secondary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.connections-event-list,
.connections-alert-list {
  display: grid;
  gap: 10px;
}

.connections-event-row,
.connections-alert-row,
.connection-info-row {
  display: grid;
  gap: 10px;
  padding: 11px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f8fafc;
}

.connections-event-row,
.connections-alert-row {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
}

.connections-event-row span,
.connections-alert-row span {
  color: #334155;
  font-size: 13px;
  line-height: 1.5;
}

.connections-event-row time {
  color: #64748b;
  font-size: 12px;
  white-space: nowrap;
}

.connection-detail-panel {
  position: sticky;
  top: 16px;
  display: grid;
  gap: 14px;
  padding: 16px;
}

.detail-head {
  margin-bottom: 0;
}

.connection-detail-identity {
  display: grid;
  grid-template-columns: 44px minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  padding: 12px;
  border: 1px solid #dbeafe;
  border-radius: 8px;
  background: #f8fafc;
}

.connection-detail-identity p {
  margin: 4px 0 0;
  color: #64748b;
  font-size: 12px;
}

.connection-detail-identity > b {
  color: #8c98ae;
  font-size: 13px;
}

.connection-detail-identity > b.online {
  color: #047857;
}

.connection-detail-identity > b.offline {
  color: #dc2626;
}

.connection-status-summary {
  padding: 14px;
  border: 1px solid #e0f2fe;
  border-radius: 8px;
  background: linear-gradient(135deg, rgba(219, 234, 254, .7), rgba(240, 253, 250, .9));
}

.connection-status-summary span,
.connection-detail-block header {
  color: #0369a1;
  font-size: 12px;
  font-weight: 750;
}

.connection-status-summary p {
  margin: 6px 0 0;
  color: #0f172a;
  font-size: 14px;
  line-height: 1.65;
}

.connection-health-list {
  display: grid;
  gap: 9px;
}

.connection-health-list div {
  display: grid;
  grid-template-columns: 10px minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #ffffff;
}

.connection-health-list i {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #98a2b3;
}

.connection-health-list i.online {
  background: #16bf78;
}

.connection-health-list i.offline {
  background: #ef4444;
}

.connection-health-list span,
.connection-info-row span {
  color: #64748b;
  font-size: 12px;
}

.connection-health-list b,
.connection-info-row b {
  color: #0f172a;
  font-size: 12px;
  text-align: right;
  word-break: break-word;
}

.connection-detail-block {
  display: grid;
  gap: 8px;
}

.connection-detail-block header {
  padding: 0 2px;
}

.connection-info-row {
  grid-template-columns: minmax(90px, .45fr) minmax(0, 1fr);
  align-items: center;
}

.connection-detail-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

@media (max-width: 900px) {
  .connections-console {
    gap: 12px;
  }

  .connections-command-center,
  .connections-workbench,
  .connections-filter-bar,
  .connections-secondary-grid,
  .connection-detail-actions,
  .connections-metric-rail {
    grid-template-columns: minmax(0, 1fr);
  }

  .connections-command-center {
    padding: 16px;
  }

  .connection-detail-panel {
    position: static;
  }

  .connection-detail-identity,
  .connections-event-row,
  .connections-alert-row,
  .connection-health-list div,
  .connection-info-row {
    grid-template-columns: minmax(0, 1fr);
  }

  .connection-health-list b,
  .connection-info-row b {
    text-align: left;
  }

  .connections-list-panel :deep(.base-table) {
    display: block;
    overflow-x: auto;
    white-space: nowrap;
    -webkit-overflow-scrolling: touch;
  }
}
</style>
