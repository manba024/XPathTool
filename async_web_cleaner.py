#!/usr/bin/env python3
"""
异步批量网页清洗工具 - 使用异步IO提高效率
"""

import aiohttp
import asyncio
from bs4 import BeautifulSoup
import os
import sys
import time
from urllib.parse import urlparse
import re
import aiofiles
from typing import List, Dict, Tuple


class AsyncBatchWebCleaner:
    def __init__(self, max_concurrent=20, timeout=30):
        """
        初始化异步批量网页清洗器
        
        Args:
            max_concurrent: 最大并发数
            timeout: 请求超时时间
        """
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.processed_count = 0
        self.success_count = 0
        self.error_count = 0
        self.start_time = None
        
    def sanitize_filename(self, url):
        """
        将URL转换为安全的文件名
        
        Args:
            url: 原始URL
            
        Returns:
            str: 安全的文件名
        """
        try:
            parsed = urlparse(url)
            # 移除协议
            filename = parsed.netloc + parsed.path
            
            # 替换特殊字符为下划线
            filename = re.sub(r'[^\w\-_\.]', '_', filename)
            
            # 移除连续的下划线
            filename = re.sub(r'_+', '_', filename)
            
            # 移除开头和结尾的下划线
            filename = filename.strip('_')
            
            # 如果文件名为空，使用时间戳
            if not filename:
                filename = f"page_{int(time.time())}"
            
            # 确保文件名不太长
            if len(filename) > 200:
                filename = filename[:200]
            
            return filename
        except Exception:
            return f"page_{int(time.time())}"
    
    async def fetch_and_clean_webpage(self, session, url):
        """
        异步获取并清洗网页内容
        
        Args:
            session: aiohttp会话
            url: 目标URL
            
        Returns:
            tuple: (success, filename, error_message)
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        }
        
        # 设置Referer
        try:
            parsed = urlparse(url)
            referer = f"{parsed.scheme}://{parsed.hostname}/"
            headers['Referer'] = referer
        except Exception:
            pass
        
        try:
            # 预热域名
            try:
                parsed = urlparse(url)
                if parsed.hostname:
                    warmup_url = f"{parsed.scheme}://{parsed.hostname}"
                    async with session.get(warmup_url, headers=headers, timeout=8) as response:
                        await response.read()
            except Exception:
                pass

            async with session.get(url, headers=headers, timeout=self.timeout) as response:
                response.raise_for_status()
                html_content = await response.text()
                
                # 使用BeautifulSoup清理和格式化HTML
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # 移除script和style标签
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # 移除注释
                for comment in soup.find_all(string=lambda text: isinstance(text, type(soup.comment))):
                    comment.extract()
                
                # 移除不需要的属性
                for tag in soup.find_all(True):
                    # 保留重要属性，移除其他属性
                    important_attrs = ['id', 'class', 'href', 'src', 'alt', 'title', 'name', 'type', 'value']
                    attrs_to_remove = []
                    for attr in tag.attrs:
                        if attr not in important_attrs and not attr.startswith('data-'):
                            attrs_to_remove.append(attr)
                    
                    for attr in attrs_to_remove:
                        del tag.attrs[attr]
                
                # 获取清理后的HTML
                cleaned_html = soup.prettify()
                
                # 生成文件名
                filename = self.sanitize_filename(url) + '.html'
                
                # 异步保存到文件
                async with aiofiles.open(filename, 'w', encoding='utf-8') as f:
                    await f.write(cleaned_html)
                
                return True, filename, None
                
        except Exception as e:
            return False, None, str(e)
    
    async def process_single_url(self, session, url):
        """
        异步处理单个URL
        
        Args:
            session: aiohttp会话
            url: 要处理的URL
            
        Returns:
            dict: 处理结果
        """
        success, filename, error = await self.fetch_and_clean_webpage(session, url)
        
        self.processed_count += 1
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
        
        # 显示进度
        progress = f"[{self.processed_count}/{self.total_count}] "
        elapsed_time = time.time() - self.start_time
        avg_time = elapsed_time / self.processed_count if self.processed_count > 0 else 0
        eta = avg_time * (self.total_count - self.processed_count) if avg_time > 0 else 0
        
        if success:
            print(f"{progress}✓ 成功: {url} -> {filename} (ETA: {eta:.1f}s)")
        else:
            print(f"{progress}✗ 失败: {url} - {error} (ETA: {eta:.1f}s)")
        
        return {
            'url': url,
            'success': success,
            'filename': filename,
            'error': error
        }
    
    def load_urls_from_file(self, file_path):
        """
        从文件加载URL列表
        
        Args:
            file_path: 文件路径
            
        Returns:
            list: URL列表
        """
        urls = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        urls.append(line)
            return urls
        except Exception as e:
            print(f"读取文件失败: {e}")
            return []
    
    async def process_urls(self, urls):
        """
        异步批量处理URL列表
        
        Args:
            urls: URL列表
            
        Returns:
            list: 处理结果列表
        """
        self.total_count = len(urls)
        self.processed_count = 0
        self.success_count = 0
        self.error_count = 0
        self.start_time = time.time()
        
        print(f"开始处理 {self.total_count} 个URL...")
        print(f"并发数: {self.max_concurrent}")
        print(f"超时时间: {self.timeout}秒")
        print("-" * 60)
        
        # 创建信号量控制并发数
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def process_with_semaphore(url):
            async with semaphore:
                return await self.process_single_url(session, url)
        
        # 创建连接池
        connector = aiohttp.TCPConnector(
            limit=self.max_concurrent,
            limit_per_host=5,  # 限制每个主机的并发连接数
            ttl_dns_cache=300,
            use_dns_cache=True
        )
        
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        ) as session:
            # 创建所有任务
            tasks = [process_with_semaphore(url) for url in urls]
            
            # 等待所有任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理异常结果
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append({
                        'url': urls[i],
                        'success': False,
                        'filename': None,
                        'error': str(result)
                    })
                    self.error_count += 1
                else:
                    processed_results.append(result)
        
        total_time = time.time() - self.start_time
        print("-" * 60)
        print(f"处理完成！")
        print(f"总数: {self.total_count}")
        print(f"成功: {self.success_count}")
        print(f"失败: {self.error_count}")
        print(f"总耗时: {total_time:.2f}秒")
        print(f"平均每个URL: {total_time/self.total_count:.2f}秒")
        
        return processed_results
    
    async def save_results_summary(self, results, output_file="cleaning_summary.txt"):
        """
        异步保存处理结果摘要
        
        Args:
            results: 处理结果列表
            output_file: 输出文件名
        """
        async with aiofiles.open(output_file, 'w', encoding='utf-8') as f:
            await f.write("异步批量网页清洗结果摘要\n")
            await f.write("=" * 50 + "\n\n")
            
            await f.write(f"处理时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            await f.write(f"总数: {len(results)}\n")
            await f.write(f"成功: {len([r for r in results if r['success']])}\n")
            await f.write(f"失败: {len([r for r in results if not r['success']])}\n\n")
            
            await f.write("成功列表:\n")
            await f.write("-" * 30 + "\n")
            for result in results:
                if result['success']:
                    await f.write(f"✓ {result['url']} -> {result['filename']}\n")
            
            await f.write("\n失败列表:\n")
            await f.write("-" * 30 + "\n")
            for result in results:
                if not result['success']:
                    await f.write(f"✗ {result['url']} - {result['error']}\n")
        
        print(f"结果摘要已保存到: {output_file}")


async def main():
    """异步主函数"""
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python async_web_cleaner.py <url1> [url2] [url3] ...")
        print("  python async_web_cleaner.py -f <urls_file>")
        print("")
        print("示例:")
        print("  python async_web_cleaner.py https://example.com https://google.com")
        print("  python async_web_cleaner.py -f urls.txt")
        sys.exit(1)
    
    # 初始化异步清洗器
    cleaner = AsyncBatchWebCleaner(max_concurrent=20, timeout=30)
    
    urls = []
    
    if sys.argv[1] == '-f':
        # 从文件读取URL
        if len(sys.argv) < 3:
            print("错误: 请指定URL文件路径")
            sys.exit(1)
        
        file_path = sys.argv[2]
        urls = cleaner.load_urls_from_file(file_path)
        if not urls:
            print("错误: 无法从文件中读取URL")
            sys.exit(1)
    else:
        # 从命令行参数读取URL
        urls = sys.argv[1:]
    
    # 处理URL
    results = await cleaner.process_urls(urls)
    
    # 保存结果摘要
    await cleaner.save_results_summary(results)


if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main())