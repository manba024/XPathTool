# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个基于LLM的智能XPath提取工具，主要用于从网页中自动提取指定元素的XPath路径。工具使用硅基流动API接入DeepSeek模型来分析HTML结构并生成准确的XPath选择器。

## 核心功能

- **智能XPath提取**：使用LLM分析HTML结构，为指定的目标元素生成XPath选择器
- **网页内容获取**：自动获取和清理网页HTML内容
- **XPath验证**：验证生成的XPath是否有效并显示匹配结果
- **多种运行方式**：支持命令行直接运行和脚本调用

## 项目结构

```
XPathTool/
├── xpath_extractor.py     # 核心提取工具类
├── backpu/               # 备份目录（包含旧版本文件）
│   ├── example_usage.py  # 使用示例
│   ├── run_extractor.py  # 虚拟环境运行脚本
│   ├── requirements.txt  # Python依赖
│   └── siliconflow_chat.py  # 硅基流动聊天工具
└── .gitignore           # Git忽略文件
```

## 核心类：XPathExtractor

位于 `xpath_extractor.py:16`，主要方法：

- `fetch_webpage(url)` - 获取网页内容并清理HTML
- `create_dom_summary(html_content)` - 创建DOM结构摘要用于LLM分析
- `extract_xpath_with_llm(html_content, target_elements)` - 使用LLM提取XPath
- `validate_xpath(html_content, xpath_dict)` - 验证XPath有效性
- `extract_xpath(url, target_elements)` - 主要提取流程

## 依赖管理

项目使用 `backpu/requirements.txt` 管理依赖，主要依赖：
- `openai==1.98.0` - 用于调用硅基流动API
- `beautifulsoup4==4.12.2` - HTML解析和清理
- `lxml==4.9.3` - XPath验证
- `requests==2.31.0` - HTTP请求

## 开发环境设置

### 创建虚拟环境
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r backpu/requirements.txt
```

### 环境变量配置
```bash
export SILICONFLOW_API_KEY='your_api_key_here'
```

## 常用命令

### 直接运行
```bash
python xpath_extractor.py <URL> <元素1> [元素2] ...
```

### 使用示例
```bash
python backpu/example_usage.py
```

### 虚拟环境运行
```bash
python backpu/run_extractor.py <URL> <元素1> [元素2] ...
```

## 输出格式

工具会输出两种格式的结果：
1. **摘要格式**：`URL + 数据名称 + XPath`
2. **详细格式**：包含XPath、状态、内容预览和匹配元素数

## 注意事项

- 需要配置硅基流动API密钥才能使用LLM功能
- 工具会自动清理HTML中的script和style标签
- 生成的XPath优先使用id、class等稳定属性
- 支持批量提取多个目标元素