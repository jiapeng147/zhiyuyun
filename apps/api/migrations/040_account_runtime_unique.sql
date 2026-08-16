-- Migration 040: each account has exactly one authoritative runtime row.
-- Existing duplicate rows deliberately make this migration fail so operators
-- reconcile them instead of silently discarding connection history.

SET NAMES utf8mb4;

SET @ddl := (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE xianyu_account_runtime ADD UNIQUE KEY uk_account_runtime_account (account_id)',
    'SELECT 1'
  )
  FROM INFORMATION_SCHEMA.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'xianyu_account_runtime'
    AND INDEX_NAME = 'uk_account_runtime_account'
);
PREPARE migration_stmt FROM @ddl;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;
