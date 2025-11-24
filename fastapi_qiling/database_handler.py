import pymysql
from pymysql import Error
from typing import List, Dict, Any, Optional
from dbutils.pooled_db import PooledDB

class DatabaseHandler:
    """MySQL数据库操作类"""
    
    _pool = None
    
    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        """初始化数据库连接参数"""
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        
        # 初始化连接池
        if DatabaseHandler._pool is None:
            DatabaseHandler._pool = PooledDB(
                creator=pymysql,
                maxconnections=5,  # 最大连接数
                mincached=2,        # 初始化时创建的连接数
                maxcached=2,       # 连接池中最多闲置的连接数
                host=self.host,
                port=self.port,
                user=self.user,
                passwd=self.password,
                db=self.database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                init_command='SET sql_mode=STRICT_TRANS_TABLES',
                connect_timeout=10,
                max_allowed_packet=10240  #
            )
        
    def connect(self) -> bool:
        """从连接池获取数据库连接"""
        try:
            self.connection = DatabaseHandler._pool.connection()
            print("成功从连接池获取MySQL数据库连接")
            return True
        except Error as e:
            print(f"从连接池获取连接时出错: {e}")
            return False
            
    def close(self) -> None:
        """归还数据库连接到连接池"""
        if self.connection:
            self.connection.close()
            self.connection = None
            print("已归还数据库连接到连接池")
            
    def execute_query(self, sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        执行查询语句
        :param sql: SQL查询语句
        :param params: 查询参数
        :return: 查询结果列表
        """
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # 检查连接是否有效
                if not self.connection:
                    if not self.connect():
                        return []
                try:
                    # 测试连接是否仍然有效
                    self.connection.ping(reconnect=False)
                except:
                    self.close()
                    if not self.connect():
                        return []
                
                with self.connection.cursor() as cursor:
                    cursor.execute(sql, params or ())
                    return cursor.fetchall()
                    
            except (Error, pymysql.err.OperationalError) as e:
                print(f"执行查询时出错: {e}")
                if 'MySQL server has gone away' in str(e) or 'Lost connection' in str(e):
                    print("尝试重新连接数据库...")
                    self.close()
                    if not self.connect():
                        retry_count += 1
                        continue
                return []
            except Exception as e:
                print(f"未知错误: {e}")
                return []
                
        print(f"达到最大重试次数({max_retries})，放弃操作")
        return []
            
    def execute_update(self, sql: str, params: Optional[tuple] = None) -> int:
        """
        执行更新/插入/删除语句
        :param sql: SQL语句
        :param params: 参数
        :return: 受影响的行数
        """
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # 检查连接是否有效
                if not self.connection:
                    if not self.connect():
                        return 0
                try:
                    # 测试连接是否仍然有效
                    self.connection.ping(reconnect=False)
                except:
                    self.close()
                    if not self.connect():
                        return 0
                
                with self.connection.cursor() as cursor:
                    affected_rows = cursor.execute(sql, params or ())
                    self.connection.commit()
                    return affected_rows
                    
            except (Error, pymysql.err.OperationalError) as e:
                print(f"执行更新时出错: {e}")
                if 'MySQL server has gone away' in str(e) or 'Lost connection' in str(e):
                    print("尝试重新连接数据库...")
                    self.close()
                    if not self.connect():
                        retry_count += 1
                        continue
                self.connection.rollback()
                return 0
            except Exception as e:
                print(f"未知错误: {e}")
                self.connection.rollback()
                return 0
                
        print(f"达到最大重试次数({max_retries})，放弃操作")
        return 0
            
    def __enter__(self):
        """支持with语句"""
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持with语句"""
        self.close()

# 快捷连接函数
def get_lizi_connection():
    """获取lizi数据库的连接，从环境变量读取配置"""
    import os
    return DatabaseHandler(
        host=os.getenv("DB_HOST", "121.43.193.176"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "123456"),
        database=os.getenv("DB_NAME", "lizi")
    )