<template>
  <div class="user-mgmt-page user-v9-shell user-quota-v25-shell">
    <div v-if="notice" :class="['global-notice', noticeType]" role="status">{{ notice }}</div>

    <section class="user-v9-hero">
      <div class="user-hero-copy">
        <span class="user-kicker">用户运营</span>
        <h1>用户运营</h1>
        <p>集中处理平台概览、套餐、手动建用户、自助注册、邮件服务与账号状态。</p>
      </div>
      <div class="user-hero-actions">
        <button class="btn" type="button" @click="loadAll">刷新数据</button>
        <button class="btn primary" type="button" :disabled="planBusy" @click="openCreatePlan">新建套餐</button>
      </div>
    </section>

    <BusinessStatusStrip :items="userStatusItems" />

    <!-- 平台概览 -->
    <section class="user-v9-card">
      <div class="user-card-head">
        <div>
          <span>Platform Overview</span>
          <h3>平台概览</h3>
        </div>
        <p>总用户、账号、商品、订单与活跃趋势，仅平台负责人可见。</p>
      </div>
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
    </section>

    <!-- 套餐管理 -->
    <section class="user-v9-card">
      <div class="user-card-head">
        <div>
          <span>Plan Catalog</span>
          <h3>套餐管理</h3>
        </div>
        <p>新增、编辑和下架套餐。已被用户引用的套餐会被下架而非删除。</p>
      </div>
      <div class="plan-toolbar">
        <button class="btn primary" type="button" :disabled="planBusy" @click="openCreatePlan">+ 新建套餐</button>
        <span class="muted">共 {{ plans.length }} 个套餐</span>
      </div>
      <div class="table-wrap">
        <table class="table plan-table">
          <thead>
            <tr>
              <th>套餐标识</th><th>名称</th><th>账号配额</th><th>AI 配额/日</th>
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
    </section>

    <!-- 优惠码管理 -->
    <section class="user-v9-card">
      <div class="user-card-head">
        <div>
          <span>Coupon Rules</span>
          <h3>优惠码管理</h3>
        </div>
        <p>配置订阅订单折扣、适用套餐和使用次数限制。</p>
      </div>
      <div class="plan-toolbar">
        <button class="btn primary" type="button" :disabled="couponBusy" @click="openCreateCoupon">+ 新建优惠码</button>
        <span class="muted">共 {{ coupons.length }} 个优惠码</span>
      </div>
      <div class="table-wrap">
        <table class="table coupon-table">
          <thead>
            <tr>
              <th>优惠码</th><th>名称</th><th>优惠</th><th>门槛</th><th>适用套餐</th>
              <th>使用</th><th>有效期</th><th>状态</th><th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="coupons.length === 0">
              <td colspan="9" class="empty-cell">暂无优惠码</td>
            </tr>
            <tr v-for="c in coupons" :key="c.id">
              <td><code>{{ c.code }}</code></td>
              <td>{{ c.name }}</td>
              <td>{{ couponDiscountText(c) }}</td>
              <td>{{ c.minAmountCents ? money(c.minAmountCents) : '无门槛' }}</td>
              <td>{{ couponScopeText(c.planScope) }}</td>
              <td>{{ c.redeemedCount }} / {{ c.maxRedemptions || '不限' }}</td>
              <td class="dim">{{ couponPeriodText(c) }}</td>
              <td>
                <span :class="['status-dot', c.status === 1 ? 'ok' : 'off']"></span>
                {{ c.status === 1 ? '启用' : '停用' }}
              </td>
              <td class="actions">
                <button class="btn small" type="button" :disabled="couponBusy" @click="openEditCoupon(c)">编辑</button>
                <button class="btn small danger" type="button" :disabled="couponBusy" @click="onDeleteCoupon(c)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- 订阅与账单 -->
    <section class="user-v9-card">
      <div class="user-card-head">
        <div>
          <span>账单运营</span>
          <h3>订阅与账单</h3>
        </div>
        <p>查看用户订阅和待确认订单，支持人工确认生效。</p>
      </div>
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
          <span>累计退款</span>
          <strong>{{ money(billingOverview.refundedAmountCents) }}</strong>
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

      <div class="billing-console-grid">
        <section class="billing-console-panel">
          <div class="panel-title">
            <strong>订阅记录</strong>
            <span class="muted">{{ subscriptions.length }} 条</span>
          </div>
          <div class="table-wrap">
            <table class="table billing-console-table">
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
        <section class="billing-console-panel">
          <div class="panel-title">
            <strong>订单记录</strong>
            <span class="muted">{{ billingOrders.length }} 条</span>
          </div>
          <div class="table-wrap">
            <table class="table billing-console-table">
              <thead>
                <tr>
                  <th>订单号</th><th>用户</th><th>套餐</th><th>金额</th><th>状态</th><th>付款凭证</th><th>有效期</th><th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="billingOrders.length === 0">
                  <td colspan="8" class="empty-cell">暂无订单</td>
                </tr>
                <tr v-for="o in billingOrders" :key="o.id">
                  <td><code>{{ o.orderNo }}</code></td>
                  <td>{{ o.username || `#${o.userId}` }}</td>
                  <td>{{ o.planCode }}</td>
                  <td>¥{{ (o.amountCents / 100).toFixed(2) }}</td>
                  <td><span :class="['status-pill', o.status]">{{ orderStatus(o.status) }}</span></td>
                  <td class="proof-cell" :title="paymentProofTitle(o)">
                    <span :class="['proof-pill', paymentProofStatus(o)]">{{ paymentProofText(o) }}</span>
                  </td>
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
                    <button
                      v-if="o.status === 'paid'"
                      class="btn small danger"
                      type="button"
                      :disabled="billingBusy"
                      @click="refundOrder(o)"
                    >
                      退款
                    </button>
                    <span v-if="o.status !== 'pending' && o.status !== 'paid'" class="dim">—</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </div>

      <div class="usage-audit-head">
        <strong>用量记录</strong>
        <span class="muted">每日用量与配额/权益拦截事件，最近各 30 条</span>
      </div>
      <div class="billing-console-grid usage-audit-grid">
        <section class="billing-console-panel">
          <div class="panel-title">
            <strong>每日用量</strong>
            <span class="muted">{{ usageDailyRows.length }} 条</span>
          </div>
          <div class="table-wrap">
            <table class="table billing-console-table audit-table">
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
        <section class="billing-console-panel">
          <div class="panel-title">
            <strong>配额事件</strong>
            <span class="muted">{{ quotaEventRows.length }} 条</span>
          </div>
          <div class="table-wrap">
            <table class="table billing-console-table audit-table">
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
    </section>

    <!-- 手动建用户 -->
    <section class="user-v9-card">
      <div class="user-card-head">
        <div>
          <span>Manual Provisioning</span>
          <h3>手动建用户</h3>
        </div>
        <p>平台负责人可直接创建账号，绕过注册开关和邮箱验证。</p>
      </div>
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
          <span>平台负责人权限（请谨慎勾选）</span>
        </label>
        <div class="form-actions">
          <button class="btn primary" type="submit" :disabled="createBusy">{{ createBusy ? '创建中...' : '创建用户' }}</button>
        </div>
      </form>
    </section>

    <!-- 注册开关 -->
    <section class="user-v9-card">
      <div class="user-card-head">
        <div>
          <span>Registration Gate</span>
          <h3>自助注册</h3>
        </div>
        <p>控制外部用户是否可以通过注册页自助注册账号。</p>
      </div>
      <div class="reg-row">
        <div class="reg-info">
          <div class="reg-state">
            当前状态：<strong :class="regEnabled ? 'on' : 'off'">{{ regEnabled ? '已开放注册' : '已关闭注册' }}</strong>
          </div>
          <div class="reg-hint">
            开放后，访客可在注册页使用邮箱验证码注册。请确保下方邮件服务已配置。
          </div>
        </div>
        <ToggleSwitch :on="regEnabled" interactive :disabled="regBusy" @click="toggleRegistration" />
      </div>
    </section>

    <!-- 邮箱服务 -->
    <section class="user-v9-card">
      <div class="user-card-head">
        <div>
          <span>Email Service</span>
          <h3>邮箱服务配置</h3>
        </div>
        <p>用于发送注册和找回密码验证码，密码不会回显。</p>
      </div>
      <div class="form-grid">
        <label class="field">
          <span>邮件服务器</span>
          <input v-model.trim="email.smtpHost" class="input" placeholder="如 smtp.qq.com" />
        </label>
        <label class="field">
          <span>端口</span>
          <input v-model.number="email.smtpPort" class="input" type="number" placeholder="465" />
        </label>
        <label class="field">
          <span>发件邮箱账号</span>
          <input v-model.trim="email.smtpUser" class="input" placeholder="service@company.com" />
        </label>
        <label class="field">
          <span>授权码 / 密码</span>
          <input v-model="email.smtpPass" class="input" type="password" :placeholder="emailConfigured ? '已配置，留空保留' : '邮箱授权码'" />
        </label>
        <label class="field">
          <span>发件人名称</span>
          <input v-model.trim="email.fromName" class="input" placeholder="智鱼云运营" />
        </label>
      </div>
      <div class="form-actions">
        <button class="btn primary" type="button" :disabled="emailBusy" @click="saveEmail">{{ emailBusy ? '保存中...' : '保存邮箱配置' }}</button>
      </div>
    </section>

    <!-- 用户列表 -->
    <section class="user-v9-card">
      <div class="user-card-head">
        <div>
          <span>User Registry</span>
          <h3>注册用户</h3>
        </div>
        <p>共 {{ users.length }} 个账号。</p>
      </div>
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
                <span :class="['role-tag', u.role === 'superadmin' ? 'role-owner' : 'role-member']">{{ u.role === 'superadmin' ? '平台负责人' : '运营成员' }}</span>
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
    </section>

    <!-- 用户商业画像 -->
    <div v-if="profileTarget" class="modal-mask" @click.self="closeUserProfile">
      <div class="modal-card profile-card">
        <div class="modal-head">
          <div>
            <h3>{{ profileTarget.username }} 的商业画像</h3>
            <p class="modal-subtitle">用户权益、经营数据、订阅账单、用量与关键事件。</p>
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
                <span>{{ profileData.user.role === 'superadmin' ? '平台负责人' : '运营成员' }}</span>
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
            <div class="profile-bar">
              <progress :value="quotaPercent(profileUsage.accounts.used, profileUsage.accounts.limit)" max="100" aria-label="用户账号配额使用率"></progress>
            </div>
            <div class="quota-line">
              <span>AI 今日额度</span>
              <strong>{{ profileUsage.aiCallsToday.used }} / {{ displayLimit(profileUsage.aiCallsToday.limit) }}</strong>
            </div>
            <div class="profile-bar ai">
              <progress :value="quotaPercent(profileUsage.aiCallsToday.used, profileUsage.aiCallsToday.limit)" max="100" aria-label="用户 AI 今日额度使用率"></progress>
            </div>
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
            <span>套餐标识 *（英文+下划线，创建后修改需谨慎）</span>
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

    <!-- 优惠码编辑模态 -->
    <div v-if="editingCoupon" class="modal-mask" @click.self="editingCoupon = null">
      <div class="modal-card coupon-modal">
        <div class="modal-head">
          <h3>{{ editingCoupon.id ? '编辑优惠码' : '新建优惠码' }}</h3>
          <button class="modal-close" type="button" aria-label="关闭" @click="editingCoupon = null">×</button>
        </div>
        <div class="modal-body">
          <div class="form-row">
            <label class="field">
              <span>优惠码 *</span>
              <input v-model.trim="editingCoupon.code" class="input coupon-code-input" placeholder="如 NEWUSER30" />
            </label>
            <label class="field">
              <span>名称 *</span>
              <input v-model.trim="editingCoupon.name" class="input" placeholder="如 新用户七折" />
            </label>
          </div>
          <div class="form-row">
            <label class="field">
              <span>优惠类型</span>
              <select v-model="editingCoupon.discountType" class="input">
                <option value="fixed">固定金额</option>
                <option value="percent">百分比</option>
              </select>
            </label>
            <label class="field">
              <span>{{ editingCoupon.discountType === 'percent' ? '折扣百分比' : '抵扣金额（分）' }}</span>
              <input v-model.number="editingCoupon.discountValue" class="input" type="number" min="1" />
            </label>
          </div>
          <div class="form-row">
            <label class="field">
              <span>最高抵扣（分，百分比可用）</span>
              <input v-model.number="editingCoupon.maxDiscountCents" class="input" type="number" min="0" />
            </label>
            <label class="field">
              <span>最低订单原价（分）</span>
              <input v-model.number="editingCoupon.minAmountCents" class="input" type="number" min="0" />
            </label>
          </div>
          <div class="form-row">
            <label class="field">
              <span>总可用次数（0=不限）</span>
              <input v-model.number="editingCoupon.maxRedemptions" class="input" type="number" min="0" />
            </label>
            <label class="field">
              <span>单用户次数（0=不限）</span>
              <input v-model.number="editingCoupon.perUserLimit" class="input" type="number" min="0" />
            </label>
          </div>
          <div class="form-row">
            <label class="field">
              <span>开始时间</span>
              <input v-model="editingCoupon.startsAt" class="input" type="datetime-local" />
            </label>
            <label class="field">
              <span>结束时间</span>
              <input v-model="editingCoupon.endsAt" class="input" type="datetime-local" />
            </label>
          </div>
          <label class="field check">
            <input v-model="editingCoupon.statusBool" type="checkbox" />
            <span>启用优惠码</span>
          </label>
          <div class="feature-editor coupon-plan-scope">
            <span class="feature-editor-title">适用套餐（不勾选表示全部套餐）</span>
            <label v-for="plan in plans" :key="plan.code" class="feature-check">
              <input v-model="editingCoupon.planScopeMap[plan.code]" type="checkbox" />
              <span>{{ plan.name }} ({{ plan.code }})</span>
            </label>
          </div>
          <div class="form-actions">
            <button class="btn" type="button" @click="editingCoupon = null">取消</button>
            <button class="btn primary" type="button" :disabled="couponBusy" @click="onSaveCoupon">
              {{ couponBusy ? '保存中...' : '保存优惠码' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import BusinessStatusStrip from '../../components/business/BusinessStatusStrip.vue'
import ToggleSwitch from '../../components/ToggleSwitch.vue'
import { friendlyError } from '../../utils/friendlyError.js'
import {
  listUsers, updateUser, createUser, resetPassword,
  getOverview, adminListPlans, adminCreatePlan, adminUpdatePlan, adminDeletePlan,
  adminListSubscriptions, adminListBillingOrders, adminActivateSubscription, adminMarkBillingOrderPaid,
  adminCloseBillingOrder, adminGetBillingOverview, adminGetBillingSettings, adminSetBillingSettings,
  adminListUsageDaily, adminListQuotaEvents, adminGetUserProfile,
  adminListBillingCoupons, adminCreateBillingCoupon, adminUpdateBillingCoupon, adminDeleteBillingCoupon,
  getRegistration, setRegistration, getEmailConfig, setEmailConfig,
  adminRefundBillingOrder,
} from '../../api/admin.js'

const users = ref([])
const plans = ref([])
const overview = ref(null)
const regEnabled = ref(false)
const regBusy = ref(false)
const emailBusy = ref(false)
const createBusy = ref(false)
const planBusy = ref(false)
const couponBusy = ref(false)
const billingBusy = ref(false)
const rowBusy = ref(0)
const emailConfigured = ref(false)
const email = reactive({ smtpHost: '', smtpPort: 465, smtpUser: '', smtpPass: '', fromName: '' })
const subscriptions = ref([])
const billingOrders = ref([])
const billingOverview = ref({})
const usageDailyRows = ref([])
const quotaEventRows = ref([])
const coupons = ref([])
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
const editingCoupon = ref(null)

const notice = ref('')
const userStatusItems = computed(() => {
  const items = []
  items.push({ key: 'overview', label: '平台概览', value: overview.value ? '已加载' : '加载中', tone: overview.value ? 'green' : 'orange' })
  items.push({ key: 'users', label: '用户总数', value: overview.value ? `${overview.value.user.total}` : '—', tone: 'blue' })
  items.push({ key: 'accounts', label: '店铺账号', value: overview.value ? `${overview.value.account.total}` : '—', tone: 'blue' })
  items.push({ key: 'orders', label: '今日订单', value: overview.value ? `+${overview.value.order.new_today}` : '—', tone: overview.value && overview.value.order.new_today ? 'orange' : 'green' })
  return items
})


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
  return ({ 0: '待付款', 1: '已付款', 2: '待发货', 3: '已发货', 4: '已完成', 5: '已关闭', 6: '待确认' })[Number(status || 0)] || '未知'
}
function defaultFeatures(source = {}) {
  return Object.fromEntries(featureCatalog.map(item => [item.key, source[item.key] !== false]))
}
function featureSummary(features = {}) {
  const enabled = featureCatalog.filter(item => defaultFeatures(features)[item.key])
  return `${enabled.length}/${featureCatalog.length}`
}
function couponDiscountText(coupon) {
  if (!coupon) return '—'
  if (coupon.discountType === 'percent') {
    const cap = Number(coupon.maxDiscountCents || 0) > 0 ? `，最高 ${money(coupon.maxDiscountCents)}` : ''
    return `${coupon.discountValue}%${cap}`
  }
  return `减 ${money(coupon.discountValue)}`
}
function couponScopeText(scope = []) {
  return Array.isArray(scope) && scope.length ? scope.join(', ') : '全部套餐'
}
function couponPeriodText(coupon) {
  if (!coupon?.startsAt && !coupon?.endsAt) return '长期'
  return `${coupon.startsAt ? fmt(coupon.startsAt) : '现在'} ~ ${coupon.endsAt ? fmt(coupon.endsAt) : '长期'}`
}
function toDatetimeLocal(value) {
  if (!value) return ''
  return String(value).replace('T', ' ').slice(0, 16).replace(' ', 'T')
}
function couponScopeMap(scope = []) {
  const selected = new Set(Array.isArray(scope) ? scope : [])
  return Object.fromEntries(plans.value.map(plan => [plan.code, selected.has(plan.code)]))
}
function couponScopeFromMap(map = {}) {
  return Object.entries(map).filter(([, enabled]) => enabled).map(([code]) => code)
}

async function loadAll() {
  try {
    const [
      uRes, pRes, rRes, eRes, oRes, sRes, boRes, billingOvRes,
      billingSettingsRes, usageRes, eventRes, couponRes,
    ] = await Promise.all([
      listUsers(), adminListPlans(), getRegistration(), getEmailConfig(), getOverview(),
      adminListSubscriptions(), adminListBillingOrders(), adminGetBillingOverview(), adminGetBillingSettings(),
      adminListUsageDaily({ current: 1, size: 30 }), adminListQuotaEvents({ current: 1, size: 30 }),
      adminListBillingCoupons(),
    ])
    users.value = uRes.data || []
    plans.value = pRes.data || []
    subscriptions.value = sRes.data || []
    billingOrders.value = boRes.data || []
    billingOverview.value = billingOvRes.data || {}
    usageDailyRows.value = usageRes.data?.records || []
    quotaEventRows.value = eventRes.data?.records || []
    coupons.value = couponRes.data || []
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
    flash(friendlyError(e, '加载失败，请确认你具备平台负责人权限'), 'error')
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

function openCreateCoupon() {
  editingCoupon.value = {
    id: 0,
    code: '',
    name: '',
    discountType: 'fixed',
    discountValue: 1000,
    maxDiscountCents: 0,
    minAmountCents: 0,
    maxRedemptions: 0,
    perUserLimit: 1,
    startsAt: '',
    endsAt: '',
    statusBool: true,
    planScopeMap: couponScopeMap([]),
  }
}

function openEditCoupon(coupon) {
  editingCoupon.value = {
    id: coupon.id,
    code: coupon.code,
    name: coupon.name,
    discountType: coupon.discountType || 'fixed',
    discountValue: coupon.discountValue || 0,
    maxDiscountCents: coupon.maxDiscountCents || 0,
    minAmountCents: coupon.minAmountCents || 0,
    maxRedemptions: coupon.maxRedemptions || 0,
    perUserLimit: coupon.perUserLimit ?? 1,
    startsAt: toDatetimeLocal(coupon.startsAt),
    endsAt: toDatetimeLocal(coupon.endsAt),
    statusBool: coupon.status === 1,
    planScopeMap: couponScopeMap(coupon.planScope || []),
  }
}

async function onSaveCoupon() {
  if (!editingCoupon.value || couponBusy.value) return
  couponBusy.value = true
  try {
    const ec = editingCoupon.value
    const payload = {
      code: ec.code,
      name: ec.name,
      discountType: ec.discountType,
      discountValue: Number(ec.discountValue || 0),
      maxDiscountCents: Number(ec.maxDiscountCents || 0),
      minAmountCents: Number(ec.minAmountCents || 0),
      planScope: couponScopeFromMap(ec.planScopeMap),
      maxRedemptions: Number(ec.maxRedemptions || 0),
      perUserLimit: Number(ec.perUserLimit || 0),
      status: ec.statusBool ? 1 : 0,
      startsAt: ec.startsAt || null,
      endsAt: ec.endsAt || null,
    }
    if (ec.id) {
      await adminUpdateBillingCoupon(ec.id, payload)
      flash(`已更新优惠码 ${ec.code}`)
    } else {
      await adminCreateBillingCoupon(payload)
      flash(`已创建优惠码 ${ec.code}`)
    }
    editingCoupon.value = null
    await loadAll()
  } catch (e) {
    flash(friendlyError(e, '保存优惠码失败'), 'error')
  } finally {
    couponBusy.value = false
  }
}

async function onDeleteCoupon(coupon) {
  if (!window.confirm(`确认删除优惠码 ${coupon.code}？已有使用记录的优惠码会改为停用。`)) return
  couponBusy.value = true
  try {
    const res = await adminDeleteBillingCoupon(coupon.id)
    flash(res.data || '已删除')
    await loadAll()
  } catch (e) {
    flash(friendlyError(e, '删除优惠码失败'), 'error')
  } finally {
    couponBusy.value = false
  }
}

function orderStatus(status) {
  return ({ pending: '待确认', paid: '已生效', closed: '已关闭', refunded: '已退款' })[status] || status || '未知'
}

function paymentProofStatus(order) {
  return order?.paymentProof?.status || 'none'
}

function paymentProofText(order) {
  const proof = order?.paymentProof
  if (!proof) return '未提交'
  const statusText = ({ submitted: '待核对', confirmed: '已确认', rejected: '已退回' })[proof.status] || '已提交'
  const amount = proof.paidAmountCents ? money(proof.paidAmountCents) : ''
  return amount ? `${statusText} ${amount}` : statusText
}

function paymentProofTitle(order) {
  const proof = order?.paymentProof
  if (!proof) return '客户尚未提交付款凭证'
  return [
    proof.channel ? `渠道：${proof.channel}` : '',
    proof.payerName ? `付款人：${proof.payerName}` : '',
    proof.transactionNo ? `交易号：${proof.transactionNo}` : '',
    proof.paidAmountCents ? `实付：${money(proof.paidAmountCents)}` : '',
    proof.proofUrl ? `凭证：${proof.proofUrl}` : '',
    proof.remark ? `备注：${proof.remark}` : '',
  ].filter(Boolean).join('\n') || '客户已提交付款凭证'
}

function subscriptionStatus(status) {
  return ({ active: '生效中', replaced: '已替换', canceled: '已取消', expired: '已过期' })[status] || status || '未知'
}

async function markOrderPaid(order) {
  if (!order || billingBusy.value) return
  if (!window.confirm(`确认订单 ${order.orderNo} 已支付并立即开通套餐？`)) return
  billingBusy.value = true
  try {
    await adminMarkBillingOrderPaid(order.id, { note: '人工确认' })
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
    await adminCloseBillingOrder(order.id, { reason: '人工关闭' })
    flash(`订单 ${order.orderNo} 已关闭`)
    await loadAll()
  } catch (e) {
    flash(friendlyError(e, '关闭订单失败'), 'error')
  } finally {
    billingBusy.value = false
  }
}

async function refundOrder(order) {
  if (!order || billingBusy.value) return
  const amountYuan = (Number(order.amountCents || 0) / 100).toFixed(2)
  const reason = window.prompt(`请输入订单 ${order.orderNo} 的退款原因`, order.refundReason || '人工退款')
  if (reason === null) return
  const amountRaw = window.prompt('请输入退款金额（元）', amountYuan)
  if (amountRaw === null) return
  const refundAmountCents = Math.max(0, Math.round(Number(amountRaw || 0) * 100))
  if (!window.confirm(`确认退款 ${money(refundAmountCents)}？该订单关联的套餐权益会被撤销或回退。`)) return
  billingBusy.value = true
  try {
    await adminRefundBillingOrder(order.id, {
      reason: reason || '人工退款',
      refundAmountCents,
    })
    flash(`订单 ${order.orderNo} 已退款`)
    await loadAll()
  } catch (e) {
    flash(friendlyError(e, '退款失败'), 'error')
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
  const planCode = window.prompt(`请输入要开通的套餐标识：${plans.value.map(p => p.code).join(' / ')}`, defaultPlan)
  if (!planCode) return
  const daysRaw = window.prompt('请输入开通天数，免费套餐可填 30', '30')
  if (!daysRaw) return
  const durationDays = Math.max(1, Number(daysRaw) || 30)
  billingBusy.value = true
  rowBusy.value = user.id
  try {
    await adminActivateSubscription(user.id, { planCode: planCode.trim(), durationDays, note: '人工开通' })
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
.user-v9-shell {
  --text: #101827;
  --muted: #667085;
  --subtle: #8a94a6;
  --line: #e3e8ef;
  --panel: #ffffff;
  --soft: #f6f8fb;
  --soft-blue: #eef5ff;
  --primary: #1d4ed8;
  --primary-strong: #1e40af;
  --accent: #0f766e;
  --accent-soft: #ecfdf5;
  --warn: #b45309;
  --danger: #b91c1c;
  --ease-out: cubic-bezier(0.23, 1, 0.32, 1);
  display: grid;
  gap: 16px;
  min-width: 0;
  color: var(--text);
}

.global-notice {
  position: sticky;
  top: 0;
  z-index: 20;
  padding: 10px 12px;
  border: 1px solid rgba(15, 118, 110, .18);
  border-radius: 8px;
  background: #f0fdfa;
  color: #0f766e;
  font-size: 13px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, .08);
}

.global-notice.error {
  border-color: rgba(185, 28, 28, .2);
  background: #fff1f2;
  color: var(--danger);
}

.user-v9-hero {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 20px;
  align-items: center;
  overflow: hidden;
  padding: 24px;
  border: 1px solid rgba(148, 163, 184, .24);
  border-radius: 8px;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, .96), rgba(248, 251, 255, .94) 54%, rgba(239, 253, 250, .94)),
    linear-gradient(90deg, rgba(29, 78, 216, .08), rgba(15, 118, 110, .08));
  box-shadow: 0 14px 40px rgba(15, 23, 42, .07);
}

.user-v9-hero::before {
  content: "";
  position: absolute;
  inset: auto 24px 0 24px;
  height: 3px;
  background: linear-gradient(90deg, var(--primary), var(--accent));
}

.user-hero-copy,
.user-hero-actions {
  position: relative;
  z-index: 1;
}

.user-kicker {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 9px;
  border: 1px solid rgba(15, 118, 110, .18);
  border-radius: 999px;
  background: rgba(236, 253, 245, .82);
  color: var(--accent);
  font-size: 12px;
  font-weight: 700;
}

.user-v9-hero h1 {
  margin: 12px 0 7px;
  color: var(--text);
  font-size: 26px;
  font-weight: 760;
  line-height: 1.18;
}

.user-v9-hero p {
  max-width: 720px;
  margin: 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.65;
}

.user-hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}

.user-v9-card {
  min-width: 0;
  padding: 16px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--panel);
  box-shadow: 0 10px 28px rgba(15, 23, 42, .05);
  transition: border-color 180ms var(--ease-out), box-shadow 180ms var(--ease-out), transform 180ms var(--ease-out);
}

.user-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 14px;
  margin-bottom: 14px;
  border-bottom: 1px solid var(--line);
}

