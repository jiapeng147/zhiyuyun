<template>
  <div class="accounts-page accounts-v11-shell" v-bind="$attrs">
    <main class="accounts-main">
      <BusinessSection class="accounts-command-section" title="账号资产" eyebrow="账号资产">
        <template #extra>
          <n-tag :type="dataAvailable === false ? 'error' : (loading ? 'warning' : 'success')" size="small" :bordered="false">
            {{ dataAvailable === false ? '列表不可用' : (loading ? '刷新中' : '可操作') }}
          </n-tag>
        </template>
        <div class="accounts-command-layout">
        <div class="accounts-command-copy">
          <p>统一管理闲鱼账号、登录凭证、资料刷新、实时连接、账号策略与商品擦亮任务。</p>
          <n-space class="accounts-command-meta" :size="[8, 8]">
            <n-tag size="small" :bordered="false" round>{{ selected ? accountTitle(selected) : '未选择账号' }}</n-tag>
            <n-tag size="small" :bordered="false" round>{{ loading ? '账号刷新中' : `当前 ${accountMetric(stats.total)} 个账号` }}</n-tag>
            <n-tag size="small" :bordered="false" round>正常 {{ accountMetric(stats.normal) }}</n-tag>
            <n-tag size="small" :bordered="false" round>在线 {{ accountMetric(stats.wsOnline) }}</n-tag>
          </n-space>
        </div>
        <div class="accounts-command-panel">
          <div class="accounts-command-panel-head">
            <span>账号动作</span>
            <strong>{{ selected ? '已选账号' : '全局操作' }}</strong>
          </div>
          <div class="accounts-command-buttons">
            <n-button type="primary" :title="accountActionHint" @click="openModal('scan')">扫码加账号</n-button>
            <n-button :title="accountActionHint" @click="openModal('manual')">手动添加</n-button>
            <n-button tertiary :title="accountActionHint" :loading="loading" @click="loadAccounts">刷新账号</n-button>
          </div>
          <p class="accounts-action-hint">{{ accountActionHint }}</p>
        </div>
        </div>
      </BusinessSection>

      <div class="accounts-intel-banner">
        <Icon name="shield" />
        <span>扫码前请确认这是你信任的平台服务；若服务不可用，页面会显示明确的不可用状态与重试入口。</span>
      </div>

      <div class="accounts-notices">
        <div v-if="error" class="global-notice error">{{ error }}</div>
        <div v-if="accountListWarning" class="global-notice warning" role="status">{{ accountListWarning }}</div>
        <div v-if="qrSuccessMsg" class="global-notice success">{{ qrSuccessMsg }}</div>
        <div v-if="polishNotice.text" :class="['global-notice', polishNotice.type]">{{ polishNotice.text }}</div>
      </div>
      <ItemPolishConflictCard
        v-if="activePolishConflict"
        :conflict="activePolishConflict"
        :refreshing="activePolishConflictRefreshing"
        :refresh-message="activePolishConflictRefreshMessage"
        @refresh="refreshActivePolishConflict"
      />

      <BusinessStatusStrip :items="accountsStatusItems" />

      <section class="accounts-metric-grid">
        <BusinessMetricCard
          v-for="item in accountStatCards"
          :key="item.key"
          :label="item.title"
          :value="item.value"
          :hint="item.change"
          :tone="item.tone"
          :icon="item.icon"
        />
      </section>

      <section class="accounts-workspace">
        <header class="accounts-workspace-head">
          <div>
            <span class="accounts-workspace-eyebrow">账号列表</span>
            <h3>账号数据与连接状态</h3>
          </div>
          <div class="accounts-workspace-tags">
            <n-tag size="small" :bordered="false">{{ dataAvailable === true ? `共 ${total} 条` : '等待加载' }}</n-tag>
            <n-tag size="small" type="info" :bordered="false">第 {{ current }} 页</n-tag>
          </div>
        </header>
        <div class="accounts-control-board">
          <n-input
            v-model:value="keyword"
            clearable
            class="accounts-search"
            placeholder="搜索昵称 / UID / 备注"
            @keyup.enter="loadAccounts"
          />
          <n-select
            v-model:value="statusFilter"
            class="accounts-filter"
            :options="statusOptions"
          />
          <n-button :loading="loading" @click="loadAccounts">刷新</n-button>
        </div>
        <div v-if="accountsRefreshing" class="refresh-status" role="status" aria-live="polite">
          正在刷新账号列表，现有数据仍可查看。
        </div>
        <EmptyState v-if="loading && dataAvailable !== true" icon="⏳" title="账号加载中" description="正在读取账号与认证状态。" />
        <EmptyState v-else-if="dataAvailable === false" icon="⚠️" title="账号列表暂不可用" description="当前无法确认账号记录，不会把失败显示为空列表。">
          <template #actions><AppButton @click="loadAccounts">重新加载</AppButton></template>
        </EmptyState>
        <BaseTable v-else-if="dataAvailable === true" :columns="cols" :rows="rows" :row-class="rowClass">
          <template #account="{ row }"><button type="button" class="product-cell account-selector" :aria-label="`查看账号 ${row.name}`" @click="selectAccount(row.raw)"><img v-if="row.avatar" :src="row.avatar" class="avatar small" alt=""><span v-else class="avatar small avatar-img" aria-hidden="true"></span><span class="account-selector-copy"><strong>{{ row.name }}</strong><em>{{ row.tag }}</em></span></button></template>
          <template #status="{ row }"><Badge :type="row.statusType">{{ row.statusText }}</Badge></template>
          <template #cookie="{ row }"><Badge :type="row.cookieType">{{ row.cookie }}</Badge></template>
          <template #ws="{ row }"><span><i :class="['dot', row.wsConnected === true ? '' : (row.wsConnected === false ? 'red' : 'orange')] "></i>{{ row.ws }}</span></template>
          <template #op="{ row }">
            <button class="link" @click="selectAccount(row.raw)">详情</button>
            <button class="link" @click="refreshProfile(row.raw.id)">刷新资料</button>
            <button class="link" @click="openRescanModal(row.raw)">重新扫码</button>
            <button
              class="link"
              type="button"
              :disabled="isPolishBusy(row.raw)"
              :aria-busy="isPolishActionLoading(row.raw)"
              :title="itemPolishRetryGuidance(polishTaskFor(row.raw)) || polishTaskFor(row.raw)?.message || '对该账号当前所有在售商品执行真实闲鱼擦亮；结果未知时不会自动重试'"
              @click="handleItemPolish(row.raw)"
            >
              {{ polishButtonText(row.raw) }}
            </button>
            <button class="link" :disabled="isWsBusy(row.raw.id) || row.wsConnected == null || row.wsPending" @click="toggleWs(row.raw)">{{ isWsBusy(row.raw.id) ? '确认中...' : (row.wsPending ? '启动中' : (row.wsConnected === true ? '断开' : (row.wsConnected === false ? '连接' : '状态未知'))) }}</button>
            <button class="link danger-text" @click="removeAccount(row.raw.id)">删除</button>
          </template>
        </BaseTable>
        <Pagination v-if="dataAvailable === true" :total="total" :current="current" :page-size="pageSize" @page-change="goPage" />
      </section>
    </main>
    <aside class="accounts-side">
      <aside class="right-drawer account-detail-drawer">
  <div class="detail-title-row">
    <h3>账号详情</h3>
    <button
      class="detail-close"
      type="button"
      aria-label="关闭账号详情"
      @click="closeDetail"
    >
      ×
    </button>
  </div>

  <template v-if="selected">
    <!-- 账号基础信息 -->
    <section class="account-summary">
      <img
        v-if="selected.avatarUrl || selected.avatar"
        :src="selected.avatarUrl || selected.avatar"
        class="detail-avatar"
        alt=""
      >
      <div v-else class="detail-avatar avatar-fallback"></div>

      <div class="account-summary-main">
        <div class="account-name-row">
          <strong>{{ accountTitle(selected) }}</strong>
          <span
            v-if="isCurrentAccount(selected)"
            class="current-account-tag"
          >
            当前账号
          </span>
        </div>

        <div class="account-meta-line">
          UID：{{ selected.externalUid || selected.unb || selected.id || '-' }}
        </div>

        <div class="account-meta-line account-meta-split">
          <span>地区：{{ selected.province && selected.city ? `${selected.province} ${selected.city}` : (selected.ipLocation || selected.province || '-') }}</span>
          <i></i>
          <span>注册时间：{{ accountRegisterDate(selected) }}</span>
        </div>
      </div>

      <span :class="['online-state', { offline: selectedWs.connected === false, unknown: selectedWs.connected == null }]">
        <i></i>
        {{ selectedWs.connected === true ? '在线' : (selectedWs.connected === false ? '离线' : '状态未知') }}
      </span>
    </section>

    <!-- Cookie 状态警告 -->
    <div v-if="selected && accountCookieStatus(selected) === 0" class="cookie-warn-banner">
      <Icon name="help" />
      <span>{{ accountLoginHint(selected) }}</span>
    </div>
    <div v-else-if="selected && accountCookieStatus(selected) === 2" class="cookie-warn-banner cookie-expired">
      <Icon name="help" />
      <span>{{ accountLoginHint(selected) }}</span>
    </div>

    <section class="drawer-section diagnosis-card">
      <h4>授权与连接</h4>
      <div v-for="item in accountDiagnostics" :key="item.title" class="diagnosis-item" :class="item.level">
        <span><i></i>{{ item.title }}</span>
        <b>{{ item.text }}</b>
        <small>{{ item.tip }}</small>
      </div>
      <div class="diagnosis-actions">
        <button type="button" class="link" @click="refreshProfile(selected.id)">刷新资料</button>
        <button type="button" class="link" @click="openCookieEdit(selected)">更新登录凭证</button>
        <button type="button" class="link" @click="openRescanModal(selected)">重新扫码</button>
        <button type="button" class="link" :disabled="selectedWs.connected == null || selectedWsPending || isWsBusy(selected.id)" @click="toggleWs(selected)">{{ selectedWsPending ? '启动中' : (selectedWs.connected === true ? '断开连接' : (selectedWs.connected === false ? '启动连接' : '状态未知')) }}</button>
      </div>
    </section>

    <!-- 闲鱼主页资料（刷新资料后展示） -->
    <section v-if="selected.displayName || selected.followers != null || selected.soldCount != null" class="profile-stats-card">
      <h4>闲鱼主页资料</h4>

      <div v-if="selected.introduction" class="profile-intro">
        <span class="profile-intro-label">简介</span>
        <p>{{ selected.introduction }}</p>
      </div>

      <div class="profile-stats-grid">
        <div v-if="selected.followers != null" class="profile-stat-item">
          <b>{{ fmtNumber(selected.followers) }}</b>
          <span>粉丝</span>
        </div>
        <div v-if="selected.following != null" class="profile-stat-item">
          <b>{{ fmtNumber(selected.following) }}</b>
          <span>关注</span>
        </div>
        <div v-if="selected.soldCount != null" class="profile-stat-item">
          <b>{{ fmtNumber(selected.soldCount) }}</b>
          <span>已售</span>
        </div>
        <div v-if="selected.reviewNum != null" class="profile-stat-item">
          <b>{{ fmtNumber(selected.reviewNum) }}</b>
          <span>评价</span>
        </div>
      </div>

      <div class="profile-extra">
        <div v-if="selected.sellerLevel" class="profile-extra-item">
          <span>卖家等级</span>
          <b>{{ selected.sellerLevel }}</b>
        </div>
        <div v-if="selected.praiseRatio" class="profile-extra-item">
          <span>好评率</span>
          <b>{{ selected.praiseRatio }}</b>
        </div>
        <div v-if="selected.fishShopScore != null" class="profile-extra-item">
          <span>鱼小铺分数</span>
          <b>{{ selected.fishShopScore }}</b>
        </div>
        <div v-if="selected.fishShopUser" class="profile-extra-item">
          <span>鱼小铺</span>
          <b class="green-tag">已开通</b>
        </div>
      </div>
    </section>

    <section v-if="selectedPolishTask" class="drawer-section polish-task-section">
      <div class="polish-status-card" role="status">
        <div class="polish-status-head">
          <strong>商品擦亮任务</strong>
          <Badge :type="polishBadgeType(selectedPolishTask.status)">{{ polishButtonText(selected) }}</Badge>
        </div>
        <p>{{ selectedPolishTask.message }}</p>
        <small v-if="itemPolishRetryGuidance(selectedPolishTask)" class="polish-recovery warn">
          {{ itemPolishRetryGuidance(selectedPolishTask) }}
        </small>
        <div class="polish-summary">
          <span>进度 {{ selectedPolishTask.processed }}/{{ selectedPolishTask.total }}</span>
          <span>已确认 {{ selectedPolishTask.polished }}</span>
          <span>今日已擦亮 {{ selectedPolishTask.alreadyDone }}</span>
          <span>明确失败 {{ selectedPolishTask.failed }}</span>
          <span v-if="selectedPolishTask.unknown">未知 {{ selectedPolishTask.unknown }}</span>
        </div>
        <small v-if="selectedPolishPollMessage" class="polish-poll-message">{{ selectedPolishPollMessage }}</small>
        <ul v-if="selectedPolishTask.results?.length" class="polish-results">
          <li v-for="result in selectedPolishTask.results.slice(0, 8)" :key="result.goodsId">
            <span>{{ result.title || `商品 #${result.goodsId}` }}</span>
            <b :class="`result-${result.status}`">{{ itemPolishResultText(result.status) }}</b>
          </li>
        </ul>
        <ItemPolishUnknownReconcile
          :task="selectedPolishTask"
          :busy-goods-id="selectedPolishReconcileBusyGoodsId"
          :error-message="selectedPolishReconcileMessage"
          @reconcile="reconcileItemPolishTask"
        />
        <button
          v-if="itemPolishCanResume(selectedPolishTask) && !isPolishBusy(selected)"
          type="button"
          class="link"
          :aria-busy="isPolishActionLoading(selected)"
          @click="handleItemPolish(selected)"
        >
          {{ selectedPolishTask.status === 'needs_verification' ? '我已完成验证，继续原任务' : (['partial', 'failed'].includes(selectedPolishTask.status) ? '复用原任务处理明确未擦亮项' : '继续安全任务') }}
        </button>
        <small v-else-if="selectedPolishTask.status === 'unknown'" class="polish-recovery warn">
          请先在闲鱼 App 核对这些商品；系统不会自动重试未知结果。
        </small>
        <small v-else-if="selectedPolishTask.status === 'needs_verification'" class="polish-recovery warn">
          请先在闲鱼 App 完成安全验证，再回到账号页手动继续；系统不会自动重试。
        </small>
      </div>
    </section>
  </template>

  <div v-else class="empty-state detail-empty">
    请选择一个账号查看详情
  </div>
