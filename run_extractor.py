#!/usr/bin/env python3
"""
XPath提取工具简化运行脚本
在虚拟环境中自动运行xpath_extractor.py
"""

import sys
import subprocess
import os

def main():
    if len(sys.argv) < 3:
        print("使用方法: python run_extractor.py <URL> <元素1> [元素2] [元素3] ...")
        print("示例: python run_extractor.py https://example.com 标题 正文")
        sys.exit(1)
    
    # 构建命令
    url = sys.argv[1]
    elements = sys.argv[2:]
    
    # 确保在项目目录中
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # 构建完整命令
    cmd = [
        "bash", "-c", 
        f"source venv/bin/activate && python xpath_extractor.py '{url}' {' '.join(f\"'{elem}'\" for elem in elements)}"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        sys.exit(result.returncode)
    except Exception as e:
        print(f"运行出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()