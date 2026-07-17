<template>
  <div class="connections-v4">
    <n-card class="connections-v4-hero" :bordered="false">
      <div>
        <n-tag size="small" type="success" :bordered="false">连接中心</n-tag>
        <h2>连接管理工作台</h2>
        <p>集中查看闲鱼账号 Cookie、WebSocket、心跳与启动状态，异常账号可直接进入详情处理。</p>
      </div>
      <n-space :size="8" align="center" wrap>
        <n-button size="small" :loading="loading" @click="load">刷新连接</n-button>
        <n-button size="small" @click="batchStart">批量启动</n-button>
        <n-button size="small" type="warning" @click="batchStop">批量断开</n-button>
      </n-space>
    </n-card>

    <section class="connections-v4-stats">
      <n-card v-for="item in connectionStatCards" :key="item.key" class="connections-v4-stat" :class="item.tone" :bordered="false">
        <span class="connections-v4-stat-icon">{{ item.symbol }}</span>
        <n-statistic :label="item.title" :value="item.value" />
        <small>{{ item.change }}</small>
      </n-card>
    </section>

  <div class="grid wide-right connections-v4-grid">
    <div>
      <div v-if="error" class="global-notice error">{{ error }}</div>
      <div v-if="notice" class="global-notice success">{{ notice }}</div>
      <n-card class="connections-v4-card" :bordered="false">
        <template #header>账号连接列表（{{ rows.length }}）</template>
        <div class="toolbar">
          <select v-model="statusFilter" class="input" style="max-width:150px">
            <option value="all">全部状态</option>
            <option value="online">仅在线</option>
            <option value="offline">仅离线</option>
            <option value="unknown">状态未知</option>
            <option value="warning">Cookie/验证异常</option>
          </select>
          <input v-model="keyword" class="input large" placeholder="搜索 账号昵称/用户名">
          <AppButton :disabled="loading" @click="load">{{ loading ? '刷新中...' : '刷新' }}</AppButton>
        </div>
        <EmptyState v-if="dataAvailable === false" icon="⚠️" title="连接列表暂不可用" description="当前无法确认账号与连接状态，不会把失败显示为离线。">
          <template #actions><AppButton @click="load">重新加载</AppButton></template>
        </EmptyState>
        <BaseTable v-else :columns="cols" :rows="filteredRows">
          <template #info="{row}"><div class="product-cell"><img v-if="row.avatar" :src="row.avatar" class="avatar small" alt=""><div v-else class="avatar small"></div><div><strong>{{ row.name }}</strong><em>{{ row.user }}</em></div></div></template>
          <template #cookie="{row}"><Badge :type="row.authState === true ? 'green' : (row.authState === false ? 'red' : 'gray')">{{ row.cookie }}</Badge></template>
          <template #ws="{row}"><div><Badge :type="row.connected === true ? 'green' : (row.connected === false ? 'red' : 'orange')">{{ row.ws }}</Badge><p v-if="row.retrying" class="subtle" style="color:var(--blue);max-width:180px;white-space:normal">⏳ 第 {{ row.retryAttempt }}/{{ row.retryMax }} 次尝试</p><p v-else-if="row.refreshError" class="subtle" style="color:#ef4444;max-width:180px;white-space:normal">⚠ {{ row.refreshError }}</p><p v-else-if="row.phase || row.lastError" class="subtle" style="max-width:180px;white-space:normal">{{ row.lastError || row.phase }}</p></div></template>
          <template #latency="{row}"><b :style="{color:row.connected === true ? '#16bf78' : (row.connected === false ? '#ff9f22' : '#8c98ae')}">{{ row.latency }}</b></template>
          <template #op="{row}">
            <button class="link" :disabled="isBusy(row.id) || row.isRefreshing || row.connected == null || row.operationPending" @click="toggle(row)">{{ isBusy(row.id) ? (row.retrying ? '确认中...' : '处理中...') : (row.operationPending ? '启动中' : (row.connected === true ? '断开' : (row.connected === false ? '启动' : '状态未知'))) }}</button>
            <button class="link" :disabled="isBusy(row.id) || row.isRefreshing" @click="refresh(row)"><span :class="{ spinning: row.isRefreshing }">↻</span></button>
            <button class="link" @click="select(row)">详情</button>
          </template>
        </BaseTable><Pagination v-if="dataAvailable === true" :total="total" :current="current" :page-size="pageSize" @page-change="goPage" />
      </n-card>
      <div class="grid two-col connections-v4-subgrid" style="margin-top:16px">
        <n-card class="connections-v4-card" title="实时连接日志" :bordered="false"><EmptyState v-if="logs.length===0" icon="📡" title="暂无本次页面操作日志" description="本页执行的连接、断开、重连操作会显示在这里。" /><div v-for="l in logs" :key="l.text+l.time" class="option-line"><span><i class="dot"></i>{{ l.text }}</span><span class="subtle">{{ l.time }}</span></div></n-card>
        <n-card class="connections-v4-card" title="异常告警列表" :bordered="false"><EmptyState v-if="dataAvailable === false" icon="⚠️" title="告警状态不可用" description="账号列表加载失败，当前无法确认是否有连接或 Cookie 异常。" /><EmptyState v-else-if="alerts.length===0" icon="✅" title="暂无已确认异常" description="当前已加载且已探测的账号中没有发现连接或 Cookie 异常。" /><div v-for="e in alerts" :key="e.id" class="option-line"><span><i class="dot orange"></i>{{ e.text }}</span><AppButton @click="handleAlert(e)">查看</AppButton></div></n-card>
      </div>
    </div>
    <div class="right-drawer connections-v4-detail">
      <div style="display:flex;justify-content:space-between"><h3>连接详情</h3><button class="link" @click="selected = null">×</button></div>
      <template v-if="selected">
        <div class="product-cell"><img v-if="selected.avatar" :src="selected.avatar" class="avatar" alt=""><div v-else class="avatar"></div><div><strong>{{ selected.name }} <Badge type="blue">账号</Badge></strong><p class="subtle">{{ selected.user }}</p></div><b :style="{marginLeft:'auto',color:selected.connected === true ? 'var(--green)' : (selected.connected === false ? '#ef4444' : '#8c98ae')}">{{ selected.ws }}</b></div>
        <div class="donut-row" style="margin:22px 0"><div class="health-summary-card"><div class="health-summary-title">实时状态</div><div class="health-summary-desc">{{ selectedStatusSummary }}</div></div><div class="donut-legend"><div><i :style="{ background: selected.connected === true ? '#16bf78' : (selected.connected === false ? '#ef4444' : '#98a2b3') }"></i><span>WebSocket</span><b>{{ selected.ws }}</b></div><div><i :style="{ background: selected.connected === true ? '#16bf78' : '#98a2b3' }"></i><span>心跳状态</span><b>{{ selected.heartbeat }}</b></div><div><i :style="{ background: selected.authState === true ? '#16bf78' : (selected.authState === false ? '#ef4444' : '#98a2b3') }"></i><span>Cookie</span><b>{{ selected.cookie }}</b></div><div><i :style="{ background: selected.lastError ? '#ef4444' : '#98a2b3' }"></i><span>状态</span><b>{{ selected.lastError || selected.status || selected.phase || '-' }}</b></div></div></div>
        <n-card class="connections-v4-card" title="连接信息" :bordered="false"><div class="option-line"><span>账号 ID</span><b>{{ selected.id }}</b></div><div class="option-line"><span>Cookie 状态</span><b>{{ selected.cookie }}</b></div><div class="option-line"><span>连接阶段</span><b>{{ selected.phase || '-' }}</b></div><div class="option-line"><span>最近错误</span><b v-if="selected.refreshError" style="color:#ef4444">{{ selected.refreshError }}</b><b v-else>{{ selected.lastError || '-' }}</b></div><div class="option-line"><span>WS Token</span><b>{{ selected.wsTokenStatus || '-' }}</b></div><div class="option-line"><span>最近消息</span><b>{{ selected.last }}</b></div><div v-if="selected.refreshError" class="option-line"><span>操作</span><AppButton size="small" @click="refresh(selected)">重新刷新状态</AppButton></div></n-card>
        <div class="grid" style="grid-template-columns:repeat(2,1fr);margin:16px 0">
          <AppButton type="primary" :disabled="isBusy(selected.id) || selected.connected == null || selected.operationPending" @click="toggle(selected)">{{ selected.operationPending ? '启动中' : '启动/断开' }}</AppButton>
          <AppButton type="danger" :disabled="isBusy(selected.id) || selected.connected !== true" @click="stop(selected)">断开连接</AppButton>
          <AppButton :disabled="isBusy(selected.id)" @click="refreshCookieAction(selected)">刷新 Cookie</AppButton>
          <AppButton :disabled="isBusy(selected.id)" @click="checkLoginAction(selected)">检查登录</AppButton>
        </div>
        <n-card class="connections-v4-card" title="重连策略" :bordered="false"><div class="option-line"><span>前端策略</span><Badge>手动控制</Badge></div><div class="option-line"><span>验证码</span><b>{{ selected.captcha || '-' }}</b></div><div class="option-line"><span>接口状态</span><b>{{ selected.status || '-' }}</b></div></n-card>
      </template>
      <EmptyState v-else icon="👈" title="请选择一个连接" description="从左侧列表选择账号，查看连接详情、重连策略和实时状态。" />
    </div>
  </div>
  </div>