</aside>
    </aside>
  </div>

  <Teleport to="body">
    <div v-if="modal" class="modal-mask" @click.self="closeModal">
      <section v-if="modal==='scan'" class="xy-modal scan-modal account-scan-modal">
        <button class="modal-close" aria-label="关闭扫码登录" @click="closeModal"><Icon name="close" /></button>
        <header class="scan-modal-head">
          <span>闲鱼账号接入</span>
          <h2>{{ qr.mode === 'rescan' ? '重新扫码更新账号' : '扫码添加闲鱼账号' }}</h2>
          <p>{{ qrFlowHint }}</p>
        </header>
        <div class="scan-status-strip" :class="`is-${qrStatusTone}`" role="status" aria-live="polite">
          <i></i>
          <span>{{ qrStatusText(qr.status) }}</span>
          <b>{{ qr.polling ? '正在监听 APP 确认' : (qrReady ? '等待操作' : '等待二维码') }}</b>
        </div>
        <div class="scan-steps">
          <div class="scan-step" :class="{ active: qrReady }"><b>1</b><span>{{ qrReady ? '二维码已生成' : '等待生成二维码' }}</span></div>
          <i></i><div class="scan-step" :class="{active: ['scanned', 'confirmed'].includes(qr.status)}"><b>2</b><span>扫码确认</span></div>
          <i></i><div class="scan-step" :class="{active: qr.status==='confirmed'}"><b>3</b><span>{{ qr.mode === 'rescan' ? '更新账号凭证' : '自动添加账号' }}</span></div>
        </div>
        <div class="scan-main">
          <div>
            <div class="qr-box" :class="[`is-${qrStatusTone}`, { 'is-polling': qr.polling }]">
              <img v-if="qr.qrUrl" :src="qr.qrUrl" alt="闲鱼登录二维码">
              <div v-else class="qr-unavailable" role="status">
                <Icon :name="qrGenerationFailed ? 'warning' : 'refresh'" />
                <span>{{ qrGenerationFailed ? '二维码生成失败' : '尚未生成可扫码二维码' }}</span>
              </div>
              <span v-if="qr.loading" class="qr-loading"></span>
            </div>
            <p class="qr-tip" :class="`is-${qrStatusTone}`">{{ qr.message || '正在自动生成二维码，请稍候...' }}</p>
          </div>
          <div class="scan-guide">
            <h4>{{ qr.mode === 'rescan' ? '重新扫码流程' : '添加流程' }}</h4>
            <p>1. {{ qrReady ? '系统已生成真实二维码' : '点击生成并等待真实二维码返回' }}</p>
            <p>2. 使用闲鱼 App 扫码并确认登录</p>
            <p>3. {{ qr.mode === 'rescan' ? '系统会把新的登录凭证回写到当前账号并刷新状态' : '系统自动添加账号并刷新资料' }}</p>
            <div class="session-box">
              <h4>会话信息</h4>
              <div v-if="qr.accountId"><span>目标账号：</span><b>{{ selected?.nickname || selected?.displayName || selected?.externalUid || qr.accountId }}</b></div>
              <div><span>会话 ID：</span><b>{{ qr.sessionId || '-' }}</b></div>
              <div><span>当前状态：</span><b>{{ qrStatusText(qr.status) }}</b><button class="inline-link" @click="startQrLogin"><Icon name="refresh" /> 生成/刷新二维码</button></div>
              <div v-if="qr.verificationUrl"><span>安全验证：</span><b>待完成</b><a class="inline-link" :href="qr.verificationUrl" target="_blank" rel="noopener noreferrer"><Icon name="link" /> 打开验证页</a></div>
              <div><span>监听次数：</span><b>{{ qr.checkCount || 0 }}</b></div>
              <div><span>上次检测：</span><b>{{ qr.lastCheckedAt || '-' }}</b></div>
            </div>
          </div>
        </div>
        <div class="notice-box">
          <b><Icon name="help" /> 说明</b>
          <p>{{ qrReady ? '二维码已生成，可使用闲鱼 App 扫码登录。' : '当前没有可扫码二维码，请等待二维码生成成功后再扫码。' }}</p>
          <p>{{ qr.mode === 'rescan' ? '登录成功后会更新当前账号登录凭证，并重新同步该账号状态。' : '登录成功后将自动添加账号并刷新资料。' }}</p>
          <p>闲鱼 App 显示的登录地点由平台服务器的网络出口决定。若地点与预期不符，请取消扫码并联系平台负责人核验服务器区域。</p>
        </div>
        <div class="modal-actions"><AppButton @click="closeModal">取消</AppButton><AppButton type="primary" :loading="qr.loading" :disabled="qr.loading" @click="startQrLogin">{{ qrReady ? '刷新二维码' : '生成二维码' }}</AppButton></div>
      </section>

      <section v-if="modal==='manual'" class="xy-modal manual-modal">
        <button class="modal-close" @click="closeModal"><Icon name="close" /></button>
        <h2>手动添加账号</h2>
        <label class="field-label">账号备注 <span>可选</span></label>
        <div class="modal-input-wrap"><input v-model="manual.accountNote" placeholder="请输入备注名称（可选，不填写显示闲鱼昵称）"><em>{{ manual.accountNote.length }}/50</em></div>
        <label class="field-label required">登录 Cookie <span>必填</span></label>
        <textarea v-model="manual.cookie" class="cookie-area" placeholder="请输入闲鱼账号 Cookie 字符串"></textarea>

        <!-- Cookie 解析预览 -->
        <div v-if="manualCookieParsed" class="cookie-parse-preview">
          <div v-if="!manualCookieParsed.validation.valid" class="cookie-parse-error">
            <Icon name="help" /> {{ manualCookieParsed.validation.error }}
          </div>
          <div v-if="manualCookieParsed.validation.valid" class="cookie-parse-fields">
            <div class="cookie-parse-header">
              <span>解析结果</span>
              <em>共 {{ manualCookieParsed.keyFields.parsedCount }} 个字段</em>
            </div>
            <div class="cookie-field-grid">
              <div class="cookie-field-item" :class="{ missing: !manualCookieParsed.keyFields.unb }">
                <label>unb（身份标识）<span class="required-mark">*必填</span></label>
                <code>{{ manualCookieParsed.masked.unb }}</code>
              </div>
              <div class="cookie-field-item" :class="{ missing: !manualCookieParsed.keyFields.mH5Tk }">
                <label>_m_h5_tk（签名令牌）</label>
                <code>{{ manualCookieParsed.masked.mH5Tk }}</code>
              </div>
              <div v-if="manualCookieParsed.keyFields.userId" class="cookie-field-item">
                <label>用户 ID（user_id）</label>
                <code>{{ manualCookieParsed.masked.userId }}</code>
              </div>
            </div>
            <div v-if="manualCookieParsed.validation.warning" class="cookie-parse-warning">
              <Icon name="help" /> {{ manualCookieParsed.validation.warning }}
            </div>
          </div>
        </div>

        <div v-if="manualError" class="input-error">{{ manualError }}</div>
        <div class="modal-hint"><Icon name="help" /> 提交后由系统解析并保存账号信息</div>
        <div class="usage-box">
          <h4><Icon name="map" /> 使用说明</h4>
          <div><span><Icon name="shield" /></span>提交前会先校验登录 Cookie 格式</div>
          <div><span><Icon name="shield" /></span>添加成功后自动刷新账号列表</div>
          <div><span><Icon name="shield" /></span>请勿把登录凭证发送到非授权渠道或第三方页面</div>
        </div>
        <div class="manual-actions"><AppButton @click="closeModal">取消</AppButton><AppButton type="primary" :disabled="manualCookieParsed && !manualCookieParsed.validation.valid" @click="submitManual">{{ submitting ? '添加中...' : '添加' }}</AppButton></div>
      </section>

      <section v-if="modal==='cookieEdit'" class="xy-modal manual-modal">
        <button class="modal-close" @click="closeModal"><Icon name="close" /></button>
        <h2>编辑账号登录凭证</h2>
        <div class="edit-account-info">
          <span>账号：</span><b>{{ selected?.nickname || selected?.displayName || selected?.externalUid || selected?.unb || selected?.id }}</b>
          <span v-if="selected?.unb" class="current-unb-tag">UNB: {{ maskValue(selected.unb) }}</span>
        </div>
        <label class="field-label required">登录 Cookie <span>必填</span></label>
        <textarea v-model="cookieEdit.cookie" class="cookie-area" placeholder="粘贴由可信浏览器会话导出的闲鱼账号 Cookie 字符串"></textarea>

        <!-- Cookie 解析预览 -->
        <div v-if="cookieEditParsed" class="cookie-parse-preview">
          <!-- 格式校验错误 -->
          <div v-if="!cookieEditParsed.validation.valid" class="cookie-parse-error">
            <Icon name="help" /> {{ cookieEditParsed.validation.error }}
          </div>

          <!-- 身份校验警告（防串号） -->
          <div v-if="cookieEditParsed.validation.valid && !cookieEditParsed.identity.valid" class="cookie-parse-error cookie-identity-error">
            <Icon name="shield" /> {{ cookieEditParsed.identity.error }}
          </div>

          <!-- 解析结果展示 -->
          <div v-if="cookieEditParsed.validation.valid" class="cookie-parse-fields">
            <div class="cookie-parse-header">
              <span>解析结果</span>
              <em>共 {{ cookieEditParsed.keyFields.parsedCount }} 个字段</em>
            </div>
            <div class="cookie-field-grid">
              <div class="cookie-field-item" :class="{ missing: !cookieEditParsed.keyFields.unb }">
                <label>unb（身份标识）<span class="required-mark">*必填</span></label>
                <code>{{ cookieEditParsed.masked.unb }}</code>
              </div>
              <div class="cookie-field-item" :class="{ missing: !cookieEditParsed.keyFields.mH5Tk }">
                <label>_m_h5_tk（签名令牌）</label>
                <code>{{ cookieEditParsed.masked.mH5Tk }}</code>
              </div>
              <div v-if="cookieEditParsed.keyFields.userId" class="cookie-field-item">
                <label>用户 ID（user_id）</label>
                <code>{{ cookieEditParsed.masked.userId }}</code>
              </div>
              <div v-if="cookieEditParsed.keyFields.loginToken" class="cookie-field-item">
                <label>登录令牌</label>
                <code>{{ cookieEditParsed.masked.loginToken }}</code>
              </div>
            </div>
            <!-- 警告信息 -->
            <div v-if="cookieEditParsed.validation.warning" class="cookie-parse-warning">
              <Icon name="help" /> {{ cookieEditParsed.validation.warning }}
            </div>
          </div>
        </div>

        <div v-if="cookieEditError" class="input-error">{{ cookieEditError }}</div>
        <div class="modal-hint"><Icon name="help" /> 提交后自动识别关键身份字段并重置登录凭证状态。保存后建议重新启动实时连接。</div>
        <div class="usage-box">
          <h4><Icon name="map" /> 使用说明</h4>
          <div><span><Icon name="shield" /></span>遇到"被挤爆"滑块验证时需要更换登录 Cookie</div>
          <div><span><Icon name="shield" /></span>请仅从本人可控的闲鱼登录环境复制 Cookie，确认账号一致后再保存</div>
          <div><span><Icon name="shield" /></span>请勿把登录凭证发送到非授权渠道或第三方页面</div>
        </div>
        <div class="manual-actions"><AppButton @click="closeModal">取消</AppButton><AppButton type="primary" :disabled="cookieEditSubmitting || (cookieEditParsed && !cookieEditParsed.validation.valid)" @click="submitCookieEdit">{{ cookieEditSubmitting ? '保存中...' : '保存' }}</AppButton></div>
      </section>

      <section v-if="modal==='autoRate'" class="xy-modal manual-modal auto-rate-modal">
        <button class="modal-close" @click="closeModal"><Icon name="close" /></button>
        <h2>自动评价</h2>
        <div class="edit-account-info">
          <span>账号：</span><b>{{ selected?.nickname || selected?.displayName || selected?.externalUid || selected?.id || '-' }}</b>
        </div>
        <label class="auto-rate-toggle">
          <input v-model="autoRateForm.enabled" type="checkbox" :disabled="!autoRateLoaded">
          <span>启用该账号的自动评价</span>
        </label>
        <label class="field-label">评价方式</label>
        <select v-model="autoRateForm.rateType" class="input large" :disabled="!autoRateLoaded">
          <option value="text">固定文本</option>
          <option value="api">外部 API</option>
        </select>
        <template v-if="autoRateForm.rateType === 'text'">
          <label class="field-label required">评价内容 <span>必填</span></label>
          <textarea
            v-model="autoRateForm.textContent"
            class="cookie-area"
            :disabled="!autoRateLoaded"
            placeholder="请输入默认评价内容，例如：交易顺利，感谢支持。"
          ></textarea>
        </template>
        <template v-else>
          <label class="field-label required">API 地址 <span>必填</span></label>
          <input
            v-model="autoRateForm.apiUrl"
            class="input large"
            :disabled="!autoRateLoaded"
            placeholder="https://api.company.com/xianyu/auto-rate"
          >
          <label class="field-label">兜底评价内容 <span>可选</span></label>
          <textarea
            v-model="autoRateForm.textContent"
            class="cookie-area"
            :disabled="!autoRateLoaded"
            placeholder="当外部服务不可用时，可回退到这段文本。"
          ></textarea>
        </template>
        <div v-if="autoRateError" class="input-error">{{ autoRateError }}</div>
        <div class="modal-hint"><Icon name="help" /> 当前先保存账号级自动评价配置，后续自动执行链路会直接复用这里的参数。</div>
        <div class="manual-actions">
          <AppButton @click="closeModal">取消</AppButton>
          <AppButton type="primary" :disabled="!autoRateLoaded || autoRateSaving" @click="saveAutoRateConfig">{{ autoRateSaving ? '保存中...' : '保存' }}</AppButton>
        </div>
      </section>

      <section v-if="modal==='strategy'" class="xy-modal manual-modal auto-rate-modal">
        <button class="modal-close" @click="closeModal"><Icon name="close" /></button>
        <h2>消息等待 / 求小红花</h2>
        <div class="edit-account-info">
          <span>账号：</span><b>{{ selected?.nickname || selected?.displayName || selected?.externalUid || selected?.id || '-' }}</b>
        </div>
        <label class="field-label required">相同消息等待时间（秒） <span>0-86400</span></label>
        <input
          v-model="strategyForm.messageExpireTime"
          class="input large"
          type="number"
          min="0"
          max="86400"
          placeholder="3600"
          :disabled="!strategyLoaded"
        >
        <label class="auto-rate-toggle">
          <input v-model="strategyForm.scheduledRedelivery" type="checkbox" :disabled="!strategyLoaded">
          <span>开启该账号的定时补发货</span>
        </label>
        <label class="auto-rate-toggle">
          <input v-model="strategyForm.autoPolish" type="checkbox" :disabled="!strategyLoaded">
          <span>开启该账号的自动擦亮商品</span>
        </label>
        <label class="auto-rate-toggle">
          <input v-model="strategyForm.requestRedFlower" type="checkbox" :disabled="!strategyLoaded">
          <span>开启该账号的求小红花（订单完成后主动请求买家评价）</span>
        </label>
        <div v-if="strategyError" class="input-error">{{ strategyError }}</div>
        <div class="modal-hint"><Icon name="help" /> 该配置会作为账号级策略保存，后续消息等待、定时补发货、商品擦亮与求小红花会直接复用这里的参数。</div>
        <div class="manual-actions">
          <AppButton @click="closeModal">取消</AppButton>
          <AppButton type="primary" :disabled="!strategyLoaded || strategySaving" @click="saveStrategyConfig">{{ strategySaving ? '保存中...' : '保存' }}</AppButton>
        </div>
      </section>

      <section v-if="modal==='unifiedConfig'" class="xy-modal manual-modal auto-rate-modal">
        <button class="modal-close" @click="closeModal"><Icon name="close" /></button>
        <h2>批量设置 / 统一应用</h2>
        <div class="edit-account-info">
          <span>基准账号：</span><b>{{ selected?.nickname || selected?.displayName || selected?.externalUid || selected?.id || '-' }}</b>
        </div>
        <p class="modal-subtitle">以当前选中的账号为基准，将自动评价、消息等待等配置快速应用到当前列表中的账号。</p>
        <div class="modal-hint"><Icon name="help" /> 当前将对 {{ accounts.length }} 个账号执行批量操作；如只想作用于部分账号，请先通过搜索缩小列表范围。</div>
        <div v-if="unifiedConfigError" class="input-error">{{ unifiedConfigError }}</div>
        <div v-if="unifiedConfigSuccess" class="global-notice success unified-config-success">{{ unifiedConfigSuccess }}</div>
        <div class="batch-auth-grid">
          <button type="button" class="batch-auth-card" :disabled="unifiedConfigBusy" @click="applyCurrentAutoRateToVisibleAccounts">
            <strong>同步自动评价</strong>
            <span>将当前账号的自动评价配置应用到当前列表中的账号。</span>
          </button>
          <button type="button" class="batch-auth-card" :disabled="unifiedConfigBusy" @click="applyCurrentStrategyToVisibleAccounts">
            <strong>同步消息等待</strong>
            <span>将消息等待、求小红花等策略配置同步到当前列表中的账号。</span>
          </button>
          <button type="button" class="batch-auth-card" :disabled="unifiedConfigBusy" @click="runBatchAuthCheckForVisibleAccounts">
            <strong>统一登录校验</strong>
            <span>批量检查当前列表账号的登录状态、登录凭证和会话有效性。</span>
          </button>
        </div>
        <div v-if="unifiedConfigBusy" class="modal-hint unified-config-progress"><Icon name="help" /> 正在执行：{{ unifiedConfigTaskText }}</div>
        <div class="manual-actions">
          <AppButton @click="closeModal">关闭</AppButton>
        </div>
      </section>

      <section v-if="modal==='confirmDelete'" class="xy-modal confirm-delete-modal">
        <button class="modal-close" @click="closeModal"><Icon name="close" /></button>
        <div class="confirm-delete-icon">
          <Icon name="warning" />
        </div>
        <h2>确认删除该闲鱼账号？</h2>
        <p class="confirm-delete-desc">删除后将移除该账号的系统连接、资料和后续自动化配置关联，请确认已不再运营该账号。</p>
        <div class="confirm-delete-actions">
          <AppButton @click="closeModal">取消</AppButton>
          <AppButton type="danger" @click="executeDelete">确认删除</AppButton>
        </div>
      </section>
    </div>
  </Teleport>
