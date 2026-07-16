-- Migration 033: 套餐权益功能开关
-- app_plan 增加 feature_flags(JSON)，用于按套餐控制模块权益。
-- 兼容策略：NULL 或缺失 key 均视为允许，避免升级后误关存量功能。

SET NAMES utf8mb4;

SET @ddl := (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE app_plan ADD COLUMN feature_flags JSON NULL COMMENT ''套餐功能权益开关(JSON)'' AFTER description',
    'SELECT 1'
  )
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'app_plan'
    AND COLUMN_NAME = 'feature_flags'
);
PREPARE migration_stmt FROM @ddl;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

UPDATE app_plan
SET feature_flags = JSON_OBJECT(
  'accounts', true,
  'products', true,
  'messages', true,
  'ai_customer_service', true,
  'auto_reply', true,
  'auto_delivery', true,
  'card_warehouse', true,
  'source_library', true,
  'rag', true,
  'scheduled_tasks', true,
  'item_polish', true,
  'notifications', true
)
WHERE feature_flags IS NULL;
