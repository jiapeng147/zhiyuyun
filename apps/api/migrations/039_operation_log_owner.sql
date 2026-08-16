-- Migration 039: 操作日志增加稳定的用户归属，避免用户名变更后跨租户读取。

SET NAMES utf8mb4;

SET @ddl := (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE operation_log ADD COLUMN owner_user_id BIGINT NULL COMMENT ''归属用户(多租户隔离)'' AFTER id',
    'SELECT 1'
  )
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'operation_log'
    AND COLUMN_NAME = 'owner_user_id'
);
PREPARE migration_stmt FROM @ddl;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @ddl := (
  SELECT IF(
    COUNT(*) = 0,
    'CREATE INDEX idx_operation_log_owner_created ON operation_log (owner_user_id, created_time)',
    'SELECT 1'
  )
  FROM INFORMATION_SCHEMA.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'operation_log'
    AND INDEX_NAME = 'idx_operation_log_owner_created'
);
PREPARE migration_stmt FROM @ddl;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

UPDATE operation_log log_row
JOIN admin_user user_row ON user_row.username = log_row.operator
SET log_row.owner_user_id = user_row.id
WHERE log_row.owner_user_id IS NULL;

UPDATE operation_log log_row
JOIN admin_user user_row ON user_row.id = CAST(log_row.target_id AS UNSIGNED)
SET log_row.owner_user_id = user_row.id
WHERE log_row.owner_user_id IS NULL
  AND log_row.target_type = 'auth'
  AND log_row.target_id REGEXP '^[0-9]+$';