.user-card-head span {
  color: var(--accent);
  font-size: 12px;
  font-weight: 760;
}

.user-card-head h3 {
  margin: 4px 0 0;
  color: var(--text);
  font-size: 17px;
  font-weight: 740;
  line-height: 1.35;
}

.user-card-head p {
  max-width: 430px;
  margin: 2px 0 0;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.55;
  text-align: right;
}

.muted,
.dim {
  color: var(--muted);
  font-size: 12px;
}

.loading {
  padding: 28px 0;
  color: var(--muted);
  text-align: center;
}

.ov-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(188px, 1fr));
  gap: 12px;
}

.ov-card,
.billing-stats div,
.profile-kpi {
  min-width: 0;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: linear-gradient(180deg, #ffffff, #f8fafc);
}

.ov-card {
  display: flex;
  min-height: 112px;
  flex-direction: column;
  justify-content: space-between;
  padding: 14px;
}

.ov-card.plan-dist {
  grid-column: span 2;
}

.ov-label {
  margin-bottom: 8px;
  color: var(--muted);
  font-size: 12px;
}

.ov-value {
  color: var(--text);
  font-size: 28px;
  font-weight: 780;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}

.ov-sub {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
  color: var(--muted);
  font-size: 12px;
}

.delta.up {
  color: var(--accent);
  font-weight: 650;
}

.plan-list {
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding: 0;
  margin: 0;
  list-style: none;
}

.plan-list li {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 6px 0;
  border-bottom: 1px dashed var(--line);
  color: var(--muted);
  font-size: 13px;
}

.plan-list li:last-child {
  border-bottom: 0;
}

.plan-list .plan-code,
code {
  padding: 2px 6px;
  border-radius: 6px;
  background: #eef2f7;
  color: #334155;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 12px;
}

.plan-list .plan-count {
  color: var(--accent);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.billing-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(154px, 1fr));
  gap: 12px;
  margin-bottom: 14px;
}

