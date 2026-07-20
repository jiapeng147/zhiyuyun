-- Migration 035: 自动发货货源与发货声明增加租户归属列
-- delivery_text_source / delivery_statement / delivery_global_config 都是用户自有配置，不能全站共享。

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS delivery_global_config (
  id BIGINT NOT NULL AUTO_INCREMENT,
  owner_user_id BIGINT NULL COMMENT '归属用户(多租户隔离)',
  config_json LONGTEXT NOT NULL,
  deleted SMALLINT DEFAULT 0,
  created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  INDEX idx_delivery_global_config_owner (owner_user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='自动发货默认配置';

ALTER TABLE delivery_text_source ADD COLUMN owner_user_id BIGINT NULL COMMENT '归属用户(多租户隔离)' AFTER id;
CREATE INDEX idx_delivery_text_source_owner ON delivery_text_source (owner_user_id);

ALTER TABLE delivery_statement ADD COLUMN owner_user_id BIGINT NULL COMMENT '归属用户(多租户隔离)' AFTER id;
CREATE INDEX idx_delivery_statement_owner ON delivery_statement (owner_user_id);

SET @ddl = IF(
  EXISTS(SELECT 1 FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = 'delivery_global_config' AND column_name = 'owner_user_id'),
  'SELECT 1',
  'ALTER TABLE delivery_global_config ADD COLUMN owner_user_id BIGINT NULL COMMENT ''归属用户(多租户隔离)'' AFTER id'
);
PREPARE migration_stmt FROM @ddl;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

SET @ddl = IF(
  EXISTS(SELECT 1 FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'delivery_global_config' AND index_name = 'idx_delivery_global_config_owner'),
  'SELECT 1',
  'CREATE INDEX idx_delivery_global_config_owner ON delivery_global_config (owner_user_id)'
);
PREPARE migration_stmt FROM @ddl;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

UPDATE delivery_text_source
SET owner_user_id = (SELECT id FROM (SELECT id FROM admin_user WHERE is_super = 1 ORDER BY id LIMIT 1) t)
WHERE owner_user_id IS NULL;

UPDATE delivery_statement
SET owner_user_id = (SELECT id FROM (SELECT id FROM admin_user WHERE is_super = 1 ORDER BY id LIMIT 1) t)
WHERE owner_user_id IS NULL;

UPDATE delivery_global_config
SET owner_user_id = (SELECT id FROM (SELECT id FROM admin_user WHERE is_super = 1 ORDER BY id LIMIT 1) t)
WHERE owner_user_id IS NULL;
