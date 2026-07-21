# 系统架构记忆

## Docker 服务

当前 Compose 服务：

- `mysql`: MySQL 8，内部 data 网络，持久卷 `mysql_data`
- `redis`: Redis 7，内部 data 网络，持久卷 `redis_data`
- `crawler`: Node + Playwright，负责滑块求解和浏览器辅助操作
- `migrate`: 一次性数据库迁移服务
- `api`: FastAPI，容器内端口 `12401`
- `worker`: 复用 API 镜像运行定时任务
- `web`: Nginx SPA，容器端口 `8080`

Compose 定义里的项目名是 `zhiyuyun`。当前机器之前的部署命令使用过：

```bash
sudo docker compose -p xianyu-assistant ...
```

因此实际容器名可能是 `xianyu-assistant-*`。操作前先用 `docker compose ps` 或 `docker ps` 确认。

## 网络边界

- Web 对宿主机发布，默认由同机 TLS 反代接入公网。
- API、Crawler、MySQL、Redis 不直接暴露公网。
- API 通过内部网络访问 Crawler、MySQL 和 Redis。
- Crawler 只允许内部 API token 和受限目标域名。
- 生产 API 文档默认关闭。

## 前端启动链路

入口：

```text
apps/web/src/main.js
  -> App.vue
  -> Naive UI NConfigProvider
  -> NLayout / NLayoutSider / NLayoutHeader / NLayoutContent
  -> Sidebar / Topbar / TabsView / PageHeader
  -> 当前 hash 路由对应页面组件
```

`App.vue` 使用当前 hash 路由，不引入完整 vue-router。关键状态：

- `active`: 当前页面 key
- `requestedRoute`: 未知路由的原始请求
- `visitedTabs`: 桌面端标签页
- `breadcrumbItems`: 面包屑
- `isMobile`: 视口判断
- `shouldUseMobileLite`: 移动端 Lite 判断

页面组件通过 `pageMap` 和 `settingsKeys` 映射，修改路由 key 会影响导航、TabsView、面包屑和移动端跳转。

## API 结构

主要 API 路由目录：

```text
apps/api/app/api/v1/routes/
```

重要服务：

- `xianyu_api_service.py`: 闲鱼 API 请求和签名
- `xianyu_goods_sync.py`: 商品同步
- `xianyu_order_sync.py`: 订单同步
- `ws_client.py`: 闲鱼消息 WebSocket
- `ws_token.py`: WebSocket token
- `captcha_solver.py`: 滑块处理
- `cookie_token_refresher.py`: Cookie/token 刷新
- `ai_provider.py`: OpenAI-compatible 通用模型
- `automation_runtime.py`: 自动回复运行时
- `rag_service.py`: RAG 检索
- `scheduled_task_runtime.py`: 定时任务执行、租约和心跳
- `commercial_bridge.py`: 广告、支付、关于页等商业桥接

## AI 模型接入

模型配置页：

```text
#/settings-model
apps/web/src/pages/admin/ModelSettingsPage.vue
```

后端实现：

```text
apps/api/app/services/ai_provider.py
```

支持：

- Chat Completions 模式
- Responses 模式
- OpenAI-compatible 中转站
- base URL 自动补 `/v1` 的标准模式
- 自定义 endpoint 模式

中转站使用时，优先检查：

1. 接口地址是否为 HTTPS 公网地址。
2. 标准兼容地址是否以 `/v1` 结束。
3. 模型名是否是中转站实际支持的模型。
4. 协议模式是否选择 `Responses` 或 `Chat Completions`。
5. 切换主机后重新填写 API Key，避免旧密钥被误用。

## 隔离原则

核心隔离工具：

```text
apps/api/app/core/tenancy.py
```

典型规则：

- `XianyuAccount` 按 `owner_user_id` 过滤。
- 有 `account_id` 的业务表按当前用户可拥有的账号集合过滤。
- 超级管理员可按平台权限读取管理数据。
- 统计接口也必须使用同样的账号集合，不能只隔离列表不隔离 count。
