from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Header, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import uuid
import time
from datetime import datetime
import logging
from logging_config import setup_logging
from dbservice import DatabaseService
# 导入大模型客户端
from ernie_multimodal import ERNIE4_5MultimodalClient
# 导入向量数据库和文物识别服务
from vector_db_service import VectorDatabaseService
from artifact_recognition_service import ArtifactRecognitionService

# 初始化日志系统
logger = setup_logging()

# 初始化大模型客户端
try:
    multimodal_client = ERNIE4_5MultimodalClient()
    logger.info("大模型客户端初始化成功")
except Exception as e:
    logger.error(f"大模型客户端初始化失败: {str(e)}")
    multimodal_client = None

# 初始化文物识别服务
try:
    recognition_service = ArtifactRecognitionService()
    logger.info("文物识别服务初始化成功")
except Exception as e:
    logger.error(f"文物识别服务初始化失败: {str(e)}")
    recognition_service = None

# 初始化向量数据库服务
try:
    vector_db_service = VectorDatabaseService()
    # 如果向量数据库不存在，尝试自动构建（需要Excel文件存在）
    if not vector_db_service.is_ready():
        logger.info("向量数据库不存在，尝试自动构建...")
        # 检查Excel文件是否存在
        import os
        excel_file = "./故宫博物院数字文物库.xlsx"
        if os.path.exists(excel_file):
            logger.info(f"找到Excel文件: {excel_file}，开始构建向量数据库...")
            logger.info("⚠️  首次构建可能需要几分钟时间，请耐心等待...")
            build_success = vector_db_service.build_vector_database(force_rebuild=False)
            if build_success:
                logger.info("✅ 向量数据库构建成功！")
            else:
                logger.warning("⚠️  向量数据库构建失败，相关功能可能无法使用")
                logger.warning("   您可以通过 API 接口 /api/vector-db/build 手动构建")
        else:
            logger.warning(f"⚠️  Excel文件不存在: {excel_file}")
            logger.warning("   向量数据库功能将不可用，请确保Excel文件存在后再构建")
            logger.warning("   构建方法：调用 API 接口 POST /api/vector-db/build")
    else:
        logger.info("✅ 向量数据库加载成功")
except Exception as e:
    logger.error(f"向量数据库服务初始化失败: {str(e)}")
    import traceback
    traceback.print_exc()
    vector_db_service = None

# 创建FastAPI应用实例
app = FastAPI(title="Qiling API", version="1.0.0")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 用于存储聊天记录和对话上下文
user_messages = {}
user_contexts = {}

# 保留中间件结构但不做认证检查
@app.middleware("http")
async def pass_through_middleware(request: Request, call_next):
    return await call_next(request)

# 日志装饰器
def log_request(endpoint_name: str):
    """增强版请求日志记录"""
    start_time = time.time()
    # 在FastAPI中，客户端IP通常在request.client.host中可以获取到
    # 这里简化处理，实际可以使用Middleware
    request_id = uuid.uuid4().hex[:16]  # 生成唯一请求ID
    
    logger.info(f"请求开始 | ID: {request_id} | 端点: {endpoint_name} | 方法: GET/POST")
    
    return {
        'start_time': start_time,
        'request_id': request_id
    }

# Pydantic模型定义
class Message(BaseModel):
    timestamp: str
    role: str
    content: str

class UserMessage(BaseModel):
    user_id: str
    messages: List[Message]

class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserInfo(BaseModel):
    id: int
    username: str
    email: str

class ConfigResponse(BaseModel):
    theme: str
    language: str

class SearchQuery(BaseModel):
    query: str
    top_k: int = 5
    use_enhanced: bool = True
    image_weight: float = 0.3

# 健康检查接口
@app.get("/api/health")
async def health_check():
    log_request('健康检查')
    return {"status": "healthy"}

# 辅助函数：处理消息中的图片路径
def process_message_content(message):
    # 直接返回原始消息内容，不处理base64编码
    return {
        "role": message["role"],
        "content": message["content"],
        "timestamp": message["timestamp"].isoformat() if hasattr(message["timestamp"], 'isoformat') else str(message["timestamp"])
    }

