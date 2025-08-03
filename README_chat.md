# 硅基流动 DeepSeek 聊天工具

这是一个通过硅基流动平台接入 DeepSeek 模型的 Python 命令行聊天工具。

## 安装依赖

### 方法1：使用虚拟环境（推荐）

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 方法2：直接安装

```bash
pip install openai
```

## 使用方法

1. 获取硅基流动 API 密钥：
   - 访问 https://cloud.siliconflow.cn
   - 注册账号并获取 API 密钥

2. 设置环境变量：
   ```bash
   export SILICONFLOW_API_KEY='your_api_key_here'
   ```

3. 运行聊天工具：
   ```bash
   # 如果使用虚拟环境，先激活
   source venv/bin/activate  # Linux/Mac
   
   # 运行程序
   python siliconflow_chat.py
   ```

## 虚拟环境的好处

1. **依赖隔离**：避免与系统Python或其他项目的依赖冲突
2. **版本管理**：精确控制依赖版本，确保环境一致性
3. **清理方便**：可以轻松删除整个虚拟环境目录
4. **部署安全**：requirements.txt确保在其他机器上重现相同环境
5. **权限隔离**：无需系统管理员权限安装包

## 功能特性

- 支持连续对话，保持上下文
- 流式输出，实时显示响应
- 支持清空对话历史（输入 `clear`）
- 支持优雅退出（输入 `quit`, `exit` 或 `q`）

## 命令说明

- `clear` - 清空对话历史
- `quit`/`exit`/`q` - 退出程序
- `Ctrl+C` - 强制退出