# 异步XPath提取工具使用指南

## 📋 概述

异步XPath提取工具是基于LLM的智能网页元素提取工具，采用异步IO架构，支持高并发批量处理，显著提升性能。

## 🚀 主要特性

- **高性能异步处理**: 使用asyncio和aiohttp实现高并发处理
- **分层并发控制**: HTTP请求、LLM调用、全局任务的三级并发控制
- **智能XPath提取**: 使用DeepSeek模型分析HTML结构生成准确XPath
- **配置文件管理**: 灵活的JSON配置文件支持
- **CSV导出**: 结构化输出结果，便于后续处理
- **错误隔离**: 单个URL失败不影响整体处理

## 🛠️ 安装依赖

```bash
pip install openai beautifulsoup4 lxml aiohttp psutil
```

## 📝 配置文件格式

```json
{
  // 全局设置配置
  "settings": {
    // 最大并发任务数
    "max_concurrent": 10,
    // HTTP请求超时时间（秒）
    "request_timeout": 30,
    // LLM API调用超时时间（秒）
    "llm_timeout": 60,
    // 失败重试次数
    "retry_count": 3,
    // 输出文件名
    "output_file": "async_batch_results.csv",
    // 使用的LLM模型
    "model": "Pro/deepseek-ai/DeepSeek-R1",
    // 是否启用异步处理
    "use_async": true,
    // HTTP请求最大并发数
    "max_http_concurrent": 20,
    // LLM API调用最大并发数
    "max_llm_concurrent": 5,
    // 批处理大小
    "batch_size": 10,
    // HTTP连接池大小
    "connection_pool_size": 100
  },
  // 需要提取的目标元素列表
  "target_elements": [
    "标题",
    "正文内容",
    "发文时间",
    "发文机构",
    "附件"
  ],
  // URL列表文件路径（用于加载要处理的URL列表）
  "urls_file": "urls.txt",
  // 输出格式配置
  "output_format": {
    // 是否包含内容预览
    "include_content_preview": true,
    // 内容预览最大长度
    "max_content_length": 200,
    // 是否包含匹配元素数量
    "include_element_count": true,
    // 是否包含处理时间
    "include_processing_time": true
  }
}
```

## 🎯 使用方法

### 1. 运行异步批量处理

```bash
python async_main.py --config async_config.json
```

### 2. 显示详细输出

```bash
python async_main.py --config async_config.json --verbose
```

### 3. 静默模式

```bash
python async_main.py --config async_config.json --quiet
```

### 4. 显示帮助信息

```bash
python async_main.py --help
```

## 🧪 性能测试

### 运行性能测试

```bash
python performance_test.py
```

## 🏗️ 架构设计

### 异步处理流程

```
主线程 → 配置管理 → 异步任务池 → 并发处理 → 结果收集
                    ↓
              分层并发控制
                    ↓
              HTTP/LLM信号量
                    ↓
              进度监控
```

### 并发控制策略

- **全局并发**: 控制总并发数 (默认: 10)
- **HTTP并发**: 控制HTTP请求并发 (默认: 20)
- **LLM并发**: 控制LLM API调用并发 (默认: 5)
- **批处理**: 自动分批处理大任务 (默认: 10个/批)

## 🔧 故障排除

### 常见问题

1. **ModuleNotFoundError: No module named 'aiohttp'**
   ```bash
   pip install aiohttp psutil
   ```

2. **API密钥未设置**
   ```bash
   export SILICONFLOW_API_KEY='your_api_key_here'
   ```

3. **并发数过高被限制**
   - 降低 `max_http_concurrent` 和 `max_llm_concurrent`
   - 增加 `request_timeout` 和 `llm_timeout`

### 性能调优建议

1. **网络状况好**:
   ```json
   {
     "max_http_concurrent": 20,
     "max_llm_concurrent": 5,
     "request_timeout": 30,
     "llm_timeout": 60
   }
   ```

2. **网络状况一般**:
   ```json
   {
     "max_http_concurrent": 10,
     "max_llm_concurrent": 3,
     "request_timeout": 60,
     "llm_timeout": 120
   }
   ```

3. **网络状况差**:
   ```json
   {
     "max_http_concurrent": 5,
     "max_llm_concurrent": 2,
     "request_timeout": 120,
     "llm_timeout": 180
   }
   ```

## 📁 项目文件结构

```
XPathTool/
├── async_xpath_extractor.py   # 异步核心提取工具类
├── async_batch_extractor.py  # 异步批量提取器类
├── async_main.py             # 异步主程序入口
├── config_manager.py         # 配置文件管理器
├── async_config.json         # 异步配置文件
├── urls.txt                  # URL列表文件示例
├── test_urls.txt             # 测试URL列表
├── demo.sh                   # 演示脚本
├── performance_test.py       # 性能测试脚本
├── CLAUDE.md                 # Claude Code 项目说明
├── README_async.md           # 异步版本使用指南
└── ARCHITECTURE.md           # 架构文档
```

## 📈 输出格式

### CSV输出列说明

- **URL**: 处理的网页地址
- **元素名称**: 目标元素名称
- **XPath**: 提取的XPath表达式
- **状态**: 成功/失败/错误
- **内容预览**: 元素内容预览
- **匹配数量**: 匹配的元素数量
- **处理时间(秒)**: 处理耗时
- **错误信息**: 错误详情

## 🎯 最佳实践

1. **从小规模开始**: 先用3-5个URL测试配置
2. **监控资源使用**: 观察CPU和内存使用情况
3. **合理设置并发**: 根据网络状况调整并发数
4. **使用批处理**: 大量URL时启用批处理
5. **注意控制并发**: 避免被目标网站封禁
6. **定期清理结果**: 避免输出文件过大

## 📞 技术支持

如有问题，请检查：
1. 依赖是否正确安装
2. API密钥是否配置
3. 网络连接是否正常
4. 配置文件格式是否正确
5. URL列表文件是否存在且格式正确

## 🔗 环境变量

```bash
export SILICONFLOW_API_KEY='your_api_key_here'
```

## 📊 性能特点

- **高并发**: 支持HTTP和LLM的分层并发控制
- **内存优化**: 使用异步IO减少内存占用
- **连接复用**: HTTP连接池提升性能
- **错误隔离**: 单个任务失败不影响整体处理
- **实时监控**: 处理进度和性能统计实时显示