.billing-stats div {
  padding: 13px 14px;
}

.billing-stats span,
.profile-kpi span {
  display: block;
  margin-bottom: 7px;
  color: var(--muted);
  font-size: 12px;
}

.billing-stats strong,
.profile-kpi strong {
  display: block;
  color: var(--text);
  font-size: 22px;
  font-weight: 760;
  line-height: 1.15;
  font-variant-numeric: tabular-nums;
}

.billing-settings,
.billing-console-panel,
.profile-quota,
.profile-panel,
.feature-editor {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #fbfdff;
}

.billing-settings {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  align-items: end;
  padding: 14px;
  margin-bottom: 14px;
}

.billing-settings .wide {
  grid-column: span 2;
}

.billing-settings-actions {
  display: flex;
  align-items: flex-end;
  justify-content: flex-end;
}

.billing-console-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.billing-console-panel,
.profile-panel {
  min-width: 0;
  padding: 12px;
}

.panel-title,
.usage-audit-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.panel-title {
  margin-bottom: 10px;
}

.panel-title strong,
.usage-audit-head strong {
  color: var(--text);
  font-size: 14px;
  font-weight: 720;
}

.billing-console-table {
  min-width: 640px;
}

.coupon-table {
  min-width: 920px;
}

.audit-table {
  min-width: 760px;
  font-size: 12px;
}