</template>
<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { NButton, NCard, NSpace, NStatistic, NTag } from 'naive-ui'
import BaseTable from '../components/BaseTable.vue';import Badge from '../components/Badge.vue';import AppButton from '../components/AppButton.vue';import Pagination from '../components/Pagination.vue';import EmptyState from '../components/EmptyState.vue'
import { getAccounts } from '../api/accounts.js'
import { recordsOf } from '../utils/apiData.js'
import { globalConfirm } from '../composables/confirmState.js'
import { useDebouncedRef } from '../composables/useDebouncedRef.js'
import { checkLogin, refreshCookie, startWebSocket, stopWebSocket, websocketStatus } from '../api/websocket.js'
import { accountAuthState, accountCookieLabel, accountWsConnected } from '../utils/accountAuth.js'
import { accountName } from '../utils/format.js'
const cols=[{key:'info',title:'账号信息'},{key:'cookie',title:'Cookie状态'},{key:'ws',title:'WS状态'},{key:'heartbeat',title:'心跳'},{key:'latency',title:'延迟'},{key:'last',title:'最近消息时间'},{key:'proxy',title:'代理'},{key:'op',title:'操作'}]
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
  if (selected.value.authState === false) return 'Cookie 不可用，请重新登录'
  if (selected.value.authState == null) return 'Cookie 登录状态尚未验证'
  if (selected.value.connected == null) return '连接状态探测失败，请先刷新状态'
  if (selected.value.operationPending) return '启动命令已提交，正在等待服务端确认连接'
  if (selected.value.lastError) return `连接异常：${selected.value.lastError}`
  if (selected.value.connected) return 'WebSocket 与心跳均已连接'
  return 'Cookie 可用，WebSocket 当前未连接'
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
  { key: 'online', title: '在线连接数', value: connectionMetric(onlineCount.value), change: '当前页已探测', symbol: '连', tone: 'tone-green' },
  { key: 'offline', title: '离线连接数', value: connectionMetric(offlineCount.value), change: '当前页已探测', symbol: '断', tone: 'tone-orange' },
  { key: 'unknown', title: '状态未知', value: connectionMetric(unknownCount.value), change: '当前页需刷新', symbol: '未', tone: 'tone-purple' },
  { key: 'cookie', title: 'Cookie正常', value: connectionMetric(cookieOkCount.value), change: '当前页实际状态', symbol: 'CK', tone: 'tone-cyan' },
  { key: 'error', title: '认证异常', value: connectionMetric(errorCount.value), change: '当前页实际状态', symbol: '异', tone: 'tone-red' }
])
const alerts = computed(() => rows.value
  .filter(r => (r.connected === false && !r.operationPending) || r.authState === false)
  .map(r => ({
    id: r.id,
    row: r,
    text: `${r.name}：${r.authState === false ? '账号登录异常' : 'WebSocket 断开'}`
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
    if (typeof startData.connected !== 'boolean') throw new Error('WebSocket 启动响应缺少连接状态')

    if (startData.connected === true) {
      showNotice(startData.optimistic
        ? `${row.name}：WS 连接已提交，未检测到滑块/验证`
        : `${row.name}：WS 连接已确认就绪`)
      log(startData.optimistic
        ? `${row.name} 连接已提交（乐观确认），未检测到验证`
        : `${row.name} 连接成功（状态探测确认）`)
    } else {
      showNotice(startData.message || `${row.name}：连接请求返回未连接状态`)
      log(`${row.name} 启动返回：${startData.message || startData.status || '未连接'}`)
    }

    if (startData.optimistic) {
      // 乐观确认：后端 12 秒内未检测到验证失败，8 秒后刷新实际状态
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
    // 等待短暂时间确保后端处理完成
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
    log(`${row.name} Cookie 刷新完成`)
    showNotice('Cookie 刷新完成')
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
    : 'Cookie 或登录状态异常，请先到账号管理更新授权信息。')
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
      loginStatusMessage: event.reason || (invalid ? 'Cookie 已失效，请重新登录闲鱼账号' : '账号登录状态正常'),
      loginStatusCode: invalid ? 'COOKIE_EXPIRED' : 'OK',
    })
    if (invalid) {
      statusMap.value = {
        ...statusMap.value,
        [accountId]: {
          ...(statusMap.value[accountId] || {}),
          connected: false,
          lastError: event.reason || 'Cookie 已失效',
          phase: 'cookie_expired',
          status: 'Cookie 失效',
        }
      }
      log(`账号 ${accountId} Cookie 已失效，连接已断开`)
    } else {
      log(`账号 ${accountId} Cookie 状态已恢复正常`)
    }
  }
}
onMounted(()=>{ window.addEventListener('xya-header-action', onHeader); window.addEventListener('xya-sse-event', onSseEvent); load() })
onBeforeUnmount(()=>{ window.removeEventListener('xya-header-action', onHeader); window.removeEventListener('xya-sse-event', onSseEvent) })
</script>