</template>
<script>
export function createItemPolishPageSingleFlight({ onPhaseChange = () => {} } = {}) {
  const flights = new Map()

  function notify(scopeKey, phase) {
    onPhaseChange(scopeKey, phase)
  }

  function clear(scopeKey, expectedFlight) {
    if (flights.get(scopeKey) !== expectedFlight) return
    flights.delete(scopeKey)
    notify(scopeKey, '')
  }

  function phaseFor(scopeKey) {
    return flights.get(String(scopeKey || ''))?.phase || ''
  }

  function requestDefinitelyNotIssued(error) {
    return error?.polishConflict
      || error?.data?.requestIssued === false
      || error?.data?.platformRequestIssued === false
      || (error?.data?.status === 'failed' && error?.data?.retrySafe === true)
  }

  function run(rawScopeKey, { confirm, submit, taskAfterFailure = () => null } = {}) {
    const scopeKey = String(rawScopeKey || '')
    if (!scopeKey) return Promise.reject(new Error('item polish scope key is required'))
    const active = flights.get(scopeKey)
    if (active) return active.promise

    const flight = { phase: 'confirming', promise: null }
    flights.set(scopeKey, flight)
    notify(scopeKey, flight.phase)
    flight.promise = (async () => {
      let requestIssued = false
      try {
        const confirmed = await confirm()
        if (!confirmed) {
          clear(scopeKey, flight)
          return null
        }
        flight.phase = 'submitting'
        notify(scopeKey, flight.phase)
        requestIssued = true
        const task = await submit()
        clear(scopeKey, flight)
        return task
      } catch (error) {
        const persistedTask = taskAfterFailure()
        if (!requestIssued || requestDefinitelyNotIssued(error) || persistedTask) {
          clear(scopeKey, flight)
        } else {
          flight.phase = 'unknown'
          notify(scopeKey, flight.phase)
        }
        throw error
      }
    })()
    return flight.promise
  }

  return { phaseFor, run }
}
</script>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { NButton, NInput, NSelect, NSpace, NTag } from 'naive-ui'
import {
  AlertCircleOutline,
  KeyOutline,
  LinkOutline,
  PeopleOutline,
  ShieldCheckmarkOutline,
} from '@vicons/ionicons5'
import BaseTable from '../components/BaseTable.vue'; import Badge from '../components/Badge.vue'; import AppButton from '../components/AppButton.vue'; import Icon from '../components/Icon.vue'; import Pagination from '../components/Pagination.vue'; import EmptyState from '../components/EmptyState.vue'
import BusinessMetricCard from '../components/business/BusinessMetricCard.vue'
import BusinessSection from '../components/business/BusinessSection.vue'
import BusinessStatusStrip from '../components/business/BusinessStatusStrip.vue'
import { checkAccountAuth, deleteAccount, getAccounts, createAccountByCookie, refreshAccountProfile, updateAccountCookie, getAccountAutoRateConfig, saveAccountAutoRateConfig, getAccountStrategyConfig, saveAccountStrategyConfig } from '../api/accounts.js'
import { startWebSocket, stopWebSocket, websocketStatus } from '../api/websocket.js'
import { useDebouncedRef } from '../composables/useDebouncedRef.js'
import { useItemPolish } from '../composables/useItemPolish.js'
import ItemPolishConflictCard from '../components/ItemPolishConflictCard.vue'
import ItemPolishUnknownReconcile from '../components/ItemPolishUnknownReconcile.vue'
import { generateQrLogin, getQrLoginStatus, cleanupQrLogin } from '../api/qrlogin.js'
import { accountName } from '../utils/format.js'
import { accountAuthState, accountCookieBadgeType, accountCookieLabel, accountCookieStatus, accountLoginHint } from '../utils/accountAuth.js'
import { extractKeyFields, maskKeyFields, validateCookie, checkIdentity, maskValue } from '../utils/cookie.js'
import { confirmAction } from '../utils/confirmAction.js'
import { createLatestRequestGuard, listRefreshRequestConfig } from '../utils/latestRequest.js'
import {
  itemPolishBlocksRetry,
  itemPolishCanStartNextBusinessDay,
  itemPolishCanResume,
  itemPolishResultText,
  itemPolishRetryGuidance,
  itemPolishScopeKey,
  itemPolishStatusText,
} from '../utils/itemPolishState.js'

const modal = ref('')
const manual = reactive({ accountNote:'', cookie:'' })
const manualError = ref('')
const submitting = ref(false)
const loading = ref(false)
const dataAvailable = ref(null)
const error = ref('')
const accountListWarning = ref('')
const keyword = ref('')
const debouncedKeyword = useDebouncedRef(keyword, 300)
const statusFilter = ref('all')
const accounts = ref([])
const current = ref(1)
const pageSize = ref(20)
const total = ref(0)
const selected = ref(null)
const selectedId = ref(null)
const wsMap = reactive({})
const wsBusyMap = reactive({})
const selectedWs = computed(() => wsMap[selected.value?.id] || {})
const accountsRefreshing = computed(() => loading.value && dataAvailable.value === true)
const accountActionHint = computed(() => {
  if (loading.value) return dataAvailable.value === true
    ? '账号列表正在后台刷新，当前数据仍可查看。'
    : '账号列表正在首次加载，请稍候。'
  if (dataAvailable.value === false) return '账号列表加载失败，请先刷新账号。'
  if (selected.value) return `当前选中：${accountTitle(selected.value)}`
  return '可扫码接入闲鱼账号、手动添加凭证，或刷新账号与连接状态。'
})
const accountsRequestGuard = createLatestRequestGuard()
const WS_START_PHASES = new Set(['starting', 'refresh_token', 'connecting', 'registering', 'syncing', 'accepted', 'pending', 'recovering'])
const selectedWsPending = computed(() => isWsPending(selected.value?.id))
let qrTimer = null
const qr = reactive({
  loading: false,
  polling: false,
  sessionId: '',
  qrUrl: '',
  status: '',
  message: '',
  mode: 'create',
  accountId: null,
  verificationUrl: '',
  checkCount: 0,
  lastCheckedAt: ''
})
const qrReady = computed(() => Boolean(qr.sessionId && qr.qrUrl))
const qrGenerationFailed = computed(() => qr.status === 'error')
const qrStatusTone = computed(() => {
  const status = normalizeQrStatus(qr.status)
  if (status === 'confirmed') return 'success'
  if (['scanned', 'verification_required'].includes(status)) return 'active'
  if (['expired', 'failed', 'cancelled', 'error'].includes(status)) return 'danger'
  if (qr.loading || qr.polling || status === 'new') return 'pending'
  return 'idle'
})
const qrFlowHint = computed(() => {
  const status = normalizeQrStatus(qr.status)
  if (qr.loading) return '正在向服务端申请真实扫码二维码。'
  if (status === 'scanned') return '已检测到扫码，请在闲鱼 App 内点击确认登录。'
  if (status === 'confirmed') return 'App 已确认，系统正在同步账号登录凭证。'
  if (['expired', 'failed', 'cancelled', 'error'].includes(status)) return '本次扫码会话不可继续，请刷新二维码后重试。'
  if (status === 'verification_required') return '闲鱼要求额外安全验证，请继续在 App 完成验证，网页会自动同步结果。'
  if (qr.polling) return '网页正在监听扫码状态；如果 App 已确认但长时间无变化，请刷新二维码重新拉起会话。'
  return qrReady.value ? '二维码已生成，等待闲鱼 App 扫码。' : '打开弹窗后会自动生成二维码。'
})
const qrSuccessMsg = ref('')
const cookieEdit = reactive({ accountId: null, cookie: '' })
const cookieEditError = ref('')
const cookieEditSubmitting = ref(false)
const batchAuthError = ref('')
const batchAuthSuccess = ref('')

// 自动评价配置
const autoRateSaving = ref(false)
const autoRateError = ref('')
const autoRateLoaded = ref(false)
const autoRateForm = reactive({ enabled: false, rateType: 'text', textContent: '', apiUrl: '' })

// 消息等待策略配置
const strategySaving = ref(false)
const strategyError = ref('')
const strategyLoaded = ref(false)
const strategyForm = reactive({ messageExpireTime: 3600, scheduledRedelivery: false, autoPolish: false, requestRedFlower: false })

// 批量设置统一配置
const unifiedConfigBusy = ref(false)
const unifiedConfigError = ref('')
const unifiedConfigSuccess = ref('')
const unifiedConfigTaskText = ref('')
const pendingDeleteId = ref(null)     // 待删除的账号ID
const polishNotice = reactive({ type: '', text: '' })
const polishConflictAccountId = ref(null)
const {
  submit: submitItemPolish,
  restore: restoreItemPolish,
  taskFor: storedPolishTaskFor,
  pollMessageFor: polishPollMessageFor,
  conflictFor: polishConflictFor,
  refreshConflict: refreshPolishConflict,
  conflictRefreshingFor: polishConflictRefreshingFor,
  conflictRefreshMessageFor: polishConflictRefreshMessageFor,
  clearAllConflicts: clearAllPolishConflicts,
  reconcile: reconcilePolishTask,
  reconcilingGoodsIdFor: polishReconcilingGoodsIdFor,
  reconcileMessageFor: polishReconcileMessageFor,
} = useItemPolish()
const selectedPolishTask = computed(() => selected.value?.id ? storedPolishTaskFor(selected.value.id) : null)
const selectedPolishPollMessage = computed(() => selected.value?.id ? polishPollMessageFor(selected.value.id) : '')
const activePolishConflict = computed(() => polishConflictAccountId.value ? polishConflictFor(polishConflictAccountId.value) : null)
const activePolishConflictRefreshing = computed(() => polishConflictAccountId.value ? polishConflictRefreshingFor(polishConflictAccountId.value) : false)
const activePolishConflictRefreshMessage = computed(() => polishConflictAccountId.value ? polishConflictRefreshMessageFor(polishConflictAccountId.value) : '')
const selectedPolishReconcileBusyGoodsId = computed(() => selected.value?.id ? polishReconcilingGoodsIdFor(selected.value.id) : 0)
const selectedPolishReconcileMessage = computed(() => selected.value?.id ? polishReconcileMessageFor(selected.value.id) : '')
const POLISH_BUSY_TASK_STATUSES = new Set(['pending', 'running', 'unknown'])
const polishFlightPhases = reactive({})
const polishSingleFlight = createItemPolishPageSingleFlight({
  onPhaseChange(scopeKey, phase) {
    if (phase) polishFlightPhases[scopeKey] = phase
    else delete polishFlightPhases[scopeKey]
  },
})