.usage-audit-head {
  align-items: baseline;
  margin: 16px 0 10px;
}

.plan-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.table-wrap {
  width: 100%;
  overflow-x: auto;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #fff;
}

.table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 13px;
}

.table th,
.table td {
  padding: 11px 12px;
  border-bottom: 1px solid var(--line);
  color: #334155;
  text-align: left;
  white-space: nowrap;
}

.table th {
  position: sticky;
  top: 0;
  z-index: 1;
  background: #f8fafc;
  color: #475569;
  font-size: 12px;
  font-weight: 720;
}

.table tbody tr {
  transition: background-color 140ms var(--ease-out);
}

.table tbody tr:last-child td {
  border-bottom: 0;
}

.empty-cell {
  padding: 30px 0;
  color: var(--muted);
  text-align: center;
}

.reason-cell {
  max-width: 260px;
  white-space: normal !important;
  word-break: break-word;
}

.status-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  margin-right: 5px;
  border-radius: 50%;
  vertical-align: middle;
}

.status-dot.ok {
  background: #10b981;
}

.status-dot.off {
  background: #cbd5e1;
}

.status-pill,
.proof-pill,
.event-delta,
.role-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 650;
  white-space: nowrap;
}

.status-pill,
.proof-pill {
  padding: 3px 8px;
  background: #eef2f7;
  color: #475569;
}

