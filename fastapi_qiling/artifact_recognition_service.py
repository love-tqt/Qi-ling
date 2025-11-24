# 文物识别服务
import os
import base64
import time
import tempfile
import requests
import logging
from openai import OpenAI
from typing import Tuple, Optional, Dict

logger = logging.getLogger(__name__)

class ArtifactRecognitionService:
    """文物识别服务类"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化文物识别服务
        
        Args:
            api_key: ERNIE API密钥，如果为None则从环境变量获取
        """
        if not api_key:
            api_key = os.environ.get("AI_STUDIO_API_KEY")
        
        if not api_key:
            logger.warning("⚠️ 警告: 未设置API密钥，图片识别功能将不可用")
            self.client = None
        else:
            try:
                self.client = OpenAI(
                    api_key=api_key,
                    base_url="https://aistudio.baidu.com/llm/lmapi/v3",
                )
                logger.info("✓ ERNIE客户端初始化成功")
            except Exception as e:
                logger.error(f"❌ 初始化ERNIE客户端失败: {str(e)}")
                self.client = None
    
    def classify_artifact_image_from_url(self, image_url: str) -> Tuple[str, str, float, str]:
        """使用ERNIE模型识别图片URL中的文物
        
        Args:
            image_url: 图片URL地址
        
        Returns:
            tuple: (artifact_type, artifact_name, confidence, description)
        """
        if self.client is None:
            return "未知文物", "未知", 0.0, "无法识别：客户端未初始化"
        
        if not image_url or not image_url.strip():
            return "未知文物", "未知", 0.0, "无法识别：图片地址为空"
        
        try:
            # 下载图片
            response = requests.get(image_url, timeout=10)
            if response.status_code != 200:
                return "未知文物", "未知", 0.0, f"无法识别：下载图片失败（状态码：{response.status_code}）"
            
            # 将图片保存到临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                tmp_file.write(response.content)
                tmp_image_path = tmp_file.name
            
            try:
                return self._classify_image_file(tmp_image_path)
            finally:
                # 清理临时文件
                if os.path.exists(tmp_image_path):
                    os.remove(tmp_image_path)
                    
        except requests.exceptions.RequestException as e:
            return "未知文物", "未知", 0.0, f"无法识别：网络请求失败 - {str(e)}"
        except Exception as e:
            return "未知文物", "未知", 0.0, f"无法识别：识别过程出错 - {str(e)}"
    
    def classify_artifact_image_from_file(self, image_path: str) -> Tuple[str, str, float, str]:
        """从本地文件识别图片中的文物
        
        Args:
            image_path: 本地图片文件路径
        
        Returns:
            tuple: (artifact_type, artifact_name, confidence, description)
        """
        if self.client is None:
            return "未知文物", "未知", 0.0, "无法识别：客户端未初始化"
        
        if not image_path or not os.path.exists(image_path):
            return "未知文物", "未知", 0.0, "无法识别：图片文件不存在"
        
        return self._classify_image_file(image_path)
    
    def _classify_image_file(self, image_path: str) -> Tuple[str, str, float, str]:
        """内部方法：识别图片文件
        
        Args:
            image_path: 图片文件路径
        
        Returns:
            tuple: (artifact_type, artifact_name, confidence, description)
        """
        try:
            # 读取图片并转换为base64
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # 构建提示词
            prompt = """你是一位专业的中国古代文物识别专家。请仔细分析这张图片中的文物，并提供以下信息：

1. 文物类型（如：青铜器、陶俑、壁画、瓷器、玉器等）
2. 具体文物名称（如：司母戊鼎、兵马俑、清明上河图等，如无法确定具体名称则说"该类文物"）
3. 识别置信度（0.0-1.0之间的数值）
4. 简要介绍（50-100字，包括历史背景、艺术特色或文化价值）

请按以下格式回答：
文物类型：青铜器
具体名称：司母戊鼎
置信度：0.95
介绍：这是商代晚期的青铜器，具有重要的历史价值..."""
            
            # 调用模型服务
            start_time = time.time()
            response = self.client.chat.completions.create(
                model="ernie-4.5-vl-28b-a3b-thinking",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.1
            )
            response_time = time.time() - start_time
            
            result_text = response.choices[0].message.content
            
            # 提取信息
            artifact_type = "未知文物"
            artifact_name = "未知"
            confidence = 0.0
            description = "无法解析识别结果"
            
            lines = result_text.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('文物类型：') or line.startswith('文物类型:'):
                    artifact_type = line.split('：', 1)[-1].split(':', 1)[-1].strip()
                elif line.startswith('具体名称：') or line.startswith('具体名称:'):
                    artifact_name = line.split('：', 1)[-1].split(':', 1)[-1].strip()
                elif line.startswith('置信度：') or line.startswith('置信度:'):
                    try:
                        conf_str = line.split('：', 1)[-1].split(':', 1)[-1].strip()
                        confidence = float(conf_str)
                    except:
                        confidence = 0.0
                elif line.startswith('介绍：') or line.startswith('介绍:'):
                    description = line.split('：', 1)[-1].split(':', 1)[-1].strip()
            
            # 如果没有找到介绍，使用整个响应作为描述
            if description == "无法解析识别结果" and result_text:
                description = result_text[:200]  # 限制长度
            
            logger.info(f"图片识别完成，耗时: {response_time:.2f}秒")
            return artifact_type, artifact_name, confidence, description
            
        except Exception as e:
            logger.error(f"识别过程出错: {str(e)}")
            return "未知文物", "未知", 0.0, f"无法识别：识别过程出错 - {str(e)}"
    
    def recognize_and_format(self, image_path: str) -> Dict:
        """识别图片并返回格式化结果
        
        Args:
            image_path: 图片路径（本地文件路径或URL）
        
        Returns:
            dict: 包含识别结果的字典
        """
        # 判断是URL还是本地路径
        if image_path.startswith('http://') or image_path.startswith('https://'):
            artifact_type, artifact_name, confidence, description = self.classify_artifact_image_from_url(image_path)
        else:
            artifact_type, artifact_name, confidence, description = self.classify_artifact_image_from_file(image_path)
        
        return {
            "artifact_type": artifact_type,
            "artifact_name": artifact_name,
            "confidence": confidence,
            "description": description
        }
    
    def is_ready(self) -> bool:
        """检查服务是否已准备好"""
        return self.client is not None

