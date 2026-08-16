# 即时接力说明

## 当前状态

### 2026-08-12 真实账号只读验收与 WebSocket 运行态修复

- 用户已用闲鱼 App 完成真实扫码，账号成功绑定为本地 `account_id=17`；加密 Cookie 存在，账号认证正常。二维码登录闭环不再是待验证项。
- 真实只读同步通过：商品 `8/8`，订单 `58/58`、失败 0；订单无重复，58 笔均有订单明细；消息 76 条，真实上下文和在线会话可读取。
- 真实 AI 中转站调用返回非空回复；管理员只读 API 矩阵 `59/59`，双租户隔离矩阵 `13/13`，普通测试用户不能读取或操作账号 17。
- WebSocket 100 秒稳定性采样 `20/20`：HTTP 均为 `connected + hasSid + phase=connected`，数据库均为 `online_status=1/ws_status=1`，心跳年龄 0-14 秒。
- 修复了 WebSocket 仅在进程内显示在线、数据库仍离线的问题：注册成功、周期心跳、停止和断线都会尽力同步 `xianyu_account_runtime`，数据库失败不影响真实连接。
- 新增迁移 `040_account_runtime_unique.sql`，保证每个账号只有一条运行态并使用原子 upsert；生产 schema `001-040` current。
- 验收期间没有创建任何 `delivery_record`、`realtime_delivery_attempt`、`ai_auto_reply_attempt` 或 `manual_message_attempt`，未执行外发消息、自动发货、发布、改价、下架或删除。
- API unittest `50/50`，API 导入 207 条路由，生产 preflight 通过，API/Worker/Web/MySQL/Redis/Crawler 全部 healthy，域名首页和 `/ready` 均为 200。
- 受控 `stop -> start` 回归通过：停止后数据库为 `0/0`，重连后 HTTP/数据库恢复在线并连续 `15/15` 稳定，旧连接清理不会覆盖新连接状态。

### 2026-08-12 QR 登录确认换票与身份验证闭环

- 真实日志已确认根因：二维码状态返回 `CONFIRMED`，但旧代码漏掉确认后的 token 换票步骤，并调用不存在的 `mtop.taobao.idle.user.hasLogin`，上游返回 `FAIL_SYS_API_NOT_FOUNDED`，因此没有 `unb`、账号未落库。
- `93ac57d` 已补齐当前协议：`CONFIRMED token -> passport login_token/login.do -> mtop.idle.web.user.page.nav -> unb -> 加密 Cookie 落库`。
- 安全验证分支已补齐：保持同一 HTTP Cookie 会话，解析 `htoken`/验证二维码，轮询 `iv/photoVerify/check.do`，code=3 后访问官方回调收集 `unb`。前端收到二次验证二维码时会在原扫码框直接展示。
- QR query 使用当前站点参数 `appName=xianyu&fromSite=77`，轮询表单补齐设备、页面、来源和导航字段；官方验证跳转只允许 HTTPS 的 `goofish.com`/`taobao.com` 子域。
- 已验证：QR 契约、完整后端契约和前端生产构建通过；API/Web 容器 healthy，域名 200，用户已用闲鱼 App 完成真实扫码并成功绑定账号。

最近一次硬化批次（`1116a1a`）已落地 P0 核心面：

- 自动发货：运行时通配规则优先级、规则按 owner_user_id 过滤、规则内空关键字拒绝、卡密 CardItem→CardGroup→Account 归属链路。
- 订单同步：状态 0/未知不再静默回落为 1=已付款，改为 6=待确认；多规格订单项解析；(account_id, external_order_id) 唯一 upsert；行锁防并发。
- 商品同步：在售/下架状态需正向证据，不能仅凭 deleted=1 反推。
- 自动回复：消息 fingerprint 必须包含方向/receiver/platform_seq/time 至少一项，缺失时禁用纯文本语义去重，避免相同文本被误判为重复。
- 租户隔离：scheduled_task_runtime / frontend_compat / items / order / restful / delivery_workflow_compat 全量走 owner_user_id + owned_account_id_subquery。
- 契约测试：21 个 unittest 用例覆盖订单状态、多规格、商在售证据、自动发货幂等、卡密并发、消息失败回滚、跨租户 SQL 编译等。
- 迁移：`036_order_delivery_rule_guards.sql` 已应用，给 `xianyu_trade_order(account_id, external_order_id)` 加唯一键、`delivery_rule` 加 `owner_user_id` 列+索引并回填存量。

## Git 状态

```text
上传前基线：8136985
最新提交：以 git log -1 --oneline 输出为准
```

六个长期容器全部健康。本轮通知/审计租户隔离、秘密权限、WebSocket 运行态修复及验收文档由 GitHub 上传批次统一提交。

## 下一次接手先做什么

按你的优先顺序，建议：

1. **受控真实自动发货验收**（会向第三方产生副作用，需用户明确安排测试订单）：
   - 验证通配规则、多规格数量、卡密扣减、失败补发和平台发货确认。
2. **受控真实商品写操作验收**（需用户明确指定测试商品）：
   - 发布、改价、下架和删除各走一次，核对平台状态、幂等记录和本地对账。
3. **P1 商业桥 mock/真实回调契约**：
   - `apps/api/app/services/commercial_bridge.py` 已有未配置 503 降级，需要补一份 mock 契约测试覆盖 套餐列表/创建支付/回调/订单关闭/到期处理。
4. **继续长时观察真实私有协议**：
   - 订单私有状态枚举和 WebSocket 协议可能随平台变化，保留告警与待确认兜底。

## 已自动验证（最近批次）

- 50 个 API unittest 全绿，管理员只读 API 矩阵 `59/59`，双租户矩阵 `13/13`。
- 真实账号商品/订单同步、消息读取、AI 中转站和 WebSocket 在线会话均已通过。
- `delivery_rule.owner_user_id`、订单唯一键和账号运行态唯一键均已生效，数据库迁移到 040。
- 生产 preflight 需以有权读取受保护 `.env`/`secrets` 的运维身份运行；`sudo python3 scripts/production_preflight.py --env-file .env` 已通过且不显示秘密。

## 仍待真实业务验证

1. 受控真实订单的自动发货、卡密消耗、人工补发和平台确认。
2. 受控测试商品的发布、改价、下架、删除和失败对账。
3. 闲鱼未来新增私有订单状态的映射；未知状态当前会进入 6=待确认，不会伪装成已付款。
4. 支付和商业桥的真实回调。

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