.status-pill.active,
.status-pill.paid,
.proof-pill.confirmed {
  background: #dcfce7;
  color: #15803d;
}

.status-pill.pending,
.proof-pill.submitted {
  background: #eff6ff;
  color: var(--primary);
}

.status-pill.replaced,
.status-pill.closed {
  background: #f1f5f9;
  color: #64748b;
}

.proof-pill.rejected {
  background: #fee2e2;
  color: var(--danger);
}

.proof-cell {
  min-width: 110px;
}

.event-delta {
  min-width: 30px;
  padding: 3px 8px;
  background: #f1f5f9;
  color: #64748b;
}

.event-delta.plus {
  background: #dcfce7;
  color: #15803d;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.reg-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.reg-info {
  min-width: 0;
}

.reg-state {
  margin-bottom: 4px;
  color: var(--text);
  font-size: 15px;
}

.reg-state .on {
  color: var(--accent);
}

.reg-state .off {
  color: var(--muted);
}

.reg-hint {
  color: var(--muted);
  font-size: 13px;
  line-height: 1.6;
}

.form-grid,
.create-form {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
}

.create-form .form-actions {
  grid-column: 1 / -1;
}

.field {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 6px;
  color: var(--muted);
  font-size: 13px;
}

.field.check {
  flex-direction: row;
  align-items: center;
  gap: 8px;
  color: #475569;
}

