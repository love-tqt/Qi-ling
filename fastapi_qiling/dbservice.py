from database_handler import get_lizi_connection
from datetime import datetime

class DatabaseService:
    @staticmethod
    def register_user(user_data):
        """注册新用户，使用雪花算法生成 userid"""
        try:
            db = get_lizi_connection()
            
            # 检查用户名是否已存在
            existing_username = db.execute_query(
                "SELECT id FROM users WHERE username = %s",
                (user_data['username'],)
            )
            
            if existing_username:
                return {'error': '用户名已存在'}, 409
            
            # 检查邮箱是否已被注册
            existing_email = db.execute_query(
                "SELECT id FROM users WHERE email = %s",
                (user_data['email'],)
            )
            
            if existing_email:
                return {'error': '邮箱已被注册'}, 409
            
            # 生成雪花算法 userid
            # 64位雪花算法：41位时间戳 + 10位机器标识 + 12位序列号
            # 时间戳从2025-01-01开始计算（1735689600000）
            # 机器标识固定为0（可扩展为分布式环境用真实机器码）
            userid = DatabaseService._generate_snowflake_id(start_timestamp=1735689600000, worker_id=0)
            
            # 插入新用户
            insert_sql = """
            INSERT INTO users (userid, username, email, password)
            VALUES (%s, %s, %s, %s)
            """
            affected_rows = db.execute_update(insert_sql, (
                userid,
                user_data['username'],
                user_data['email'],
                user_data['password']
            ))
            
            if affected_rows > 0:
                return {'status': 'success', 'user_id': str(userid)}, 200
            else:
                return {'error': 'Failed to register user'}, 500
                
        except Exception as e:
            print(f"数据库操作失败: {str(e)}")
            return {'error': 'Internal server error'}, 500
        finally:
            if db:
                db.close()

    # 雪花算法实现（纯代码实现，不依赖外部库）
    @staticmethod
    def _generate_snowflake_id(start_timestamp=1735689600000, worker_id=0):
        """
        生成雪花算法格式的ID
        :param start_timestamp: 起始时间戳（毫秒），建议设为未来某个时间点
        :param worker_id: 工作机器标识（0-1023）
        :return: 64位雪花算法整数
        """
        from time import time
        
        # 毫秒级时间戳
        timestamp = int(time() * 1000)
        
        # 偏移量 = 当前时间戳 - 起始时间戳
        offset = timestamp - start_timestamp
        
        # 确保时间戳偏移量不超过41位（2^41 - 1）
        if offset >= (1 << 41):
            raise ValueError("时间戳超过最大范围")
        
        # 生成序列号（12位）
        # 简单模拟：每次调用时递增，这里用全局变量记录
        global _snowflake_sequence
        if '_snowflake_sequence' not in globals():
            _snowflake_sequence = 0
        
        # 序列号溢出则重置（实际生产中应使用原子锁）
        _snowflake_sequence = (_snowflake_sequence + 1) % (1 << 12)
        
        # 组合64位
        # 1. 时间戳（41位）左移22位
        # 2. 机器标识（10位）左移12位
        # 3. 序列号（12位）右移0位
        id_64bit = (offset << 22) | (worker_id << 12) | _snowflake_sequence
        
        return id_64bit

    @staticmethod
    def get_user_by_credentials(username, password):
        """根据凭证获取用户"""
        try:
            db = get_lizi_connection()
            
            # 先检查用户名是否存在
            user_exists = db.execute_query(
                "SELECT userid FROM users WHERE username = %s",
                (username,)
            )
            
            if not user_exists:
                return None, '用户名不存在'
            
            # 再检查用户名和密码是否匹配
            user = db.execute_query(
                "SELECT userid, username, email FROM users WHERE username = %s AND password = %s",
                (username, password)
            )
            
            if user:
                return user[0], None
            else:
                return None, '密码错误'
                
        except Exception as e:
            print(f"数据库操作失败: {str(e)}")
            return None, 'Internal server error'
        finally:
            if db:
                db.close()

    @staticmethod
    def save_message(user_id, role, content, timestamp=None):
        """保存消息到数据库，使用上下文管理器确保连接安全释放
        支持输入 string (UUID) 或 int (Snowflake ID) 的 user_id
        """
        import logging
        from datetime import datetime
        
        if timestamp is None:
            timestamp = datetime.now()
        
        try:
            # 转换 user_id 为整数（用于雪花算法）
            if isinstance(user_id, str):
                try:
                    user_id = int(user_id)
                except ValueError:
                    logging.warning(f"用户ID格式错误: {user_id}，尝试转为整数失败")
                    return False
            
            with get_lizi_connection() as db:
                insert_sql = """
                INSERT INTO messages (userid, role, content, timestamp)
                VALUES (%s, %s, %s, %s)
                """
                affected_rows = db.execute_update(insert_sql, (
                    user_id, role, content, timestamp
                ))
                
                if affected_rows <= 0:
                    logging.warning(f"保存消息失败: 受影响行数为 {affected_rows}, user_id={user_id}, role={role}")
                    return False
                
                logging.info(f"成功保存消息，用户ID: {user_id}, 角色: {role}, 内容长度: {len(content)}")
                return True
                
        except Exception as e:
            logging.error(f"保存消息失败 - 用户ID: {user_id}, 角色: {role}, 内容: {content[:100]}..., 错误: {str(e)}")
            return False

    @staticmethod
    def get_recent_messages(user_id, limit=10):
        """获取用户最近的消息"""
        print(f"正在获取用户 {user_id} 的最近 {limit} 条消息...")
        try:
            db = get_lizi_connection()
            
            query_sql = """
            SELECT role, content, timestamp 
            FROM messages 
            WHERE userid = %s 
            ORDER BY timestamp DESC 
            LIMIT %s
            """
            messages = db.execute_query(query_sql, (user_id, limit))
            
            if not messages:
                print(f"未找到用户 {user_id} 的消息记录")
                return []
            
            # 只做基本格式转换，不处理图片
            formatted_messages = []
            for msg in reversed(messages):  # 反转顺序，从旧到新
                formatted_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            print(f"成功获取 {len(formatted_messages)} 条消息")
            return formatted_messages
                
        except Exception as e:
            print(f"获取消息失败: {str(e)}")
            return []
        finally:
            if db:
                db.close()

    @staticmethod
    def get_chat_history(user_id, limit=20):
        """获取用户聊天历史（最新的在前）"""
        db = None
        try:
            db = get_lizi_connection()
            
            query_sql = """
            SELECT role, content, timestamp 
            FROM messages 
            WHERE userid = %s 
            ORDER BY timestamp DESC 
            LIMIT %s
            """
            messages = db.execute_query(query_sql, (user_id, limit))
            
            # 转换为前端需要的格式（保持时间降序）
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                    "timestamp": msg["timestamp"].isoformat() if hasattr(msg["timestamp"], 'isoformat') else str(msg["timestamp"])
                })
            
            return formatted_messages
                
        except Exception as e:
            print(f"获取聊天历史失败 - 用户ID: {user_id}, 错误详情: {str(e)}")
            return []
        finally:
            if db:
                db.close()