# 路由和 UI 记忆

## 主导航

### 概览

- `data`: 数据面板

### 账号与商品

- `accounts`: 闲鱼账号
- `connections`: 连接管理
- `products`: 商品管理
- `orders`: 订单管理
- `product-publish`: 发布商品

### 消息

- `messages`: 在线消息

### 自动化

- `auto-delivery`: 自动发货
- `delivery-source-library`: 货源库
- `delivery-statement`: 发货声明
- `card-warehouse`: 卡密仓库
- `delivery-records`: 发货记录
- `scheduled-tasks`: 定时任务
- `auto-reply`: 自动回复

### 商业管理

- `admin-users`: 用户管理，仅平台负责人

### 系统

- `billing`: 套餐账单
- `logs`: 操作日志
- `feedback`: 反馈建议
- `ad-application`: 广告申请
- `settings-notify`: 通知设置
- `settings-system`: 系统设置

## 设置路由

- `settings-ai-cs`: AI 客服配置
- `settings-system`: 系统配置
- `settings-amap`: 高德地图
- `settings-model`: 模型配置
- `settings-embedding`: 向量模型
- `settings-rag`: RAG 知识库
- `settings-product`: 商品操作
- `settings-about`: 平台信息

## 移动端 Lite

移动端 Lite 入口：

```text
apps/web/src/components/MobileLite.vue
```

主 Tab：

- `home`: 移动首页
- `message`: 移动消息
- `automation`: 移动自动化
- `profile`: 移动个人中心

移动子页面：

- `products`: 移动商品
- `accounts`: 移动账号
- `data`: 移动数据

移动端暂不支持的复杂页面会通过 `force-desktop` 切到桌面壳层。

## 商业 UI 组件

共享组件：

```text
apps/web/src/components/business/BusinessSection.vue
apps/web/src/components/business/BusinessMetricCard.vue
apps/web/src/components/business/BusinessStatusStrip.vue
```

使用约定：

- `BusinessSection`: 统一 NCard 页面分区和标题。
- `BusinessMetricCard`: 统一指标卡、图标、数值和辅助文案。
- `BusinessStatusStrip`: 在页面 hero/主工作台之后展示关键状态。
- 状态条必须使用真实状态，不要把未知、未配置和 0 混为一谈。

## 已迁移页面

阶段 150-174 已覆盖：

数据面板、商品、订单、货源库、账号、消息、连接、自动发货、自动回复、发货记录、发货声明、卡密仓库、定时任务、操作日志、反馈建议、广告申请、套餐账单、用户管理、系统设置、AI 客服配置、模型配置、RAG 知识库、高德地图、向量模型、通知设置。

阶段 175-177 补充：

- 商品操作设置
- 平台信息
- 发布商品
- 个人中心

阶段 178：

- 移动端 Lite 导航、滚动、安全区和语义。

## 当前页面改造约束

- 发布商品页很大，必须保留图片上传、分类、AI、位置搜索、发布幂等恢复和提交参数。
- 个人中心必须保留统计、套餐展示、安全等级和修改密码。
- 业务页不要批量删除脚本或事件。
- 修改 App 壳层时必须同时验证侧边栏、header、面包屑、TabsView 和移动端切换。