// Cookie 编辑弹窗 - 实时解析预览
const cookieEditParsed = computed(() => {
  if (!cookieEdit.cookie.trim()) return null
  const validation = validateCookie(cookieEdit.cookie)
  const keyFields = extractKeyFields(cookieEdit.cookie)
  const masked = maskKeyFields(keyFields)
  // 身份校验：与当前选中账号的 unb 对比
  const identity = selected.value
    ? checkIdentity(keyFields.unb, selected.value)
    : { valid: true, error: null, unbChanged: false }
  return { validation, keyFields, masked, identity }
})

// 手动添加账号弹窗 - 实时解析预览
const manualCookieParsed = computed(() => {
  if (!manual.cookie.trim()) return null
  const validation = validateCookie(manual.cookie)
  const keyFields = extractKeyFields(manual.cookie)
  const masked = maskKeyFields(keyFields)
  return { validation, keyFields, masked }
})

function accountTitle(account){ return accountName(account) }
function accountStatus(status){ return ({ 1:'正常', '-1':'需手机验证', '-2':'需人机验证' }[status] || '未知') }

function accountRegisterDate(account) {
  const value =
    account?.registerTime ||
    account?.createdTime ||
    account?.createTime

  if (!value) return '-'

  return String(value)
    .replace('T', ' ')
    .slice(0, 10)
}

function fmtNumber(num) {
  if (num == null) return '-'
  if (num >= 10000) {
    return (num / 10000).toFixed(1).replace(/\.0$/, '') + '万'
  }
  return String(num)
}

function isCurrentAccount(account) {
  return (
    account?.isCurrentAccount === true ||
    account?.current === true ||
    account?.id === accounts.value[0]?.id
  )
}

function closeDetail() {
  clearAllPolishConflicts()
  polishConflictAccountId.value = null
  setPolishNotice('', '')
  selected.value = null
}

function polishTaskFor(account) {
  return account?.id ? storedPolishTaskFor(account.id) : null
}

function polishScopeKeyFor(account) {
  return itemPolishScopeKey(account?.id)
}

function polishFlightPhaseFor(account) {
  return polishFlightPhases[polishScopeKeyFor(account)] || ''
}

function isPolishReconciling(account) {
  return Boolean(account?.id && polishReconcilingGoodsIdFor(account.id))
}

function isPolishBusy(account) {
  const task = polishTaskFor(account)
  return Boolean(
    polishFlightPhaseFor(account)
      || POLISH_BUSY_TASK_STATUSES.has(String(task?.status || ''))
      || isPolishReconciling(account)
      || itemPolishBlocksRetry(task)
      || (account?.id && polishConflictFor(account.id)),
  )
}

function isPolishActionLoading(account) {
  return ['confirming', 'submitting'].includes(polishFlightPhaseFor(account)) || isPolishReconciling(account)
}

function polishButtonText(account) {
  const phase = polishFlightPhaseFor(account)
  if (phase === 'confirming') return '确认中...'
  if (phase === 'submitting') return '提交中...'
  if (phase === 'unknown') return '结果待核对'
  if (isPolishReconciling(account)) return '核对结果中...'
  const task = polishTaskFor(account)
  if (task?.status === 'pending') {
    return task.recovery === 'resume_task' ? '提交待确认' : '等待执行'
  }
  return task ? itemPolishStatusText(task) : '一键擦亮'
}

function polishBadgeType(status) {
  return {
    pending: 'orange',
    running: 'blue',
    completed: 'green',
    partial: 'orange',
    failed: 'red',
    needs_verification: 'orange',
    unknown: 'gray',
  }[status] || 'gray'
}

function setPolishNotice(type, text) {
  polishNotice.type = type
  polishNotice.text = text
}

async function handleItemPolish(account) {
  if (!account?.id || isPolishBusy(account)) return
  if (Number(selected.value?.id || 0) !== Number(account.id)) selectAccount(account)
  const requestedAccountId = Number(account.id)
  if (Number(polishConflictAccountId.value || 0) !== requestedAccountId) {
    clearAllPolishConflicts()
    polishConflictAccountId.value = requestedAccountId
    setPolishNotice('', '')
  }
  const existingConflict = polishConflictFor(requestedAccountId)
  if (existingConflict) {
    setPolishNotice(
      'warn',
      existingConflict.existingTask?.status === 'unknown'
        ? '既有任务结果未知，当前继续禁止重试或重新提交；请只刷新冲突卡片并在闲鱼 App 核对。'
        : '该账号仍有既有任务冲突；请使用冲突卡片只读刷新状态，不要重复提交。',
    )
    return
  }
  const authState = accountAuthState(account)
  if (authState !== true) {
    setPolishNotice(
      authState === false ? 'error' : 'warn',
      authState === false
        ? '账号登录状态不可用，请先重新扫码或更新登录凭证，再执行擦亮。'
        : '账号登录状态尚未确认，请先点击“登录验证”。',
    )
    return
  }
  const currentTask = polishTaskFor(account)
  if (itemPolishBlocksRetry(currentTask)) {
    const retryGuidance = itemPolishRetryGuidance(currentTask)
    setPolishNotice(
      'warn',
      retryGuidance || (currentTask.status === 'unknown'
        ? '上次平台结果未知，请先在闲鱼 App 核对逐项结果；系统不会自动或手动重复提交该未知任务。'
        : '闲鱼要求完成安全验证。请先在闲鱼 App 验证，当前页面不会自动重试。'),
    )
    return
  }
  const isResume = itemPolishCanResume(currentTask)
  const isVerificationResume = currentTask?.status === 'needs_verification'
  const isNextBusinessDayTask = itemPolishCanStartNextBusinessDay(currentTask)
  const confirmation = isNextBusinessDayTask
    ? {
        title: '新建次日擦亮任务？',
        description: `${itemPolishRetryGuidance(currentTask)} 本次提交会创建新的任务和安全凭证，绝不会复用昨日终态。`,
        confirmText: '新建任务并擦亮',
      }
    : {
        title: isVerificationResume ? '确认已完成闲鱼安全验证？' : (isResume ? '继续安全擦亮任务？' : '确认一键擦亮在售商品？'),
        description: isVerificationResume
          ? '仅当你已在闲鱼 App 完成安全验证时继续。系统会复用原任务和原范围，不会创建新任务。'
          : isResume
          ? '将复用原任务和原商品范围，只恢复明确可安全执行的操作项；未知结果不会重试。'
          : '系统会先记录任务和逐项操作，再提交闲鱼真实擦亮请求。请求超时或中断将标记为结果未知并停止自动重试。',
        confirmText: isVerificationResume ? '我已完成验证，继续原任务' : (isResume ? '继续原任务' : '开始擦亮'),
      }
  try {
    const task = await polishSingleFlight.run(polishScopeKeyFor(account), {
      confirm: () => confirmAction(confirmation),
      submit: () => submitItemPolish({
        accountId: account.id,
        forceNew: currentTask?.status === 'completed',
      }),
      taskAfterFailure: () => polishTaskFor(account),
    })
    if (!task) return
    setPolishNotice(
      task.status === 'completed' ? 'success' : 'info',
      task.message,
    )
  } catch (requestError) {
    const preserved = polishTaskFor(account)
    const resultUnknown = polishFlightPhaseFor(account) === 'unknown'
    setPolishNotice(
      resultUnknown || requestError?.timeout || requestError?.code === 'NETWORK_ERROR' ? 'warn' : 'error',
      resultUnknown
        ? '擦亮请求是否已提交尚未确认，当前任务已锁定。请先在闲鱼 App 核对并刷新任务状态，系统不会重复提交。'
        : requestError?.polishConflict?.message || preserved?.message || requestError?.message || '擦亮任务提交失败，请检查账号状态后重试。',
    )
  }
}

async function refreshActivePolishConflict() {
  if (!polishConflictAccountId.value) return
  await refreshPolishConflict(polishConflictAccountId.value)
}

async function reconcileItemPolishTask({ goodsId, outcome }) {
  if (!selected.value?.id) return
  try {
    await reconcilePolishTask({ accountId: selected.value.id, goodsId, outcome })
    setPolishNotice(
      'success',
      outcome === 'confirmed_not_polished'
        ? '该商品已记录为今天未擦亮。为防迟到请求重复操作，本日不再自动重试，次日可新建任务。'
        : '该商品的人工核对结论已记录，任务状态已更新。',
    )
  } catch {
    setPolishNotice('error', '人工核对结论保存失败；原任务快照已保留，可在网络恢复后重试当前这一项。')
  }
}


const accountDiagnostics = computed(() => {
  const a = selected.value || {}
  const ws = selectedWs.value || {}
  const authState = accountAuthState(a)
  const verify = a.status === -1 || a.status === -2
  const accountStateKnown = a.status !== undefined && a.status !== null
  return [
    {
      title: '登录凭证状态',
      level: authState === true ? 'ok' : (authState === false ? 'danger' : 'warn'),
      text: accountCookieLabel(a),
      tip: authState === true ? '系统已确认登录凭证可用。' : accountLoginHint(a)
    },
    {
      title: '安全验证',
      level: !accountStateKnown || verify ? 'warn' : 'ok',
      text: !accountStateKnown ? '状态未知' : (verify ? accountStatus(a.status) : '无需处理'),
      tip: !accountStateKnown ? '账号状态尚未加载，请刷新后再执行敏感操作。' : (verify ? '请先在闲鱼完成手机/人机验证，再回到系统刷新。' : '当前账号无需额外验证。')
    },
    {
      title: '消息通道',
      level: ws.connected === true ? 'ok' : 'warn',
      text: ws.connected === true ? '实时连接在线' : (ws.connected === false ? (isWsPending(a.id) ? '启动中' : '未连接') : '状态未知'),
      tip: ws.connected === true ? '系统已确认消息通道在线。' : (ws.connected === false ? '自动回复前请启动并等待连接确认。' : '暂未确认连接状态，当前不会按离线处理。')
    }
  ]
})

function resetQrState() {
  qr.loading = false
  qr.polling = false
  qr.sessionId = ''
  qr.qrUrl = ''
  qr.status = ''
  qr.message = ''
  qr.mode = 'create'
  qr.accountId = null
  qr.verificationUrl = ''
  qr.checkCount = 0
  qr.lastCheckedAt = ''
}

function normalizeQrStatus(status) {
  const value = String(status || '').trim().toLowerCase()
  return ({
    scaned: 'scanned',
    scanning: 'scanned',
    scanned: 'scanned',
    confirmed: 'confirmed',
    success: 'confirmed',
    new: 'new',
    pending: 'new',
    waiting: 'new',
    expired: 'expired',
    cancel: 'cancelled',
    canceled: 'cancelled',
    cancelled: 'cancelled',
    failed: 'failed',
    error: 'error',
    verification: 'verification_required',
    verification_required: 'verification_required'
  })[value] || value
}

function qrStatusText(status) {
  return ({
    new: '等待扫码',
    scanned: '已扫码，待确认',
    confirmed: '已确认',
    expired: '已过期',
    cancelled: '已取消',
    failed: '失败',
    error: '异常',
    verification_required: '需要安全验证'
  })[normalizeQrStatus(status)] || (status || '-')
}

function qrStatusMessage(status, fallback = '') {
  return fallback || ({
    new: '请使用闲鱼 App 扫码登录。',
    scanned: '已扫码，请在闲鱼 App 点击确认登录。',
    confirmed: '扫码已确认，正在同步账号登录凭证。',
    expired: '二维码已过期，请刷新二维码后重新扫码。',
    cancelled: '本次扫码登录已取消，请刷新二维码后重试。',
    failed: '扫码登录失败，请刷新二维码后重试。',
    error: '扫码登录状态异常，请刷新二维码后重试。',
    verification_required: '扫码已确认，闲鱼要求额外安全验证。请继续在闲鱼 App 内完成验证，网页会自动同步结果。'
  })[normalizeQrStatus(status)] || '正在确认扫码登录状态...'
}

