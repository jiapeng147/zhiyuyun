-- Migration 037: 自动发货模板增加租户归属。
-- 旧模板回填给首个超级管理员；没有超级管理员时保持未分配，普通用户不可见。

SET NAMES utf8mb4;

SET @ddl := (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE delivery_template ADD COLUMN owner_user_id BIGINT NULL COMMENT ''归属用户(多租户隔离)'' AFTER id',
    'SELECT 1'
  )
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'delivery_template'
    AND COLUMN_NAME = 'owner_user_id'
);
PREPARE migration_stmt FROM @ddl;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @ddl := (
  SELECT IF(
    COUNT(*) = 0,
    'CREATE INDEX idx_delivery_template_owner ON delivery_template (owner_user_id)',
    'SELECT 1'
  )
  FROM INFORMATION_SCHEMA.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'delivery_template'
    AND INDEX_NAME = 'idx_delivery_template_owner'
);
PREPARE migration_stmt FROM @ddl;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

UPDATE delivery_template
SET owner_user_id = (
  SELECT id FROM (
    SELECT id FROM admin_user WHERE is_super = 1 ORDER BY id LIMIT 1
  ) super_user
)
WHERE owner_user_id IS NULL;
