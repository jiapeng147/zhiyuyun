# 运行、部署和验收

## 当前环境

项目目录：

```text
/www/wwwroot/zhiyuyun.com
```

当前生产 Web/API 入口在本机通过 Web 容器和反向代理提供。实际端口以 `.env` 和 Nginx 配置为准，不要把记忆文件中的端口当成唯一真值。

## 安全规则

- 不打印 `.env` 内容。
- 不打印 `secrets/` 文件内容。
- 不把 token、Cookie、密码、API Key 写入日志或记忆。
- Git 操作使用仓库当前要求的用户：

```bash
sudo -u mysql git status --short
sudo -u mysql git log --oneline -10
```

- 不使用 `git reset --hard`、`git checkout --` 覆盖用户改动。

## 前端验证

```bash
cd /www/wwwroot/zhiyuyun.com/apps/web
npm run lint
npm run build
```

当前裸机 Node 可能显示 Vite 的 patch 版本提示，但项目构建已经成功；Docker Web 镜像中的 Node 版本是构建最终依据。

## Docker 部署

当前历史工作使用：

```bash
cd /www/wwwroot/zhiyuyun.com
sudo docker compose -p xianyu-assistant build web
sudo docker compose -p xianyu-assistant up -d web
```

API 或 Worker 变更：

```bash
sudo docker compose -p xianyu-assistant build api
sudo docker compose -p xianyu-assistant up -d api worker
```

检查：

```bash
sudo docker ps --format '{{.Names}}\t{{.Status}}'
sudo docker inspect -f '{{.State.Health.Status}}' xianyu-assistant-web-1
sudo docker inspect -f '{{.State.Health.Status}}' xianyu-assistant-api-1
```

## 浏览器冒烟

Crawler 容器名通常是：

```text
xianyu-assistant-crawler-1
```

标准方式：

1. 通过 API 登录取得临时 token。
2. 将 token 写入 Playwright context 的 sessionStorage。
3. 访问 `http://zhiyuyun.com:8080/#/<route>`。
4. 使用 `domcontentloaded` 加固定等待，不使用 `networkidle`，因为页面存在 SSE 长连接。
5. 检查 console error、pageerror、500、空白页、状态条和关键文本。

阶段 180 最终验收：

- 桌面端 29 个路由通过
- 移动端 5 个路由通过
- 登录页通过
- 广告 503 按预期未配置状态处理

## 记忆导出前状态

```text
HEAD: 46fa634
branch: master
working tree: clean
```

## 常见故障

### MySQL healthy 后 API/Web 没有启动

先确认 MySQL healthy，再重新执行一次：

```bash
sudo docker compose -p xianyu-assistant up -d
```

### Docker 构建快照异常

30G 小盘可能有 BuildKit 快照问题。先确认无并行构建，再按运维窗口清理 builder 缓存并重启 Docker。不要在不了解卷和镜像用途时执行全盘清理。

### 静态资源 404

检查 Nginx 对 `/assets/` 和 `/xya/` 是否使用 `^~` 优先代理到 Web 容器。