.field.check input {
  width: 16px;
  height: 16px;
  accent-color: var(--primary);
}

.input {
  width: 100%;
  min-height: 34px;
  box-sizing: border-box;
  padding: 7px 10px;
  border: 1px solid #d8e0ea;
  border-radius: 8px;
  outline: none;
  background: #fff;
  color: var(--text);
  font-size: 13px;
  transition: border-color 140ms var(--ease-out), box-shadow 140ms var(--ease-out), background-color 140ms var(--ease-out);
}

textarea.input {
  min-height: 66px;
  line-height: 1.5;
  resize: vertical;
}

.input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(29, 78, 216, .12);
}

.input:disabled {
  background: #f1f5f9;
  color: #94a3b8;
}

.plan-select {
  min-width: 108px;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.form-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.feature-editor {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px 12px;
  padding: 12px;
}

.feature-editor-title {
  grid-column: 1 / -1;
  color: var(--muted);
  font-size: 13px;
  font-weight: 650;
}

.feature-check {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: #374151;
  font-size: 13px;
}

.feature-check input {
  width: 15px;
  height: 15px;
  accent-color: var(--primary);
}

.coupon-code-input {
  text-transform: uppercase;
}

.coupon-plan-scope {
  max-height: 180px;
  overflow: auto;
}

.role-tag {
  padding: 3px 8px;
}

.role-tag.role-owner {
  background: rgba(15, 118, 110, .1);
  color: var(--accent);
}

.role-tag.role-member {
  background: #eef2f7;
  color: #475569;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 34px;
  padding: 0 13px;
  border: 1px solid #d8e0ea;
  border-radius: 8px;
  background: #fff;
  color: #1f2937;
  cursor: pointer;
  font-size: 13px;
  font-weight: 650;
  line-height: 1;
  white-space: nowrap;
  transition: transform 140ms var(--ease-out), border-color 140ms var(--ease-out), background-color 140ms var(--ease-out), color 140ms var(--ease-out), box-shadow 140ms var(--ease-out);
}

.btn:active {
  transform: scale(.98);
}

.btn.primary {
  border-color: var(--primary);
  background: var(--primary);
  color: #fff;
  box-shadow: 0 8px 18px rgba(29, 78, 216, .18);
}

.btn.danger {
  border-color: rgba(185, 28, 28, .24);
  color: var(--danger);
}

.btn.small,
.actions .btn.small {
  min-height: 28px;
  padding: 0 9px;
  font-size: 12px;
}

.btn:disabled {
  cursor: not-allowed;
  opacity: .5;
  transform: none;
  box-shadow: none;
}

.modal-mask {
  position: fixed;
  inset: 0;
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: rgba(15, 23, 42, .48);
}

.modal-card {
  width: min(520px, 92vw);
  padding: 20px;
  border: 1px solid rgba(226, 232, 240, .88);
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 24px 70px rgba(15, 23, 42, .24);
}

.modal-card.small {
  width: min(420px, 92vw);
}

.modal-card.coupon-modal {
  width: min(720px, 94vw);
}

.modal-card.profile-card {
  display: flex;
  width: min(1180px, 94vw);
  max-height: 88vh;
  flex-direction: column;
  overflow: hidden;
}

.modal-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 16px;
}