# 从数据库获取最新的5条聊天消息
@app.get("/api/chat/latest")
async def get_latest_messages(x_user_id: str = Header(...)):
    log_request('获取最新消息')
    try:
        # 从数据库获取最近5条消息
        messages = DatabaseService.get_chat_history(x_user_id, 5)
        # 处理每条消息的图片路径
        processed_messages = [process_message_content(msg) for msg in messages]
        return {"history": processed_messages, "count": len(processed_messages)}
    except Exception as e:
        logger.error(f"获取最新消息失败: {str(e)}")
        return {"history": [], "count": 0}

# 获取聊天历史（20条）
@app.get("/api/chat/history")
async def get_chat_history(x_user_id: str = Header(...)):
    log_request('获取聊天历史')
    try:
        # 从数据库获取聊天历史
        messages = DatabaseService.get_chat_history(x_user_id, 20)
        # 处理每条消息的图片路径
        processed_messages = [process_message_content(msg) for msg in messages]
        return {"history": processed_messages, "count": len(processed_messages)}
    except Exception as e:
        logger.error(f"获取聊天历史失败: {str(e)}")
        return {"history": [], "count": 0}

# 用户注册
@app.post("/api/auth/register")
async def register(user_data: UserRegister):
    log_request('用户注册')
    # 验证必填字段
    if not user_data.username or not user_data.email or not user_data.password:
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    # 验证邮箱格式
    if '@' not in user_data.email:
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    # 验证密码强度
    if len(user_data.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    try:
        # 调用数据库服务进行注册
        result, status_code = DatabaseService.register_user(user_data.dict())
        
        if status_code == 200:
            return {"success": True, "message": "User registered successfully", "data": {"user_id": result['user_id']}}
        else:
            # 返回错误响应，保持格式一致
            return {"success": False, "message": result.get('error', 'Registration failed')}
    except Exception as e:
        logger.error(f"注册失败: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# 用户登录
@app.post("/api/auth/login")
async def login(credentials: UserLogin):
    log_request('用户登录')
    if not credentials.username or not credentials.password:
        raise HTTPException(status_code=400, detail="Missing credentials")
    
    try:
        # 使用数据库服务进行登录验证
        user, error = DatabaseService.get_user_by_credentials(
            credentials.username, 
            credentials.password
        )
        if user:
            from datetime import datetime, timedelta
            # 设置1小时后过期
            expires_in = 3600
            expires_at = (datetime.now() + timedelta(seconds=expires_in)).isoformat()
            
            return {
                "success": True,
                "data": {
                    "userid": str(user['userid']),
                    "expires_in": expires_in,
                    "expires_at": expires_at,
                    "created_at": datetime.now().isoformat()
                }
            }
            # 可选: 返回 token 用于后续请求认证
            # "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiOWUwM2YxZmUtNTQ4Ny00NGE3LTk5NDUtYWQyYTExZDg3NThhIiwiaWF0IjoxNjY5NzQ1MDAwLCJleHAiOjE2Njk3NDg2MDB9.XXXXXXX"
        else:
            # 返回错误响应，保持格式一致
            return {
                "success": False,
                "message": error or "登录失败"
            }
            
    except Exception as e:
        logger.error(f"登录失败: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# 获取用户信息
@app.get("/api/auth/user/{user_id}")
async def get_user_info(user_id: int, x_user_id: str = Header(...)):
    log_request('获取用户信息')
    
    # 验证请求头中的用户ID是否匹配
    if int(x_user_id) != user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        # 这里需要实现获取用户详细信息的逻辑
        # 暂时返回基本用户信息
        return {
            "id": user_id,
            "username": f"用户{user_id}",  # 实际应从数据库获取
            "email": f"user{user_id}@example.com",  # 实际应从数据库获取
            "created_at": "2024-01-01T00:00:00Z"  # 实际应从数据库获取
        }
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# 图片上传接口
@app.post("/api/send")
async def upload_send(
    image: UploadFile = File(...),
    description: str = Form(...),
    upload_time: Optional[str] = Form(None),
    user_id: str = Form("unknown")
):
    log_request('图片上传')
    
    # 打印接收到的数据
    logger.info(f"接收到图片上传请求:")
    logger.info(f"  图片文件名: {image.filename}")
    logger.info(f"  图片文件大小: {image.size} bytes")
    logger.info(f"  图片内容类型: {image.content_type}")
    logger.info(f"  描述: '{description}'")
    logger.info(f"  用户ID: {user_id}")
    
    # 文件类型检查
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    file_ext = image.filename.split('.')[-1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="不支持的文件类型")
    
    # 验证文本数据
    if not description.strip():
        raise HTTPException(status_code=400, detail="描述不能为空")
    
    # 保存文件
    uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    file_path = os.path.join(uploads_dir, f"{uuid.uuid4().hex}.{file_ext}")
    with open(file_path, "wb") as buffer:
        content = await image.read()
        buffer.write(content)
    
    # 调用文物识别服务识别图片
    recognition_result = None
    if recognition_service and recognition_service.is_ready():
        try:
            recognition_result = recognition_service.recognize_and_format(file_path)
            logger.info(f"文物识别结果: {recognition_result}")
        except Exception as e:
            logger.error(f"文物识别失败: {str(e)}")
            recognition_result = None
    
    # 调用大模型处理图片和描述（结合识别结果）
    ai_response = ""
    if multimodal_client:
        try:
            # 构建增强的描述（包含识别结果）
            enhanced_description = description
            if recognition_result:
                artifact_type = recognition_result.get("artifact_type", "")
                artifact_name = recognition_result.get("artifact_name", "")
                rec_description = recognition_result.get("description", "")
                enhanced_description = f"{description}\n\n识别结果：\n文物类型：{artifact_type}\n文物名称：{artifact_name}\n介绍：{rec_description}"
            
            # 调用大模型进行分析
            ai_response = multimodal_client.image_base64_query(file_path, enhanced_description)
            
            # 记录大模型响应
            logger.info(f"大模型响应: {ai_response}")
        except Exception as e:
            logger.error(f"大模型处理失败: {str(e)}")
            ai_response = "抱歉，大模型处理出现问题，请稍后再试。"
    else:
        logger.warning("大模型客户端未初始化，使用默认响应")
        ai_response = "大模型服务不可用，这是模拟响应。"
    
    # 构造响应数据
    file_info = {
        "original_name": image.filename,
        "saved_name": os.path.basename(file_path),
        "file_size": os.path.getsize(file_path),
        "content_type": image.content_type
    }
    
    # 返回成功响应
    response_data = {
        "success": True,
        "message": "上传成功",
        "data": {
            "description": description,
            "file_info": file_info,
            "upload_time": upload_time or datetime.now().isoformat(),
            "user_id": user_id,
            "file_url": f"/uploads/{os.path.basename(file_path)}",
            "ai_response": ai_response,  # 添加AI分析结果
            "recognition": recognition_result  # 添加文物识别结果
        }
    }
    
    return response_data

# 发送消息（支持上下文对话）
@app.post("/api/chat/send")
async def send_message(
    message: str = Form(...),
    x_user_id: str = Header(...),
    image: Optional[UploadFile] = File(None)
):
    log_request('发送消息')
    
    # 构建当前消息
    current_message = {
        "role": "user",
        "content": []
    }
    
    # 添加文本消息（如果有）
    if message and message.strip():
        current_message["content"].append({
            "type": "text",
            "text": message
        })
    
    # 处理图片（如果有）
    if image:
        try:
            # 文件类型检查（参考/api/send接口）
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
            file_ext = image.filename.split('.')[-1].lower()
            if file_ext not in allowed_extensions:
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "message": "不支持的文件类型"}
                )
            
            # 读取图片内容并转换为base64（参考multimodal_client.image_base64_query）
            content = await image.read()
            import base64
            image_base64 = base64.b64encode(content).decode('utf-8')
            
            # 添加图片到消息内容（使用base64格式，参考multimodal_client.image_base64_query）
            current_message["content"].append({
                "type": "image_url",
                "image_url": {"url": f"data:image/{file_ext};base64,{image_base64}"}
            })
        except Exception as e:
            logger.error(f"图片处理失败: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": "图片处理失败"}
            )
    
    # 从数据库获取最近5条消息作为上下文
    try:
        context_messages = DatabaseService.get_recent_messages(x_user_id, 5)
        
        # 处理历史消息中的图片路径
        processed_messages = []
        for msg in context_messages:
            content = msg["content"]
            
            # 处理包含图片路径的消息
            if content.startswith("{") and content.endswith("}"):
                try:
                    import ast
                    content_dict = ast.literal_eval(content)
                    if "image_path" in content_dict:
                        # 读取图片并转换为base64
                        image_path = content_dict["image_path"].lstrip("/")
                        full_path = os.path.join(os.path.dirname(__file__), image_path)
                        
                        if os.path.exists(full_path):
                            with open(full_path, "rb") as image_file:
                                image_data = image_file.read()
                                import base64
                                image_base64 = base64.b64encode(image_data).decode('utf-8')
                                file_ext = os.path.splitext(full_path)[1].lstrip(".")
                                content_dict["image_url"] = f"data:image/{file_ext};base64,{image_base64}"
                                content = str(content_dict)
                except Exception as e:
                    logger.error(f"处理图片消息时出错: {str(e)}")
            
            processed_messages.append({
                "role": msg["role"],
                "content": content
            })
        
        context_messages = processed_messages
    except Exception as e:
        logger.error(f"获取上下文失败: {str(e)}")
        context_messages = []
    
    messages_to_send = context_messages + [current_message]
    
    # 如果包含文本消息，尝试使用向量数据库增强回复
    vector_search_results = []
    if message and message.strip() and vector_db_service and vector_db_service.is_ready():
        try:
            # 使用增强搜索查找相关文物
            vector_search_results = vector_db_service.search_enhanced(
                query_text=message,
                top_k=3,
                image_weight=0.3
            )
            logger.info(f"向量搜索找到 {len(vector_search_results)} 个相关文物")
            
            # 如果有搜索结果，将相关信息添加到消息中
            if vector_search_results:
                context_info = "\n\n相关文物信息：\n"
                for i, result in enumerate(vector_search_results, 1):
                    metadata = result.get("metadata", {})
                    artifact_name = metadata.get("artifact_name", "未知")
                    number_period = metadata.get("number_period", "")
                    history = metadata.get("history", "")
                    context_info += f"{i}. {artifact_name}（{number_period}）\n"
                    if history:
                        context_info += f"   历史：{history[:100]}...\n"
                
                # 将上下文信息添加到用户消息中
                if current_message["content"]:
                    current_message["content"][0]["text"] = message + context_info
        except Exception as e:
            logger.error(f"向量搜索失败: {str(e)}")
    
    # 调用大模型生成回复
    ai_response = ""
    if multimodal_client:
        try:
            ai_response = multimodal_client._make_request(messages_to_send)
            
            # 保存用户消息（使用当前时间戳）
            user_timestamp = datetime.now()
            if image:
                # 保存图片到本地
                uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
                os.makedirs(uploads_dir, exist_ok=True)
                file_ext = image.filename.split('.')[-1].lower()
                image_filename = f"{uuid.uuid4().hex}.{file_ext}"
                image_path = os.path.join(uploads_dir, image_filename)
                
                with open(image_path, "wb") as buffer:
                    content = await image.read()
                    buffer.write(content)
                
                # 保存用户消息（包含图片路径）
                user_message_content = {
                    "text": message,
                    "image_path": f"/uploads/{image_filename}"
                }
                DatabaseService.save_message(x_user_id, "user", str(user_message_content), user_timestamp)
            else:
                # 保存纯文本用户消息
                DatabaseService.save_message(x_user_id, "user", message, user_timestamp)
            
            # 保存AI回复（延迟1秒保存）
            if ai_response:
                import time
                time.sleep(1)  # 延迟1秒
                ai_timestamp = datetime.now()
                DatabaseService.save_message(x_user_id, "assistant", ai_response, ai_timestamp)
                
        except Exception as e:
            logger.error(f"大模型处理失败: {str(e)}")
            ai_response = "抱歉，大模型处理出现问题，请稍后再试。"
    else:
        ai_response = "大模型服务不可用，这是模拟响应。"
    
    return {
        "success": True,
        "data": {
            "ai_response": ai_response,
            "timestamp": datetime.now().isoformat(),
            "related_artifacts": [
                {
                    "artifact_name": r.get("metadata", {}).get("artifact_name", ""),
                    "number_period": r.get("metadata", {}).get("number_period", ""),
                    "score": r.get("score", 0.0)
                }
                for r in vector_search_results
            ] if vector_search_results else []
        }
    }

