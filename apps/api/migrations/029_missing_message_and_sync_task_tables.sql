-- 修复开源版模型/迁移不一致: xianyu_message 与 xianyu_goods_sync_task 两表
-- 在 ORM 模型(entities.py)中定义并被代码读写(ws_storage.py / dashboard),
-- 但历史迁移脚本从未创建, 导致仪表盘/消息/商品同步接口 500。幂等补建。

CREATE TABLE IF NOT EXISTS xianyu_message (
  id BIGINT NOT NULL AUTO_INCREMENT,
  account_id BIGINT NULL,
  conversation_id BIGINT NULL,
  session_id VARCHAR(200) NULL COMMENT '会话session ID，用于关联xianyu_chat_message.s_id',
  from_user_id VARCHAR(200) NULL,
  to_user_id VARCHAR(200) NULL,
  content TEXT NULL,
  message_type VARCHAR(50) NULL COMMENT 'text/image/card',
  direction VARCHAR(20) NULL COMMENT 'sent/received',
  is_auto_reply SMALLINT NULL COMMENT '0否 1是',
  deleted SMALLINT NULL,
  created_time DATETIME NULL,
  PRIMARY KEY (id),
  KEY idx_xymsg_acc_del (account_id, deleted),
  KEY idx_xymsg_session (session_id),
  KEY idx_xymsg_conv (conversation_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS xianyu_goods_sync_task (
  id BIGINT NOT NULL AUTO_INCREMENT,
  sync_id VARCHAR(80) NOT NULL COMMENT '同步任务ID',
  account_id BIGINT NOT NULL,
  status VARCHAR(30) NOT NULL COMMENT 'queued/running/completed/failed',
  progress INTEGER NULL,
  total_count INTEGER NULL,
  new_count INTEGER NULL,
  updated_count INTEGER NULL,
  skipped_count INTEGER NULL,
  off_shelf_count INTEGER NULL,
  detail_synced_count INTEGER NULL,
  duration_seconds FLOAT NULL,
  error_message TEXT NULL,
  started_time DATETIME NULL,
  finished_time DATETIME NULL,
  deleted SMALLINT NULL,
  created_time DATETIME NULL,
  updated_time DATETIME NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_xygst_sync_id (sync_id),
  KEY idx_xygst_acc (account_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
