#!/usr/bin/env python3
"""
异步批量XPath提取工具主程序
"""

import asyncio
import sys
import os
import argparse
from typing import Dict, Any

# 导入配置管理器和异步批量提取器
from config_manager import ConfigManager
from async_batch_extractor import AsyncBatchXPathExtractor


def create_argument_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description='异步批量XPath提取工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 创建配置文件模板
  python async_main.py --init-config async_config.json
  
  # 验证配置文件
  python async_main.py --validate-config async_config.json
  
  # 运行异步批量处理
  python async_main.py --config async_config.json
  
  # 显示详细输出
  python async_main.py --config async_config.json --verbose
  
  # 显示性能统计
  python async_main.py --config async_config.json --show-stats
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='配置文件路径'
    )
    
    parser.add_argument(
        '--init-config',
        type=str,
        help='创建配置文件模板到指定路径'
    )
    
    parser.add_argument(
        '--validate-config',
        type=str,
        help='验证配置文件'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细输出'
    )
    
    parser.add_argument(
        '--show-stats',
        action='store_true',
        help='显示性能统计'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='静默模式，只显示错误信息'
    )
    
    return parser


async def run_async_batch_processing(config_path: str, verbose: bool = False, quiet: bool = False, show_stats: bool = False):
    """运行异步批量处理"""
    
    if quiet:
        # 重定向标准输出到/dev/null
        import io
        sys.stdout = io.StringIO()
    
    try:
        # 加载配置
        config_manager = ConfigManager()
        config = config_manager.load_config(config_path)
        
        if not quiet:
            print("配置加载成功")
            print(f"异步模式: {'启用' if config.get('use_async', True) else '禁用'}")
        
        # 检查URL列表
        if not config.get("urls"):
            print("错误: 配置文件中没有有效的URL")
            return False
        
        # 检查目标元素
        if not config.get("target_elements"):
            print("错误: 配置文件中没有目标元素")
            return False
        
        # 初始化异步批量提取器
        extractor = AsyncBatchXPathExtractor(config)
        
        # 获取处理参数
        urls = config["urls"]
        target_elements = config["target_elements"]
        
        if not quiet:
            print(f"开始处理 {len(urls)} 个URL")
            print(f"目标元素: {', '.join(target_elements)}")
        
        # 执行异步批量处理
        results = await extractor.process_batch_async(urls, target_elements)
        
        # 导出结果
        extractor.export_to_csv(results, target_elements)
        
        # 打印摘要
        if not quiet:
            extractor.print_summary(results)
            
            # 显示性能统计
            if show_stats:
                extractor.print_performance_stats()
        
        return True
        
    except Exception as e:
        print(f"处理失败: {str(e)}")
        return False
    finally:
        if quiet:
            # 恢复标准输出
            sys.stdout = sys.__stdout__


def main():
    """主函数"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # 检查API密钥
    if not os.getenv('SILICONFLOW_API_KEY'):
        print("警告: 未设置环境变量 SILICONFLOW_API_KEY")
        print("请设置API密钥: export SILICONFLOW_API_KEY='your_api_key_here'")
        return
    
    # 处理不同的命令
    if args.init_config:
        # 创建配置文件模板
        config_manager = ConfigManager()
        config_manager.create_template_config(args.init_config)
        print(f"配置文件模板已创建: {args.init_config}")
        
    elif args.validate_config:
        # 验证配置文件
        config_manager = ConfigManager()
        is_valid = config_manager.validate_config_file(args.validate_config)
        if not is_valid:
            sys.exit(1)
        
    elif args.config:
        # 运行异步批量处理
        success = asyncio.run(run_async_batch_processing(
            args.config,
            verbose=args.verbose,
            quiet=args.quiet,
            show_stats=args.show_stats
        ))
        
        if not success:
            sys.exit(1)
        
    else:
        # 显示帮助信息
        parser.print_help()


if __name__ == "__main__":
    main()