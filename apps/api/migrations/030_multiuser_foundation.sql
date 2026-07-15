-- Migration 030: 多用户 SaaS 地基
-- 智鱼云商业化第一阶段(2A): 把单管理员架构升级为多用户。
--   1) 扩展 admin_user 为统一用户表(同时承载超管与注册用户): 验证/资料/套餐/配额/登录列
--   2) 新建 app_plan 套餐目录表 + 种入 free/pro/max
--   3) xianyu_account 增加 owner_user_id 归属锚点 + 索引(多租户行级隔离锚点)
--   4) 种子超管: 存量闲鱼账号回填其名下; 从 legacy 设置同步权威密码; 置 max 套餐+已验证
-- 说明: 本迁移仅新增列/表, 对存量数据无破坏; owner_user_id 可空, 隔离强制在 2B 落地。

SET NAMES utf8mb4;

-- 1) admin_user 扩展为统一用户表 ------------------------------------------------
ALTER TABLE admin_user ADD COLUMN email_verified TINYINT NULL DEFAULT 0 COMMENT '邮箱是否已验证' AFTER email;
ALTER TABLE admin_user ADD COLUMN nickname VARCHAR(100) NULL COMMENT '昵称' AFTER email_verified;
ALTER TABLE admin_user ADD COLUMN phone VARCHAR(30) NULL COMMENT '手机号' AFTER nickname;
ALTER TABLE admin_user ADD COLUMN avatar_url TEXT NULL COMMENT '头像URL' AFTER phone;
ALTER TABLE admin_user ADD COLUMN plan_code VARCHAR(50) NULL DEFAULT 'free' COMMENT '套餐代码' AFTER is_super;
ALTER TABLE admin_user ADD COLUMN plan_expire_time DATETIME NULL COMMENT '套餐到期(NULL=永久/免费)' AFTER plan_code;
ALTER TABLE admin_user ADD COLUMN max_accounts INT NULL DEFAULT 1 COMMENT '可绑定闲鱼账号数配额' AFTER plan_expire_time;
ALTER TABLE admin_user ADD COLUMN ai_daily_quota INT NULL DEFAULT 100 COMMENT 'AI每日调用配额' AFTER max_accounts;
ALTER TABLE admin_user ADD COLUMN last_login_time DATETIME NULL COMMENT '最近登录时间' AFTER ai_daily_quota;
ALTER TABLE admin_user ADD COLUMN register_ip VARCHAR(64) NULL COMMENT '注册IP' AFTER last_login_time;

-- 2) 套餐目录表 --------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app_plan (
  id BIGINT NOT NULL AUTO_INCREMENT,
  code VARCHAR(50) NOT NULL,
  name VARCHAR(100) NOT NULL,
  max_accounts INT NOT NULL DEFAULT 1 COMMENT '可绑定闲鱼账号数',
  ai_daily_quota INT NOT NULL DEFAULT 100 COMMENT 'AI每日调用配额',
  price_cents INT NOT NULL DEFAULT 0 COMMENT '月价(分)',
  sort_order INT NOT NULL DEFAULT 0,
  status TINYINT NOT NULL DEFAULT 1 COMMENT '1上架 0下架',
  description VARCHAR(500) NULL,
  created_time DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
  updated_time DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE INDEX uk_app_plan_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='套餐目录';

INSERT INTO app_plan (code, name, max_accounts, ai_daily_quota, price_cents, sort_order, description)
SELECT 'free','免费版',1,100,0,1,'单个闲鱼账号, 每日100次AI回复, 体验核心功能'
WHERE NOT EXISTS (SELECT 1 FROM app_plan WHERE code='free');
INSERT INTO app_plan (code, name, max_accounts, ai_daily_quota, price_cents, sort_order, description)
SELECT 'pro','专业版',5,2000,9900,2,'5个闲鱼账号, 每日2000次AI, 定时任务/自动发货/擦亮'
WHERE NOT EXISTS (SELECT 1 FROM app_plan WHERE code='pro');
INSERT INTO app_plan (code, name, max_accounts, ai_daily_quota, price_cents, sort_order, description)
SELECT 'max','旗舰版',30,20000,29900,3,'30个闲鱼账号, 每日20000次AI, 全部商用能力'
WHERE NOT EXISTS (SELECT 1 FROM app_plan WHERE code='max');

-- 3) 归属锚点 ----------------------------------------------------------------
ALTER TABLE xianyu_account ADD COLUMN owner_user_id BIGINT NULL COMMENT '归属用户ID(多租户行级隔离锚点)' AFTER id;
CREATE INDEX idx_xianyu_account_owner ON xianyu_account (owner_user_id);

-- 4) 种子超管处理 ------------------------------------------------------------
-- 4a) 存量闲鱼账号回填给种子超管(is_super=1 最小id)
UPDATE xianyu_account
SET owner_user_id = (SELECT id FROM (SELECT id FROM admin_user WHERE is_super=1 ORDER BY id LIMIT 1) t)
WHERE owner_user_id IS NULL;

-- 4b) 权威密码同步: 若 legacy 设置 admin_password_hash 存在, 写入种子 admin 行,
--     使 admin_user 表成为登录权威(历史上改密写在设置里)。
UPDATE admin_user au
JOIN xianyu_sys_setting s ON s.setting_key='admin_password_hash'
SET au.password_hash = s.setting_value
WHERE au.username='admin' AND au.is_super=1 AND s.setting_value IS NOT NULL AND s.setting_value <> '';

-- 4c) 种子超管: max 套餐 + 已验证 + 高配额
UPDATE admin_user SET plan_code='max', email_verified=1, max_accounts=30, ai_daily_quota=20000
WHERE is_super=1;