function normalizeQrVerificationUrl(value) {
  const raw = String(value || '').trim()
  if (!raw) return ''
  const url = raw.startsWith('//') ? `https:${raw}` : raw
  if (/^https:\/\/(passport\.goofish\.com|login\.taobao\.com|passport\.taobao\.com)\//i.test(url)) return url
  return ''
}

function openModal(type){
  modal.value = type
  if(type === 'manual') {
    manual.accountNote=''
    manual.cookie=''
    manualError.value=''
  }
  if(type === 'scan') {
    qr.mode = 'create'
    qr.accountId = null
    startQrLogin()
  }
}
function closeModal(){
  modal.value = ''
  batchAuthError.value = ''
  batchAuthSuccess.value = ''
  unifiedConfigError.value = ''
  unifiedConfigSuccess.value = ''
  unifiedConfigTaskText.value = ''
  unifiedConfigBusy.value = false
  autoRateError.value = ''
  strategyError.value = ''
  stopQrPolling()
  resetQrState()
}
function openRescanModal(account) {
  if (!account?.id) return
  modal.value = 'scan'
  qr.mode = 'rescan'
  qr.accountId = account.id
  startQrLogin()
}

function requireResponseObject(res, label) {
  const data = res?.data
  if (!data || typeof data !== 'object' || Array.isArray(data)) {
    throw new Error(`${label}响应格式异常`)
  }
  return data
}

function autoRateConfigOf(res) {
  const data = requireResponseObject(res, '自动评价配置')
  if (typeof data.enabled !== 'boolean' || !['text', 'api'].includes(data.rateType)) {
    throw new Error('自动评价配置缺少有效开关或评价方式')
  }
  if (typeof data.textContent !== 'string' || typeof data.apiUrl !== 'string') {
    throw new Error('自动评价配置内容响应格式异常')
  }
  return data
}

function strategyConfigOf(res) {
  const data = requireResponseObject(res, '账号策略配置')
  const messageExpireTime = Number(data.messageExpireTime)
  if (!Number.isFinite(messageExpireTime) || messageExpireTime < 0 || messageExpireTime > 86400) {
    throw new Error('账号策略等待时间响应格式异常')
  }
  if (typeof data.scheduledRedelivery !== 'boolean' || typeof data.autoPolish !== 'boolean') {
    throw new Error('账号策略开关响应格式异常')
  }
  return { ...data, messageExpireTime }
}

async function saveAutoRateConfig() {
  if (!selected.value?.id || !autoRateLoaded.value || autoRateSaving.value) return
  autoRateError.value = ''
  if (autoRateForm.rateType === 'text' && !autoRateForm.textContent.trim()) {
    autoRateError.value = '请输入评价内容'
    return
  }
  if (autoRateForm.rateType === 'api' && !autoRateForm.apiUrl.trim()) {
    autoRateError.value = '请输入 API 地址'
    return
  }
  autoRateSaving.value = true
  try {
    const res = await saveAccountAutoRateConfig(selected.value.id, {
      enabled: autoRateForm.enabled,
      rateType: autoRateForm.rateType,
      textContent: autoRateForm.textContent.trim(),
      apiUrl: autoRateForm.apiUrl.trim(),
    })
    autoRateConfigOf(res)
    closeModal()
    qrSuccessMsg.value = '自动评价配置已保存'
    setTimeout(() => { if (qrSuccessMsg.value === '自动评价配置已保存') qrSuccessMsg.value = '' }, 4000)
    await loadAccounts()
  } catch (e) {
    autoRateError.value = e.message || '保存自动评价配置失败'
  } finally {
    autoRateSaving.value = false
  }
}

async function saveStrategyConfig() {
  if (!selected.value?.id || !strategyLoaded.value || strategySaving.value) return
  strategyError.value = ''
  const messageExpireTime = Number(strategyForm.messageExpireTime)
  if (!Number.isFinite(messageExpireTime) || messageExpireTime < 0 || messageExpireTime > 86400) {
    strategyError.value = '消息等待时间需在 0 到 86400 秒之间'
    return
  }
  strategySaving.value = true
  try {
    const res = await saveAccountStrategyConfig(selected.value.id, {
      messageExpireTime: Math.round(messageExpireTime),
      scheduledRedelivery: strategyForm.scheduledRedelivery,
      autoPolish: strategyForm.autoPolish,
      requestRedFlower: strategyForm.requestRedFlower,
    })
    strategyConfigOf(res)
    closeModal()
    qrSuccessMsg.value = '账号策略已保存'
    setTimeout(() => { if (qrSuccessMsg.value === '账号策略已保存') qrSuccessMsg.value = '' }, 4000)
    await loadAccounts()
  } catch (e) {
    strategyError.value = e.message || '保存账号策略失败'
  } finally {
    strategySaving.value = false
  }
}

function visibleAccountsForUnifiedConfig() {
  return accounts.value.filter(account => Number(account?.id) > 0)
}

async function applyUnifiedAction(taskText, runner) {
  if (unifiedConfigBusy.value) return
  const visibleAccounts = visibleAccountsForUnifiedConfig()
  if (!selected.value?.id) {
    unifiedConfigError.value = '请先选择一个基准账号'
    return
  }
  if (visibleAccounts.length === 0) {
    unifiedConfigError.value = '当前页面没有可处理的账号'
    return
  }
  unifiedConfigBusy.value = true
  unifiedConfigError.value = ''
  unifiedConfigSuccess.value = ''
  unifiedConfigTaskText.value = taskText
  try {
    const summary = await runner(visibleAccounts)
    const failed = Number(summary?.failed || 0)
    const success = Number(summary?.success || 0)
    unifiedConfigSuccess.value = `${taskText}完成，成功 ${success} 个账号${failed ? `，失败 ${failed} 个` : ''}`
    if (summary?.message) {
      unifiedConfigError.value = summary.message
    }
    await loadAccounts()
  } catch (e) {
    unifiedConfigError.value = e.message || `${taskText}失败`
  } finally {
    unifiedConfigBusy.value = false
    unifiedConfigTaskText.value = ''
  }
}

async function applyCurrentAutoRateToVisibleAccounts() {
  await applyUnifiedAction('同步自动评价', async (visibleAccounts) => {
    const sourceRes = await getAccountAutoRateConfig(selected.value.id)
    const source = autoRateConfigOf(sourceRes)
    const payload = {
      enabled: source.enabled,
      rateType: source.rateType,
      textContent: source.textContent,
      apiUrl: source.apiUrl,
    }
    let success = 0
    let failed = 0
    const errors = []
    for (const account of visibleAccounts) {
      try {
        await saveAccountAutoRateConfig(account.id, payload)
        success += 1
      } catch (e) {
        failed += 1
        errors.push(`${accountTitle(account)}: ${e.message || '保存失败'}`)
      }
    }
    return {
      success,
      failed,
      message: errors.slice(0, 3).join('; '),
    }
  })
}

async function applyCurrentStrategyToVisibleAccounts() {
  await applyUnifiedAction('同步消息等待', async (visibleAccounts) => {
    const sourceRes = await getAccountStrategyConfig(selected.value.id)
    const source = strategyConfigOf(sourceRes)
    const payload = {
      messageExpireTime: source.messageExpireTime,
      scheduledRedelivery: source.scheduledRedelivery,
      autoPolish: source.autoPolish,
      requestRedFlower: source.requestRedFlower === true,
    }
    let success = 0
    let failed = 0
    const errors = []
    for (const account of visibleAccounts) {
      try {
        await saveAccountStrategyConfig(account.id, payload)
        success += 1
      } catch (e) {
        failed += 1
        errors.push(`${accountTitle(account)}: ${e.message || '保存失败'}`)
      }
    }
    return {
      success,
      failed,
      message: errors.slice(0, 3).join('; '),
    }
  })
}

async function runBatchAuthCheckForVisibleAccounts() {
  await applyUnifiedAction('统一登录校验', async (visibleAccounts) => {
    let success = 0
    let failed = 0
    const errors = []
    for (const account of visibleAccounts) {
      try {
        await checkAccountAuth(account.id)
        success += 1
      } catch (e) {
        failed += 1
        errors.push(`${accountTitle(account)}: ${e.message || '校验失败'}`)
      }
    }
    return {
      success,
      failed,
      message: errors.slice(0, 3).join('; '),
    }
  })
}

function handleHeaderAction(e){ if(e.detail === 'open-scan-account') openModal('scan'); if(e.detail === 'open-manual-account') openModal('manual'); if(e.detail === 'refresh-accounts') loadAccounts() }

const cols=[{key:'account',title:'账号信息'},{key:'uid',title:'UID'},{key:'area',title:'地区'},{key:'level',title:'等级'},{key:'status',title:'账号状态'},{key:'cookie',title:'登录凭证'},{key:'ws',title:'实时连接'},{key:'sync',title:'资料同步'},{key:'op',title:'操作'}]

const rowClass = (row) => row.raw?.id === selectedId.value ? 'row-selected' : ''

const rows = computed(() => {
  const kw = (debouncedKeyword.value || '').trim().toLowerCase()
  const searchFields = ['nickname', 'displayName', 'accountNote', 'externalUid', 'unb', 'province', 'city', 'ipLocation', 'remark']
  return accounts.value
  .filter(a => {
    // 状态筛选
    if (statusFilter.value === 'normal' && a.status !== 1) return false
    if (statusFilter.value === 'verify' && a.status !== -1 && a.status !== -2) return false
    if (statusFilter.value === 'cookieWarn' && accountAuthState(a) !== false) return false
    if (statusFilter.value === 'wsOnline' && wsMap[a.id]?.connected !== true) return false
    // 关键词筛选
    if (!kw) return true
    // 仅匹配用户可见字段，避免匹配 id/时间戳等无关字段导致搜索结果不准
    return searchFields.some(f => String(a[f] || '').toLowerCase().includes(kw))
  })
  .map(a => {
    const ws = wsMap[a.id] || {}
    const wsConnected = typeof ws.connected === 'boolean' && ws.statusUnavailable !== true ? ws.connected : null
    return {
      raw: a,
      name: accountTitle(a),
      avatar: a.avatarUrl || a.avatar,
      tag: a.accountNote && (a.nickname || a.displayName) ? (a.nickname || a.displayName) : '',
      uid: a.externalUid || a.unb || a.id,
      area: a.province && a.city ? `${a.province} ${a.city}` : (a.ipLocation || a.province || '-'),
      level: a.accountLevel || a.sellerLevel || a.fishShopLevel || '-',
      statusText: accountStatus(a.status),
      statusType: a.status === 1 ? 'green' : 'orange',
      cookie: accountCookieLabel(a),
      cookieType: accountCookieBadgeType(a),
      ws: wsConnected === true ? '在线' : (wsConnected === false ? (isWsPending(a.id) ? '启动中' : '离线') : '状态未知'),
      wsConnected,
      wsPending: isWsPending(a.id),
      sync: a.lastSyncTime || a.profileUpdatedTime || a.updatedTime || '-'
    }
  })
})

const stats = computed(() => ({
  total: total.value,
  normal: accounts.value.filter(a => a.status === 1).length,
  verify: accounts.value.filter(a => a.status === -1 || a.status === -2).length,
  wsOnline: Object.values(wsMap).filter(s => s?.connected === true).length,
  cookieWarn: accounts.value.filter(a => accountAuthState(a) === false).length
}))

const statusOptions = [
  { label: '全部状态', value: 'all' },
  { label: '正常', value: 'normal' },
  { label: '需验证', value: 'verify' },
  { label: '登录凭证异常', value: 'cookieWarn' },
  { label: '实时在线', value: 'wsOnline' },
]

const accountStatCards = computed(() => [
  { key: 'total', title: '账号总数', value: accountMetric(stats.value.total), change: '全部记录', icon: PeopleOutline, tone: 'blue' },
  { key: 'normal', title: '正常账号', value: accountMetric(stats.value.normal), change: '当前页', icon: ShieldCheckmarkOutline, tone: 'green' },
  { key: 'verify', title: '需验证', value: accountMetric(stats.value.verify), change: '当前页', icon: AlertCircleOutline, tone: 'orange' },
  { key: 'wsOnline', title: '实时在线', value: accountMetric(stats.value.wsOnline), change: '当前页已确认', icon: LinkOutline, tone: 'purple' },
  { key: 'cookieWarn', title: '登录凭证异常', value: accountMetric(stats.value.cookieWarn), change: '当前页已确认', icon: KeyOutline, tone: stats.value.cookieWarn ? 'red' : 'green' },
])

const accountsStatusItems = computed(() => [
  {
    key: 'list',
    label: '账号列表',
    value: dataAvailable.value === true ? '已加载' : (dataAvailable.value === false ? '不可用' : '加载中'),
    tone: dataAvailable.value === false ? 'red' : (dataAvailable.value === true ? 'green' : 'orange'),
  },
  {
    key: 'selected',
    label: '当前账号',
    value: selected.value ? '已选择' : '未选择',
    tone: selected.value ? 'blue' : 'orange',
  },
  {
    key: 'auth',
    label: '登录凭证异常',
    value: dataAvailable.value === true ? `${stats.value.cookieWarn} 个` : '待确认',
    tone: dataAvailable.value !== true ? 'orange' : (stats.value.cookieWarn ? 'red' : 'green'),
  },
  {
    key: 'qr',
    label: '扫码监听',
    value: qr.polling ? '监听中' : (qrReady.value ? '二维码就绪' : '空闲'),
    tone: ['error', 'expired', 'failed', 'cancelled'].includes(normalizeQrStatus(qr.status))
      ? 'red'
      : (qr.polling ? 'orange' : (qrReady.value ? 'blue' : 'green')),
  },
])

function accountMetric(value) {
  return dataAvailable.value === true ? value : '—'
}

async function loadAccounts() {
  const request = accountsRequestGuard.begin()
  const hadSnapshot = dataAvailable.value === true
  loading.value = true
  error.value = ''
  accountListWarning.value = ''
  try {
    const requestConfig = listRefreshRequestConfig(hadSnapshot)
    const res = await getAccounts({ current: current.value, size: pageSize.value }, requestConfig)
    if (!request.isCurrent()) return
    // Support both array and object response formats
    const list = Array.isArray(res.data) ? res.data : (res.data?.records || res.data?.accounts || res.data?.list || res.data?.rows || [])
    accounts.value = list
    total.value = Number(res.data?.total ?? res.data?.totalCount ?? res.data?.count ?? list.length) || 0
    dataAvailable.value = true
    // 更新 selected，确保指向新数组中的对象（避免指向旧引用导致 cookie_status 不同步）
    if (selected.value) {
      const updated = accounts.value.find(a => a.id === selected.value.id)
      if (updated) {
        selected.value = updated
      } else {
        selected.value = null
        selectedId.value = null
      }
    } else if (accounts.value.length) {
      selected.value = accounts.value[0]
      selectedId.value = accounts.value[0].id
    }
    const statusResults = await Promise.allSettled(accounts.value.map(a => loadWsStatus(a.id, {
      isCurrent: request.isCurrent,
      requestConfig,
    })))
    if (!request.isCurrent()) return
    const failedStatusCount = statusResults.filter(result => (
      result.status === 'rejected' || result.value?.statusUnavailable === true
    )).length
    if (failedStatusCount) accountListWarning.value = `${failedStatusCount} 个账号的连接状态暂不可用；未知状态不会显示为离线。`
  } catch (e) {
    if (!request.isCurrent()) return
    if (hadSnapshot) {
      accountListWarning.value = `账号列表刷新失败，继续显示上次成功加载的账号数据。${e.message ? ` ${e.message}` : ''}`
    } else {
      accounts.value = []
      total.value = 0
      selected.value = null
      selectedId.value = null
      dataAvailable.value = false
      error.value = e.message || '账号列表加载失败'
    }
  } finally {
    if (request.isCurrent()) loading.value = false
  }
}
function goPage(p) {
  current.value = p
  loadAccounts()
}

function selectAccount(account) {
  if (Number(selected.value?.id || 0) !== Number(account?.id || 0)) {
    clearAllPolishConflicts()
    polishConflictAccountId.value = null
    setPolishNotice('', '')
  }
  selected.value = account
  selectedId.value = account.id
  loadWsStatus(account.id).catch(() => {})
}

async function loadWsStatus(accountId, options = {}) {
  if (!accountId) return
  const isCurrent = typeof options.isCurrent === 'function' ? options.isCurrent : () => true
  try {
    const res = await websocketStatus(accountId, options.requestConfig)
    if (!isCurrent()) return null
    const data = res.data || {}
    if (typeof data.connected !== 'boolean') throw new Error('连接状态响应无法确认')
    wsMap[accountId] = data
    return data
  } catch (e) {
    if (!isCurrent()) return null
    wsMap[accountId] = {
      connected: null,
      statusUnavailable: true,
      status: '状态未知',
      refreshError: e.message || '连接状态暂不可用'
    }
    throw e
  }
}

async function refreshProfile(accountId) {
  try {
    error.value = ''
    const res = await refreshAccountProfile(accountId)
    const data = res.data?.account || res.data || res
    // 刷新成功后的提示
    const displayName = data.displayName || data.nickname || ''
    qrSuccessMsg.value = displayName ? `资料刷新成功: ${displayName}` : '资料刷新成功'
    setTimeout(() => { if (qrSuccessMsg.value && qrSuccessMsg.value.startsWith('资料刷新')) qrSuccessMsg.value = '' }, 4000)
    // 更新选中账号的详情
    if (selected.value && selected.value.id === accountId) {
      selected.value = { ...selected.value, ...data }
    }
    await loadAccounts()
  } catch (e) {
    error.value = e.message || '刷新资料失败'
  }
}

function isWsBusy(accountId) { return !!wsBusyMap[accountId] }

function isWsPending(accountId) {
  const state = wsMap[accountId] || {}
  const phase = String(state.phase || state.status || '').toLowerCase()
  return state.connected !== true && state.statusUnavailable !== true && WS_START_PHASES.has(phase)
}

async function toggleWs(account) {
  if (!account?.id || isWsBusy(account.id)) return
  const initialState = wsMap[account.id] || {}
  if (initialState.connected == null || initialState.statusUnavailable === true) {
    error.value = '连接状态未知，请先刷新并确认状态；系统不会在未知状态下提交启动或断开命令。'
    return
  }
  if (isWsPending(account.id)) {
    error.value = '启动命令仍在处理中，请稍后刷新；系统不会重复提交。'
    return
  }
  wsBusyMap[account.id] = true
  error.value = ''
  try {
    if (initialState.connected === true) {
      await stopWebSocket(account.id)
      qrSuccessMsg.value = '断开请求已提交，正在确认状态'
      await new Promise(resolve => setTimeout(resolve, 800))
      const stoppedState = await loadWsStatus(account.id)
      if (stoppedState.connected === false) {
        qrSuccessMsg.value = '实时连接已确认断开'
      } else {
        error.value = '断开请求已提交，但连接仍显示在线，请稍后刷新核对。'
      }
    } else {
      const res = await startWebSocket(account.id)
      const data = res?.data || {}
      wsMap[account.id] = { ...initialState, ...data }
      if (typeof data.connected !== 'boolean') {
        throw new Error('实时连接启动响应缺少连接状态')
      }
      if (data.connected === true) {
        qrSuccessMsg.value = data.optimistic
          ? '实时连接已提交，未检测到滑块/验证'
          : '实时连接已就绪，正在接收消息'
      } else {
        qrSuccessMsg.value = data.message || '连接请求返回未连接状态，请刷新后确认'
      }
      if (data.optimistic) {
        // 乐观确认：系统 12 秒内未检测到验证失败，8 秒后刷新实际状态
        setTimeout(() => loadWsStatus(account.id), 8000)
      } else {
        // 已确认连接/恢复中：短暂等待后刷新状态
        await new Promise(resolve => setTimeout(resolve, 1200))
        await loadWsStatus(account.id)
      }
      // 连接成功后刷新账号列表，同步 Cookie 状态
      // （自动登录校验已将 cookie_status 更新为 1，但 accounts 列表仍为旧值）
      loadAccounts()
    }
  } catch (e) {
    error.value = e.message || '实时连接操作失败'
  } finally {
    wsBusyMap[account.id] = false
  }
}

async function removeAccount(accountId) {
  pendingDeleteId.value = accountId
  modal.value = 'confirmDelete'
}

async function executeDelete() {
  if (pendingDeleteId.value === null) return
  const id = pendingDeleteId.value
  pendingDeleteId.value = null
  closeModal()
  try {
    await deleteAccount(id)
    if (selected.value?.id === id) selected.value = null
    await loadAccounts()
  } catch (e) {
    error.value = e.message || '删除失败'
  }
}

async function submitManual() {
  manualError.value = ''
  if (!manual.cookie.trim()) return (manualError.value = '请输入登录 Cookie 字符串')
  // 前端预校验
  const validation = validateCookie(manual.cookie)
  if (!validation.valid) {
    manualError.value = validation.error
    return
  }
  submitting.value = true
  try {
    const keyFields = extractKeyFields(manual.cookie)
    await createAccountByCookie({
      accountNote: manual.accountNote.trim(),
      cookie: manual.cookie.trim(),
      extractedUnb: keyFields.unb,
      extractedMH5Tk: keyFields.mH5Tk,
    })
    closeModal()
    await loadAccounts()
  } catch (e) {
    manualError.value = e.message || '添加账号失败'
  } finally {
    submitting.value = false
  }
}

function openCookieEdit(account) {
  if (!account) return
  cookieEdit.accountId = account.id
  cookieEdit.cookie = ''
  cookieEditError.value = ''
  cookieEditSubmitting.value = false
  modal.value = 'cookieEdit'
}

async function submitCookieEdit() {
  cookieEditError.value = ''
  if (!cookieEdit.cookie.trim()) {
    cookieEditError.value = '请输入登录 Cookie 字符串'
    return
  }
  // 前端预校验
  const validation = validateCookie(cookieEdit.cookie)
  if (!validation.valid) {
    cookieEditError.value = validation.error
    return
  }
  // 身份校验（防串号）
  if (selected.value) {
    const keyFields = extractKeyFields(cookieEdit.cookie)
    const identity = checkIdentity(keyFields.unb, selected.value)
    if (!identity.valid) {
      cookieEditError.value = identity.error
      return
    }
  }
  cookieEditSubmitting.value = true
  try {
    // 提取关键字段一并提交
    const keyFields = extractKeyFields(cookieEdit.cookie)
    await updateAccountCookie(cookieEdit.accountId, cookieEdit.cookie.trim(), {
      unb: keyFields.unb,
      mH5Tk: keyFields.mH5Tk,
    })
    closeModal()
    qrSuccessMsg.value = '登录凭证更新成功'
    setTimeout(() => { if (qrSuccessMsg.value === '登录凭证更新成功') qrSuccessMsg.value = '' }, 4000)
    await loadAccounts()
  } catch (e) {
    cookieEditError.value = e.message || '更新登录凭证失败'
  } finally {
    cookieEditSubmitting.value = false
  }
}

async function startQrLogin() {
  qr.loading = true
  qr.polling = false
  qr.message = ''
  qr.sessionId = ''
  qr.qrUrl = ''
  qr.status = ''
  qr.verificationUrl = ''
  qr.checkCount = 0
  qr.lastCheckedAt = ''
  stopQrPolling()
  try {
    const res = qr.accountId
      ? await generateQrLogin({ accountId: qr.accountId })
      : await generateQrLogin()
    const data = res.data || {}
    qr.sessionId = data.sessionId || data.id || ''
    qr.qrUrl = data.qrCodeBase64 || data.qrImage || data.qrUrl || data.qrcodeUrl || data.qrCodeUrl || data.url || ''
    if (!qr.sessionId || !qr.qrUrl) throw new Error('二维码服务响应不完整，请稍后重试')
    qr.status = normalizeQrStatus(data.status || 'new')
    qr.message = qrStatusMessage(qr.status, data.message)
    startQrPolling()
  } catch (e) {
    qr.sessionId = ''
    qr.qrUrl = ''
    qr.status = 'error'
    qr.message = e.message || '生成二维码失败'
  } finally {
    qr.loading = false
  }
}

function startQrPolling() {
  stopQrPolling()
  qr.polling = true
  checkQrStatus()
  qrTimer = setInterval(checkQrStatus, 2000)
}
function stopQrPolling() {
  if (qrTimer) {
    clearInterval(qrTimer)
    qrTimer = null
  }
  qr.polling = false
}
async function checkQrStatus() {
  if (!qr.sessionId) return
  qr.checkCount += 1
  qr.lastCheckedAt = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  try {
    const res = qr.accountId
      ? await getQrLoginStatus(qr.sessionId, { accountId: qr.accountId })
      : await getQrLoginStatus(qr.sessionId)
    const data = res.data || {}
    const prevStatus = normalizeQrStatus(qr.status)
    const nextStatus = normalizeQrStatus(data.status || qr.status)
    qr.status = nextStatus || qr.status
    qr.verificationUrl = normalizeQrVerificationUrl(data.iframe_redirect_url || data.iframeRedirectUrl || data.verificationUrl)
    const faceQrImage = data.faceQrImage || data.face_qr_image || ''
    if (qr.status === 'verification_required' && faceQrImage.startsWith('data:image/')) {
      qr.qrUrl = faceQrImage
    }
    qr.message = data.message || (nextStatus !== prevStatus ? qrStatusMessage(qr.status) : (qr.message || qrStatusMessage(qr.status)))

    if (qr.status === 'confirmed') {
      if (data.accountId) {
        stopQrPolling()
        const isRescan = qr.mode === 'rescan'
        closeModal()
        const externalUid = data.externalUid || data.unb || ''
        qrSuccessMsg.value = externalUid
          ? `账号 ${externalUid.slice(0, 8)}... 登录成功`
          : '账号登录成功'
        if (isRescan) {
          qrSuccessMsg.value = data.message || (data.authUsable === false
            ? (data.loginStatusMessage || '重新扫码成功，但统一登录校验未通过')
            : '账号登录凭证已更新')
        }
        if (!isRescan) {
          current.value = 1
        }
        try {
          await loadAccounts()
          const nextAccountId = Number(data.accountId || 0) || null
          if (nextAccountId && !isRescan) {
            const target = accounts.value.find(a => a.id === nextAccountId)
            if (target) {
              selectAccount(target)
            }
            // 扫码成功后自动刷新账号资料
            refreshProfile(nextAccountId).catch(() => {
              if (import.meta.env.DEV) console.warn('自动刷新资料失败')
            })
          }
        } catch {
          if (import.meta.env.DEV) console.warn('账号列表刷新失败')
          qrSuccessMsg.value = '账号已保存，但列表刷新失败，请手动刷新'
        }
        setTimeout(() => { if (qrSuccessMsg.value) qrSuccessMsg.value = '' }, 6000)
      } else if (prevStatus !== 'confirmed' || data.credentialsAvailable) {
        qr.message = data.credentialsAvailable
          ? '扫码已确认，系统正在安全同步账号信息...'
          : (data.message || '扫码已确认，等待系统完成账号同步...')
      }
    }
    if (qr.status === 'verification_required') {
      qr.message = qrStatusMessage(qr.status, data.message)
    }
    if (qr.status === 'error') {
      stopQrPolling()
      qr.message = data.message || '账号保存失败，请重试'
      if (data.errorCode) {
        if (import.meta.env.DEV) console.warn('扫码保存返回失败状态')
      }
    }
    if (['expired', 'failed', 'cancelled'].includes(qr.status)) {
      stopQrPolling()
      qr.message = qrStatusMessage(qr.status, data.message)
    }
  } catch (e) {
    qr.message = e.message || '查询扫码状态失败'
  }
}

async function handleSseEvent(e) {
  const event = e.detail
  if (!event) return
  if (event.type === 'account_added') {
    qrSuccessMsg.value = '账号登录成功'
    current.value = 1
    try {
      await loadAccounts()
      const addedAccountId = Number(event.accountId || event.account_id || 0) || null
      if (addedAccountId) {
        const target = accounts.value.find(a => a.id === addedAccountId)
        if (target) {
          selectAccount(target)
        }
        // 自动刷新账号资料
        refreshProfile(addedAccountId).catch(() => {
          if (import.meta.env.DEV) console.warn('自动刷新资料失败')
        })
      } else if (accounts.value[0]) {
        selectAccount(accounts.value[0])
      }
    } catch {
      if (import.meta.env.DEV) console.warn('账号列表刷新失败')
    }
    setTimeout(() => { qrSuccessMsg.value = '' }, 4000)
  } else if (event.type === 'cookie_status_changed') {
    // 重新拉取账号列表，确保 cookie 状态一致
    const targetId = event.accountId
    const newStatus = event.cookieStatus
    // 先更新本地缓存，避免列表闪现旧状态
    const account = accounts.value.find(a => a.id === targetId)
    if (account) {
      account.cookieStatus = newStatus
      account.authUsable = Number(newStatus) === 1
      account.loginStatusCode = Number(newStatus) === 1 ? 'OK' : 'COOKIE_EXPIRED'
      account.loginStatusMessage = Number(newStatus) === 1 ? '账号登录状态正常' : '登录凭证已失效，请重新登录闲鱼账号'
      if (selected.value && selected.value.id === targetId) {
        selected.value.cookieStatus = newStatus
        selected.value.authUsable = Number(newStatus) === 1
        selected.value.loginStatusCode = Number(newStatus) === 1 ? 'OK' : 'COOKIE_EXPIRED'
        selected.value.loginStatusMessage = Number(newStatus) === 1 ? '账号登录状态正常' : '登录凭证已失效，请重新登录闲鱼账号'
      }
    }
    // 显示提示信息
    if (newStatus === 0) {
      qrSuccessMsg.value = `账号 ${targetId} 登录凭证已失效（可能遇到滑块验证），请更换登录 Cookie 或重新扫码登录`
      setTimeout(() => { if (qrSuccessMsg.value && qrSuccessMsg.value.includes('登录凭证已失效')) qrSuccessMsg.value = '' }, 8000)
    }
    // 重新拉取，确保数据同步
    loadAccounts()
  }
}

onMounted(() => {
  window.addEventListener('xya-header-action', handleHeaderAction)
  window.addEventListener('xya-sse-event', handleSseEvent)
  loadAccounts()
  void restoreItemPolish()
})
onBeforeUnmount(() => {
  accountsRequestGuard.invalidate()
  window.removeEventListener('xya-header-action', handleHeaderAction)
  window.removeEventListener('xya-sse-event', handleSseEvent)
  stopQrPolling()
  void cleanupQrLogin()
})
</script>

<style scoped>
.accounts-page {
  --accounts-text: #101828;
  --accounts-muted: #64748b;
  --accounts-line: #e5eaf0;
  --accounts-primary: #1d4ed8;
  --accounts-ease: cubic-bezier(0.23, 1, 0.32, 1);
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 16px;
  align-items: start;
}

.accounts-main,
.accounts-side {
  min-width: 0;
  display: grid;
  gap: 16px;
}

.accounts-side {
  position: sticky;
  top: 118px;
}

.accounts-command-section :deep(.n-card-header) {
  padding-bottom: 8px;
}

.accounts-command-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 340px;
  gap: 18px;
  align-items: start;
}

