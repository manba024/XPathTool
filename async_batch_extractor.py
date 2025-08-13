#!/usr/bin/env python3
"""
异步批量XPath提取工具 - 支持配置文件和CSV导出
"""

import asyncio
import json
import csv
import time
import sys
import os
import argparse
from urllib.parse import urlparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import aiohttp

# 导入异步XPathExtractor
from async_xpath_extractor import AsyncXPathExtractor


class AsyncBatchXPathExtractor(AsyncXPathExtractor):
    """异步批量XPath提取器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化异步批量提取器
        
        Args:
            config: 配置字典
        """
        # 初始化父类
        super().__init__(
            api_key=config.get('api_key'),
            api_base=config.get('api_base'),
            model=config.get('model', 'Pro/deepseek-ai/DeepSeek-R1'),
            max_http_concurrent=config.get('max_http_concurrent', 20),
            max_llm_concurrent=config.get('max_llm_concurrent', 5),
            max_global_concurrent=config.get('max_global_concurrent', 50),
            request_timeout=config.get('request_timeout', 30),
            max_tokens=config.get('max_tokens', 1000),
            temperature=config.get('temperature', 0.1),
            connection_pool_size=config.get('connection_pool_size', 100)
        )
        
        self.config = config
        
        # 异步配置参数
        self.use_async = config.get('use_async', True)
        self.max_concurrent = config.get('max_concurrent', 10)
        self.max_http_concurrent = config.get('max_http_concurrent', 20)
        self.max_llm_concurrent = config.get('max_llm_concurrent', 5)
        self.batch_size = config.get('batch_size', 10)
        self.request_timeout = config.get('request_timeout', 30)
        self.llm_timeout = config.get('llm_timeout', 60)
        self.retry_count = config.get('retry_count', 3)
        self.output_file = config.get('output_file', 'async_batch_results.csv')
        self.max_tokens = config.get('max_tokens', 1000)
        self.temperature = config.get('temperature', 0.1)
        self.connection_pool_size = config.get('connection_pool_size', 100)
        self.batch_rest_time = config.get('batch_rest_time', 0.1)
        
        # 更新信号量限制
        self.http_semaphore = asyncio.Semaphore(self.max_http_concurrent)
        self.llm_semaphore = asyncio.Semaphore(self.max_llm_concurrent)
        self.global_semaphore = asyncio.Semaphore(self.max_concurrent * 2)  # 全局并发为max_concurrent的2倍
        
        # 进度跟踪
        self.processed_count = 0
        self.total_count = 0
        self.success_count = 0
        self.error_count = 0
        self.start_time = None
        
        # 性能监控
        self.qps_counter = 0
        self.qps_start_time = None
        
    def validate_url(self, url: str) -> bool:
        """验证URL格式"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def load_urls_from_file(self, file_path: str) -> List[str]:
        """从文件加载URL列表"""
        urls = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if self.validate_url(line):
                            urls.append(line)
                        else:
                            print(f"警告: 跳过无效URL: {line}")
            return urls
        except FileNotFoundError:
            raise Exception(f"URL文件未找到: {file_path}")
        except Exception as e:
            raise Exception(f"读取URL文件失败: {str(e)}")
    
    async def process_single_url_async(self, url: str, target_elements: List[str]) -> Dict[str, Any]:
        """异步处理单个URL"""
        start_time = time.time()
        
        try:
            # 调用父类的异步extract_xpath_async方法
            result = await super().extract_xpath_async(url, target_elements)
            
            # 更新QPS计数器
            self.qps_counter += 1
            
            # 更新进度
            if result['status'] == 'success':
                self.success_count += 1
            else:
                self.error_count += 1
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            # 更新进度
            self.error_count += 1
            
            return {
                'url': url,
                'status': 'error',
                'error': str(e),
                'processing_time': round(processing_time, 2),
                'xpath_results': {},
                'summary': {
                    'total_elements': len(target_elements),
                    'successful_extractions': 0,
                    'failed_extractions': len(target_elements)
                }
            }
    
    def update_progress_display(self):
        """更新进度显示"""
        if self.total_count == 0:
            return
            
        progress = (self.processed_count / self.total_count) * 100
        
        # 计算QPS
        qps = 0
        if self.qps_start_time and (time.time() - self.qps_start_time) > 0:
            qps = self.qps_counter / (time.time() - self.qps_start_time)
        
        # 计算ETA
        eta = "未知"
        if self.processed_count > 0 and self.total_count > self.processed_count:
            avg_time_per_url = (time.time() - self.start_time) / self.processed_count
            remaining_urls = self.total_count - self.processed_count
            eta_seconds = avg_time_per_url * remaining_urls
            eta = f"{int(eta_seconds // 60)}分{int(eta_seconds % 60)}秒"
        
        print(f"\r进度: {self.processed_count}/{self.total_count} ({progress:.1f}%) "
              f"成功: {self.success_count} 错误: {self.error_count} "
              f"QPS: {qps:.2f} ETA: {eta}", 
              end='', flush=True)
    
    def chunk_list(self, lst: List[Any], chunk_size: int) -> List[List[Any]]:
        """将列表分块"""
        return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]
    
    async def process_batch_async(self, urls: List[str], target_elements: List[str]) -> List[Dict[str, Any]]:
        """异步批量处理URL"""
        self.total_count = len(urls)
        self.processed_count = 0
        self.success_count = 0
        self.error_count = 0
        self.start_time = time.time()
        self.qps_start_time = time.time()
        self.qps_counter = 0
        
        print(f"开始异步批量处理 {len(urls)} 个URL")
        print(f"目标元素: {', '.join(target_elements)}")
        print(f"并发数: {self.max_concurrent}")
        print(f"HTTP并发: {self.max_http_concurrent}")
        print(f"LLM并发: {self.max_llm_concurrent}")
        print(f"批处理大小: {self.batch_size}")
        print("-" * 50)
        
        results = []
        
        try:
            # 分批处理以避免内存问题
            url_batches = self.chunk_list(urls, self.batch_size)
            
            for batch_idx, batch in enumerate(url_batches, 1):
                print(f"\n处理第 {batch_idx}/{len(url_batches)} 批 (共 {len(batch)} 个URL)")
                
                # 创建任务列表
                tasks = []
                for url in batch:
                    task = asyncio.create_task(
                        self.process_single_url_async(url, target_elements)
                    )
                    tasks.append(task)
                
                # 等待当前批次完成
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 处理结果
                for result in batch_results:
                    if isinstance(result, Exception):
                        # 处理异常
                        error_result = {
                            'url': 'unknown',
                            'status': 'error',
                            'error': f"处理异常: {str(result)}",
                            'processing_time': 0,
                            'xpath_results': {},
                            'summary': {
                                'total_elements': len(target_elements),
                                'successful_extractions': 0,
                                'failed_extractions': len(target_elements)
                            }
                        }
                        results.append(error_result)
                        self.error_count += 1
                    else:
                        results.append(result)
                    
                    self.processed_count += 1
                    self.update_progress_display()
                
                # 批次间短暂休息，避免过载
                if batch_idx < len(url_batches):
                    await asyncio.sleep(self.batch_rest_time)
            
        except Exception as e:
            print(f"\n批量处理过程中发生错误: {str(e)}")
        
        print()  # 换行
        return results
    
    def export_to_csv(self, results: List[Dict[str, Any]], target_elements: List[str]):
        """导出结果到CSV文件"""
        output_format = self.config.get('output_format', {})
        include_content_preview = output_format.get('include_content_preview', True)
        max_content_length = output_format.get('max_content_length', 200)
        include_element_count = output_format.get('include_element_count', True)
        include_processing_time = output_format.get('include_processing_time', True)
        
        try:
            with open(self.output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
                # 构建表头
                headers = ['URL', '元素名称', 'XPath', '状态']
                if include_content_preview:
                    headers.append('内容预览')
                if include_element_count:
                    headers.append('匹配数量')
                if include_processing_time:
                    headers.append('处理时间(秒)')
                headers.append('错误信息')
                
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                
                # 写入数据
                for result in results:
                    url = result['url']
                    processing_time = result.get('processing_time', 0)
                    
                    if result['status'] == 'success':
                        # 为每个元素写入一行
                        for element_name, element_result in result['xpath_results'].items():
                            row = {
                                'URL': url,
                                '元素名称': element_name,
                                'XPath': element_result.get('xpath', ''),
                                '状态': '成功' if element_result.get('found', False) else '失败',
                                '错误信息': ''
                            }
                            
                            if include_content_preview and element_result.get('content'):
                                content = element_result['content']
                                row['内容预览'] = content[:max_content_length] + '...' if len(content) > max_content_length else content
                            else:
                                row['内容预览'] = ''
                            
                            if include_element_count:
                                row['匹配数量'] = element_result.get('element_count', 0)
                            
                            if include_processing_time:
                                row['处理时间(秒)'] = processing_time
                            
                            writer.writerow(row)
                    else:
                        # 写入错误行
                        for element_name in target_elements:
                            row = {
                                'URL': url,
                                '元素名称': element_name,
                                'XPath': '',
                                '状态': '错误',
                                '内容预览': '',
                                '匹配数量': 0,
                                '处理时间(秒)': processing_time,
                                '错误信息': result.get('error', '未知错误')
                            }
                            writer.writerow(row)
            
            print(f"结果已导出到: {self.output_file}")
            
        except Exception as e:
            raise Exception(f"导出CSV失败: {str(e)}")
    
    def print_summary(self, results: List[Dict[str, Any]]):
        """打印处理摘要"""
        total_urls = len(results)
        successful_urls = sum(1 for r in results if r['status'] == 'success')
        error_urls = sum(1 for r in results if r['status'] == 'error')
        
        total_elements = sum(r['summary']['total_elements'] for r in results)
        successful_extractions = sum(r['summary']['successful_extractions'] for r in results)
        failed_extractions = sum(r['summary']['failed_extractions'] for r in results)
        
        avg_processing_time = sum(r.get('processing_time', 0) for r in results) / total_urls if total_urls > 0 else 0
        
        # 计算总体QPS
        total_time = time.time() - self.start_time if self.start_time else 0
        overall_qps = total_urls / total_time if total_time > 0 else 0
        
        print("\n" + "=" * 60)
        print("异步批量处理摘要")
        print("=" * 60)
        print(f"总URL数: {total_urls}")
        print(f"成功处理: {successful_urls} ({successful_urls/total_urls*100:.1f}%)")
        print(f"处理失败: {error_urls} ({error_urls/total_urls*100:.1f}%)")
        print(f"总元素数: {total_elements}")
        print(f"成功提取: {successful_extractions} ({successful_extractions/total_elements*100:.1f}%)")
        print(f"提取失败: {failed_extractions}")
        print(f"平均处理时间: {avg_processing_time:.2f}秒")
        print(f"总体QPS: {overall_qps:.2f}")
        print(f"总处理时间: {total_time:.2f}秒")
        print("=" * 60)
    
    def print_performance_stats(self):
        """打印性能统计"""
        if not self.start_time:
            return
            
        total_time = time.time() - self.start_time
        overall_qps = self.total_count / total_time if total_time > 0 else 0
        
        print("\n" + "=" * 60)
        print("性能统计")
        print("=" * 60)
        print(f"总处理时间: {total_time:.2f}秒")
        print(f"总体QPS: {overall_qps:.2f}")
        print(f"平均每URL处理时间: {total_time/self.total_count:.2f}秒" if self.total_count > 0 else "平均每URL处理时间: N/A")
        print(f"并发效率: {overall_qps/self.max_concurrent:.2%}" if self.max_concurrent > 0 else "并发效率: N/A")
        print("=" * 60)