-- Migration 032: 商业计费底座
-- 增加会员订阅、会员支付订单、用户每日用量和配额事件表。

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS app_subscription (
  id BIGINT NOT NULL AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  plan_code VARCHAR(50) NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'active' COMMENT 'active/expired/canceled/replaced',
  current_period_start DATETIME NULL,
  current_period_end DATETIME NULL,
  source_order_id BIGINT NULL,
  cancel_at_period_end TINYINT NOT NULL DEFAULT 0,
  created_time DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
  updated_time DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  INDEX idx_app_subscription_user (user_id),
  INDEX idx_app_subscription_user_status (user_id, status),
  INDEX idx_app_subscription_period_end (current_period_end)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户套餐订阅周期';

CREATE TABLE IF NOT EXISTS app_billing_order (
  id BIGINT NOT NULL AUTO_INCREMENT,
  order_no VARCHAR(64) NOT NULL,
  user_id BIGINT NOT NULL,
  plan_code VARCHAR(50) NOT NULL,
  order_type VARCHAR(32) NOT NULL DEFAULT 'subscription' COMMENT 'subscription/renew/upgrade/manual',
  amount_cents INT NOT NULL DEFAULT 0,
  duration_days INT NOT NULL DEFAULT 30,
  status VARCHAR(32) NOT NULL DEFAULT 'pending' COMMENT 'pending/paid/closed/refunded',
  payment_provider VARCHAR(64) NULL,
  payment_method VARCHAR(64) NULL,
  paid_time DATETIME NULL,
  closed_time DATETIME NULL,
  expire_time DATETIME NULL,
  metadata_json JSON NULL,
  created_time DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
  updated_time DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE INDEX uk_app_billing_order_no (order_no),
  INDEX idx_app_billing_order_user (user_id),
  INDEX idx_app_billing_order_user_status (user_id, status),
  INDEX idx_app_billing_order_created (created_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会员套餐支付订单';

CREATE TABLE IF NOT EXISTS app_usage_daily (
  id BIGINT NOT NULL AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  usage_date DATE NOT NULL,
  metric VARCHAR(64) NOT NULL COMMENT 'accounts/ai_calls/rag_docs/storage_mb 等',
  used_count INT NOT NULL DEFAULT 0,
  limit_count INT NOT NULL DEFAULT 0,
  created_time DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
  updated_time DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE INDEX uk_app_usage_daily_metric (user_id, usage_date, metric),
  INDEX idx_app_usage_daily_user (user_id),
  INDEX idx_app_usage_daily_date_metric (usage_date, metric)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户每日用量汇总';

CREATE TABLE IF NOT EXISTS app_quota_event (
  id BIGINT NOT NULL AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  metric VARCHAR(64) NOT NULL,
  delta INT NOT NULL DEFAULT 0,
  source_type VARCHAR(64) NULL,
  source_id VARCHAR(128) NULL,
  reason VARCHAR(255) NULL,
  created_time DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  INDEX idx_app_quota_event_user (user_id),
  INDEX idx_app_quota_event_user_metric (user_id, metric, created_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='配额消耗与拦截事件';

-- 给存量用户补一条当前套餐订阅记录，便于用户中心直接展示。
INSERT INTO app_subscription (
  user_id,
  plan_code,
  status,
  current_period_start,
  current_period_end,
  created_time,
  updated_time
)
SELECT
  au.id,
  COALESCE(NULLIF(au.plan_code, ''), 'free'),
  CASE
    WHEN au.plan_expire_time IS NOT NULL AND au.plan_expire_time < NOW() THEN 'expired'
    ELSE 'active'
  END,
  COALESCE(au.created_time, NOW()),
  au.plan_expire_time,
  NOW(),
  NOW()
FROM admin_user au
WHERE NOT EXISTS (
  SELECT 1 FROM app_subscription s WHERE s.user_id = au.id
);