<style scoped>
.connections-v4 {
  display: grid;
  gap: 16px;
  min-width: 0;
}

.connections-v4-hero,
.connections-v4-card,
.connections-v4-stat,
.connections-v4-detail {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, .04);
}

.connections-v4-hero :deep(.n-card__content) {
  padding: 18px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.connections-v4-hero h2 {
  margin: 12px 0 6px;
  color: #111827;
  font-size: 22px;
  font-weight: 650;
  line-height: 1.25;
}

.connections-v4-hero p {
  margin: 0;
  color: #64748b;
  font-size: 13px;
  line-height: 1.65;
}

.connections-v4-stats {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
}

.connections-v4-stat :deep(.n-card__content) {
  padding: 16px;
  display: grid;
  gap: 8px;
}

.connections-v4-stat-icon {
  width: 36px;
  height: 36px;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
}

.connections-v4-stat.tone-blue .connections-v4-stat-icon { background: #eff6ff; color: #2563eb; }
.connections-v4-stat.tone-green .connections-v4-stat-icon { background: #ecfdf5; color: #059669; }
.connections-v4-stat.tone-orange .connections-v4-stat-icon { background: #fff7ed; color: #ea580c; }
.connections-v4-stat.tone-purple .connections-v4-stat-icon { background: #f5f3ff; color: #7c3aed; }
.connections-v4-stat.tone-cyan .connections-v4-stat-icon { background: #ecfeff; color: #0891b2; }
.connections-v4-stat.tone-red .connections-v4-stat-icon { background: #fef2f2; color: #dc2626; }

.connections-v4-stat :deep(.n-statistic .n-statistic-label) {
  color: #64748b;
  font-size: 12px;
}

.connections-v4-stat :deep(.n-statistic .n-statistic-value) {
  color: #111827;
  font-size: 24px;
  font-weight: 700;
}

.connections-v4-stat small {
  color: #64748b;
  font-size: 12px;
  line-height: 1.4;
}

.connections-v4-grid {
  align-items: start;
  grid-template-columns: minmax(0, 1fr) 360px;
}

.connections-v4-subgrid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.connections-v4-card :deep(.n-card__content) {
  padding: 16px;
}

.connections-v4-card :deep(.n-card-header) {
  padding: 16px 16px 0;
}

.connections-v4-detail {
  position: sticky;
  top: 16px;
  padding: 16px;
  min-width: 0;
}

.connections-v4-detail h3 {
  margin: 0 0 12px;
  color: #111827;
  font-size: 16px;
  font-weight: 650;
}

/* === 移动端适配 (max-width: 900px) === */
@media (max-width: 900px) {
  .connections-v4 {
    gap: 12px;
  }

  .connections-v4-hero :deep(.n-card__content) {
    flex-direction: column;
    padding: 14px;
  }

  .connections-v4-stats,
  .connections-v4-grid,
  .connections-v4-subgrid {
    grid-template-columns: minmax(0, 1fr);
  }

  .connections-v4-detail {
    position: static;
  }

  .connections-v4-card :deep(.n-card__content) {
    padding: 12px;
  }

  /* 覆盖右侧详情操作按钮区内联 grid: repeat(2,1fr) → 单列堆叠 */
  .grid[style*="repeat(2,1fr)"] {
    grid-template-columns: minmax(0, 1fr) !important;
    margin: 12px 0 !important;
    gap: 8px !important;
  }
  /* 健康度环形图行：移动端纵向堆叠 */
  .donut-row {
    flex-direction: column !important;
    align-items: stretch !important;
    gap: 12px;
    margin: 14px 0 !important;
  }
  .donut-row .health-summary-card,
  .donut-row .donut-legend {
    width: 100%;
    max-width: none;
  }
  .donut-legend {
    gap: 8px;
  }
  /* 右侧抽屉头部允许换行 */
  .right-drawer > div:first-child {
    flex-wrap: wrap;
    gap: 8px;
  }
  /* 右侧抽屉中的账号信息行允许换行，避免长文本溢出 */
  .right-drawer .product-cell {
    flex-wrap: wrap;
    gap: 8px;
  }
  .right-drawer .product-cell b {
    margin-left: 0 !important;
    width: 100%;
  }
  /* 状态文本段落限制宽度，避免撑破布局 */
  .right-drawer p {
    max-width: 100% !important;
    white-space: normal !important;
    word-break: break-word;
  }
  /* 宽表格横向滚动 */
  :deep(.base-table) {
    display: block;
    overflow-x: auto;
    white-space: nowrap;
    -webkit-overflow-scrolling: touch;
  }
}
</style>
