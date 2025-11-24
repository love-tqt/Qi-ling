import os
import base64
import json
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class ERNIE4_5MultimodalClient:
    def __init__(self):
        """
        初始化 ERNIE 4.5 多模态客户端
        """
        self.api_key = os.environ.get("AI_STUDIO_API_KEY")
        self.base_url = "https://aistudio.baidu.com/llm/lmapi/v3"
        self.model = "ernie-4.5-vl-28b-a3b"  # ERNIE-4.5-VL-28B-A3B 的模型参数值
        
        if not self.api_key:
            raise ValueError("AI_STUDIO_API_KEY 环境变量未设置")
    
    def _make_request(self, messages, stream=False):
        """
        发送请求到百度文心 API
        """
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            # 检查响应状态
            if response.status_code != 200:
                error_msg = f"API返回错误状态码: {response.status_code}"
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_msg = f"{error_msg} - {error_data['error']}"
                except:
                    pass
                return error_msg
            
            result = response.json()
            
            # 检查API返回的错误信息
            if 'error' in result:
                return f"API错误: {result['error']}"
                
            if 'choices' not in result or len(result['choices']) == 0:
                return "API返回格式异常: 缺少choices字段"
                
            if 'message' not in result['choices'][0]:
                return "API返回格式异常: 缺少message字段"
                
            return result['choices'][0]['message']['content']
                
        except requests.exceptions.HTTPError as e:
            if response.status_code == 400:
                # 400错误通常是请求格式问题
                try:
                    error_data = response.json()
                    return f"请求格式错误: {error_data.get('error', str(e))}"
                except:
                    return f"HTTP 400错误: 请求格式不正确 - {str(e)}"
            elif response.status_code == 401:
                return "API密钥无效或已过期"
            elif response.status_code == 403:
                return "API访问权限不足"
            elif response.status_code == 429:
                return "API调用频率限制"
            else:
                return f"HTTP错误 {response.status_code}: {str(e)}"
                
        except Exception as e:
            return f"请求异常: {str(e)}"
    
    def text_only_query(self, prompt):
        """
        纯文本查询
        """
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]
        return self._make_request(messages)
    
    def text_only_stream(self, prompt):
        """
        纯文本流式输出
        """
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]
        return self._make_request(messages, stream=True)
    
    def image_url_query(self, image_url, text_prompt):
        """
        图片URL输入查询
        """
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": text_prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        }
                    }
                ]
            }
        ]
        return self._make_request(messages)
    
    def image_base64_query(self, image_path, text_prompt):
        """
        图片base64输入查询
        """
        # 编码图片为base64
        base64_image = self.encode_image(image_path)
        
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": text_prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
        return self._make_request(messages)
    
    def encode_image(self, image_path):
        """
        将图片编码为base64
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    
    def multimodal_stream(self, text_prompt, image_url=None, image_path=None):
        """
        多模态流式输出
        """
        content = [{"type": "text", "text": text_prompt}]
        
        if image_url:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": image_url
                }
            })
        elif image_path:
            base64_image = self.encode_image(image_path)
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
            })
        
        messages = [{"role": "user", "content": content}]
        
        return self._make_request(messages, stream=True)

def quick_test():
    """
    快速测试函数
    """
    print("ERNIE-4.5 多模态模型快速测试...")
    
    client = ERNIE4_5MultimodalClient()
    
    # 简单文本测试
    response = client.text_only_query("你好，请简单介绍一下你自己")
    print(f"模型回复: {response}")

if __name__ == "__main__":
    # 检查环境变量是否设置
    if not os.environ.get("AI_STUDIO_API_KEY"):
        print("警告: 未设置 AI_STUDIO_API_KEY 环境变量")
        print("请在项目根目录创建 .env 文件并添加:")
        print("AI_STUDIO_API_KEY=您的访问令牌")
    else:
        quick_test()