.accounts-command-copy {
  min-width: 0;
}

.accounts-command-copy p {
  margin: 0;
  max-width: 720px;
  color: #4b5563;
  font-size: 14px;
  line-height: 1.75;
}

.accounts-command-meta {
  margin-top: 12px;
}

.accounts-command-panel {
  display: grid;
  gap: 12px;
  align-content: center;
  padding: 14px;
  border: 1px solid rgba(148, 163, 184, .24);
  border-radius: 8px;
  background: rgba(255, 255, 255, .82);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, .7);
}

.accounts-command-panel-head {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  color: #64748b;
  font-size: 12px;
}

.accounts-command-panel-head strong {
  color: #101828;
  font-size: 13px;
}

.accounts-command-buttons {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.accounts-command-buttons :deep(.n-button) {
  min-width: 0;
}

.accounts-action-hint {
  margin: 0;
  min-height: 18px;
  color: var(--accounts-muted);
  font-size: 12px;
  line-height: 1.55;
}

.accounts-intel-banner {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 14px;
  border: 1px solid #dbeafe;
  border-radius: 8px;
  background: #eff6ff;
  color: #1e3a8a;
  font-size: 13px;
  line-height: 1.55;
}

.accounts-intel-banner :deep(.ui-icon) {
  flex: 0 0 auto;
  width: 18px;
  height: 18px;
  margin-top: 1px;
}

.accounts-notices {
  display: grid;
  gap: 8px;
}

.accounts-metric-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
}

