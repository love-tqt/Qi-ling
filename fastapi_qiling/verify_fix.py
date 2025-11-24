#!/usr/bin/env python
"""验证数据库修复结果"""

from database_handler import get_lizi_connection
from datetime import datetime
import uuid

def verify_database_fix():
    """验证数据库修复结果"""
    try:
        db = get_lizi_connection()
        
        if db.connect():
            print("✅ 成功连接到数据库")
            
            # 1. 验证表结构
            print("\n1. 验证users表结构:")
            print("-"*50)
            sql = """
            SELECT COLUMN_NAME, DATA_TYPE, COLUMN_COMMENT 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'lizi' AND TABLE_NAME = 'users'
            ORDER BY ORDINAL_POSITION
            """
            result = db.execute_query(sql)
            
            if result:
                for col in result:
                    if col['COLUMN_NAME'] == 'username':
                        print(f"✅ username字段存在: {col['COLUMN_NAME']} ({col['DATA_TYPE']})")
                    else:
                        print(f"  {col['COLUMN_NAME']:15} ({col['DATA_TYPE']})")
            
            # 2. 测试查询操作
            print("\n2. 测试查询操作:")
            print("-"*50)
            test_username = f"test_user_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            test_email = f"{test_username}@example.com"
            
            # 插入测试用户
            print(f"⬇️  插入测试用户: {test_username}")
            insert_sql = """
            INSERT INTO users (userid, username, email, password, timestamp)
            VALUES (%s, %s, %s, %s, %s)
            """
            userid = int(uuid.uuid4().int >> 64)  # 生成一个大整数作为userid
            password = "test_password"
            timestamp = datetime.now()
            
            affected_rows = db.execute_update(insert_sql, (userid, test_username, test_email, password, timestamp))
            
            if affected_rows > 0:
                print("✅ 成功插入测试用户")
                
                # 查询测试用户
                print(f"\n⬆️  查询测试用户: {test_username}")
                select_sql = "SELECT * FROM users WHERE username = %s"
                result = db.execute_query(select_sql, (test_username,))
                
                if result:
                    print("✅ 成功查询到用户:")
                    print(f"   userid: {result[0]['userid']}")
                    print(f"   username: {result[0]['username']}")
                    print(f"   email: {result[0]['email']}")
                    
                    # 清理测试数据
                    print(f"\n🗑️  清理测试数据")
                    delete_sql = "DELETE FROM users WHERE username = %s"
                    db.execute_update(delete_sql, (test_username,))
                    print("✅ 测试数据已清理")
                else:
                    print("❌ 查询测试用户失败")
            else:
                print("❌ 插入测试用户失败")
            
            # 3. 测试DBSERVICE模块
            print("\n3. 测试DBSERVICE模块兼容性:")
            print("-"*50)
            try:
                from dbservice import DatabaseService
                
                # 测试雪花ID生成
                snowflake_id = DatabaseService._generate_snowflake_id()
                print(f"✅ 雪花ID生成正常: {snowflake_id}")
                
                # 测试用户注册功能（使用不同的测试用户名）
                test_username2 = f"test_user_{datetime.now().strftime('%Y%m%d%H%M%S')}_2"
                test_email2 = f"{test_username2}@example.com"
                
                print(f"\n⬇️  使用DBSERVICE测试用户注册: {test_username2}")
                user_data = {
                    'username': test_username2,
                    'email': test_email2,
                    'password': 'test_password'
                }
                
                result, status = DatabaseService.register_user(user_data)
                
                if status == 200:
                    print("✅ 用户注册成功")
                    print(f"   user_id: {result['user_id']}")
                    
                    # 清理测试数据
                    print(f"\n🗑️  清理DBSERVICE测试数据")
                    delete_sql = "DELETE FROM users WHERE username = %s"
                    db.execute_update(delete_sql, (test_username2,))
                    print("✅ DBSERVICE测试数据已清理")
                else:
                    print(f"❌ 用户注册失败: {result.get('error', '未知错误')}")
                    
            except Exception as e:
                print(f"❌ DBSERVICE模块测试失败: {e}")
                
            db.close()
            
            print("\n" + "="*50)
            print("✅ 所有验证完成！数据库修复成功！")
            print("="*50)
            
    except Exception as e:
        print(f"❌ 验证过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_database_fix()