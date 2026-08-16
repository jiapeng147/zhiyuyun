-- Migration 038: 站内通知增加租户归属。
-- 只回填能够从业务外键证明归属的旧记录；其余记录保留 NULL，仅超管可见。

SET NAMES utf8mb4;

SET @ddl := (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE notification ADD COLUMN owner_user_id BIGINT NULL COMMENT ''归属用户(多租户隔离)'' AFTER id',
    'SELECT 1'
  )
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'notification'
    AND COLUMN_NAME = 'owner_user_id'
);
PREPARE migration_stmt FROM @ddl;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @ddl := (
  SELECT IF(
    COUNT(*) = 0,
    'CREATE INDEX idx_notification_owner_created ON notification (owner_user_id, created_time)',
    'SELECT 1'
  )
  FROM INFORMATION_SCHEMA.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'notification'
    AND INDEX_NAME = 'idx_notification_owner_created'
);
PREPARE migration_stmt FROM @ddl;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

UPDATE notification n
JOIN xianyu_account a ON a.id = n.reference_id AND a.deleted = 0
SET n.owner_user_id = a.owner_user_id
WHERE n.owner_user_id IS NULL
  AND n.reference_type IN ('人机验证提醒', '账号掉线提醒', 'Cookie失效提醒');

UPDATE notification n
JOIN ai_auto_reply_attempt attempt ON attempt.id = n.reference_id
JOIN xianyu_account a ON a.id = attempt.account_id AND a.deleted = 0
SET n.owner_user_id = a.owner_user_id
WHERE n.owner_user_id IS NULL
  AND n.reference_type = 'AI 自动回复核对提醒';

UPDATE notification n
JOIN app_billing_order billing_order ON billing_order.id = n.reference_id
SET n.owner_user_id = billing_order.user_id
WHERE n.owner_user_id IS NULL
  AND n.reference_type LIKE 'billing_order_%%';

UPDATE notification n
JOIN app_subscription subscription ON subscription.id = n.reference_id
SET n.owner_user_id = subscription.user_id
WHERE n.owner_user_id IS NULL
  AND n.reference_type LIKE 'subscription_%%';

UPDATE notification
SET owner_user_id = reference_id
WHERE owner_user_id IS NULL
  AND (
    reference_type LIKE 'quota_%%'
    OR reference_type LIKE 'feature_block_%%'
  );
