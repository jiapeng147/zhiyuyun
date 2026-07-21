# BUG、风险和未完成事项

## 已修复并验证

### 请求忙碌状态永久卡住

位置：`apps/web/src/utils/request.js`

问题：请求开始登记使用客户端 `X-Request-Id`，结束时错误地优先读取响应头中的另一个 request id，导致 pending 集合无法清空，后台长期显示加载。

处理：结束时优先使用客户端配置中的 request id。

### 缺少数据库表导致消息和同步接口 500

迁移：`apps/api/migrations/029_missing_message_and_sync_task_tables.sql`

补齐：

- `xianyu_message`
- `xianyu_goods_sync_task`

### 宝塔静态资源反代导致白屏

问题：宝塔正则 location 抢先处理 `/assets/` 和 `/xya/`，静态资源 404，浏览器把 HTML 当 JS。

处理：反代配置使用 `location ^~ /assets/`、`location ^~ /xya/` 等路径优先级。

配置位置不在本仓库时，按服务器当前 Nginx 托管配置检查。

### AI 中转站 Responses 兼容

用户实际使用中转站时遇到官方地址 404。当前代码已经支持：

- Responses 模式
- Chat Completions 模式
- 标准 `/v1` base URL
- 自定义 endpoint
- 404 时返回检查 `/v1` 的明确提示

后端位置：`apps/api/app/services/ai_provider.py`
配置页面：`apps/web/src/pages/admin/ModelSettingsPage.vue`

### 商品发布和个人中心阶段问题

- AboutSettings 的 `ref` 在模板中误用 `.value` 已修正。
- AboutSettings 的 computed 在 `aboutContent` 声明前定义已修正。
- ProductPublishPage 的发布状态、账号、图片和核验状态已接入统一状态带。
- ProfileCenterPage 的状态带已接入，安全等级重复文本问题在当前版本中未再出现。

## 预期降级，不是前端崩溃

### 广告商业服务未配置

接口：

```text
/api/ads/plans
/api/ads/payment/methods
/api/ads/applications
```

商业桥未配置时返回 503 是设计行为。前端必须：

- 显示广告商业服务未配置
- 不展示临时套餐
- 禁用提交申请
- 禁用支付
- 不伪造成功订单

当前全量回归已经验证该状态能正常显示。

## 仍需实际业务复现的风险

以下来自静态审查或历史交接，不能直接当作已确认 BUG：

1. `apps/api/app/services/xianyu_goods_sync.py` 的商品 status 映射语义需要拿真实闲鱼响应确认，可能存在在售/下架反转风险。
2. `automation_runtime.py` 在消息 UID 缺失时会使用内容摘要做幂等键，相同文本消息可能被误判为重复。
3. `external_operation.py` 外部操作重试次数少，并发锁粒度需要继续检查，重复发布会带来风控风险。
4. 自动发货通配规则和多规格订单需要真实订单回归，避免错误发卡。
5. 闲鱼二维码登录需要真实手机扫码验证，浏览器页面有 QR 状态更新不等于闲鱼 App 登录链路完全成功。
6. 移动端目前只有 Lite 页面；复杂业务页会切换到桌面版，不能把 Lite 覆盖率误认为全部移动功能。

## 闲鱼风控风险

当前系统具备签名、Cookie/token 刷新、滑块和 WebSocket 等能力，但商业化前仍需评估：

- SPM、UA、appKey 等参数存在硬编码或共享指纹风险。
- 多账号同 IP 可能触发平台风控。
- 当前没有完整的账号级代理池、指数退避和失败隔离方案。
- 闲鱼接口会变化，签名和字段需要长期维护。

不要向客户承诺“不会封号”或“100% 稳定”。
