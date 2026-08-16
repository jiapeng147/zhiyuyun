# 智鱼云项目记忆目录

更新时间：2026-08-12 UTC
当前分支：`master`
上传前基线提交：`8136985`
当前提交：以 `git log -1 --oneline` 输出为准

这是本项目交接给后续 AI 或开发者的总入口。先读本文件，再按任务读取对应文档。

## 当前结论

- 阶段 175-180 已完成 UI 收尾。
- 真实闲鱼 App 扫码已成功，账号商品、订单、消息、AI 和 WebSocket 只读链路已通过生产验收。
- P0 核心面已落地；当前 API suite 为 50 个 unittest，管理员只读矩阵 `59/59`、双租户矩阵 `13/13`。
- WebSocket 进程状态和数据库运行态已同步，迁移 `001-040` current，100 秒采样 `20/20`。
- 当前 Docker 服务健康：API、Worker、Web、MySQL、Redis、Crawler。
- 广告申请页 503 是商业桥接未配置时的预期降级，不是页面崩溃。
- 没有遗留的 175-180 UI 阶段。

## 记忆文件

| 文件 | 内容 |
|---|---|
| `PROJECT.md` | 产品目标、技术栈、目录结构和用户要求 |
| `ARCHITECTURE.md` | Docker 服务、前后端边界、路由、AI 和多租户结构 |
| `ROUTES_UI.md` | 后台路由、移动端 Lite、商业 UI 组件体系 |
| `HISTORY.md` | 阶段 1-180 的改造历史和 P0 硬化批次 |
| `BUGS_AND_RISKS.md` | 已修复问题、契约测试和仍需真实业务复现的风险 |
| `OPERATIONS.md` | 构建、部署、验收、Git 和故障处理命令 |
| `WORKING_RULES.md` | 用户偏好、协作方式和继续任务规则 |
| `HANDOFF.md` | 下一次接手时的即时状态、已完成和待人工验证清单 |

## 脱敏说明

本目录不保存任何秘密值。包括但不限于：

- 登录密码、管理员密码、SSH 密码
- JWT、Cookie、API Key、内部 token
- 数据库 root/app 密码和 Redis 密码
- 第三方网站 token、Cookie 和授权凭证

需要凭据时只能读取受保护的 `secrets/` 或由用户重新提供。
