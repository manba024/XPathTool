#!/usr/bin/env python3
"""
批量XPath提取工具 - 支持配置文件和CSV导出
"""

import json
import csv
import time
import sys
import os
import argparse
from urllib.parse import urlparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from datetime import datetime

# 导入原有的XPathExtractor
from xpath_extractor import XPathExtractor


class BatchXPathExtractor(XPathExtractor):
    """批量XPath提取器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化批量提取器
        
        Args:
            config: 配置字典
        """
        # 初始化父类
        super().__init__(
            api_key=config.get('api_key'),
            api_base=config.get('api_base'),
            model=config.get('model', 'Pro/deepseek-ai/DeepSeek-R1')
        )
        
        self.config = config
        self.max_concurrent = config.get('max_concurrent', 5)
        self.request_timeout = config.get('request_timeout', 30)
        self.llm_timeout = config.get('llm_timeout', 60)
        self.retry_count = config.get('retry_count', 3)
        self.output_file = config.get('output_file', 'batch_results.csv')
        
        # 进度跟踪
        self.progress_lock = threading.Lock()
        self.processed_count = 0
        self.total_count = 0
        self.success_count = 0
        self.error_count = 0
        
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
    
    def process_single_url(self, url: str, target_elements: List[str]) -> Dict[str, Any]:
        """处理单个URL"""
        start_time = time.time()
        
        try:
            # 调用父类的extract_xpath方法
            result = super().extract_xpath(url, target_elements)
            
            # 添加处理时间
            result['processing_time'] = round(time.time() - start_time, 2)
            result['status'] = 'success'
            
            # 更新进度
            with self.progress_lock:
                self.success_count += 1
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            # 更新进度
            with self.progress_lock:
                self.error_count += 1
            
            return {
                'url': url,
                'status': 'error',
                'error': str(e),
                'processing_time': round(processing_time, 2),
                'results': {},
                'summary': {
                    'total_elements': len(target_elements),
                    'successful_extractions': 0,
                    'failed_extractions': len(target_elements)
                }
            }
    
    def update_progress(self):
        """更新进度显示"""
        with self.progress_lock:
            self.processed_count += 1
            progress = (self.processed_count / self.total_count) * 100
            
            print(f"\r进度: {self.processed_count}/{self.total_count} ({progress:.1f}%) "
                  f"成功: {self.success_count} 错误: {self.error_count}", 
                  end='', flush=True)
    
    def process_batch(self, urls: List[str], target_elements: List[str]) -> List[Dict[str, Any]]:
        """批量处理URL"""
        self.total_count = len(urls)
        self.processed_count = 0
        self.success_count = 0
        self.error_count = 0
        
        print(f"开始批量处理 {len(urls)} 个URL")
        print(f"目标元素: {', '.join(target_elements)}")
        print(f"并发数: {self.max_concurrent}")
        print("-" * 50)
        
        results = []
        
        # 使用线程池处理
        with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            # 提交所有任务
            future_to_url = {
                executor.submit(self.process_single_url, url, target_elements): url 
                for url in urls
            }
            
            # 收集结果
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    results.append(result)
                    self.update_progress()
                except Exception as e:
                    error_result = {
                        'url': url,
                        'status': 'error',
                        'error': f"处理异常: {str(e)}",
                        'processing_time': 0,
                        'results': {},
                        'summary': {
                            'total_elements': len(target_elements),
                            'successful_extractions': 0,
                            'failed_extractions': len(target_elements)
                        }
                    }
                    results.append(error_result)
                    with self.progress_lock:
                        self.error_count += 1
                        self.processed_count += 1
                    self.update_progress()
        
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
            with open(self.output_file, 'w', newline='', encoding='utf-8') as csvfile:
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
        
        print("\n" + "=" * 60)
        print("批量处理摘要")
        print("=" * 60)
        print(f"总URL数: {total_urls}")
        print(f"成功处理: {successful_urls} ({successful_urls/total_urls*100:.1f}%)")
        print(f"处理失败: {error_urls} ({error_urls/total_urls*100:.1f}%)")
        print(f"总元素数: {total_elements}")
        print(f"成功提取: {successful_extractions} ({successful_extractions/total_elements*100:.1f}%)")
        print(f"提取失败: {failed_extractions}")
        print(f"平均处理时间: {avg_processing_time:.2f}秒")
        print("=" * 60)