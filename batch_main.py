#!/usr/bin/env python3
"""
批量XPath提取工具主程序
"""

import sys
import os
import argparse
from pathlib import Path

# 导入自定义模块
from batch_extractor import BatchXPathExtractor
from config_manager import ConfigManager


def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description='批量XPath提取工具 - 支持配置文件和CSV导出',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 使用配置文件
  python batch_main.py --config config.json
  
  # 验证配置文件
  python batch_main.py --validate-config config.json
  
  # 创建配置文件模板
  python batch_main.py --init-config template.json
  
  # 显示版本信息
  python batch_main.py --version
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='配置文件路径'
    )
    
    parser.add_argument(
        '--validate-config', '-v',
        type=str,
        help='验证配置文件'
    )
    
    parser.add_argument(
        '--init-config', '-i',
        type=str,
        help='创建配置文件模板'
    )
    
    parser.add_argument(
        '--version', '-V',
        action='version',
        version='批量XPath提取工具 v1.0.0'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='显示详细输出'
    )
    
    return parser


def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    # 初始化配置管理器
    config_manager = ConfigManager()
    
    try:
        # 处理不同的命令
        if args.validate_config:
            # 验证配置文件
            success = config_manager.validate_config_file(args.validate_config)
            sys.exit(0 if success else 1)
            
        elif args.init_config:
            # 创建配置文件模板
            config_manager.create_template_config(args.init_config)
            sys.exit(0)
            
        elif args.config:
            # 使用配置文件运行
            config_path = args.config
            
            if not os.path.exists(config_path):
                print(f"错误: 配置文件不存在: {config_path}")
                sys.exit(1)
            
            print(f"加载配置文件: {config_path}")
            
            # 加载配置
            try:
                config = config_manager.load_config(config_path)
            except Exception as e:
                print(f"错误: 加载配置文件失败: {str(e)}")
                sys.exit(1)
            
            # 检查URL列表
            urls = config.get('urls', [])
            if not urls:
                print("错误: 配置文件中没有有效的URL")
                sys.exit(1)
            
            target_elements = config.get('target_elements', [])
            if not target_elements:
                print("错误: 配置文件中没有目标元素")
                sys.exit(1)
            
            print(f"找到 {len(urls)} 个URL")
            print(f"目标元素: {', '.join(target_elements)}")
            
            # 检查API密钥
            api_key = config.get('api_key') or os.getenv('SILICONFLOW_API_KEY')
            if not api_key:
                print("错误: 未设置API密钥")
                print("请设置环境变量 SILICONFLOW_API_KEY 或在配置文件中指定 api_key")
                sys.exit(1)
            
            # 初始化批量提取器
            extractor = BatchXPathExtractor(config)
            
            # 显示配置信息
            if args.verbose:
                print("\n配置信息:")
                print(f"  - 并发数: {config['max_concurrent']}")
                print(f"  - 请求超时: {config['request_timeout']}秒")
                print(f"  - LLM超时: {config['llm_timeout']}秒")
                print(f"  - 重试次数: {config['retry_count']}")
                print(f"  - 输出文件: {config['output_file']}")
                print(f"  - 模型: {config['model']}")
                print()
            
            # 开始批量处理
            try:
                results = extractor.process_batch(urls, target_elements)
                
                # 打印摘要
                extractor.print_summary(results)
                
                # 导出CSV
                extractor.export_to_csv(results, target_elements)
                
                print("\n批量处理完成!")
                
            except KeyboardInterrupt:
                print("\n\n用户中断处理")
                sys.exit(1)
            except Exception as e:
                print(f"\n错误: 批量处理失败: {str(e)}")
                if args.verbose:
                    import traceback
                    traceback.print_exc()
                sys.exit(1)
                
        else:
            # 没有提供参数
            parser.print_help()
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"错误: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()