.modal-head h3 {
  margin: 0;
  color: var(--text);
  font-size: 17px;
  font-weight: 740;
}

.modal-subtitle {
  margin: 5px 0 0;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.5;
}

.modal-close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  padding: 0;
  border: 1px solid transparent;
  border-radius: 8px;
  background: transparent;
  color: var(--muted);
  cursor: pointer;
  font-size: 22px;
  line-height: 1;
  transition: transform 140ms var(--ease-out), background-color 140ms var(--ease-out), color 140ms var(--ease-out);
}

.modal-close:active {
  transform: scale(.96);
}

.modal-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.profile-loading {
  padding: 44px 0;
  color: var(--muted);
  text-align: center;
}

.profile-body {
  display: grid;
  min-height: 0;
  gap: 14px;
  overflow-y: auto;
  padding-right: 4px;
}

.profile-identity {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  padding: 14px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: linear-gradient(135deg, #f8fafc, #eef5ff);
}

.profile-name {
  color: var(--text);
  font-size: 22px;
  font-weight: 760;
  line-height: 1.25;
}

.profile-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
  color: var(--muted);
  font-size: 12px;
}

.profile-meta span {
  padding: 3px 8px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: #fff;
}

.profile-plan {
  display: grid;
  min-width: 180px;
  gap: 3px;
  text-align: right;
}

