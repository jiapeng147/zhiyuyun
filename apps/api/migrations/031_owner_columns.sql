-- Migration 031: 账号无关的用户自有表加 owner_user_id 归属列(多租户隔离)
-- card_group(卡密组) / rag_knowledge_base(知识库) / scheduled_task(定时任务)
-- 存量回填给种子超管。card_item 通过 group 归属, rag_document/chunk 通过 kb 归属, 不单独加列。
ALTER TABLE card_group ADD COLUMN owner_user_id BIGINT NULL COMMENT '归属用户(多租户隔离)' AFTER id;
CREATE INDEX idx_card_group_owner ON card_group (owner_user_id);
ALTER TABLE rag_knowledge_base ADD COLUMN owner_user_id BIGINT NULL COMMENT '归属用户(多租户隔离)' AFTER id;
CREATE INDEX idx_rag_kb_owner ON rag_knowledge_base (owner_user_id);
ALTER TABLE scheduled_task ADD COLUMN owner_user_id BIGINT NULL COMMENT '归属用户(多租户隔离)' AFTER id;
CREATE INDEX idx_scheduled_task_owner ON scheduled_task (owner_user_id);

UPDATE card_group SET owner_user_id=(SELECT id FROM (SELECT id FROM admin_user WHERE is_super=1 ORDER BY id LIMIT 1) t) WHERE owner_user_id IS NULL;
UPDATE rag_knowledge_base SET owner_user_id=(SELECT id FROM (SELECT id FROM admin_user WHERE is_super=1 ORDER BY id LIMIT 1) t) WHERE owner_user_id IS NULL;
UPDATE scheduled_task SET owner_user_id=(SELECT id FROM (SELECT id FROM admin_user WHERE is_super=1 ORDER BY id LIMIT 1) t) WHERE owner_user_id IS NULL;
