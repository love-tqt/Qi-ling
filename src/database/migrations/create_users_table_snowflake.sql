-- 重构用户表：采用雪花算法生成 userid
-- 优势：
--   - 64位整数，可排序，适合主键
--   - 全局唯一，支持分布式环境
--   - 无需依赖数据库自增或UUID
--   - 有良好索引支持

CREATE TABLE IF NOT EXISTS users (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '主键，自增',
    userid BIGINT NOT NULL UNIQUE COMMENT '雪花算法生成的全局唯一标识',
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    email VARCHAR(255) NOT NULL UNIQUE COMMENT '用户邮箱',
    password VARCHAR(255) NOT NULL COMMENT '密码哈希值',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    INDEX idx_userid (userid),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户信息表（雪花算法版）';