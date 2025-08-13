#!/usr/bin/env python3
"""
性能对比测试脚本 - 同步vs异步模式性能对比
"""

import asyncio
import time
import sys
import os
import json
import psutil
import threading
from typing import List, Dict, Any
from datetime import datetime

# 导入同步和异步模块
from batch_extractor import BatchXPathExtractor
from async_batch_extractor import AsyncBatchXPathExtractor
from config_manager import ConfigManager


class PerformanceTester:
    """性能测试器"""
    
    def __init__(self):
        self.test_results = []
        
    def get_memory_usage(self) -> float:
        """获取当前内存使用量（MB）"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    
    def get_cpu_usage(self) -> float:
        """获取当前CPU使用率"""
        return psutil.cpu_percent(interval=0.1)
    
    def create_test_config(self, num_urls: int, use_async: bool = True) -> Dict[str, Any]:
        """创建测试配置"""
        # 创建测试URL列表（使用不同的URL进行测试）
        test_urls = [
            "https://httpbin.org/html",
            "https://httpbin.org/json",
            "https://jsonplaceholder.typicode.com/posts/1",
            "https://jsonplaceholder.typicode.com/posts/2",
            "https://jsonplaceholder.typicode.com/posts/3",
        ]
        
        # 如果需要更多URL，重复使用但添加不同的参数
        urls = []
        for i in range(num_urls):
            url = test_urls[i % len(test_urls)]
            if i >= len(test_urls):
                url += f"?test={i}"  # 添加参数使URL不同
            urls.append(url)
        
        config = {
            "max_concurrent": 5 if use_async else 3,  # 异步使用更高并发
            "request_timeout": 30,
            "llm_timeout": 60,
            "retry_count": 1,  # 减少重试以加快测试
            "output_file": f"test_results_{'async' if use_async else 'sync'}.csv",
            "model": "Pro/deepseek-ai/DeepSeek-R1",
            "use_async": use_async,
            "max_http_concurrent": 10 if use_async else 5,
            "max_llm_concurrent": 3 if use_async else 2,
            "batch_size": 5,
            "connection_pool_size": 50,
            "target_elements": ["标题", "内容"],
            "urls": urls,
            "output_format": {
                "include_content_preview": True,
                "max_content_length": 100,
                "include_element_count": True,
                "include_processing_time": True
            }
        }
        
        return config
    
    async def run_async_test(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """运行异步测试"""
        print("开始异步模式测试...")
        
        start_time = time.time()
        start_memory = self.get_memory_usage()
        start_cpu = self.get_cpu_usage()
        
        try:
            # 初始化异步提取器
            extractor = AsyncBatchXPathExtractor(config)
            
            # 获取测试参数
            urls = config["urls"]
            target_elements = config["target_elements"]
            
            # 运行异步批量处理
            results = await extractor.process_batch_async(urls, target_elements)
            
            # 计算统计信息
            end_time = time.time()
            end_memory = self.get_memory_usage()
            end_cpu = self.get_cpu_usage()
            
            total_time = end_time - start_time
            total_urls = len(urls)
            successful_urls = sum(1 for r in results if r['status'] == 'success')
            
            return {
                "mode": "async",
                "total_urls": total_urls,
                "successful_urls": successful_urls,
                "total_time": total_time,
                "qps": total_urls / total_time if total_time > 0 else 0,
                "avg_time_per_url": total_time / total_urls if total_urls > 0 else 0,
                "memory_usage": end_memory - start_memory,
                "cpu_usage": end_cpu,
                "max_concurrent": config["max_concurrent"],
                "results": results
            }
            
        except Exception as e:
            print(f"异步测试失败: {str(e)}")
            return {
                "mode": "async",
                "error": str(e),
                "total_urls": len(config["urls"]),
                "successful_urls": 0,
                "total_time": 0,
                "qps": 0,
                "avg_time_per_url": 0,
                "memory_usage": 0,
                "cpu_usage": 0
            }
    
    def run_sync_test(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """运行同步测试"""
        print("开始同步模式测试...")
        
        start_time = time.time()
        start_memory = self.get_memory_usage()
        start_cpu = self.get_cpu_usage()
        
        try:
            # 初始化同步提取器
            extractor = BatchXPathExtractor(config)
            
            # 获取测试参数
            urls = config["urls"]
            target_elements = config["target_elements"]
            
            # 运行同步批量处理
            results = extractor.process_batch(urls, target_elements)
            
            # 计算统计信息
            end_time = time.time()
            end_memory = self.get_memory_usage()
            end_cpu = self.get_cpu_usage()
            
            total_time = end_time - start_time
            total_urls = len(urls)
            successful_urls = sum(1 for r in results if r['status'] == 'success')
            
            return {
                "mode": "sync",
                "total_urls": total_urls,
                "successful_urls": successful_urls,
                "total_time": total_time,
                "qps": total_urls / total_time if total_time > 0 else 0,
                "avg_time_per_url": total_time / total_urls if total_urls > 0 else 0,
                "memory_usage": end_memory - start_memory,
                "cpu_usage": end_cpu,
                "max_concurrent": config["max_concurrent"],
                "results": results
            }
            
        except Exception as e:
            print(f"同步测试失败: {str(e)}")
            return {
                "mode": "sync",
                "error": str(e),
                "total_urls": len(config["urls"]),
                "successful_urls": 0,
                "total_time": 0,
                "qps": 0,
                "avg_time_per_url": 0,
                "memory_usage": 0,
                "cpu_usage": 0
            }
    
    async def run_comparison_test(self, num_urls: int = 10) -> Dict[str, Any]:
        """运行对比测试"""
        print(f"开始性能对比测试，测试URL数量: {num_urls}")
        print("=" * 60)
        
        # 创建测试配置
        async_config = self.create_test_config(num_urls, use_async=True)
        sync_config = self.create_test_config(num_urls, use_async=False)
        
        # 运行异步测试
        async_result = await self.run_async_test(async_config)
        
        # 运行同步测试
        sync_result = self.run_sync_test(sync_config)
        
        # 生成对比报告
        comparison = self.generate_comparison_report(async_result, sync_result)
        
        return {
            "test_info": {
                "num_urls": num_urls,
                "test_time": datetime.now().isoformat(),
                "system_info": {
                    "cpu_count": psutil.cpu_count(),
                    "memory_total": psutil.virtual_memory().total / 1024 / 1024 / 1024,
                    "platform": sys.platform
                }
            },
            "async_result": async_result,
            "sync_result": sync_result,
            "comparison": comparison
        }
    
    def generate_comparison_report(self, async_result: Dict[str, Any], sync_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成对比报告"""
        comparison = {}
        
        # QPS对比
        if async_result["qps"] > 0 and sync_result["qps"] > 0:
            comparison["qps_improvement"] = (async_result["qps"] / sync_result["qps"] - 1) * 100
            comparison["qps_ratio"] = async_result["qps"] / sync_result["qps"]
        
        # 处理时间对比
        if async_result["avg_time_per_url"] > 0 and sync_result["avg_time_per_url"] > 0:
            comparison["time_improvement"] = (sync_result["avg_time_per_url"] / async_result["avg_time_per_url"] - 1) * 100
            comparison["time_ratio"] = sync_result["avg_time_per_url"] / async_result["avg_time_per_url"]
        
        # 内存使用对比
        if async_result["memory_usage"] > 0 and sync_result["memory_usage"] > 0:
            comparison["memory_improvement"] = (sync_result["memory_usage"] / async_result["memory_usage"] - 1) * 100
            comparison["memory_ratio"] = sync_result["memory_usage"] / async_result["memory_usage"]
        
        # 成功率对比
        if async_result["successful_urls"] > 0 and sync_result["successful_urls"] > 0:
            async_success_rate = async_result["successful_urls"] / async_result["total_urls"] * 100
            sync_success_rate = sync_result["successful_urls"] / sync_result["total_urls"] * 100
            comparison["success_rate_diff"] = async_success_rate - sync_success_rate
        
        return comparison
    
    def print_test_results(self, results: Dict[str, Any]):
        """打印测试结果"""
        print("\n" + "=" * 60)
        print("性能测试结果")
        print("=" * 60)
        
        # 系统信息
        sys_info = results["test_info"]["system_info"]
        print(f"测试时间: {results['test_info']['test_time']}")
        print(f"测试URL数量: {results['test_info']['num_urls']}")
        print(f"CPU核心数: {sys_info['cpu_count']}")
        print(f"总内存: {sys_info['memory_total']:.1f} GB")
        print(f"平台: {sys_info['platform']}")
        
        # 异步结果
        async_result = results["async_result"]
        print(f"\n🚀 异步模式结果:")
        print(f"  处理URL数: {async_result['total_urls']}")
        print(f"  成功URL数: {async_result['successful_urls']}")
        print(f"  总耗时: {async_result['total_time']:.2f}秒")
        print(f"  QPS: {async_result['qps']:.2f}")
        print(f"  平均每URL时间: {async_result['avg_time_per_url']:.2f}秒")
        print(f"  内存使用: {async_result['memory_usage']:.2f} MB")
        print(f"  CPU使用率: {async_result['cpu_usage']:.1f}%")
        print(f"  最大并发: {async_result['max_concurrent']}")
        
        # 同步结果
        sync_result = results["sync_result"]
        print(f"\n🔄 同步模式结果:")
        print(f"  处理URL数: {sync_result['total_urls']}")
        print(f"  成功URL数: {sync_result['successful_urls']}")
        print(f"  总耗时: {sync_result['total_time']:.2f}秒")
        print(f"  QPS: {sync_result['qps']:.2f}")
        print(f"  平均每URL时间: {sync_result['avg_time_per_url']:.2f}秒")
        print(f"  内存使用: {sync_result['memory_usage']:.2f} MB")
        print(f"  CPU使用率: {sync_result['cpu_usage']:.1f}%")
        print(f"  最大并发: {sync_result['max_concurrent']}")
        
        # 对比结果
        comparison = results["comparison"]
        print(f"\n📊 性能提升:")
        if "qps_improvement" in comparison:
            print(f"  QPS提升: {comparison['qps_improvement']:.1f}% ({comparison['qps_ratio']:.1f}x)")
        if "time_improvement" in comparison:
            print(f"  处理时间减少: {comparison['time_improvement']:.1f}% ({comparison['time_ratio']:.1f}x)")
        if "memory_improvement" in comparison:
            print(f"  内存使用减少: {comparison['memory_improvement']:.1f}% ({comparison['memory_ratio']:.1f}x)")
        if "success_rate_diff" in comparison:
            print(f"  成功率差异: {comparison['success_rate_diff']:.1f}%")
        
        print("=" * 60)
    
    def save_test_results(self, results: Dict[str, Any], output_file: str = "performance_test_results.json"):
        """保存测试结果到文件"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"测试结果已保存到: {output_file}")
        except Exception as e:
            print(f"保存测试结果失败: {str(e)}")


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='性能对比测试')
    parser.add_argument('--urls', type=int, default=10, help='测试URL数量')
    parser.add_argument('--output', type=str, default='performance_test_results.json', help='输出文件路径')
    parser.add_argument('--no-save', action='store_true', help='不保存测试结果')
    
    args = parser.parse_args()
    
    # 检查API密钥
    if not os.getenv('SILICONFLOW_API_KEY'):
        print("警告: 未设置环境变量 SILICONFLOW_API_KEY")
        print("请设置API密钥: export SILICONFLOW_API_KEY='your_api_key_here'")
        return
    
    # 运行测试
    tester = PerformanceTester()
    results = await tester.run_comparison_test(args.urls)
    
    # 打印结果
    tester.print_test_results(results)
    
    # 保存结果
    if not args.no_save:
        tester.save_test_results(results, args.output)


if __name__ == "__main__":
    asyncio.run(main())