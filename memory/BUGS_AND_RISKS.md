# BUG、风险和未完成事项

## 已修复并验证（最近批次 93ac57d）

### 闲鱼扫码确认后未绑定账号

位置：`apps/api/app/core/xianyu_qr_login.py`、`apps/api/tests/test_qr_login_contract.py`

处理：

- 问题根因不是二维码过期，而是确认态漏掉 token 换票，旧 MTOP hasLogin API 又已不存在，导致 `unb` 无法落库。
- 当前链路为：确认 token -> `login_token/login.do` -> `mtop.idle.web.user.page.nav` -> Cookie 加密保存与账号绑定。
- 身份验证分支保持同一会话，解析 `htoken` 和二次二维码，轮询 `photoVerify/check.do`，完成后访问官方回调拿 `unb`。
- 前端会在原二维码区域切换显示身份验证二维码，不再只给一个不明确的小链接。
- 日志只输出状态码、是否拿到 UID、顶层 key、cookie key 名称，不输出 cookie/token 值。

验证：

- QR 契约 17/17、完整后端契约 38/38、前端生产构建均通过。
- API/Web 容器 healthy，域名 200，真实上游二维码生成和测试会话清理成功。

仍需真实验收：用户使用闲鱼 App 重新扫码并完成身份校验，确认账号能出现在账号列表。

### 自动发货规则匹配缺优先级、空关键字、全租户

位置：`apps/api/app/services/ws_delivery_handler.py`、迁移 `036_order_delivery_rule_guards.sql`

处理：

- 通配规则 / 关键字规则按优先级排序，精确匹配优先于通配。
- 规则内 `goods_keywords` 空时不创建规则，运行时也拒绝空规则触发。
- `DeliveryRule.owner_user_id` 列加上并索引，存量回填账号 owner。
- 运行时通过 `owner_user_id` 过滤 + 跨账号白名单校验，防止租户越权触发他人规则。

### 自动发货幂等 + 平台重试不重发 + 失败回滚

位置：`apps/api/app/services/ws_delivery_handler.py`、`apps/api/app/services/realtime_delivery.py`

契约：

- 同一 `delivery_record` 二次进入成功路径不再发送第二条消息（test_idempotent_success_does_not_send_twice）。
- 平台推送同一 delivery 回调时不重发消息（test_platform_retry_does_not_resend_message）。
- 结果 unknown 不自动重试（test_unknown_message_result_is_not_automatically_retried）。
- 卡密并发扣减只允许消耗可用库存（test_concurrent_card_claim_only_consumes_available_inventory）。
- 消息发送失败回滚已占用卡密（test_message_failure_releases_claimed_cards）。

### 订单状态未知不再静默回落到 1=已付款

位置：`apps/api/app/services/xianyu_order_sync.py`、`apps/api/app/models/entities.py`

处理：

- `_map_order_status` 的 0/未知 路径返回 `order_status = 6`（新增“待确认”枚举）并附带 last_error。
- 前端 `OrdersPage` + `orderPageState` 暴露 `待确认` 状态。
- 不在 UI 上把未知错误展示为“已付款未发货”假状态。

### 订单 (account_id, external_order_id) 唯一 upsert + 行锁

位置：迁移 `036_order_delivery_rule_guards.sql`、`xianyu_order_sync.py`

处理：

- 库上加 `UNIQUE KEY uk_trade_order_account_external`，避免重复订单入库。
- 同步路径先 `SELECT ... FOR UPDATE` 行锁，再 upsert。
- 多规格订单项解析每条 SKU 单独入库到 `xianyu_trade_order_item`。

### 商品在售/下架需正向证据

位置：`apps/api/app/services/xianyu_goods_sync.py`

处理：

- 不再以 `deleted=1` 作为唯一下架信号。
- 同步结果中只有显式“在售/下架/已售完”标记才能落相应状态；缺证据时落 last_error 并保留原状态。

### AI 重复消息误判

位置：`apps/api/app/services/ai_reply_batcher.py`

处理：

- `_message_fingerprint` 加 `direction + receiver + platform_seq + time` 至少一项证据；任一缺失时 `semantic_fingerprint` 返回空，禁用语义去重。
- 仍未防住的同内容重放由 `pnm/source UID` 直接命中。

### 多租户隔离补全（scheduled_task + 兼容 + 兼容账号）

位置：`frontend_compat.py` / `scheduled_task_runtime.py` / `order.py` / `items.py` / `restful.py` / `delivery_workflow_compat.py`

覆盖：

- `scheduled-task` 列表/详情/创建/更新/删除/手动触发走 `owner_user_id`。
- 自动发货、卡密、货源、配置按租户过滤。
- `target_goods draft + sync progress + accounts summary` 按租户过滤。

### 测试体系扩张

新增位置：

- `apps/api/tests/test_business_contracts.py` (11)
- `apps/api/tests/test_delivery_contracts.py` (5)
- `apps/api/tests/test_tenant_scope_sql_contract.py` (5)

合计 21 个用例，使用 in-process SQLAlchemy 编译 + Mock，不依赖 DB。

## 历史已修复

### 请求忙碌状态永久卡住

位置：`apps/web/src/utils/request.js`

处理：pending 集合结束时优先使用客户端 X-Request-Id 而不是响应头。

### 缺少数据库表导致消息和同步接口 500

迁移：`029_missing_message_and_sync_task_tables.sql`

补齐：`xianyu_message`、`xianyu_goods_sync_task`。

### 宝塔静态资源反代白屏

处理：location `^~ /assets/`、`^~ /xya/` 等路径优先级。

### AI 中转站 Responses 兼容

位置：`apps/api/app/services/ai_provider.py`

支持 Responses、Chat Completions、标准 /v1、自定义 endpoint，404 时提示检查 base URL。

## 预期降级，不是前端崩溃

### 广告商业服务未配置

`/api/ads/*` 在商业桥未配置时返回 503 是设计行为。前端必须：

- 显示“广告商业服务未配置”
- 不展示临时套餐
- 禁用提交申请与支付
- 不伪造订单成功

### 自动发货桥未配置

类似：runner 与上游告警系统未配置时不能伪造成功率/告警。

## 仍需实际业务复现的风险（不可自动验证）

1. 真实闲鱼 App 二维码扫码闭环：UI 的 QR 轮询不等于闲鱼 App 登录链路完全成功。
2. 闲鱼订单状态枚举的真实取值：私有枚举可能演变，6=待确认 是兜底边界。
3. 自动发货通配规则在真实订单下的优先级表现（电商大促场景）。
4. 中转站 AI Responses/Chat Completions 双模式在真实流量下的稳定性。
5. 支付与商业桥的真实回调。

## 安全提醒

任何凭据（API key、cookie、token、第三方账号密码）不得写在源码、日志或本目录。需要密钥时读取受保护的 `secrets/` 或由用户重新提供。
