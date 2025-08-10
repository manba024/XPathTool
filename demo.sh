#!/bin/bash

# 批量XPath提取工具使用示例脚本

echo "=== 批量XPath提取工具使用示例 ==="
echo

# 设置Python路径
PYTHON_CMD="/Library/Developer/CommandLineTools/usr/bin/python3"

echo "1. 创建配置文件模板..."
$PYTHON_CMD batch_main.py --init-config example_config.json
echo

echo "2. 验证配置文件..."
$PYTHON_CMD batch_main.py --validate-config test_config.json
echo

echo "3. 显示帮助信息..."
$PYTHON_CMD batch_main.py --help
echo

echo "=== 注意事项 ==="
echo "- 请确保设置了环境变量 SILICONFLOW_API_KEY"
echo "- 配置文件中的URL数量建议从小批量开始测试"
echo "- 可以根据网络状况调整并发数和超时设置"
echo "- 结果将导出为CSV格式，便于后续处理"
echo

echo "=== 配置完成 ==="
echo "现在可以使用以下命令开始批量处理："
echo "$PYTHON_CMD batch_main.py --config test_config.json"