.accounts-workspace {
  min-width: 0;
  padding: 16px;
  border: 1px solid #e5eaf0;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 10px 28px rgba(15, 23, 42, .045);
}

.accounts-workspace-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.accounts-workspace-eyebrow {
  color: #64748b;
  font-size: 12px;
  font-weight: 750;
}

.accounts-workspace-head h3 {
  margin: 4px 0 0;
  color: #101828;
  font-size: 18px;
  font-weight: 800;
}

.accounts-workspace-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}

.accounts-control-board {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  margin-bottom: 14px;
  padding: 12px;
  border: 1px solid #edf1f5;
  border-radius: 8px;
  background: #f8fafc;
}

.accounts-search {
  width: min(360px, 42vw);
}

.accounts-filter {
  width: 150px;
}

.accounts-workspace > .empty-state,
.accounts-workspace > .base-table-wrap,
.accounts-workspace > .pagination {
  margin-top: 12px;
}

@media (max-width: 1500px) {
  .accounts-metric-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .accounts-command-layout {
    grid-template-columns: minmax(0, 1fr);
  }

  .accounts-command-buttons {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 1280px) {
  .accounts-page {
    grid-template-columns: minmax(0, 1fr);
  }

  .accounts-side {
    position: static;
  }
}

@media (max-width: 900px) {
  .accounts-page,
  .accounts-main,
  .accounts-side {
    gap: 12px;
  }

  .accounts-workspace {
    padding: 14px;
    border-radius: 8px;
  }

  .accounts-command-section :deep(.n-card-header) {
    padding: 16px 16px 10px;
  }

  .accounts-command-section :deep(.n-card__content) {
    padding: 0 16px 16px;
  }

  .accounts-command-buttons {
    grid-template-columns: minmax(0, 1fr);
  }

  .accounts-metric-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .accounts-workspace-head {
    display: grid;
  }

  .accounts-workspace-tags {
    justify-content: flex-start;
  }

  .accounts-control-board {
    display: grid;
  }

  .accounts-search,
  .accounts-filter {
    width: 100%;
  }

  .account-scan-modal {
    width: 100vw;
    max-width: 100vw;
    max-height: 92vh;
    border-radius: 8px 8px 0 0;
    overflow-y: auto;
  }

  .scan-modal-head {
    padding: 16px 54px 12px 16px;
  }

  .scan-status-strip {
    margin: 12px 16px 0;
    display: grid;
    grid-template-columns: auto minmax(0, 1fr);
  }

  .scan-status-strip b {
    margin-left: 18px;
  }

  .account-scan-modal .scan-steps,
  .account-scan-modal .scan-main,
  .account-scan-modal .notice-box {
    margin-left: 16px;
    margin-right: 16px;
  }

  .account-scan-modal .scan-main {
    grid-template-columns: minmax(0, 1fr);
  }

  .account-scan-modal .qr-box {
    width: min(260px, 100%);
    height: auto;
    aspect-ratio: 1;
    margin: 0 auto;
  }

  .account-scan-modal .modal-actions {
    padding: 14px 16px 16px;
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.account-selector { width: 100%; padding: 0; border: 0; background: transparent; color: inherit; font: inherit; text-align: left; cursor: pointer; }
.account-selector-copy { min-width: 0; }
.refresh-status {
  margin-bottom: 10px;
  color: #526079;
  font-size: 13px;
}

.polish-status-card {
  margin-top: 12px;
  padding: 12px;
  border: 1px solid #dbe8fb;
  border-radius: 8px;
  background: #FAFAFA;
}

.polish-status-head,
.polish-summary,
.polish-results li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.polish-status-card p,
.polish-poll-message,
.polish-recovery {
  display: block;
  margin: 8px 0;
  color: #667085;
  font-size: 12px;
  line-height: 1.55;
}

.polish-summary {
  flex-wrap: wrap;
  justify-content: flex-start;
  color: #475467;
  font-size: 12px;
}

.polish-results {
  margin: 8px 0;
  padding: 8px 0 0;
  border-top: 1px solid #e5edf8;
  list-style: none;
}

.polish-results li {
  padding: 4px 0;
  font-size: 12px;
}

.polish-results li span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-confirmed,
.result-already_done { color: #16803c; }
.result-failed,
.result-needs_verification { color: #b54708; }
.result-unknown { color: #b42318; }

.qr-unavailable {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 18px;
  box-sizing: border-box;
  color: #667085;
  background: #f8fafc;
  text-align: center;
  font-size: 12px;
}

.modal-mask {
  --accounts-ease: cubic-bezier(0.23, 1, 0.32, 1);
}

.account-scan-modal {
  width: min(920px, calc(100vw - 32px));
  padding: 0;
  border: 1px solid #e5eaf0;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 24px 70px rgba(15, 23, 42, .24);
  overflow: hidden;
  animation: accountScanModalIn 220ms var(--accounts-ease);
}

.account-scan-modal .modal-close {
  top: 16px;
  right: 16px;
  width: 34px;
  height: 34px;
  border-radius: 8px;
  transition: background-color 150ms var(--accounts-ease), transform 150ms var(--accounts-ease);
}

.account-scan-modal .modal-close:active {
  transform: scale(.96);
}

.scan-modal-head {
  padding: 20px 64px 16px 24px;
  border-bottom: 1px solid #eef2f7;
}

.scan-modal-head span {
  color: #64748b;
  font-size: 12px;
  font-weight: 750;
}

.scan-modal-head h2 {
  margin: 4px 0 0;
  color: #101828;
  font-size: 20px;
  font-weight: 800;
  line-height: 1.25;
}

.scan-modal-head p {
  margin: 8px 0 0;
  color: #526079;
  font-size: 13px;
  line-height: 1.6;
}

.scan-status-strip {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 16px 24px 0;
  padding: 10px 12px;
  border: 1px solid #dbeafe;
  border-radius: 8px;
  background: #eff6ff;
  color: #1e3a8a;
}

.scan-status-strip i {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: currentColor;
}

.scan-status-strip span {
  font-size: 13px;
  font-weight: 750;
}

.scan-status-strip b {
  margin-left: auto;
  color: #334155;
  font-size: 12px;
  font-weight: 650;
}

.scan-status-strip.is-success {
  border-color: #bbf7d0;
  background: #f0fdf4;
  color: #15803d;
}

.scan-status-strip.is-danger {
  border-color: #fecaca;
  background: #fef2f2;
  color: #b42318;
}

.scan-status-strip.is-active {
  border-color: #fed7aa;
  background: #fff7ed;
  color: #c2410c;
}

.account-scan-modal .scan-steps {
  margin: 16px 24px 0;
}

.account-scan-modal .scan-main {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: 18px;
  margin: 16px 24px 0;
}

.account-scan-modal .qr-box {
  position: relative;
  width: 260px;
  height: 260px;
  border: 1px solid #dbe3ef;
  border-radius: 8px;
  background: #f8fafc;
  overflow: hidden;
}

.account-scan-modal .qr-box img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  padding: 14px;
  box-sizing: border-box;
  background: #fff;
}

.account-scan-modal .qr-box.is-polling {
  border-color: rgba(29, 78, 216, .34);
}

.account-scan-modal .qr-box.is-polling::after {
  content: "";
  position: absolute;
  inset: 8px;
  border: 1px solid rgba(29, 78, 216, .28);
  border-radius: 8px;
  pointer-events: none;
}

.account-scan-modal .qr-loading {
  position: absolute;
  right: 12px;
  bottom: 12px;
  width: 18px;
  height: 18px;
  border: 2px solid rgba(29, 78, 216, .18);
  border-top-color: #1d4ed8;
  border-radius: 999px;
  animation: accountQrSpin 800ms linear infinite;
}

.account-scan-modal .qr-tip {
  margin: 10px 0 0;
  color: #475569;
  font-size: 13px;
  line-height: 1.6;
}

.account-scan-modal .qr-tip.is-danger {
  color: #b42318;
}

.account-scan-modal .qr-tip.is-success {
  color: #15803d;
}

.account-scan-modal .scan-guide {
  min-width: 0;
  padding: 14px;
  border: 1px solid #e5eaf0;
  border-radius: 8px;
  background: #fbfdff;
}

.account-scan-modal .scan-guide h4,
.account-scan-modal .session-box h4 {
  margin: 0 0 10px;
  color: #101828;
  font-size: 14px;
  font-weight: 800;
}

.account-scan-modal .scan-guide p {
  margin: 7px 0;
  color: #526079;
  font-size: 13px;
  line-height: 1.55;
}

.account-scan-modal .session-box {
  margin-top: 14px;
  padding: 12px;
  border: 1px solid #edf1f5;
  border-radius: 8px;
  background: #fff;
}

.account-scan-modal .session-box div {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  padding: 6px 0;
  color: #64748b;
  font-size: 12px;
}

.account-scan-modal .session-box b {
  min-width: 0;
  color: #101828;
  font-weight: 700;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.account-scan-modal .inline-link {
  margin-left: auto;
  border: 0;
  background: transparent;
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: color 150ms var(--accounts-ease), transform 150ms var(--accounts-ease);
}

.account-scan-modal .inline-link:active {
  transform: scale(.97);
}

.account-scan-modal .notice-box {
  margin: 16px 24px 0;
  padding: 12px 14px;
  border: 1px solid #fde68a;
  border-radius: 8px;
  background: #fffbeb;
  color: #92400e;
}

.account-scan-modal .notice-box b {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.account-scan-modal .notice-box p {
  margin: 8px 0 0;
  font-size: 12px;
  line-height: 1.55;
}

.account-scan-modal .modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin: 0;
  padding: 16px 24px 20px;
}

.accounts-v11-shell .link,
.accounts-v11-shell .text-action {
  transition:
    color 150ms var(--accounts-ease),
    opacity 150ms var(--accounts-ease),
    transform 150ms var(--accounts-ease);
}

.accounts-v11-shell .link:active:not(:disabled),
.accounts-v11-shell .text-action:active:not(:disabled) {
  transform: scale(.97);
}

.accounts-v11-shell .link:disabled,
.accounts-v11-shell .text-action:disabled {
  cursor: not-allowed;
  opacity: .45;
}

@keyframes accountScanModalIn {
  from {
    opacity: 0;
    transform: translateY(12px) scale(.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes accountQrSpin {
  to { transform: rotate(360deg); }
}

@media (prefers-reduced-motion: reduce) {
  .account-scan-modal,
  .account-scan-modal .qr-loading {
    animation: none;
  }
}

.grid.wide-right {
  grid-template-columns: minmax(0, 1fr) 392px;
  gap: 16px;
  align-items: start;
}

.account-detail-drawer {
  min-width: 0;
  padding: 15px 14px 14px;
  border: 1px solid #e6edf5;
  border-radius: 9px;
  background: #fff;
  box-shadow: 0 2px 12px rgba(118, 63, 39, 0.045);
  color: #51362a;
}

.detail-title-row,
.account-summary,
.account-name-row,
.health-footer {
  display: flex;
  align-items: center;
}

.detail-title-row {
  justify-content: space-between;
}

.detail-title-row h3,
.account-detail-drawer h4 {
  margin: 0;
  color: #1e2d47;
  font-weight: 700;
}

.detail-title-row h3 {
  font-size: 15px;
  line-height: 24px;
}

.account-detail-drawer h4 {
  font-size: 14px;
  line-height: 22px;
}

.detail-close {
  width: 26px;
  height: 26px;
  border: 0;
  background: transparent;
  color: #51627c;
  font-size: 24px;
  font-weight: 300;
  line-height: 20px;
  cursor: pointer;
}

.account-summary {
  position: relative;
  gap: 12px;
  margin-top: 14px;
  padding: 0 0 13px;
}

.detail-avatar {
  width: 56px;
  height: 56px;
  flex: 0 0 56px;
  border-radius: 50%;
  object-fit: cover;
  background: linear-gradient(135deg, #e7f0fa, #f7fbff);
  box-shadow: inset 0 0 0 1px #e5edf5;
}

.avatar-fallback {
  position: relative;
}

.avatar-fallback::before {
  position: absolute;
  inset: 13px;
  border-radius: 50%;
  background: #e7d6cf;
  content: '';
}

.account-summary-main {
  min-width: 0;
  padding-right: 4px;
}

.account-name-row {
  gap: 8px;
  min-height: 22px;
}

.account-name-row strong {
  max-width: 128px;
  overflow: hidden;
  color: #4b2f23;
  font-size: 15px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.current-account-tag,
.plan-tag {
  display: inline-flex;
  align-items: center;
  min-height: 21px;
  padding: 0 9px;
  border-radius: 4px;
  background: #edf4ff;
  color: #ff7940;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
}

.account-meta-line {
  margin-top: 4px;
  color: #687891;
  font-size: 12px;
  line-height: 18px;
  white-space: nowrap;
}

.account-meta-split {
  display: flex;
  align-items: center;
  gap: 10px;
}

.account-meta-split i {
  width: 1px;
  height: 12px;
  background: #f1e6e2;
}

.online-state {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
  align-self: flex-start;
  padding-top: 3px;
  color: #19bd78;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.online-state i,
.health-metrics i {
  display: inline-block;
  border-radius: 50%;
  background: #18bf78;
}

.online-state i {
  width: 7px;
  height: 7px;
}

.online-state.offline {
  color: #9aa8ba;
}

.online-state.offline i {
  background: #9aa8ba;
}

.online-state.unknown {
  color: #a05b00;
}

.online-state.unknown i {
  background: #ffb547;
}

.health-card,
.profile-stats-card {
  border: 1px solid #e8eef5;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 2px 7px rgba(113, 56, 31, 0.035);
}

.health-card {
  padding: 11px 12px 10px;
}

.health-content {
  display: grid;
  grid-template-columns: 134px 1fr;
  align-items: center;
  min-height: 110px;
}

.health-ring-wrap {
  display: flex;
  justify-content: center;
}

.health-ring {
  position: relative;
  width: 88px;
  height: 88px;
  border-radius: 50%;
  background:
    conic-gradient(
      #16bf78 var(--health-score),
      #e8f1ee 0
    );
}

.health-ring::before {
  position: absolute;
  inset: 8px;
  border-radius: 50%;
  background: #fff;
  content: '';
}

.health-ring-inner {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  flex-direction: column;
  justify-content: center;
}

.health-ring-inner strong {
  color: #4a2e22;
  font-size: 22px;
  line-height: 24px;
}

.health-ring-inner small {
  margin-left: 1px;
  font-size: 10px;
}

.health-ring-inner span {
  margin-top: 2px;
  color: #6d7c91;
  font-size: 11px;
}

.health-metrics {
  display: grid;
  gap: 8px;
}

.health-metrics div {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: #5d6d84;
  font-size: 12px;
}

.health-metrics span {
  display: flex;
  align-items: center;
  gap: 9px;
  white-space: nowrap;
}

.health-metrics i {
  width: 6px;
  height: 6px;
}

.health-metrics b {
  color: #19bd78;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.health-footer {
  justify-content: space-between;
  gap: 12px;
  padding-top: 4px;
  color: #78879b;
  font-size: 11px;
}

.text-action {
  border: 0;
  background: transparent;
  color: #ff7134;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}

.text-action b {
  font-size: 18px;
  font-weight: 400;
  vertical-align: -1px;
}

.drawer-section {
  padding: 17px 3px 0;
}

.activity-list {
  display: grid;
  gap: 8px;
  margin-top: 10px;
}

.activity-list div {
  display: grid;
  grid-template-columns: 94px minmax(0, 1fr);
  gap: 10px;
  color: #617189;
  font-size: 12px;
  line-height: 17px;
}

.activity-list time {
  color: #74849a;
}

.activity-more {
  padding: 7px 0 0;
}

.modal-subtitle {
  margin: 10px 0 0;
  color: #66768f;
  font-size: 13px;
  line-height: 1.6;
}

.batch-auth-grid {
  display: grid;
  gap: 10px;
  margin-top: 14px;
}

.unified-config-success {
  margin-top: 12px;
}

.unified-config-progress {
  margin-top: 14px;
}

.batch-auth-card {
  width: 100%;
  padding: 14px 16px;
  border: 1px solid #f1e2db;
  border-radius: 8px;
  background: #fff;
  text-align: left;
  cursor: pointer;
  transition:
    border-color 150ms var(--accounts-ease),
    box-shadow 150ms var(--accounts-ease),
    transform 150ms var(--accounts-ease);
}

.batch-auth-card:hover:not(:disabled) {
  border-color: #f7a582;
  box-shadow: 0 8px 20px rgba(188, 101, 64, 0.08);
  transform: translateY(-1px);
}

.batch-auth-card:disabled {
  cursor: not-allowed;
  opacity: .65;
}

.batch-auth-card strong {
  display: block;
  color: #4a2d20;
  font-size: 14px;
}

.batch-auth-card span {
  display: block;
  margin-top: 6px;
  color: #6b7b92;
  font-size: 12px;
  line-height: 1.6;
}

.more-actions-backdrop {
  position: fixed;
  inset: 0;
  z-index: 240;
}

.more-actions-menu {
  position: absolute;
  right: 0;
  top: 100%;
  margin-top: 6px;
  z-index: 250;
  background: #fff;
  border: 1px solid #E8E8E8;
  border-radius: 8px;
  box-shadow: 0 12px 32px rgba(94, 50, 31, .14);
  padding: 6px;
  display: flex;
  flex-direction: column;
  min-width: 160px;
}

.more-actions-menu button {
  appearance: none;
  border: none;
  background: transparent;
  padding: 10px 14px;
  font-size: 14px;
  color: #2c3e50;
  text-align: left;
  border-radius: 8px;
  cursor: pointer;
  transition: background .15s;
}

.more-actions-menu button:hover {
  background: #f1f6ff;
  color: #ff6c2d;
}

.detail-empty {
  min-height: 280px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9aa8ba;
}

/* Table row selection highlight */
.base-table tbody tr.row-selected {
  background: #e6f4ff;
  box-shadow: inset 3px 0 0 #0f766e;
}
.base-table tbody tr.row-selected:hover {
  background: #ffe2d6;
}

/* ===== 闲鱼主页资料卡片 ===== */
.profile-stats-card {
  margin-top: 13px;
  padding: 12px 12px 11px;
}

.profile-stats-card h4 {
  margin: 0 0 10px 0;
}

.profile-intro {
  margin-bottom: 10px;
  padding: 8px 10px;
  border-radius: 5px;
  background: #f7f9fc;
}

.profile-intro-label {
  display: block;
  margin-bottom: 4px;
  color: #8e9cb0;
  font-size: 11px;
}

.profile-intro p {
  margin: 0;
  color: #3a4b63;
  font-size: 12px;
  line-height: 18px;
  word-break: break-all;
}

.profile-stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-bottom: 10px;
}

.profile-stat-item {
  text-align: center;
  padding: 8px 4px;
  border-radius: 5px;
  background: #f7f9fc;
}

.profile-stat-item b {
  display: block;
  color: #1e2d47;
  font-size: 16px;
  font-weight: 700;
  line-height: 22px;
}

.profile-stat-item span {
  color: #7a8ca5;
  font-size: 11px;
}

.profile-extra {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6px 12px;
}

.profile-extra-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 5px 0;
  color: #687891;
  font-size: 12px;
}

.profile-extra-item b {
  color: #34425a;
  font-weight: 600;
}

.green-tag {
  color: #13be77 !important;
}

/* Cookie 状态警告横幅 */
.cookie-warn-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 6px;
  background: #fff3e0;
  border: 1px solid #ffcc80;
  color: #e65100;
  font-size: 12px;
  line-height: 18px;
}

.cookie-warn-banner.cookie-expired {
  background: #ffebee;
  border-color: #ef9a9a;
  color: #c62828;
}

/* 编辑账号信息 */
.edit-account-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
  padding: 8px 12px;
  border-radius: 5px;
  background: #f5f7fa;
  font-size: 13px;
  color: #58687a;
}

.edit-account-info b {
  color: #1e2d47;
  font-weight: 600;
}

@media (max-width: 1480px) {
  .grid.wide-right {
    grid-template-columns: minmax(0, 1fr) 360px;
  }

  .account-meta-split {
    display: block;
  }

  .account-meta-split i {
    display: none;
  }

  .health-content {
    grid-template-columns: 118px minmax(0, 1fr);
  }
}

/* ===== Cookie 解析预览 ===== */
.cookie-parse-preview {
  margin-top: 10px;
  border: 1px solid #f0e6e2;
  border-radius: 8px;
  overflow: hidden;
}

.cookie-parse-error {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  background: #fff3e0;
  border-bottom: 1px solid #ffcc80;
  color: #e65100;
  font-size: 12px;
  line-height: 18px;
}

.cookie-parse-error.cookie-identity-error {
  background: #ffebee;
  border-color: #ef9a9a;
  color: #c62828;
}

.cookie-parse-fields {
  padding: 10px 12px;
  background: #f8fafc;
}

.cookie-parse-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.cookie-parse-header span {
  font-size: 13px;
  font-weight: 600;
  color: #334155;
}

.cookie-parse-header em {
  font-size: 11px;
  color: #94a3b8;
  font-style: normal;
}

.cookie-field-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6px;
}

.cookie-field-item {
  padding: 6px 8px;
  background: #fff;
  border: 1px solid #f0e6e2;
  border-radius: 5px;
}

.cookie-field-item.missing {
  background: #fff8f8;
  border-color: #fecaca;
}

.cookie-field-item label {
  display: block;
  font-size: 11px;
  color: #64748b;
  margin-bottom: 2px;
}

.cookie-field-item code {
  display: block;
  font-size: 12px;
  color: #334155;
  font-family: 'SF Mono', 'Cascadia Code', 'Consolas', monospace;
  word-break: break-all;
}

.cookie-field-item.missing code {
  color: #dc2626;
}

.required-mark {
  color: #ef4444;
  font-size: 10px;
  margin-left: 4px;
}

.cookie-parse-warning {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin-top: 8px;
  padding: 6px 8px;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 5px;
  color: #92400e;
  font-size: 11px;
  line-height: 16px;
}

.current-unb-tag {
  display: inline-flex;
  align-items: center;
  margin-left: 8px;
  padding: 2px 8px;
  background: #eef2ff;
  border: 1px solid #fed7c7;
  border-radius: 4px;
  color: #ca6438;
  font-size: 11px;
  font-weight: 500;
}

.diagnosis-card{border:1px solid #E8E8E8;border-radius:8px;padding:16px;background:#FFFFFF;margin:14px 0}
.diagnosis-card h4{margin:0 0 12px;color:#16213e}
.diagnosis-item{padding:10px 0;border-bottom:1px solid #F0F0F0}
.diagnosis-item:last-child{border-bottom:0}
.diagnosis-item span{display:flex;align-items:center;gap:8px;color:#526079;font-weight:700}
.diagnosis-item i{width:9px;height:9px;border-radius:50%;background:#16bf78}.diagnosis-item.warn i{background:#f79009}.diagnosis-item.danger i{background:#ef4444}
.diagnosis-item b{display:block;margin-top:5px;color:#16213e}.diagnosis-item small{display:block;margin-top:4px;color:#667085;line-height:1.5}
.diagnosis-actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px}

/* 删除确认弹窗 */
.confirm-delete-modal {
  width: 420px;
  text-align: center;
  padding: 40px 36px 28px;
}

.confirm-delete-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  margin: 0 auto 18px;
  border-radius: 50%;
  background: #fef2f2;
}

.confirm-delete-icon .ui-icon {
  width: 32px;
  height: 32px;
}

.confirm-delete-modal h2 {
  margin: 0 0 12px;
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
}

.confirm-delete-desc {
  margin: 0 0 28px;
  font-size: 13px;
  line-height: 1.6;
  color: #64748b;
}

.confirm-delete-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.confirm-delete-actions .app-btn {
  min-width: 120px;
  height: 40px;
  font-size: 14px;
}

/* ===== 移动端响应式 (max-width: 900px) ===== */
@media (max-width: 900px) {
  /* 双列网格 → 单列堆叠 */
  .grid.wide-right {
    grid-template-columns: minmax(0, 1fr);
    gap: 12px;
  }

  /* 账号详情抽屉：减小内边距 */
  .account-detail-drawer {
    padding: 12px;
  }

  /* 详情标题字号收敛 */
  .detail-title-row h3 {
    font-size: 16px;
    line-height: 22px;
  }

  .account-detail-drawer h4 {
    font-size: 14px;
    line-height: 20px;
  }

  /* 账号摘要：保持 flex 但收紧间距 */
  .account-summary {
    gap: 10px;
    margin-top: 10px;
    padding: 0 0 10px;
    flex-wrap: wrap;
  }

  .detail-avatar {
    width: 48px;
    height: 48px;
    flex: 0 0 48px;
  }

  .account-name-row strong {
    max-width: 100%;
    font-size: 14px;
  }

  /* 在线状态换行 */
  .online-state {
    margin-left: 0;
  }

  /* 健康卡：双列 → 单列 */
  .health-content {
    grid-template-columns: minmax(0, 1fr);
    gap: 12px;
    min-height: auto;
  }

  .health-ring {
    width: 76px;
    height: 76px;
  }

  .health-ring-inner strong {
    font-size: 18px;
    line-height: 20px;
  }

  /* 最近活动：时间列变窄 */
  .activity-list div {
    grid-template-columns: 80px minmax(0, 1fr);
    gap: 8px;
  }

  /* 闲鱼主页资料：4列 → 2列 */
  .profile-stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }

  .profile-stat-item b {
    font-size: 15px;
  }

  /* 资料附加项：2列 → 1列 */
  .profile-extra {
    grid-template-columns: minmax(0, 1fr);
    gap: 4px;
  }

  /* Cookie 解析字段网格：2列 → 1列 */
  .cookie-field-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  /* 网格子元素防止溢出 */
  .health-content > *,
  .profile-stats-grid > *,
  .profile-extra > *,
  .cookie-field-grid > * {
    min-width: 0;
  }

  /* 诊断卡内边距收敛 */
  .diagnosis-card {
    padding: 12px;
    border-radius: 8px;
    margin: 10px 0;
  }

  .diagnosis-actions {
    gap: 8px;
  }

  /* 批量登录检查卡片内边距收敛 */
  .batch-auth-card {
    padding: 12px;
  }

  /* 删除确认弹窗：固定宽度 → 全宽底部弹出 */
  .confirm-delete-modal {
    width: 100%;
    max-width: 420px;
    padding: 24px 18px 20px;
  }

  .confirm-delete-icon {
    width: 56px;
    height: 56px;
    margin: 0 auto 14px;
  }

  .confirm-delete-modal h2 {
    font-size: 17px;
  }

  .confirm-delete-desc {
    margin: 0 0 20px;
    font-size: 13px;
  }

  .confirm-delete-actions .app-btn {
    min-width: 100px;
    height: 40px;
  }

  /* 更多操作菜单：固定定位底部弹出 */
  .more-actions-menu {
    position: fixed;
    left: 12px;
    right: 12px;
    top: auto;
    bottom: 12px;
    margin: 0;
    min-width: 0;
    border-radius: 8px;
  }

  /* 宽表格横向滚动 */
  .base-table {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .base-table tbody {
    white-space: nowrap;
  }

  /* 编辑账号信息行允许换行 */
  .edit-account-info {
    flex-wrap: wrap;
    gap: 6px;
    font-size: 12px;
  }

  /* Cookie 警告横幅内边距收敛 */
  .cookie-warn-banner {
    padding: 8px 10px;
    font-size: 12px;
    line-height: 16px;
  }
}
</style>