# 向量数据库搜索接口
@app.post("/api/search")
async def search_artifacts(search_query: SearchQuery):
    """搜索文物
    
    Args:
        search_query: 搜索查询对象，包含查询文本、返回数量等参数
    
    Returns:
        搜索结果列表
    """
    log_request('向量数据库搜索')
    
    if not vector_db_service or not vector_db_service.is_ready():
        raise HTTPException(status_code=503, detail="向量数据库服务不可用")
    
    try:
        if search_query.use_enhanced:
            results = vector_db_service.search_enhanced(
                query_text=search_query.query,
                top_k=search_query.top_k,
                image_weight=search_query.image_weight
            )
        else:
            results = vector_db_service.search_normal(
                query_text=search_query.query,
                top_k=search_query.top_k
            )
        
        # 格式化返回结果
        formatted_results = []
        for result in results:
            metadata = result.get("metadata", {})
            formatted_results.append({
                "artifact_name": metadata.get("artifact_name", ""),
                "number_period": metadata.get("number_period", ""),
                "history": metadata.get("history", ""),
                "craft": metadata.get("craft", ""),
                "image_url": metadata.get("image_url", ""),
                "score": result.get("score", 0.0),
                "content": result.get("content", "")
            })
        
        return {
            "success": True,
            "data": {
                "results": formatted_results,
                "count": len(formatted_results),
                "query": search_query.query
            }
        }
    except Exception as e:
        logger.error(f"搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

# 构建向量数据库接口
@app.post("/api/vector-db/build")
async def build_vector_database(force_rebuild: bool = False):
    """构建向量数据库
    
    Args:
        force_rebuild: 是否强制重建（删除已存在的数据库）
    
    Returns:
        构建结果
    """
    log_request('构建向量数据库')
    
    if not vector_db_service:
        raise HTTPException(status_code=503, detail="向量数据库服务不可用")
    
    try:
        success = vector_db_service.build_vector_database(force_rebuild=force_rebuild)
        
        if success:
            return {
                "success": True,
                "message": "向量数据库构建成功",
                "data": {
                    "document_count": len(vector_db_service.documents) if vector_db_service.documents else 0
                }
            }
        else:
            return {
                "success": False,
                "message": "向量数据库构建失败，请检查日志"
            }
    except Exception as e:
        logger.error(f"构建向量数据库失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"构建失败: {str(e)}")

# 图片识别接口
@app.post("/api/recognize")
async def recognize_artifact(
    image: UploadFile = File(...)
):
    """识别图片中的文物
    
    Args:
        image: 上传的图片文件
    
    Returns:
        识别结果
    """
    log_request('图片识别')
    
    if not recognition_service or not recognition_service.is_ready():
        raise HTTPException(status_code=503, detail="文物识别服务不可用")
    
    # 文件类型检查
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    file_ext = image.filename.split('.')[-1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="不支持的文件类型")
    
    # 保存文件
    uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    file_path = os.path.join(uploads_dir, f"{uuid.uuid4().hex}.{file_ext}")
    
    try:
        with open(file_path, "wb") as buffer:
            content = await image.read()
            buffer.write(content)
        
        # 识别文物
        recognition_result = recognition_service.recognize_and_format(file_path)
        
        # 如果向量数据库可用，基于识别结果搜索相似文物
        similar_artifacts = []
        if vector_db_service and vector_db_service.is_ready() and recognition_result:
            try:
                # 构建搜索查询
                search_query = f"{recognition_result.get('artifact_type', '')} {recognition_result.get('artifact_name', '')}"
                if search_query.strip():
                    similar_artifacts = vector_db_service.search_enhanced(
                        query_text=search_query,
                        top_k=5,
                        image_weight=0.3
                    )
                    # 格式化结果
                    similar_artifacts = [
                        {
                            "artifact_name": r.get("metadata", {}).get("artifact_name", ""),
                            "number_period": r.get("metadata", {}).get("number_period", ""),
                            "score": r.get("score", 0.0)
                        }
                        for r in similar_artifacts
                    ]
            except Exception as e:
                logger.error(f"搜索相似文物失败: {str(e)}")
        
        return {
            "success": True,
            "data": {
                "recognition": recognition_result,
                "similar_artifacts": similar_artifacts,
                "file_url": f"/uploads/{os.path.basename(file_path)}"
            }
        }
    except Exception as e:
        logger.error(f"识别失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"识别失败: {str(e)}")
    finally:
        # 注意：这里不删除文件，因为可能需要后续使用
        pass

# 获取配置
@app.get("/api/config", response_model=ConfigResponse)
async def get_config():
    log_request('获取配置')
    # 这里需要实现配置获取逻辑
    return {"theme": "light", "language": "zh-CN"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
