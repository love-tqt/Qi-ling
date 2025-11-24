-- 消息表：采用雪花算法生成 userid
-- 字段说明：
--   id: 主键，自增
--   userid: 雪花算法生成的全局唯一标识
--   role: 消息角色 (user/assistant/system)
--   content: 消息正文，支持长文本
--   timestamp: 消息创建时间，默认当前时间

CREATE TABLE IF NOT EXISTS messages (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '主键，自增',
    userid BIGINT NOT NULL COMMENT '雪花算法生成的全局唯一标识',
    role VARCHAR(20) NOT NULL COMMENT '消息角色 (user/assistant/system)',
    content LONGTEXT NOT NULL COMMENT '消息内容',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    INDEX idx_userid (userid),
    INDEX idx_role (role),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户消息记录表（雪花算法版）';