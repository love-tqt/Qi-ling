#!/usr/bin/env python
"""添加username字段到users表"""

from database_handler import get_lizi_connection

def add_username_column():
    """添加username字段到users表"""
    try:
        db = get_lizi_connection()
        
        if db.connect():
            print("✅ 成功连接到数据库")
            
            # 添加username字段的SQL
            sql = """
            ALTER TABLE users 
            ADD COLUMN username VARCHAR(50) NOT NULL AFTER email,
            ADD UNIQUE KEY uk_username (username),
            MODIFY COLUMN email VARCHAR(100) NULL
            """
            
            # 先查询是否已经存在username字段
            check_sql = """
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'lizi' AND TABLE_NAME = 'users' AND COLUMN_NAME = 'username'
            """
            
            result = db.execute_query(check_sql)
            
            if result:
                print("ℹ️ username字段已经存在，无需重复添加")
            else:
                print("正在添加username字段到users表...")
                affected_rows = db.execute_update(sql)
                
                if affected_rows >= 0:
                    print("✅ 成功添加username字段")
                    
                    # 为现有用户设置初始username（使用email作为默认值）
                    print("正在为现有用户设置初始username...")
                    update_sql = """
                    UPDATE users 
                    SET username = SUBSTRING_INDEX(email, '@', 1) 
                    WHERE username IS NULL OR username = ''
                    """
                    db.execute_update(update_sql)
                    print("✅ 已为现有用户设置初始username")
                    
                else:
                    print("❌ 添加username字段失败")
            
            db.close()
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_username_column()