.profile-plan span,
.profile-plan em {
  color: var(--muted);
  font-size: 12px;
  font-style: normal;
}

.profile-plan strong {
  color: var(--text);
  font-size: 18px;
}

.profile-kpis {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
}

.profile-kpi {
  padding: 12px;
}

.profile-kpi em {
  display: block;
  margin-top: 6px;
  overflow: hidden;
  color: var(--muted);
  font-size: 12px;
  font-style: normal;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.profile-quota {
  display: grid;
  gap: 8px;
  padding: 12px;
}

.quota-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: var(--muted);
  font-size: 13px;
}

.quota-line strong {
  color: var(--text);
}

.profile-bar {
  height: 7px;
  overflow: hidden;
  border-radius: 999px;
  background: #e8edf5;
}

.profile-bar progress {
  display: block;
  width: 100%;
  height: 100%;
  overflow: hidden;
  appearance: none;
  border: 0;
  border-radius: inherit;
  background: transparent;
}

.profile-bar progress::-webkit-progress-bar {
  border-radius: inherit;
  background: #e8edf5;
}

.profile-bar progress::-webkit-progress-value {
  border-radius: inherit;
  background: var(--accent);
}

.profile-bar progress::-moz-progress-bar {
  border-radius: inherit;
  background: var(--accent);
}

.profile-bar.ai progress::-webkit-progress-value {
  background: var(--primary);
}

.profile-bar.ai progress::-moz-progress-bar {
  background: var(--primary);
}

.profile-features {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 4px;
}

.profile-features span {
  padding: 3px 8px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 12px;
}

.profile-features span.off {
  background: #f1f5f9;
  color: #94a3b8;
  text-decoration: line-through;
}

.profile-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.profile-table {
  min-width: 520px;
  font-size: 12px;
}

@media (hover: hover) and (pointer: fine) {
  .user-v9-card:hover {
    border-color: rgba(29, 78, 216, .22);
    box-shadow: 0 14px 34px rgba(15, 23, 42, .08);
    transform: translateY(-1px);
  }

  .table tbody tr:hover {
    background: #f8fafc;
  }

  .btn:hover {
    border-color: #b7c3d4;
    background: #f8fafc;
  }

  .btn.primary:hover {
    border-color: var(--primary-strong);
    background: var(--primary-strong);
  }

  .btn.danger:hover {
    border-color: rgba(185, 28, 28, .38);
    background: #fff1f2;
  }

  .modal-close:hover {
    background: #f1f5f9;
    color: var(--text);
  }
}

@media (max-width: 1100px) {
  .billing-settings {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .billing-console-grid {
    grid-template-columns: 1fr;
  }

  .profile-kpis {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .user-v9-shell {
    gap: 12px;
  }

  .user-v9-hero {
    grid-template-columns: 1fr;
    padding: 20px;
  }

  .user-hero-actions {
    justify-content: flex-start;
  }

  .user-v9-card {
    padding: 12px;
  }

  .user-card-head {
    display: grid;
    gap: 8px;
  }

  .user-card-head p {
    max-width: none;
    text-align: left;
  }

  .ov-card.plan-dist,
  .billing-settings .wide {
    grid-column: auto;
  }

  .billing-settings,
  .profile-grid {
    grid-template-columns: 1fr;
  }

  .profile-identity {
    flex-direction: column;
  }

  .profile-plan {
    text-align: left;
  }
}

@media (max-width: 640px) {
  .user-v9-hero h1 {
    font-size: 22px;
  }

  .billing-stats,
  .form-grid,
  .create-form,
  .form-row,
  .profile-kpis {
    grid-template-columns: 1fr;
  }

  .reg-row,
  .plan-toolbar,
  .usage-audit-head {
    align-items: flex-start;
    flex-direction: column;
  }

  .modal-mask {
    align-items: flex-start;
    padding: 12px;
  }

  .modal-card,
  .modal-card.small,
  .modal-card.coupon-modal,
  .modal-card.profile-card {
    width: 100%;
  }
}
</style>
