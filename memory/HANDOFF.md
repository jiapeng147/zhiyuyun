# 即时接力说明

## 当前状态

当前项目已完成原计划的 UI 阶段 175-180：

- 阶段 175：商品操作、平台信息
- 阶段 176：发布商品
- 阶段 177：个人中心
- 阶段 178：移动端 Lite
- 阶段 179：旧 CSS 收尾
- 阶段 180：全量回归

当前 HEAD：

```text
46fa634 阶段180: 全量桌面移动端与登录回归验收通过
```

工作树干净，容器已健康。

## 下一次接手先做什么

如果用户继续说“继续”，不要再创建 181 这种纯 UI 阶段，先和用户确认或按商业逻辑进入功能成熟度阶段。推荐顺序：

1. 真实闲鱼二维码登录闭环验证。
2. 商品状态映射真实数据验证。
3. 发布、下架、删除和改价的并发/幂等回归。
4. 自动回复重复消息和 RAG account_id 隔离回归。
5. 自动发货通配规则、多规格订单和卡密消耗回归。
6. AI 中转站 Responses/Chat Completions 两种模式的真实兼容测试。
7. 商业版功能：商品搜索、店铺爬取、AI 搬运、生图和批量工作流。
8. 闲鱼风控：账号级代理、SPM/UA 池、指数退避、失败隔离。

## 不能误判的状态

- 广告 `/api/ads/*` 返回 503 时，先看页面是否显示“广告商业服务未配置”。这是预期降级。
- 页面存在 SSE 时，Playwright 不要等待 `networkidle`。
- 看到 `admin` 只先确认它是当前登录用户名还是旧品牌遗留，不能直接改 API 返回。
- 移动端 Lite 只覆盖固定页面，复杂页面的桌面切换是当前设计。
- API 的 HTTP 状态码优先于顶层 `code/msg/data` 信封。

## 当前主要代码入口

```text
apps/web/src/App.vue
apps/web/src/pages/ProductPublishPage.vue
apps/web/src/pages/ProfileCenterPage.vue
apps/web/src/components/MobileLite.vue
apps/web/src/components/business/
apps/api/app/services/ai_provider.py
apps/api/app/core/tenancy.py
apps/api/app/services/commercial_bridge.py
apps/api/app/services/xianyu_goods_sync.py
apps/api/app/services/external_operation.py
```

## 安全提醒

本接力文件和 `memory/` 目录不包含任何生产凭据。不要从旧聊天记录或旧 handoff 中复制敏感信息到源码或新文档。
