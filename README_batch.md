# 批量XPath提取工具使用指南

## 快速开始

### 1. 创建配置文件

```bash
# 生成配置文件模板
python batch_main.py --init-config my_config.json
```

### 2. 编辑配置文件

编辑 `my_config.json` 文件，设置：
- `target_elements`: 要提取的元素列表
- `urls`: URL列表或设置 `urls_file` 指定URL文件
- `output_file`: 输出CSV文件路径

### 3. 准备URL列表

创建 `urls.txt` 文件，每行一个URL：

```
https://example.com/article1
https://example.com/article2
https://news.example.com/story1
```

### 4. 运行批量处理

```bash
# 使用配置文件运行
python batch_main.py --config my_config.json

# 显示详细输出
python batch_main.py --config my_config.json --verbose
```

## 配置文件说明

### 基本配置
```json
{
  "settings": {
    "max_concurrent": 5,           // 最大并发数
    "request_timeout": 30,         // 请求超时时间(秒)
    "llm_timeout": 60,             // LLM处理超时时间(秒)
    "retry_count": 3,              // 重试次数
    "output_file": "results.csv",  // 输出文件路径
    "model": "Pro/deepseek-ai/DeepSeek-R1"  // 使用的模型
  },
  "target_elements": [            // 要提取的元素列表
    "标题",
    "正文",
    "作者",
    "发布时间"
  ],
  "urls": [                       // 直接在配置文件中指定URL
    "https://example.com/article1"
  ],
  "urls_file": "urls.txt",        // 或者指定URL文件
  "output_format": {              // 输出格式设置
    "include_content_preview": true,
    "max_content_length": 200,
    "include_element_count": true,
    "include_processing_time": true
  }
}
```

### 高级配置
```json
{
  "settings": {
    "max_concurrent": 10,
    "request_timeout": 60,
    "llm_timeout": 120,
    "retry_count": 5,
    "output_file": "production_results.csv"
  },
  "target_elements": [
    "标题",
    "正文",
    "作者",
    "发布时间",
    "摘要",
    "标签",
    "评论数"
  ],
  "urls_file": "production_urls.txt",
  "exclude_urls_file": "exclude_urls.txt",
  "output_format": {
    "include_content_preview": true,
    "max_content_length": 500,
    "include_element_count": true,
    "include_processing_time": true
  }
}
```

## 使用示例

### 示例1: 简单批量处理

```bash
# 创建配置文件
python batch_main.py --init-config simple_config.json

# 编辑配置文件，设置目标元素和URL

# 运行处理
python batch_main.py --config simple_config.json
```

### 示例2: 大规模批量处理

```bash
# 创建配置文件
python batch_main.py --init-config large_config.json

# 编辑配置文件，设置较高的并发数
# "max_concurrent": 10

# 创建URL列表文件
echo "https://example.com/article1" >> urls.txt
echo "https://example.com/article2" >> urls.txt

# 运行处理
python batch_main.py --config large_config.json --verbose
```

### 示例3: 验证配置文件

```bash
# 验证配置文件格式
python batch_main.py --validate-config my_config.json
```

## 输出格式

生成的CSV文件包含以下列：
- **URL**: 处理的网页地址
- **元素名称**: 目标元素名称
- **XPath**: 提取的XPath表达式
- **状态**: 成功/失败/错误
- **内容预览**: 元素内容预览(可选)
- **匹配数量**: 匹配的元素数量(可选)
- **处理时间(秒)**: 处理耗时(可选)
- **错误信息**: 错误详情(如果有)

## 性能优化建议

### 1. 并发数设置
- **少量URL(1-10)**: 3-5个并发
- **中等数量(10-50)**: 5-10个并发
- **大量URL(50+)**: 10-20个并发

### 2. 超时设置
- **网络状况好**: request_timeout=30, llm_timeout=60
- **网络状况一般**: request_timeout=60, llm_timeout=120
- **网络状况差**: request_timeout=120, llm_timeout=180

### 3. 重试设置
- **重要任务**: retry_count=5
- **一般任务**: retry_count=3
- **快速测试**: retry_count=1

## 故障排除

### 常见问题

1. **API密钥错误**
   ```
   错误: 未设置API密钥
   解决方案: 设置环境变量 SILICONFLOW_API_KEY 或在配置文件中指定 api_key
   ```

2. **网络连接问题**
   ```
   错误: 获取网页失败
   解决方案: 检查网络连接，增加 request_timeout 和 retry_count
   ```

3. **LLM处理超时**
   ```
   错误: LLM分析失败
   解决方案: 增加 llm_timeout，减少目标元素数量
   ```

4. **内存不足**
   ```
   错误: 处理大量URL时内存不足
   解决方案: 减少 max_concurrent，分批处理URL
   ```

### 调试技巧

1. **启用详细输出**
   ```bash
   python batch_main.py --config config.json --verbose
   ```

2. **先验证配置文件**
   ```bash
   python batch_main.py --validate-config config.json
   ```

3. **小规模测试**
   先用少量URL测试配置是否正确

4. **检查输出文件**
   确保输出目录存在且有写入权限