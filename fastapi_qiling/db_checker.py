#!/usr/bin/env python
"""数据库表结构检查工具"""

from database_handler import get_lizi_connection

def check_table_structure():
    """检查数据库表结构"""
    try:
        db = get_lizi_connection()
        
        if db.connect():
            print("✅ 成功连接到数据库")
            
            # 查询users表结构
            print("\n正在查询users表结构...")
            sql = """
            SELECT COLUMN_NAME, DATA_TYPE, COLUMN_COMMENT 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'lizi' AND TABLE_NAME = 'users'
            ORDER BY ORDINAL_POSITION
            """
            result = db.execute_query(sql)
            
            if result:
                print("users表结构:")
                print("="*60)
                for col in result:
                    print(f"字段: {col['COLUMN_NAME']:15} 类型: {col['DATA_TYPE']:15} 备注: {col['COLUMN_COMMENT']}")
            else:
                print("❌ 查询users表结构失败")
                
            # 查询数据库中的所有表
            print("\n\n数据库中的所有表:")
            print("="*60)
            tables = db.execute_query("SHOW TABLES")
            for table in tables:
                table_name = list(table.values())[0]
                print(f"- {table_name}")
                
            db.close()
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_table_structure()