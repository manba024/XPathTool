# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个基于LLM的智能XPath提取工具，主要用于从网页中自动提取指定元素的XPath路径。工具使用硅基流动API接入DeepSeek模型来分析HTML结构并生成准确的XPath选择器。项目采用异步架构，支持高并发批量处理。

## 核心功能

- **智能XPath提取**：使用LLM分析HTML结构，为指定的目标元素生成XPath选择器
- **异步网页内容获取**：使用aiohttp异步获取和清理网页HTML内容
- **XPath验证**：验证生成的XPath是否有效并显示匹配结果
- **异步批量处理**：支持高并发处理多个URL，显著提升效率
- **CSV导出**：结构化输出结果，便于后续处理和分析
- **配置文件管理**：使用JSON配置文件，支持灵活的参数设置

## 架构设计

项目采用异步模块化设计，分为以下核心组件：

### 核心类层次结构

1. **AsyncXPathExtractor** (`async_xpath_extractor.py:19`) - 异步基础提取器类
   - `fetch_webpage(url)` - 异步获取网页内容并清理HTML
   - `create_dom_summary(html_content)` - 创建DOM结构摘要用于LLM分析
   - `extract_xpath_with_llm(html_content, target_elements)` - 异步使用LLM提取XPath
   - `validate_xpath(html_content, xpath_dict)` - 验证XPath有效性
   - `extract_xpath(url, target_elements)` - 主要异步提取流程
   - `close()` - 关闭连接池

2. **AsyncBatchXPathExtractor** (`async_batch_extractor.py:26`) - 异步批量提取器类（继承自AsyncXPathExtractor）
   - `process_batch(urls, target_elements)` - 异步批量处理多个URL
   - `process_single_url(url, target_elements)` - 异步处理单个URL
   - `export_to_csv(results, target_elements)` - 导出结果到CSV文件
   - `load_urls_from_file(file_path)` - 从文件加载URL列表
   - `close()` - 关闭连接池

3. **ConfigManager** (`config_manager.py:13`) - 配置文件管理器
   - `load_config(config_path)` - 加载和验证配置文件
   - `validate_config_file(config_path)` - 验证配置文件格式
   - `normalize_config(config)` - 标准化配置格式

### 异步批量处理架构

批量处理采用异步并发模式，使用asyncio和aiohttp实现高并发：

- **异步任务池**：使用asyncio.create_task管理并发任务
- **HTTP连接池**：使用aiohttp.ClientSession复用HTTP连接
- **并发控制**：分别控制HTTP和LLM的并发数量
- **批处理**：支持批量提交任务提升效率
- **错误隔离**：单个URL失败不影响整体处理

## 依赖管理

项目依赖以下主要包（需要手动安装）：
```bash
pip install openai==1.98.0 beautifulsoup4==4.12.2 lxml==4.9.3 aiohttp==3.8.5 aiofiles
```

- `openai==1.98.0` - 用于调用硅基流动API
- `beautifulsoup4==4.12.2` - HTML解析和清理
- `lxml==4.9.3` - XPath验证
- `aiohttp==3.8.5` - 异步HTTP请求
- `aiofiles` - 异步文件操作
- `asyncio` - 异步编程（Python标准库）

## 环境配置

### Python环境
项目需要使用系统Python运行（推荐使用 Python 3.8+）

### 环境变量配置
```bash
export SILICONFLOW_API_KEY='your_api_key_here'
```

**重要提示**：必须设置此环境变量才能使用LLM功能，否则所有XPath提取操作都会失败。

## 常用命令

### 异步批量处理
```bash
# 运行异步批量处理
python3 async_main.py --config async_config.json

# 显示详细输出
python3 async_main.py --config async_config.json --verbose

# 静默模式
python3 async_main.py --config async_config.json --quiet
```

### 运行演示
```bash
./demo.sh
```

## 配置文件格式

异步批量处理使用JSON配置文件，支持以下配置：

```json
{
  "settings": {
    "max_concurrent": 10,
    "request_timeout": 30,
    "llm_timeout": 60,
    "retry_count": 3,
    "output_file": "async_batch_results.csv",
    "model": "Pro/deepseek-ai/DeepSeek-R1",
    "use_async": true,
    "max_http_concurrent": 20,
    "max_llm_concurrent": 5,
    "batch_size": 10,
    "connection_pool_size": 100
  },
  "target_elements": ["标题", "正文", "作者", "发布时间"],
  "urls_file": "urls.txt",
  "output_format": {
    "include_content_preview": true,
    "max_content_length": 200,
    "include_element_count": true,
    "include_processing_time": true
  }
}
```

## 输出格式

### 异步批量处理输出
CSV文件包含以下列：
- **URL**: 处理的网页地址
- **元素名称**: 目标元素名称
- **XPath**: 提取的XPath表达式
- **状态**: 成功/失败/错误
- **内容预览**: 元素内容预览
- **匹配数量**: 匹配的元素数量
- **处理时间(秒)**: 处理耗时
- **错误信息**: 错误详情

## 性能优化

### 异步并发控制
- **HTTP并发**: 建议设置为10-20，避免过多并发导致网站封禁
- **LLM并发**: 建议设置为3-5，避免API频率限制
- **批处理大小**: 建议设置为10-20，平衡效率和控制
- **连接池大小**: 建议设置为100，复用HTTP连接

### 超时设置
- **网络状况好**: request_timeout=30, llm_timeout=60
- **网络状况一般**: request_timeout=60, llm_timeout=120
- **网络状况差**: request_timeout=120, llm_timeout=180

## 项目结构

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

## 开发注意事项

- 需要配置硅基流动API密钥才能使用LLM功能
- 工具会自动清理HTML中的script和style标签
- 生成的XPath优先使用id、class等稳定属性
- 异步批量处理时建议先小规模测试配置
- 使用异步IO时注意资源管理和连接池关闭
- 配置文件支持相对路径和绝对路径
- 注意控制并发数量，避免被目标网站封禁