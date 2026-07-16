<template>
  <div class="user-mgmt-page">
    <div v-if="notice" :class="['global-notice', noticeType]" role="status">{{ notice }}</div>

    <n-card class="user-v4-hero" :bordered="false">
      <div>
        <n-tag size="small" type="success" :bordered="false">User Operations</n-tag>
        <h2>用户管理</h2>
        <p>集中处理平台概览、套餐、手动建用户、自助注册、SMTP 与账号状态。</p>
      </div>
      <n-space :size="8" align="center" wrap>
        <button class="btn" type="button" @click="loadAll">刷新数据</button>
        <button class="btn primary" type="button" :disabled="planBusy" @click="openCreatePlan">新建套餐</button>
      </n-space>
    </n-card>

    <!-- 平台概览 -->
    <n-card class="dashboard-section user-v4-card" :bordered="false">
      <template #header>平台概览</template>
      <template #header-extra><span class="user-v4-desc">总用户/账号/商品/订单与活跃趋势（仅超管可见）</span></template>
      <div v-if="overview" class="ov-grid">
        <div class="ov-card">
          <div class="ov-label">用户总数</div>
          <div class="ov-value">{{ overview.user.total }}</div>
          <div class="ov-sub">
            <span class="delta up">+{{ overview.user.new_today }} 今日</span>
            <span class="delta up">{{ overview.user.active_7d }} 7日活跃</span>
          </div>
        </div>
        <div class="ov-card">
          <div class="ov-label">店铺账号</div>
          <div class="ov-value">{{ overview.account.total }}</div>
          <div class="ov-sub">跨所有用户的可用账号</div>
        </div>
        <div class="ov-card">
          <div class="ov-label">在售商品</div>
          <div class="ov-value">{{ overview.goods.total }}</div>
          <div class="ov-sub">未软删的商品数</div>
        </div>
        <div class="ov-card">
          <div class="ov-label">订单总数</div>
          <div class="ov-value">{{ overview.order.total }}</div>
          <div class="ov-sub">
            <span class="delta up">+{{ overview.order.new_today }} 今日</span>
          </div>
        </div>
        <div class="ov-card plan-dist">
          <div class="ov-label">套餐分布</div>
          <div v-if="overview.plan_distribution.length === 0" class="ov-sub">暂无用户</div>
          <ul v-else class="plan-list">
            <li v-for="p in overview.plan_distribution" :key="p.plan_code">
              <span class="plan-code">{{ p.plan_code }}</span>
              <span class="plan-count">{{ p.count }}</span>
            </li>
          </ul>
        </div>
      </div>
      <div v-else class="loading">加载中…</div>
    </n-card>

    <!-- 套餐管理 -->
    <n-card class="dashboard-section user-v4-card" :bordered="false">
      <template #header>套餐管理</template>
      <template #header-extra><span class="user-v4-desc">新增/编辑/下架套餐。已被用户引用的套餐会被下架而非删除。</span></template>
      <div class="plan-toolbar">
        <button class="btn primary" type="button" :disabled="planBusy" @click="openCreatePlan">+ 新建套餐</button>
        <span class="muted">共 {{ plans.length }} 个套餐</span>
      </div>
      <div class="table-wrap">
        <table class="table plan-table">
          <thead>
            <tr>
              <th>代码</th><th>名称</th><th>账号配额</th><th>AI 配额/日</th>
              <th>月价</th><th>权益</th><th>排序</th><th>状态</th><th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="plans.length === 0">
              <td colspan="9" class="empty-cell">暂无套餐</td>
            </tr>
            <tr v-for="p in plans" :key="p.id">
              <td><code>{{ p.code }}</code></td>
              <td>{{ p.name }}</td>
              <td>{{ p.maxAccounts }}</td>
              <td>{{ p.aiDailyQuota }}</td>
              <td>¥{{ (p.priceCents / 100).toFixed(2) }}</td>
              <td>{{ featureSummary(p.features) }}</td>
              <td>{{ p.sortOrder }}</td>
              <td>
                <span :class="['status-dot', p.status === 1 ? 'ok' : 'off']"></span>
                {{ p.status === 1 ? '上架' : '下架' }}
              </td>
              <td class="actions">
                <button class="btn small" type="button" :disabled="planBusy" @click="openEditPlan(p)">编辑</button>
                <button class="btn small danger" type="button" :disabled="planBusy" @click="onDeletePlan(p)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </n-card>

    <!-- 订阅与账单 -->
    <n-card class="dashboard-section user-v4-card" :bordered="false">
      <template #header>订阅与账单</template>
      <template #header-extra><span class="user-v4-desc">查看用户订阅和待确认订单，支持人工确认生效。</span></template>
      <div class="billing-stats">
        <div>
          <span>累计确认收入</span>
          <strong>{{ money(billingOverview.paidAmountCents) }}</strong>
        </div>
        <div>
          <span>今日确认收入</span>
          <strong>{{ money(billingOverview.paidTodayCents) }}</strong>
        </div>
        <div>
          <span>待确认订单</span>
          <strong>{{ billingOverview.pendingOrderCount || 0 }}</strong>
        </div>
        <div>
          <span>生效订阅</span>
          <strong>{{ billingOverview.activeSubscriptionCount || 0 }}</strong>
        </div>
      </div>

      <div class="billing-settings">
        <label class="field check">
          <input v-model="billingSettings.enabled" type="checkbox" />
          <span>在客户账单页展示支付说明</span>
        </label>
        <label class="field">
          <span>订单有效期（分钟）</span>
          <input v-model.number="billingSettings.orderExpireMinutes" class="input" type="number" min="5" />
        </label>
        <label class="field wide">
          <span>支付说明</span>
          <textarea v-model="billingSettings.instructions" class="input" rows="2" placeholder="付款流程、备注订单号、确认时效等"></textarea>
        </label>
        <label class="field">
          <span>联系方式</span>
          <input v-model.trim="billingSettings.contact" class="input" placeholder="微信/邮箱/客服账号" />
        </label>
        <label class="field">
          <span>收款账户</span>
          <input v-model.trim="billingSettings.bankAccount" class="input" placeholder="银行卡/对公账户/收款说明" />
        </label>
        <label class="field">
          <span>支付宝收款码 URL</span>
          <input v-model.trim="billingSettings.alipayQrUrl" class="input" placeholder="https://..." />
        </label>
        <label class="field">
          <span>微信收款码 URL</span>
          <input v-model.trim="billingSettings.wechatQrUrl" class="input" placeholder="https://..." />
        </label>
        <div class="billing-settings-actions">
          <button class="btn primary" type="button" :disabled="billingBusy" @click="saveBillingSettings">保存账单设置</button>
        </div>
      </div>

      <div class="billing-admin-grid">
        <section class="billing-admin-panel">
          <div class="panel-title">
            <strong>订阅记录</strong>
            <span class="muted">{{ subscriptions.length }} 条</span>
          </div>
          <div class="table-wrap">
            <table class="table billing-admin-table">
              <thead>
                <tr>
                  <th>用户</th><th>套餐</th><th>状态</th><th>开始</th><th>结束</th><th>来源订单</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="subscriptions.length === 0">
                  <td colspan="6" class="empty-cell">暂无订阅</td>
                </tr>
                <tr v-for="s in subscriptions" :key="s.id">
                  <td>{{ s.username || `#${s.userId}` }}</td>
                  <td><code>{{ s.planCode }}</code></td>
                  <td><span :class="['status-pill', s.status]">{{ subscriptionStatus(s.status) }}</span></td>
                  <td class="dim">{{ fmt(s.currentPeriodStart) }}</td>
                  <td class="dim">{{ s.currentPeriodEnd ? fmt(s.currentPeriodEnd) : '长期' }}</td>
                  <td>{{ s.sourceOrderId || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
        <section class="billing-admin-panel">
          <div class="panel-title">
            <strong>订单记录</strong>
            <span class="muted">{{ billingOrders.length }} 条</span>
          </div>
          <div class="table-wrap">
            <table class="table billing-admin-table">
              <thead>
                <tr>
                  <th>订单号</th><th>用户</th><th>套餐</th><th>金额</th><th>状态</th><th>有效期</th><th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="billingOrders.length === 0">
                  <td colspan="7" class="empty-cell">暂无订单</td>
                </tr>
                <tr v-for="o in billingOrders" :key="o.id">
                  <td><code>{{ o.orderNo }}</code></td>
                  <td>{{ o.username || `#${o.userId}` }}</td>
                  <td>{{ o.planCode }}</td>
                  <td>¥{{ (o.amountCents / 100).toFixed(2) }}</td>
                  <td><span :class="['status-pill', o.status]">{{ orderStatus(o.status) }}</span></td>
                  <td class="dim">{{ fmt(o.expireTime) }}</td>
                  <td class="actions">
                    <button
                      v-if="o.status === 'pending'"
                      class="btn small primary"
                      type="button"
                      :disabled="billingBusy"
                      @click="markOrderPaid(o)"
                    >
                      确认生效
                    </button>
                    <button
                      v-if="o.status === 'pending'"
                      class="btn small danger"
                      type="button"
                      :disabled="billingBusy"
                      @click="closeAdminOrder(o)"
                    >
                      关闭
                    </button>
                    <span v-else class="dim">—</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </div>

      <div class="usage-audit-head">
        <strong>用量审计</strong>
        <span class="muted">每日用量与配额/权益拦截事件，最近各 30 条</span>
      </div>
      <div class="billing-admin-grid usage-audit-grid">
        <section class="billing-admin-panel">
          <div class="panel-title">
            <strong>每日用量</strong>
            <span class="muted">{{ usageDailyRows.length }} 条</span>
          </div>
          <div class="table-wrap">
            <table class="table billing-admin-table audit-table">
              <thead>
                <tr>
                  <th>用户</th><th>日期</th><th>指标</th><th>已用</th><th>上限</th><th>更新时间</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="usageDailyRows.length === 0">
                  <td colspan="6" class="empty-cell">暂无用量记录</td>
                </tr>
                <tr v-for="row in usageDailyRows" :key="row.id">
                  <td>{{ row.username || `#${row.userId}` }}</td>
                  <td>{{ row.usageDate || '—' }}</td>
                  <td>{{ row.metricLabel || row.metric }}</td>
                  <td>{{ row.usedCount }}</td>
                  <td>{{ displayLimit(row.limitCount) }}</td>
                  <td class="dim">{{ fmt(row.updatedTime) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
        <section class="billing-admin-panel">
          <div class="panel-title">
            <strong>配额事件</strong>
            <span class="muted">{{ quotaEventRows.length }} 条</span>
          </div>
          <div class="table-wrap">
            <table class="table billing-admin-table audit-table">
              <thead>
                <tr>
                  <th>用户</th><th>指标</th><th>变化</th><th>来源</th><th>原因</th><th>时间</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="quotaEventRows.length === 0">
                  <td colspan="6" class="empty-cell">暂无配额事件</td>
                </tr>
                <tr v-for="row in quotaEventRows" :key="row.id">
                  <td>{{ row.username || `#${row.userId}` }}</td>
                  <td>{{ row.metricLabel || row.metric }}</td>
                  <td><span :class="['event-delta', Number(row.delta || 0) > 0 ? 'plus' : 'zero']">{{ eventDelta(row.delta) }}</span></td>
                  <td>{{ sourceText(row.sourceType) }}</td>
                  <td class="reason-cell">{{ row.reason || '—' }}</td>
                  <td class="dim">{{ fmt(row.createdTime) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </n-card>

    <!-- 手动建用户 -->
    <n-card class="dashboard-section user-v4-card" :bordered="false">
      <template #header>手动建用户</template>
      <template #header-extra><span class="user-v4-desc">超管可直接创建账号，绕过注册开关和邮箱验证。</span></template>
      <form class="create-form" @submit.prevent="onCreateUser">
        <label class="field">
          <span>用户名 *</span>
          <input v-model.trim="createForm.username" class="input" placeholder="如 shop_owner_3" required />
        </label>
        <label class="field">
          <span>邮箱</span>
          <input v-model.trim="createForm.email" class="input" type="email" placeholder="可选, 用于找回密码" />
        </label>
        <label class="field">
          <span>初始密码 *</span>
          <input v-model="createForm.password" class="input" type="text" placeholder="≥ 8 位" required />
        </label>
        <label class="field">
          <span>套餐</span>
          <select v-model="createForm.planCode" class="input">
            <option v-for="p in plans" :key="p.code" :value="p.code">{{ p.name }} ({{ p.code }})</option>
          </select>
        </label>
        <label class="field check">
          <input v-model="createForm.isSuper" type="checkbox" />
          <span>超级管理员（请谨慎勾选）</span>
        </label>
        <div class="form-actions">
          <button class="btn primary" type="submit" :disabled="createBusy">{{ createBusy ? '创建中...' : '创建用户' }}</button>
        </div>
      </form>
    </n-card>

    <!-- 注册开关 -->
    <n-card class="dashboard-section user-v4-card" :bordered="false">
      <template #header>自助注册</template>
      <template #header-extra><span class="user-v4-desc">控制外部用户是否可以通过注册页自助注册账号</span></template>
      <div class="reg-row">
        <div class="reg-info">
          <div class="reg-state">
            当前状态：<strong :class="regEnabled ? 'on' : 'off'">{{ regEnabled ? '已开放注册' : '已关闭注册' }}</strong>
          </div>
          <div class="reg-hint">
            开放后，任何人可在 <code>/#/register</code> 用邮箱验证码注册。请确保下方 SMTP 已配置。
          </div>
        </div>
        <ToggleSwitch :on="regEnabled" interactive :disabled="regBusy" @click="toggleRegistration" />
      </div>
    </n-card>

    <!-- 邮箱 SMTP -->
    <n-card class="dashboard-section user-v4-card" :bordered="false">
      <template #header>邮箱 SMTP 配置</template>
      <template #header-extra><span class="user-v4-desc">用于发送注册/找回密码验证码。密码不回显。</span></template>
      <div class="form-grid">
        <label class="field">
          <span>SMTP 服务器</span>
          <input v-model.trim="email.smtpHost" class="input" placeholder="如 smtp.qq.com" />
        </label>
        <label class="field">
          <span>端口</span>
          <input v-model.number="email.smtpPort" class="input" type="number" placeholder="465" />
        </label>
        <label class="field">
          <span>发件邮箱账号</span>
          <input v-model.trim="email.smtpUser" class="input" placeholder="you@example.com" />
        </label>
        <label class="field">
          <span>授权码 / 密码</span>
          <input v-model="email.smtpPass" class="input" type="password" :placeholder="emailConfigured ? '已配置，留空保留' : '邮箱授权码'" />
        </label>
        <label class="field">
          <span>发件人名称</span>
          <input v-model.trim="email.fromName" class="input" placeholder="Lumen Ops" />
        </label>
      </div>
      <div class="form-actions">
        <button class="btn primary" type="button" :disabled="emailBusy" @click="saveEmail">{{ emailBusy ? '保存中...' : '保存邮箱配置' }}</button>
      </div>
    </n-card>

    <!-- 用户列表 -->
    <n-card class="dashboard-section user-v4-card" :bordered="false">
      <template #header>注册用户</template>
      <template #header-extra><span class="user-v4-desc">共 {{ users.length }} 个账号</span></template>
      <div class="table-wrap">
        <table class="table user-table">
          <thead>
            <tr>
              <th>ID</th><th>用户名</th><th>邮箱</th><th>角色</th><th>套餐</th>
              <th>账号配额</th><th>状态</th><th>注册时间</th><th>最近登录</th><th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="users.length === 0">
              <td colspan="10" class="empty-cell">暂无用户</td>
            </tr>
            <tr v-for="u in users" :key="u.id">
              <td>{{ u.id }}</td>
              <td><strong>{{ u.username }}</strong></td>
              <td>{{ u.email || '—' }}</td>
              <td>
                <span :class="['role-tag', u.role]">{{ u.role === 'superadmin' ? '超级管理员' : '普通用户' }}</span>
              </td>
              <td>
                <select
                  class="input plan-select"
                  :value="u.planCode"
                  :disabled="u.role === 'superadmin' || rowBusy === u.id"
                  @change="changePlan(u, $event.target.value)"
                >
                  <option v-for="p in plans" :key="p.code" :value="p.code">{{ p.name }}</option>
                </select>
              </td>
              <td>{{ u.maxAccounts }} 账号 / {{ u.aiDailyQuota }} AI</td>
              <td>
                <span :class="['status-dot', u.status === 1 ? 'ok' : 'off']"></span>
                {{ u.status === 1 ? '启用' : '禁用' }}
              </td>
              <td class="dim">{{ fmt(u.createdTime) }}</td>
              <td class="dim">{{ fmt(u.lastLoginTime) }}</td>
              <td class="actions">
                <button
                  class="btn small"
                  type="button"
                  :disabled="profileLoading && profileTarget?.id === u.id"
                  @click="openUserProfile(u)"
                >
                  画像
                </button>
                <button
                  v-if="u.role !== 'superadmin'"
                  class="btn small"
                  type="button"
                  :disabled="rowBusy === u.id"
                  @click="toggleStatus(u)"
                >
                  {{ u.status === 1 ? '禁用' : '启用' }}
                </button>
                <button
                  class="btn small"
                  type="button"
                  :disabled="rowBusy === u.id"
                  @click="openResetPwd(u)"
                >
                  重置密码
                </button>
                <button
                  v-if="u.role !== 'superadmin'"
                  class="btn small primary"
                  type="button"
                  :disabled="rowBusy === u.id || billingBusy"
                  @click="openSubscription(u)"
                >
                  开通套餐
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </n-card>

    <!-- 用户商业画像 -->
    <div v-if="profileTarget" class="modal-mask" @click.self="closeUserProfile">
      <div class="modal-card profile-card">
        <div class="modal-head">
          <div>
            <h3>{{ profileTarget.username }} 的商业画像</h3>
            <p class="modal-subtitle">用户权益、经营数据、订阅账单、用量与审计事件。</p>
          </div>
          <button class="modal-close" type="button" aria-label="关闭" @click="closeUserProfile">×</button>
        </div>
        <div v-if="profileLoading" class="profile-loading">画像加载中…</div>
        <div v-else-if="profileData" class="profile-body">
          <section class="profile-identity">
            <div>
              <div class="profile-name">{{ profileData.user.username }}</div>
              <div class="profile-meta">
                <span>ID {{ profileData.user.id }}</span>
                <span>{{ profileData.user.email || '未填写邮箱' }}</span>
                <span>{{ profileData.user.role === 'superadmin' ? '超级管理员' : '普通用户' }}</span>
              </div>
            </div>
            <div class="profile-plan">
              <span>当前套餐</span>
              <strong>{{ profileData.billing?.plan?.name || profileData.user.planCode }}</strong>
              <em>{{ profileData.billing?.plan?.expireTime ? fmt(profileData.billing.plan.expireTime) : '长期有效' }}</em>
            </div>
          </section>

          <section class="profile-kpis">
            <div class="profile-kpi">
              <span>闲鱼账号</span>
              <strong>{{ profileData.summary.accounts.total }}</strong>
              <em>{{ profileData.summary.accounts.active }} 正常 / {{ displayLimit(profileData.summary.accounts.quota) }} 配额</em>
            </div>
            <div class="profile-kpi">
              <span>商品</span>
              <strong>{{ profileData.summary.goods.total }}</strong>
              <em>{{ profileData.summary.goods.onSale }} 在售 / {{ profileData.summary.goods.sold }} 已售</em>
            </div>
            <div class="profile-kpi">
              <span>业务订单</span>
              <strong>{{ profileData.summary.orders.total }}</strong>
              <em>{{ profileData.summary.orders.newToday }} 今日新增</em>
            </div>
            <div class="profile-kpi">
              <span>会话</span>
              <strong>{{ profileData.summary.messages.conversations }}</strong>
              <em>{{ profileData.summary.messages.unread }} 未读</em>
            </div>
            <div class="profile-kpi">
              <span>确认收入</span>
              <strong>{{ money(profileData.summary.billing.paidAmountCents) }}</strong>
              <em>{{ profileData.summary.billing.pendingOrderCount }} 待确认订单</em>
            </div>
          </section>

          <section class="profile-quota">
            <div class="quota-line">
              <span>账号配额</span>
              <strong>{{ profileUsage.accounts.used }} / {{ displayLimit(profileUsage.accounts.limit) }}</strong>
            </div>
            <div class="profile-bar"><i :style="{ width: quotaPercent(profileUsage.accounts.used, profileUsage.accounts.limit) + '%' }"></i></div>
            <div class="quota-line">
              <span>AI 今日额度</span>
              <strong>{{ profileUsage.aiCallsToday.used }} / {{ displayLimit(profileUsage.aiCallsToday.limit) }}</strong>
            </div>
            <div class="profile-bar ai"><i :style="{ width: quotaPercent(profileUsage.aiCallsToday.used, profileUsage.aiCallsToday.limit) + '%' }"></i></div>
            <div class="profile-features">
              <span
                v-for="feature in profileData.billing?.plan?.featureItems || []"
                :key="feature.key"
                :class="{ off: !feature.enabled }"
              >
                {{ feature.label }}
              </span>
            </div>
          </section>

          <section class="profile-grid">
            <div class="profile-panel">
              <div class="panel-title"><strong>最近账号</strong><span class="muted">{{ profileData.recentAccounts.length }} 条</span></div>
              <table class="table profile-table">
                <thead><tr><th>账号</th><th>状态</th><th>粉丝</th><th>创建</th></tr></thead>
                <tbody>
                  <tr v-if="profileData.recentAccounts.length === 0"><td colspan="4" class="empty-cell">暂无账号</td></tr>
                  <tr v-for="row in profileData.recentAccounts" :key="row.id">
                    <td>{{ row.nickname || row.externalUid || `#${row.id}` }}</td>
                    <td>{{ row.status === 1 ? '正常' : '停用' }}</td>
                    <td>{{ row.followers }}</td>
                    <td class="dim">{{ fmt(row.createdTime) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div class="profile-panel">
              <div class="panel-title"><strong>订阅历史</strong><span class="muted">{{ profileData.subscriptions.length }} 条</span></div>
              <table class="table profile-table">
                <thead><tr><th>套餐</th><th>状态</th><th>开始</th><th>结束</th></tr></thead>
                <tbody>
                  <tr v-if="profileData.subscriptions.length === 0"><td colspan="4" class="empty-cell">暂无订阅</td></tr>
                  <tr v-for="row in profileData.subscriptions" :key="row.id">
                    <td><code>{{ row.planCode }}</code></td>
                    <td>{{ subscriptionStatus(row.status) }}</td>
                    <td class="dim">{{ fmt(row.currentPeriodStart) }}</td>
                    <td class="dim">{{ row.currentPeriodEnd ? fmt(row.currentPeriodEnd) : '长期' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div class="profile-panel">
              <div class="panel-title"><strong>账单订单</strong><span class="muted">{{ profileData.billingOrders.length }} 条</span></div>
              <table class="table profile-table">
                <thead><tr><th>订单号</th><th>套餐</th><th>金额</th><th>状态</th></tr></thead>
                <tbody>
                  <tr v-if="profileData.billingOrders.length === 0"><td colspan="4" class="empty-cell">暂无账单订单</td></tr>
                  <tr v-for="row in profileData.billingOrders" :key="row.id">
                    <td><code>{{ row.orderNo }}</code></td>
                    <td>{{ row.planCode }}</td>
                    <td>{{ money(row.amountCents) }}</td>
                    <td>{{ orderStatus(row.status) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div class="profile-panel">
              <div class="panel-title"><strong>业务订单</strong><span class="muted">{{ profileData.recentTradeOrders.length }} 条</span></div>
              <table class="table profile-table">
                <thead><tr><th>订单</th><th>买家</th><th>金额</th><th>状态</th></tr></thead>
                <tbody>
                  <tr v-if="profileData.recentTradeOrders.length === 0"><td colspan="4" class="empty-cell">暂无业务订单</td></tr>
                  <tr v-for="row in profileData.recentTradeOrders" :key="row.id">
                    <td>{{ row.externalOrderId || `#${row.id}` }}</td>
                    <td>{{ row.buyerName || '—' }}</td>
                    <td>{{ row.totalAmount || '—' }}</td>
                    <td>{{ tradeOrderStatus(row.orderStatus) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div class="profile-panel">
              <div class="panel-title"><strong>用量趋势</strong><span class="muted">{{ profileData.usageDaily.records.length }} 条</span></div>
              <table class="table profile-table">
                <thead><tr><th>日期</th><th>指标</th><th>已用</th><th>上限</th></tr></thead>
                <tbody>
                  <tr v-if="profileData.usageDaily.records.length === 0"><td colspan="4" class="empty-cell">暂无用量</td></tr>
                  <tr v-for="row in profileData.usageDaily.records" :key="row.id">
                    <td>{{ row.usageDate || '—' }}</td>
                    <td>{{ row.metricLabel || row.metric }}</td>
                    <td>{{ row.usedCount }}</td>
                    <td>{{ displayLimit(row.limitCount) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div class="profile-panel">
              <div class="panel-title"><strong>配额事件</strong><span class="muted">{{ profileData.quotaEvents.records.length }} 条</span></div>
              <table class="table profile-table">
                <thead><tr><th>指标</th><th>变化</th><th>来源</th><th>时间</th></tr></thead>
                <tbody>
                  <tr v-if="profileData.quotaEvents.records.length === 0"><td colspan="4" class="empty-cell">暂无事件</td></tr>
                  <tr v-for="row in profileData.quotaEvents.records" :key="row.id" :title="row.reason || ''">
                    <td>{{ row.metricLabel || row.metric }}</td>
                    <td><span :class="['event-delta', Number(row.delta || 0) > 0 ? 'plus' : 'zero']">{{ eventDelta(row.delta) }}</span></td>
                    <td>{{ sourceText(row.sourceType) }}</td>
                    <td class="dim">{{ fmt(row.createdTime) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
        </div>
      </div>
    </div>

    <!-- 重置密码模态 -->
    <div v-if="resetTarget" class="modal-mask" @click.self="resetTarget = null">
      <div class="modal-card small">
        <div class="modal-head">
          <h3>重置 {{ resetTarget.username }} 的密码</h3>
          <button class="modal-close" type="button" aria-label="关闭" @click="resetTarget = null">×</button>
        </div>
        <div class="modal-body">
          <label class="field">
            <span>新密码 (≥ 8 位)</span>
            <input v-model="resetPwd" class="input" type="text" placeholder="新密码" />
          </label>
          <div class="form-actions">
            <button class="btn" type="button" @click="resetTarget = null">取消</button>
            <button class="btn primary" type="button" :disabled="resetBusy || resetPwd.length < 8" @click="onResetPwd">
              {{ resetBusy ? '重置中...' : '确认重置' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 套餐编辑模态 -->
    <div v-if="editingPlan" class="modal-mask" @click.self="editingPlan = null">
      <div class="modal-card small">
        <div class="modal-head">
          <h3>{{ editingPlan.id ? '编辑套餐' : '新建套餐' }}</h3>
          <button class="modal-close" type="button" aria-label="关闭" @click="editingPlan = null">×</button>
        </div>
        <div class="modal-body">
          <label class="field">
            <span>代码 * (英文+下划线,创建后修改需谨慎)</span>
            <input v-model.trim="editingPlan.code" class="input" placeholder="如 starter / pro / max" />
          </label>
          <label class="field">
            <span>名称 *</span>
            <input v-model.trim="editingPlan.name" class="input" placeholder="如 入门版 / 专业版" />
          </label>
          <div class="form-row">
            <label class="field">
              <span>账号配额</span>
              <input v-model.number="editingPlan.maxAccounts" class="input" type="number" min="0" />
            </label>
            <label class="field">
              <span>AI 配额/日</span>
              <input v-model.number="editingPlan.aiDailyQuota" class="input" type="number" min="0" />
            </label>
          </div>
          <div class="form-row">
            <label class="field">
              <span>月价 (分, 0=免费)</span>
              <input v-model.number="editingPlan.priceCents" class="input" type="number" min="0" />
            </label>
            <label class="field">
              <span>排序</span>
              <input v-model.number="editingPlan.sortOrder" class="input" type="number" />
            </label>
          </div>
          <label class="field check">
            <input v-model="editingPlan.statusBool" type="checkbox" />
            <span>上架 (status=1)</span>
          </label>
          <label class="field">
            <span>描述</span>
            <textarea v-model="editingPlan.description" class="input" rows="2" placeholder="显示在注册/升级页"></textarea>
          </label>
          <div class="feature-editor">
            <span class="feature-editor-title">套餐权益</span>
            <label v-for="feature in featureCatalog" :key="feature.key" class="feature-check">
              <input v-model="editingPlan.features[feature.key]" type="checkbox" />
              <span>{{ feature.label }}</span>
            </label>
          </div>
          <div class="form-actions">
            <button class="btn" type="button" @click="editingPlan = null">取消</button>
            <button class="btn primary" type="button" :disabled="planBusy" @click="onSavePlan">
              {{ planBusy ? '保存中...' : '保存' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { NCard, NSpace, NTag } from 'naive-ui'
import ToggleSwitch from '../../components/ToggleSwitch.vue'
import { friendlyError } from '../../utils/friendlyError.js'
import {
  listUsers, updateUser, createUser, resetPassword,
  getOverview, adminListPlans, adminCreatePlan, adminUpdatePlan, adminDeletePlan,
  adminListSubscriptions, adminListBillingOrders, adminActivateSubscription, adminMarkBillingOrderPaid,
  adminCloseBillingOrder, adminGetBillingOverview, adminGetBillingSettings, adminSetBillingSettings,
  adminListUsageDaily, adminListQuotaEvents, adminGetUserProfile,
  getRegistration, setRegistration, getEmailConfig, setEmailConfig,
} from '../../api/admin.js'

const users = ref([])
const plans = ref([])
const overview = ref(null)
const regEnabled = ref(false)
const regBusy = ref(false)
const emailBusy = ref(false)
const createBusy = ref(false)
const planBusy = ref(false)
const billingBusy = ref(false)
const rowBusy = ref(0)
const emailConfigured = ref(false)
const email = reactive({ smtpHost: '', smtpPort: 465, smtpUser: '', smtpPass: '', fromName: '' })
const subscriptions = ref([])
const billingOrders = ref([])
const billingOverview = ref({})
const usageDailyRows = ref([])
const quotaEventRows = ref([])
const billingSettings = reactive({
  enabled: false,
  orderExpireMinutes: 1440,
  paymentMethods: ['manual_transfer'],
  instructions: '',
  contact: '',
  bankAccount: '',
  alipayQrUrl: '',
  wechatQrUrl: '',
})

const createForm = reactive({ username: '', email: '', password: '', planCode: 'free', isSuper: false })

const resetTarget = ref(null)
const resetPwd = ref('')
const resetBusy = ref(false)
const profileTarget = ref(null)
const profileData = ref(null)
const profileLoading = ref(false)

const editingPlan = ref(null)

const notice = ref('')
const noticeType = ref('success')
const featureCatalog = [
  { key: 'accounts', label: '闲鱼账号' },
  { key: 'products', label: '商品管理' },
  { key: 'messages', label: '在线消息' },
  { key: 'ai_customer_service', label: 'AI 客服' },
  { key: 'auto_reply', label: '自动回复' },
  { key: 'auto_delivery', label: '自动发货' },
  { key: 'card_warehouse', label: '卡密仓库' },
  { key: 'source_library', label: '货源库' },
  { key: 'rag', label: 'RAG 知识库' },
  { key: 'scheduled_tasks', label: '定时任务' },
  { key: 'item_polish', label: '商品擦亮' },
  { key: 'notifications', label: '通知设置' },
]
const emptyProfileUsage = { used: 0, limit: 0, remaining: 0 }
const profileUsage = computed(() => ({
  accounts: profileData.value?.billing?.usage?.accounts || emptyProfileUsage,
  aiCallsToday: profileData.value?.billing?.usage?.aiCallsToday || emptyProfileUsage,
}))

function flash(msg, type = 'success') { notice.value = msg; noticeType.value = type; setTimeout(() => { if (notice.value === msg) notice.value = '' }, 4000) }
function fmt(v) { if (!v) return '—'; return String(v).replace('T', ' ').slice(0, 16) }
function money(cents) { return `¥${(Number(cents || 0) / 100).toFixed(2)}` }
function displayLimit(value) {
  const n = Number(value || 0)
  return n >= 999999 ? '不限' : n
}
function eventDelta(delta) {
  const n = Number(delta || 0)
  return n > 0 ? `+${n}` : String(n)
}
function sourceText(sourceType) {
  const map = {
    ai: 'AI 调用',
    quota_block: '配额拦截',
    feature_block: '权益拦截',
  }
  return map[sourceType] || sourceType || '系统'
}
function quotaPercent(used, limit) {
  const max = Number(limit || 0)
  if (max <= 0 || max >= 999999) return max >= 999999 ? 8 : 100
  return Math.max(4, Math.min(100, Math.round((Number(used || 0) / max) * 100)))
}
function tradeOrderStatus(status) {
  return ({ 0: '待付款', 1: '已付款', 2: '待发货', 3: '已发货', 4: '已完成', 5: '已关闭' })[Number(status || 0)] || '未知'
}
function defaultFeatures(source = {}) {
  return Object.fromEntries(featureCatalog.map(item => [item.key, source[item.key] !== false]))
}
function featureSummary(features = {}) {
  const enabled = featureCatalog.filter(item => defaultFeatures(features)[item.key])
  return `${enabled.length}/${featureCatalog.length}`
}

async function loadAll() {
  try {
    const [uRes, pRes, rRes, eRes, oRes, sRes, boRes, billingOvRes, billingSettingsRes, usageRes, eventRes] = await Promise.all([
      listUsers(), adminListPlans(), getRegistration(), getEmailConfig(), getOverview(),
      adminListSubscriptions(), adminListBillingOrders(), adminGetBillingOverview(), adminGetBillingSettings(),
      adminListUsageDaily({ current: 1, size: 30 }), adminListQuotaEvents({ current: 1, size: 30 }),
    ])
    users.value = uRes.data || []
    plans.value = pRes.data || []
    subscriptions.value = sRes.data || []
    billingOrders.value = boRes.data || []
    billingOverview.value = billingOvRes.data || {}
    usageDailyRows.value = usageRes.data?.records || []
    quotaEventRows.value = eventRes.data?.records || []
    Object.assign(billingSettings, {
      enabled: !!billingSettingsRes.data?.enabled,
      orderExpireMinutes: Number(billingSettingsRes.data?.orderExpireMinutes || 1440),
      paymentMethods: billingSettingsRes.data?.paymentMethods || ['manual_transfer'],
      instructions: billingSettingsRes.data?.instructions || '',
      contact: billingSettingsRes.data?.contact || '',
      bankAccount: billingSettingsRes.data?.bankAccount || '',
      alipayQrUrl: billingSettingsRes.data?.alipayQrUrl || '',
      wechatQrUrl: billingSettingsRes.data?.wechatQrUrl || '',
    })
    regEnabled.value = !!(rRes.data && rRes.data.enabled)
    overview.value = oRes.data || null
    const cfg = eRes.data || {}
    email.smtpHost = cfg.smtpHost || ''
    email.smtpPort = cfg.smtpPort || 465
    email.smtpUser = cfg.smtpUser || ''
    email.fromName = cfg.fromName || ''
    emailConfigured.value = !!(cfg.smtpHost || cfg.smtpUser)
    if (!createForm.planCode && plans.value.length) createForm.planCode = plans.value[0].code
  } catch (e) {
    flash(friendlyError(e, '加载失败，请确认你是超级管理员'), 'error')
  }
}

async function toggleRegistration() {
  if (regBusy.value) return; regBusy.value = true
  try { const r = await setRegistration(!regEnabled.value); regEnabled.value = !!(r.data && r.data.enabled); flash(regEnabled.value ? '已开放自助注册' : '已关闭自助注册') }
  catch (e) { flash(friendlyError(e, '切换失败'), 'error') } finally { regBusy.value = false }
}

async function saveEmail() {
  if (emailBusy.value) return; emailBusy.value = true
  try {
    const payload = { smtpHost: email.smtpHost, smtpPort: email.smtpPort, smtpUser: email.smtpUser, fromName: email.fromName }
    if (email.smtpPass) payload.smtpPass = email.smtpPass
    await setEmailConfig(payload); email.smtpPass = ''; emailConfigured.value = !!(email.smtpHost || email.smtpUser); flash('邮箱配置已保存')
  } catch (e) { flash(friendlyError(e, '保存失败'), 'error') } finally { emailBusy.value = false }
}

async function changePlan(u, planCode) {
  if (!planCode || planCode === u.planCode) return
  rowBusy.value = u.id
  try { await updateUser(u.id, { planCode }); flash(`已将 ${u.username} 的套餐改为 ${planCode}`); await loadAll() }
  catch (e) { flash(friendlyError(e, '修改套餐失败'), 'error') } finally { rowBusy.value = 0 }
}

async function toggleStatus(u) {
  rowBusy.value = u.id
  try { await updateUser(u.id, { status: u.status === 1 ? 0 : 1 }); flash(`已${u.status === 1 ? '禁用' : '启用'} ${u.username}`); await loadAll() }
  catch (e) { flash(friendlyError(e, '操作失败'), 'error') } finally { rowBusy.value = 0 }
}

// === 手动建用户 ===
async function onCreateUser() {
  if (createBusy.value) return; createBusy.value = true
  try {
    const payload = { username: createForm.username, email: createForm.email || null, password: createForm.password, planCode: createForm.planCode, isSuper: createForm.isSuper }
    await createUser(payload)
    flash(`已创建用户 ${createForm.username}`)
    createForm.username = ''; createForm.email = ''; createForm.password = ''; createForm.isSuper = false
    await loadAll()
  } catch (e) { flash(friendlyError(e, '创建失败'), 'error') } finally { createBusy.value = false }
}

// === 重置密码 ===
function openResetPwd(u) { resetTarget.value = u; resetPwd.value = '' }
async function onResetPwd() {
  if (!resetTarget.value) return; if (resetBusy.value) return
  resetBusy.value = true
  try {
    await resetPassword(resetTarget.value.id, resetPwd.value)
    flash(`已重置 ${resetTarget.value.username} 的密码`)
    resetTarget.value = null; resetPwd.value = ''
  } catch (e) { flash(friendlyError(e, '重置失败'), 'error') } finally { resetBusy.value = false }
}

async function openUserProfile(user) {
  if (!user) return
  profileTarget.value = user
  profileData.value = null
  profileLoading.value = true
  try {
    const res = await adminGetUserProfile(user.id)
    profileData.value = res.data || null
  } catch (e) {
    flash(friendlyError(e, '用户画像加载失败'), 'error')
    profileTarget.value = null
  } finally {
    profileLoading.value = false
  }
}

function closeUserProfile() {
  profileTarget.value = null
  profileData.value = null
  profileLoading.value = false
}

// === 套餐编辑 ===
function openCreatePlan() {
  editingPlan.value = { id: 0, code: '', name: '', maxAccounts: 1, aiDailyQuota: 100, priceCents: 0, sortOrder: plans.value.length + 1, statusBool: true, description: '', features: defaultFeatures() }
}
function openEditPlan(p) {
  editingPlan.value = { id: p.id, code: p.code, name: p.name, maxAccounts: p.maxAccounts, aiDailyQuota: p.aiDailyQuota, priceCents: p.priceCents, sortOrder: p.sortOrder, statusBool: p.status === 1, description: p.description || '', features: defaultFeatures(p.features || {}) }
}
async function onSavePlan() {
  if (!editingPlan.value) return; if (planBusy.value) return
  planBusy.value = true
  try {
    const ep = editingPlan.value
    const payload = { code: ep.code.trim(), name: ep.name.trim(), maxAccounts: ep.maxAccounts, aiDailyQuota: ep.aiDailyQuota, priceCents: ep.priceCents, sortOrder: ep.sortOrder, status: ep.statusBool ? 1 : 0, description: ep.description || null, features: defaultFeatures(ep.features || {}) }
    if (ep.id) {
      await adminUpdatePlan(ep.id, payload); flash(`已更新套餐 ${ep.code}`)
    } else {
      await adminCreatePlan(payload); flash(`已创建套餐 ${ep.code}`)
    }
    editingPlan.value = null
    await loadAll()
  } catch (e) { flash(friendlyError(e, '保存失败'), 'error') } finally { planBusy.value = false }
}
async function onDeletePlan(p) {
  if (!window.confirm(`确认删除套餐 ${p.code}？若已被用户引用将自动改为下架。`)) return
  planBusy.value = true
  try { const r = await adminDeletePlan(p.id); flash(r.data || '已删除'); await loadAll() }
  catch (e) { flash(friendlyError(e, '删除失败'), 'error') } finally { planBusy.value = false }
}

function orderStatus(status) {
  return ({ pending: '待确认', paid: '已生效', closed: '已关闭', refunded: '已退款' })[status] || status || '未知'
}

function subscriptionStatus(status) {
  return ({ active: '生效中', replaced: '已替换', canceled: '已取消', expired: '已过期' })[status] || status || '未知'
}

async function markOrderPaid(order) {
  if (!order || billingBusy.value) return
  if (!window.confirm(`确认订单 ${order.orderNo} 已支付并立即开通套餐？`)) return
  billingBusy.value = true
  try {
    await adminMarkBillingOrderPaid(order.id, { note: 'manual-confirm' })
    flash(`订单 ${order.orderNo} 已确认生效`)
    await loadAll()
  } catch (e) {
    flash(friendlyError(e, '确认订单失败'), 'error')
  } finally {
    billingBusy.value = false
  }
}

async function closeAdminOrder(order) {
  if (!order || billingBusy.value) return
  if (!window.confirm(`确认关闭订单 ${order.orderNo}？`)) return
  billingBusy.value = true
  try {
    await adminCloseBillingOrder(order.id, { reason: 'admin_close' })
    flash(`订单 ${order.orderNo} 已关闭`)
    await loadAll()
  } catch (e) {
    flash(friendlyError(e, '关闭订单失败'), 'error')
  } finally {
    billingBusy.value = false
  }
}

async function saveBillingSettings() {
  if (billingBusy.value) return
  billingBusy.value = true
  try {
    await adminSetBillingSettings({
      enabled: billingSettings.enabled,
      orderExpireMinutes: Number(billingSettings.orderExpireMinutes || 1440),
      paymentMethods: billingSettings.paymentMethods,
      instructions: billingSettings.instructions,
      contact: billingSettings.contact,
      bankAccount: billingSettings.bankAccount,
      alipayQrUrl: billingSettings.alipayQrUrl,
      wechatQrUrl: billingSettings.wechatQrUrl,
    })
    flash('账单设置已保存')
    await loadAll()
  } catch (e) {
    flash(friendlyError(e, '保存账单设置失败'), 'error')
  } finally {
    billingBusy.value = false
  }
}

async function openSubscription(user) {
  if (!user || billingBusy.value) return
  const defaultPlan = user.planCode || plans.value[0]?.code || 'free'
  const planCode = window.prompt(`请输入要开通的套餐代码：${plans.value.map(p => p.code).join(' / ')}`, defaultPlan)
  if (!planCode) return
  const daysRaw = window.prompt('请输入开通天数，免费套餐可填 30', '30')
  if (!daysRaw) return
  const durationDays = Math.max(1, Number(daysRaw) || 30)
  billingBusy.value = true
  rowBusy.value = user.id
  try {
    await adminActivateSubscription(user.id, { planCode: planCode.trim(), durationDays, note: 'manual-open' })
    flash(`已为 ${user.username} 开通 ${planCode.trim()}`)
    await loadAll()
  } catch (e) {
    flash(friendlyError(e, '开通套餐失败'), 'error')
  } finally {
    billingBusy.value = false
    rowBusy.value = 0
  }
}

onMounted(loadAll)
</script>

<style scoped>
.user-mgmt-page {
  display: grid;
  gap: 16px;
  min-width: 0;
}

.user-v4-hero,
.user-v4-card {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, .04);
}

.user-v4-hero :deep(.n-card__content) {
  padding: 18px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.user-v4-hero h2 {
  margin: 12px 0 6px;
  color: #111827;
  font-size: 22px;
  font-weight: 650;
  line-height: 1.25;
}

.user-v4-hero p {
  margin: 0;
  color: #64748b;
  font-size: 13px;
  line-height: 1.65;
}

.user-v4-card :deep(.n-card__content) {
  padding: 16px;
}

.user-v4-card :deep(.n-card-header) {
  padding: 16px 16px 0;
}

.user-v4-desc {
  max-width: 340px;
  color: #64748b;
  font-size: 12px;
  line-height: 1.5;
}

.dashboard-section { margin-top: 0; }
.muted { color: var(--muted, #6b6b6b); font-size: 12px; }
.loading { padding: 24px 0; text-align: center; color: var(--muted, #6b6b6b); }

/* 概览 */
.ov-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; }
.ov-card { background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 6px; padding: 14px 16px; }
.ov-card.plan-dist { grid-column: span 2; }
.ov-label { font-size: 12px; color: var(--muted, #6b6b6b); margin-bottom: 6px; }
.ov-value { font-size: 28px; font-weight: 700; color: var(--text, #111); }
.ov-sub { margin-top: 6px; font-size: 12px; color: var(--muted, #6b6b6b); display: flex; gap: 10px; flex-wrap: wrap; }
.delta.up { color: #16bf78; }
.plan-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 4px; }
.plan-list li { display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px dashed var(--line, #e5e5e5); font-size: 13px; }
.plan-list li:last-child { border-bottom: 0; }
.plan-list .plan-code { font-family: ui-monospace, monospace; color: var(--text, #111); }
.plan-list .plan-count { color: #0f766e; font-weight: 600; }

/* 订阅与账单 */
.billing-stats { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-bottom: 14px; }
.billing-stats div { padding: 12px; border: 1px solid #e5e7eb; border-radius: 6px; background: #f8fafc; }
.billing-stats span { display: block; color: #64748b; font-size: 12px; margin-bottom: 6px; }
.billing-stats strong { display: block; color: #111827; font-size: 22px; line-height: 1.2; }
.billing-settings { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; align-items: end; margin-bottom: 14px; padding: 12px; border: 1px solid #e5e7eb; border-radius: 6px; background: #fbfdff; }
.billing-settings .wide { grid-column: span 2; }
.billing-settings-actions { display: flex; align-items: flex-end; justify-content: flex-end; }
.billing-admin-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.billing-admin-panel { min-width: 0; padding: 12px; border: 1px solid #e5e7eb; border-radius: 6px; background: #fbfdff; }
.panel-title { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 10px; }
.panel-title strong { color: #111827; font-size: 14px; }
.billing-admin-table { min-width: 640px; }
.usage-audit-head { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; margin: 16px 0 10px; }
.usage-audit-head strong { color: #111827; font-size: 14px; }
.audit-table { min-width: 760px; font-size: 12px; }
.event-delta { display: inline-flex; align-items: center; justify-content: center; min-width: 28px; padding: 2px 7px; border-radius: 999px; background: #f1f5f9; color: #64748b; }
.event-delta.plus { background: #dcfce7; color: #15803d; }
.reason-cell { max-width: 260px; white-space: normal !important; word-break: break-word; }
.status-pill { display: inline-flex; align-items: center; padding: 2px 8px; border-radius: 999px; background: #eef2f7; color: #334155; font-size: 12px; }
.status-pill.active,
.status-pill.paid { background: #dcfce7; color: #15803d; }
.status-pill.pending { background: #fef3c7; color: #92400e; }
.status-pill.replaced,
.status-pill.closed { background: #f1f5f9; color: #64748b; }

/* 套餐管理 */
.plan-toolbar { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.table-wrap { overflow-x: auto; }
.plan-table, .user-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.plan-table th, .plan-table td, .user-table th, .user-table td { padding: 12px 10px; text-align: left; border-bottom: 1px solid var(--line, #e5e5e5); white-space: nowrap; }
.plan-table th, .user-table th { color: var(--muted, #6b6b6b); font-weight: 600; }
.empty-cell { text-align: center; color: var(--muted, #6b6b6b); padding: 28px 0; }
.plan-table code { background: #f2f2f2; padding: 1px 6px; border-radius: 4px; }
.status-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 4px; vertical-align: middle; }
.status-dot.ok { background: #16bf78; }
.status-dot.off { background: #c0c0c0; }
.actions { display: flex; gap: 6px; }
.actions .btn.small { padding: 4px 8px; font-size: 12px; }

/* 注册开关 */
.reg-row { display: flex; align-items: center; justify-content: space-between; gap: 20px; }
.reg-info { min-width: 0; }
.reg-state { font-size: 15px; margin-bottom: 4px; }
.reg-state .on { color: #16bf78; }
.reg-state .off { color: var(--muted, #6b6b6b); }
.reg-hint { color: var(--muted, #6b6b6b); font-size: 13px; line-height: 1.6; }
.reg-hint code { background: #f2f2f2; padding: 1px 6px; border-radius: 5px; }

/* 表单 */
.form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; }
.create-form { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; }
.create-form .form-actions { grid-column: 1 / -1; }
.field { display: flex; flex-direction: column; gap: 6px; font-size: 13px; color: var(--muted, #6b6b6b); }
.field.check { flex-direction: row; align-items: center; gap: 8px; }
.field.check input { width: 16px; height: 16px; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.form-actions { margin-top: 12px; display: flex; gap: 8px; }
.feature-editor { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px 12px; padding: 10px; border: 1px solid #e5e7eb; border-radius: 6px; background: #f8fafc; }
.feature-editor-title { grid-column: 1 / -1; color: #64748b; font-size: 13px; }
.feature-check { display: inline-flex; align-items: center; gap: 7px; color: #374151; font-size: 13px; }
.feature-check input { width: 15px; height: 15px; }

/* modal */
.modal-mask { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 200; }
.modal-card { background: #fff; border-radius: 6px; padding: 20px; width: min(520px, 92vw); box-shadow: 0 16px 48px rgba(0,0,0,.18); }
.modal-card.small { width: min(420px, 92vw); }
.modal-card.profile-card { width: min(1180px, 94vw); max-height: 88vh; overflow: hidden; display: flex; flex-direction: column; }
.modal-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.modal-head h3 { margin: 0; font-size: 16px; }
.modal-subtitle { margin: 5px 0 0; color: #64748b; font-size: 12px; line-height: 1.5; }
.modal-close { background: transparent; border: 0; font-size: 22px; line-height: 1; color: var(--muted, #6b6b6b); cursor: pointer; padding: 4px 8px; }
.modal-body { display: flex; flex-direction: column; gap: 12px; }

.profile-loading { padding: 44px 0; color: #64748b; text-align: center; }
.profile-body { min-height: 0; overflow-y: auto; padding-right: 4px; display: grid; gap: 14px; }
.profile-identity { display: flex; align-items: flex-start; justify-content: space-between; gap: 18px; padding: 14px; border: 1px solid #e5e7eb; border-radius: 6px; background: #f8fafc; }
.profile-name { color: #111827; font-size: 22px; font-weight: 750; line-height: 1.25; }
.profile-meta { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; color: #64748b; font-size: 12px; }
.profile-meta span { padding: 2px 7px; border-radius: 999px; background: #fff; border: 1px solid #e5e7eb; }
.profile-plan { min-width: 180px; text-align: right; display: grid; gap: 3px; }
.profile-plan span { color: #64748b; font-size: 12px; }
.profile-plan strong { color: #111827; font-size: 18px; }
.profile-plan em { color: #64748b; font-size: 12px; font-style: normal; }
.profile-kpis { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 10px; }
.profile-kpi { min-width: 0; padding: 12px; border: 1px solid #e5e7eb; border-radius: 6px; background: #fff; }
.profile-kpi span { display: block; color: #64748b; font-size: 12px; margin-bottom: 6px; }
.profile-kpi strong { display: block; color: #111827; font-size: 24px; line-height: 1.15; }
.profile-kpi em { display: block; margin-top: 6px; color: #64748b; font-size: 12px; font-style: normal; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.profile-quota { padding: 12px; border: 1px solid #e5e7eb; border-radius: 6px; background: #fbfdff; display: grid; gap: 8px; }
.quota-line { display: flex; align-items: center; justify-content: space-between; gap: 12px; color: #64748b; font-size: 13px; }
.quota-line strong { color: #111827; }
.profile-bar { height: 7px; overflow: hidden; border-radius: 999px; background: #eef2f7; }
.profile-bar i { display: block; height: 100%; border-radius: inherit; background: #0f766e; }
.profile-bar.ai i { background: #2563eb; }
.profile-features { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px; }
.profile-features span { padding: 2px 7px; border-radius: 999px; background: #eefbf6; color: #0f766e; font-size: 12px; }
.profile-features span.off { background: #f1f5f9; color: #94a3b8; text-decoration: line-through; }
.profile-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.profile-panel { min-width: 0; padding: 12px; border: 1px solid #e5e7eb; border-radius: 6px; background: #fff; }
.profile-table { min-width: 520px; width: 100%; border-collapse: collapse; font-size: 12px; }
.profile-table th, .profile-table td { padding: 9px 8px; border-bottom: 1px solid #e5e7eb; text-align: left; white-space: nowrap; }
.profile-table th { color: #64748b; font-weight: 650; }
.profile-table code { padding: 1px 5px; border-radius: 4px; background: #eef2f7; color: #334155; }

/* role / status */
.plan-select { padding: 5px 8px; min-width: 96px; }
.role-tag { padding: 2px 8px; border-radius: 6px; font-size: 12px; }
.role-tag.superadmin { background: rgba(20, 184, 166,.1); color: #0f766e; }
.role-tag.user { background: #f0f0f0; color: #555; }
.dim { color: var(--muted, #999); }

/* buttons */
.btn { padding: 6px 14px; border: 1px solid var(--line, #d0d0d0); background: #fff; border-radius: 6px; cursor: pointer; font-size: 13px; }
.btn:hover { border-color: #b0b0b0; }
.btn.primary { background: #2563eb; color: #fff; border-color: #2563eb; }
.btn.primary:hover { background: #1d4ed8; border-color: #1d4ed8; }
.btn.danger { color: #c0392b; border-color: rgba(192,57,43,.3); }
.btn.small { padding: 4px 10px; font-size: 12px; }
.btn:disabled { opacity: .5; cursor: not-allowed; }

@media (max-width: 900px) {
  .user-mgmt-page {
    gap: 12px;
  }

  .user-v4-hero :deep(.n-card__content) {
    flex-direction: column;
    padding: 14px;
  }

  .user-v4-card :deep(.n-card__content) {
    padding: 12px;
  }

  .ov-card.plan-dist {
    grid-column: auto;
  }

  .billing-admin-grid {
    grid-template-columns: 1fr;
  }

  .profile-identity {
    flex-direction: column;
  }

  .profile-plan {
    text-align: left;
  }

  .profile-kpis,
  .profile-grid {
    grid-template-columns: 1fr;
  }

  .billing-stats,
  .billing-settings {
    grid-template-columns: 1fr;
  }

  .billing-settings .wide {
    grid-column: auto;
  }
}
</style>
