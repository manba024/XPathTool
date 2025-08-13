#!/bin/bash

# 异步批量XPath提取工具使用示例脚本

echo "=== 异步批量XPath提取工具使用示例 ==="
echo

# 设置Python路径
PYTHON_CMD="python3"

echo "1. 检查异步配置文件..."
if [ -f "async_config.json" ]; then
    echo "✓ 异步配置文件存在"
else
    echo "✗ 异步配置文件不存在，请创建async_config.json"
    exit 1
fi
echo

echo "2. 验证异步配置文件..."
$PYTHON_CMD async_main.py --config async_config.json --quiet
if [ $? -eq 0 ]; then
    echo "✓ 配置文件验证通过"
else
    echo "✗ 配置文件验证失败"
    exit 1
fi
echo

echo "3. 显示帮助信息..."
$PYTHON_CMD async_main.py --help
echo

echo "4. 运行性能测试（可选）..."
if [ -f "performance_test.py" ]; then
    echo "运行性能测试脚本..."
    $PYTHON_CMD performance_test.py
else
    echo "性能测试脚本不存在，跳过"
fi
echo

echo "=== 注意事项 ==="
echo "- 请确保设置了环境变量 SILICONFLOW_API_KEY"
echo "- 配置文件中的URL数量建议从小批量开始测试"
echo "- 异步处理效率高，但注意控制并发数量避免被封禁"
echo "- 结果将导出为CSV格式，便于后续处理"
echo "- 推荐HTTP并发设置为10-20，LLM并发设置为3-5"
echo

echo "=== 配置完成 ==="
echo "现在可以使用以下命令开始异步批量处理："
echo "$PYTHON_CMD async_main.py --config async_config.json"
echo
echo "使用详细输出模式："
echo "$PYTHON_CMD async_main.py --config async_config.json --verbose"