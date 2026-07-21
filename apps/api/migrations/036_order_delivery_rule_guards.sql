-- Migration 036: 订单唯一性、规则归属和订单未知状态保护。
--
-- The order unique key intentionally fails closed when legacy duplicate rows
-- exist. Operators must reconcile those rows from approved evidence before
-- rerunning this migration; the migration never silently deletes orders.

SET NAMES utf8mb4;

SET @ddl := (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE xianyu_trade_order ADD UNIQUE KEY uk_trade_order_account_external (account_id, external_order_id)',
    'SELECT 1'
  )
  FROM INFORMATION_SCHEMA.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'xianyu_trade_order'
    AND INDEX_NAME = 'uk_trade_order_account_external'
);
PREPARE migration_stmt FROM @ddl;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @ddl := (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE delivery_rule ADD COLUMN owner_user_id BIGINT NULL COMMENT ''归属用户(多租户隔离)'' AFTER id',
    'SELECT 1'
  )
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'delivery_rule'
    AND COLUMN_NAME = 'owner_user_id'
);
PREPARE migration_stmt FROM @ddl;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @ddl := (
  SELECT IF(
    COUNT(*) = 0,
    'CREATE INDEX idx_delivery_rule_owner ON delivery_rule (owner_user_id)',
    'SELECT 1'
  )
  FROM INFORMATION_SCHEMA.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'delivery_rule'
    AND INDEX_NAME = 'idx_delivery_rule_owner'
);
PREPARE migration_stmt FROM @ddl;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

-- Account-scoped legacy rules inherit the account owner. A rule with no
-- account is intentionally left unassigned and is not exposed to ordinary
-- tenants until an owner explicitly claims it.
UPDATE delivery_rule r
JOIN xianyu_account a ON a.id = r.account_id
SET r.owner_user_id = a.owner_user_id
WHERE r.owner_user_id IS NULL
  AND r.account_id IS NOT NULL;
