# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个基于LLM的智能XPath提取工具，主要用于从网页中自动提取指定元素的XPath路径。工具使用硅基流动API接入DeepSeek模型来分析HTML结构并生成准确的XPath选择器。项目支持单个URL处理和批量处理两种模式。

## 核心功能

- **智能XPath提取**：使用LLM分析HTML结构，为指定的目标元素生成XPath选择器
- **网页内容获取**：自动获取和清理网页HTML内容
- **XPath验证**：验证生成的XPath是否有效并显示匹配结果
- **批量处理**：支持同时处理多个URL，显著提升效率
- **CSV导出**：结构化输出结果，便于后续处理和分析
- **配置文件管理**：使用JSON配置文件，支持灵活的参数设置

## 架构设计

项目采用模块化设计，分为以下核心组件：

### 核心类层次结构

1. **XPathExtractor** (`xpath_extractor.py:16`) - 基础提取器类
   - `fetch_webpage(url)` - 获取网页内容并清理HTML
   - `create_dom_summary(html_content)` - 创建DOM结构摘要用于LLM分析
   - `extract_xpath_with_llm(html_content, target_elements)` - 使用LLM提取XPath
   - `validate_xpath(html_content, xpath_dict)` - 验证XPath有效性
   - `extract_xpath(url, target_elements)` - 主要提取流程

2. **BatchXPathExtractor** (`batch_extractor.py:23`) - 批量提取器类（继承自XPathExtractor）
   - `process_batch(urls, target_elements)` - 批量处理多个URL
   - `process_single_url(url, target_elements)` - 处理单个URL（线程池任务）
   - `export_to_csv(results, target_elements)` - 导出结果到CSV文件
   - `load_urls_from_file(file_path)` - 从文件加载URL列表

3. **ConfigManager** (`config_manager.py:8`) - 配置文件管理器
   - `load_config(config_path)` - 加载和验证配置文件
   - `validate_config_file(config_path)` - 验证配置文件格式
   - `create_template_config(output_path)` - 创建配置文件模板

### 批量处理架构

批量处理采用生产者-消费者模式，使用线程池实现并发：

- **主线程**：负责任务分发和进度监控
- **工作线程**：处理单个URL的XPath提取
- **进度跟踪**：使用线程锁确保进度显示的线程安全
- **错误隔离**：单个URL失败不影响整体处理

## 依赖管理

项目使用 `backpu/requirements.txt` 管理依赖，主要依赖：
- `openai==1.98.0` - 用于调用硅基流动API
- `beautifulsoup4==4.12.2` - HTML解析和清理
- `lxml==4.9.3` - XPath验证
- `requests==2.31.0` - HTTP请求
- `concurrent.futures` - 线程池（Python标准库）

## 环境配置

### Python环境
项目需要使用系统Python运行（推荐使用 `/Library/Developer/CommandLineTools/usr/bin/python3`）

### 环境变量配置
```bash
export SILICONFLOW_API_KEY='your_api_key_here'
```

## 常用命令

### 单个URL处理
```bash
python3 xpath_extractor.py <URL> <元素1> [元素2] ...
```

### 批量处理
```bash
# 创建配置文件模板
python3 batch_main.py --init-config config.json

# 验证配置文件
python3 batch_main.py --validate-config config.json

# 运行批量处理
python3 batch_main.py --config config.json

# 显示详细输出
python3 batch_main.py --config config.json --verbose
```

### 运行演示
```bash
./demo.sh
```

## 配置文件格式

批量处理使用JSON配置文件，支持以下配置：

```json
{
  "settings": {
    "max_concurrent": 5,
    "request_timeout": 30,
    "llm_timeout": 60,
    "retry_count": 3,
    "output_file": "results.csv"
  },
  "target_elements": ["标题", "正文", "作者"],
  "urls": ["https://example.com/article1"],
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

### 单个URL处理输出
1. **摘要格式**：`URL + 数据名称 + XPath`
2. **详细格式**：包含XPath、状态、内容预览和匹配元素数

### 批量处理输出
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

### 并发控制
- **少量URL(1-10)**: 3-5个并发
- **中等数量(10-50)**: 5-10个并发
- **大量URL(50+)**: 10-20个并发

### 超时设置
- **网络状况好**: request_timeout=30, llm_timeout=60
- **网络状况一般**: request_timeout=60, llm_timeout=120
- **网络状况差**: request_timeout=120, llm_timeout=180

## 项目结构

```
XPathTool/
├── xpath_extractor.py        # 核心提取工具类
├── batch_extractor.py        # 批量提取器类
├── config_manager.py         # 配置文件管理器
├── batch_main.py             # 主程序入口
├── config_template.json      # 配置文件模板
├── test_config.json          # 测试配置文件
├── urls.txt                  # URL列表文件示例
├── demo.sh                   # 演示脚本
├── README_batch.md           # 批量处理使用指南
├── backpu/                   # 备份目录（包含旧版本文件）
│   ├── example_usage.py      # 使用示例
│   ├── run_extractor.py      # 虚拟环境运行脚本
│   ├── requirements.txt      # Python依赖
│   └── siliconflow_chat.py  # 硅基流动聊天工具
└── .gitignore               # Git忽略文件
```

## 开发注意事项

- 需要配置硅基流动API密钥才能使用LLM功能
- 工具会自动清理HTML中的script和style标签
- 生成的XPath优先使用id、class等稳定属性
- 批量处理时建议先小规模测试配置
- 使用线程池时注意资源管理和错误处理
- 配置文件支持相对路径和绝对路径