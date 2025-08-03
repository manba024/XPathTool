#!/usr/bin/env python3
"""
硅基流动 DeepSeek 命令行聊天工具
使用前请设置环境变量 SILICONFLOW_API_KEY
"""

import os
import sys
from openai import OpenAI

class SiliconFlowChat:
    def __init__(self):
        API_KEY = os.getenv('SILICONFLOW_API_KEY')
        self.api_key = API_KEY
        if not self.api_key:
            print("错误：请设置环境变量 SILICONFLOW_API_KEY")
            print("例如：export SILICONFLOW_API_KEY='your_api_key_here'")
            sys.exit(1)
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.siliconflow.cn/v1"
        )
        
        self.conversation_history = []
        
    def chat(self, user_input):
        """发送消息并获取回复"""
        self.conversation_history.append({"role": "user", "content": user_input})
        
        try:
            response = self.client.chat.completions.create(
                # model="deepseek-ai/DeepSeek-R1",
                model="Pro/deepseek-ai/DeepSeek-R1",
                messages=self.conversation_history,
                stream=True,
                max_tokens=2048,
                temperature=0.7
            )
            
            assistant_response = ""
            print("DeepSeek: ", end="", flush=True)
            
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
                    assistant_response += content
            
            print()  # 换行
            self.conversation_history.append({"role": "assistant", "content": assistant_response})
            
        except Exception as e:
            print(f"错误：{e}")
    
    def run(self):
        """启动命令行聊天循环"""
        print("硅基流动 DeepSeek 聊天助手")
        print("输入 'quit', 'exit' 或 'q' 退出")
        print("输入 'clear' 清空对话历史")
        print("-" * 50)
        
        while True:
            try:
                user_input = input("你: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("再见！")
                    break
                elif user_input.lower() == 'clear':
                    self.conversation_history = []
                    print("对话历史已清空")
                    continue
                elif not user_input:
                    continue
                
                self.chat(user_input)
                
            except KeyboardInterrupt:
                print("\n再见！")
                break
            except EOFError:
                print("\n再见！")
                break

if __name__ == "__main__":
    chat_bot = SiliconFlowChat()
    chat_bot.run()