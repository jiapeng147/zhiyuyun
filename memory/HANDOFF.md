# 即时接力说明

## 当前状态

### 2026-07-21 QR 登录专项修复

- 真实扫码现象：闲鱼 App 确认并完成身份校验后，网页仍未绑定账号；日志显示确认态只有基础 cookie key，没有 `unb`。
- 已补强：`xianyu_qr_login.py` 在确认态无 `unb` 时，依次从确认 payload、passport `hasLogin.do`、MTOP `mtop.taobao.idle.user.hasLogin` 反查 UID；成功后注入 `unb` 并走原有加密 cookie 落库。
- 已验证：`tests.test_qr_login_contract` 增加 MTOP hasLogin fallback 用例；后端契约套件 34 个 unittest 全绿。
- 已部署：API 镜像已重建并启动健康；`/api/qrlogin/generate` 冒烟 200，初始状态 `new`。
- 待用户手动验证：真实闲鱼 App 扫码、确认、身份校验完成后，观察 API 日志是否出现 `passport/mtop hasLogin 反查完成 hasUid=True`，并确认账号列表出现新账号。

最近一次硬化批次（`1116a1a`）已落地 P0 核心面：

- 自动发货：运行时通配规则优先级、规则按 owner_user_id 过滤、规则内空关键字拒绝、卡密 CardItem→CardGroup→Account 归属链路。
- 订单同步：状态 0/未知不再静默回落为 1=已付款，改为 6=待确认；多规格订单项解析；(account_id, external_order_id) 唯一 upsert；行锁防并发。
- 商品同步：在售/下架状态需正向证据，不能仅凭 deleted=1 反推。
- 自动回复：消息 fingerprint 必须包含方向/receiver/platform_seq/time 至少一项，缺失时禁用纯文本语义去重，避免相同文本被误判为重复。
- 租户隔离：scheduled_task_runtime / frontend_compat / items / order / restful / delivery_workflow_compat 全量走 owner_user_id + owned_account_id_subquery。
- 契约测试：21 个 unittest 用例覆盖订单状态、多规格、商在售证据、自动发货幂等、卡密并发、消息失败回滚、跨租户 SQL 编译等。
- 迁移：`036_order_delivery_rule_guards.sql` 已应用，给 `xianyu_trade_order(account_id, external_order_id)` 加唯一键、`delivery_rule` 加 `owner_user_id` 列+索引并回填存量。

## 当前 HEAD

```text
1116a1a P0 硬化批次: 自动发货/订单/商品/AI 重复消息/多租户契约与代码同步
```

工作树干净。所有 Docker 服务健康：API、Worker、Web、MySQL、Redis、Crawler。

## 下一次接手先做什么

按你的优先顺序，建议：

1. **真实闲鱼 App 二维码扫码联调**（不可自动验证）：
   - 在 admin 个人中心 -> 账号管理 -> 扫码登录。
   - 开启 API 日志 `tail -f /var/lib/docker/volumes/xianyu-assistant_api-logs/_data/api.log | grep -E 'qrcode|qr_session|cookie_store'`。
   - 观察从 `init → scanned → confirmed → cookie_persisted` 的状态迁移，验证加密 cookie 落库。
2. **真实订单接入回归**（不可自动验证）：
   - 找一个有历史订单的闲鱼账号，确保商品/订单/发货流程跑完一次。
   - 主要看订单状态 6=待确认 是否真的出现在状态映射表上。
3. **P1 商业桥 mock 契约**：
   - `apps/api/app/services/commercial_bridge.py` 已有未配置 503 降级，需要补一份 mock 契约测试覆盖 套餐列表/创建支付/回调/订单关闭/到期处理。
4. **P3 生产 preflight**：
   - 当前因为 `.env` 不可读所以 `scripts/production-readiness.sh` 走 fail-closed。可以补一份不读 `.env` 的纯配置契约测试。

## 已自动验证（最近批次）

- 21 个 unittest 全绿（11 业务契约 + 5 自动发货契约 + 5 跨租户 SQL 契约）。
- API 容器健康，`POST /api/dashboard/stats`、`POST /api/item/list`、`POST /api/order/list`、`GET /api/profile/overview`、`GET /api/navigation/overview` 用 tester token 调用返回 200。
- `deliver_rule.owner_user_id` 已存在并索引，`xianyu_trade_order.uk_trade_order_account_external` 已生效，DB schema_migration 036 落到顶部。

## 仍待真实业务验证

1. 闲鱼二维码 App 端扫码闭环（无法自动验证，UI 端 QR 状态更新不等于登录链路完全成功）。
2. 闲鱼订单的状态枚举真实映射（闲鱼平台私有枚举可能变动，需要真实订单再确认 6=待确认 的边界）。
3. 自动发货通配规则的优先级排序在生产订单下表现。
4. AI 中转站 Responses/Chat Completions 双模式真实联调（中转站 URL 不固定）。
5. 支付和商业桥的真实回调。

## 主要代码入口

```text
apps/web/src/App.vue
apps/web/src/pages/ProductPublishPage.vue
apps/web/src/pages/ProfileCenterPage.vue
apps/web/src/components/MobileLite.vue
apps/web/src/components/business/
apps/api/app/services/ai_provider.py
apps/api/app/services/ai_reply_batcher.py
apps/api/app/core/tenancy.py
apps/api/app/services/ws_delivery_handler.py
apps/api/app/services/realtime_delivery.py
apps/api/app/services/xianyu_goods_sync.py
apps/api/app/services/xianyu_order_sync.py
apps/api/app/services/commercial_bridge.py
apps/api/app/services/external_operation.py
apps/api/migrations/036_order_delivery_rule_guards.sql
apps/api/tests/test_business_contracts.py
apps/api/tests/test_delivery_contracts.py
apps/api/tests/test_tenant_scope_sql_contract.py
```

## 安全提醒

本接力文件和 `memory/` 目录不包含任何生产凭据。不要从旧聊天记录或旧 handoff 中复制敏感信息到源码或新文档。
