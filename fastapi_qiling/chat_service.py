import os
from openai import OpenAI
from typing import List, Dict

class ChatService:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.environ.get("AI_STUDIO_API_KEY"),
            base_url="https://aistudio.baidu.com/llm/lmapi/v3"
        )
        self.system_prompt = "你是 AI Studio 开发者助理，你精通开发相关的知识，负责给开发者提供搜索帮助建议。"
        self.max_history = 10  # 最大对话历史记录数

    def get_response(self, messages: List[Dict]) -> str:
        try:
            completion = self.client.chat.completions.create(
                model="ernie-3.5-8k",
                messages=messages
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"发生错误: {str(e)}"

    def start_chat(self):
        messages = [{"role": "system", "content": self.system_prompt}]
        print("""输入："结束"，结束对话""")
        
        while True:
            user_input = input("请输入：").strip()
            if user_input.lower() in ["结束", "exit", "quit"]:
                print("对话结束")
                break

            if not user_input:
                print("输入不能为空，请重新输入")
                continue

            messages.append({"role": "user", "content": user_input})
            
            # 限制对话历史长度
            if len(messages) > self.max_history * 2 + 1:  # 保留最近的n轮对话
                messages = [messages[0]] + messages[-self.max_history * 2:]
            
            response = self.get_response(messages)
            messages.append({"role": "assistant", "content": response})
            
            print(f"模型输出：{response}\n")

if __name__ == "__main__":
    chat = ChatService()
    chat.start_chat()