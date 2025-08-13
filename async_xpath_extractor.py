#!/usr/bin/env python3
"""
异步XPath提取工具 - 使用LLM智能提取网页元素的XPath
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from openai import AsyncOpenAI
import json
import sys
import os
from urllib.parse import urljoin, urlparse
import re
import time
from typing import Dict, List, Any, Optional, Tuple


class AsyncXPathExtractor:
    def __init__(self, api_key=None, api_base=None, model="Pro/deepseek-ai/DeepSeek-R1", 
                 max_http_concurrent=20, max_llm_concurrent=5, max_global_concurrent=50,
                 request_timeout=30, max_tokens=1000, temperature=0.1, connection_pool_size=100):
        """
        初始化异步XPath提取器
        
        Args:
            api_key: API密钥（默认从环境变量SILICONFLOW_API_KEY获取）
            api_base: API基础URL（默认使用硅基流动）
            model: 使用的模型名称
            max_http_concurrent: HTTP请求最大并发数
            max_llm_concurrent: LLM API调用最大并发数
            max_global_concurrent: 全局最大并发数
            request_timeout: HTTP请求超时时间（秒）
            max_tokens: LLM输出最大token数
            temperature: LLM温度参数
            connection_pool_size: HTTP连接池大小
        """
        self.api_key = api_key or os.getenv('SILICONFLOW_API_KEY')
        self.api_base = api_base or "https://api.siliconflow.cn/v1"
        self.model = model
        
        # 配置参数
        self.max_http_concurrent = max_http_concurrent
        self.max_llm_concurrent = max_llm_concurrent
        self.max_global_concurrent = max_global_concurrent
        self.request_timeout = request_timeout
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.connection_pool_size = connection_pool_size
        
        if not self.api_key:
            print("警告：未设置API密钥。请设置环境变量 SILICONFLOW_API_KEY 或在初始化时传入api_key参数")
            return
        
        self.async_client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.api_base
        )
        
        # 并发控制信号量
        self.http_semaphore = asyncio.Semaphore(max_http_concurrent)  # HTTP请求并发
        self.llm_semaphore = asyncio.Semaphore(max_llm_concurrent)    # LLM API并发
        self.global_semaphore = asyncio.Semaphore(max_global_concurrent) # 全局并发控制
    
    async def fetch_webpage_async(self, session: aiohttp.ClientSession, url: str) -> Tuple[str, str]:
        """
        异步获取网页内容
        
        Args:
            session: aiohttp会话
            url: 目标URL
            
        Returns:
            tuple: (html_content, cleaned_html)
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        async with self.http_semaphore:
            try:
                async with session.get(url, headers=headers, timeout=self.request_timeout) as response:
                    response.raise_for_status()
                    html_content = await response.text()
                    
                    # 使用BeautifulSoup清理和格式化HTML
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # 移除script和style标签
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    # 获取清理后的HTML
                    cleaned_html = str(soup)
                    
                    return html_content, cleaned_html
                    
            except Exception as e:
                raise Exception(f"获取网页失败: {str(e)}")
    
    def create_dom_summary(self, html_content: str) -> str:
        """
        创建DOM结构摘要，减少LLM输入长度
        
        Args:
            html_content: HTML内容
            
        Returns:
            str: DOM结构摘要
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 提取关键结构信息
        structure_info = []
        
        # 提取title
        title = soup.find('title')
        if title:
            structure_info.append(f"<title>{title.get_text().strip()}</title>")
        
        # 提取主要内容区域
        for tag in soup.find_all(['h1', 'h2', 'h3', 'article', 'main', 'div'], limit=50):
            tag_info = f"<{tag.name}"
            
            # 添加重要属性
            important_attrs = ['id', 'class', 'data-*']
            for attr in tag.attrs:
                if attr in ['id', 'class'] or attr.startswith('data-'):
                    tag_info += f' {attr}="{" ".join(tag.attrs[attr]) if isinstance(tag.attrs[attr], list) else tag.attrs[attr]}"'
            
            tag_info += ">"
            
            # 添加文本内容（截断）
            text = tag.get_text().strip()
            if text:
                text = re.sub(r'\s+', ' ', text)[:100]
                tag_info += text
                if len(tag.get_text().strip()) > 100:
                    tag_info += "..."
            
            tag_info += f"</{tag.name}>"
            structure_info.append(tag_info)
        
        return "\n".join(structure_info)
    
    async def extract_xpath_with_llm_async(self, html_content: str, target_elements: List[str]) -> Dict[str, str]:
        """
        异步使用LLM提取XPath
        
        Args:
            html_content: HTML内容
            target_elements: 要提取的元素列表 (如: ["标题", "正文"])
            
        Returns:
            dict: 元素名称到XPath的映射
        """
        dom_summary = self.create_dom_summary(html_content)
        
        prompt = f"""
请分析以下HTML结构，为指定的元素提取准确的XPath选择器。

HTML结构摘要：
{dom_summary}

需要提取的元素：{', '.join(target_elements)}

请返回JSON格式的结果，包含每个元素的XPath：
{{
    "元素名": "xpath表达式",
    ...
}}

要求：
1. XPath应该尽可能精确和稳定
2. 优先使用id、class等稳定属性
3. 避免使用绝对位置路径
4. 考虑元素的语义和上下文

请只返回JSON，不要添加其他说明。
"""

        async with self.llm_semaphore:
            try:
                if not hasattr(self, 'async_client'):
                    raise Exception("API客户端未初始化，请检查API密钥配置")
                    
                response = await self.async_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "你是一个专业的网页分析专家，擅长提取DOM元素的XPath选择器。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                
                result_text = response.choices[0].message.content.strip()
                
                # 尝试解析JSON
                try:
                    return json.loads(result_text)
                except json.JSONDecodeError:
                    # 如果不是标准JSON，尝试提取JSON部分
                    json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group())
                    else:
                        raise Exception("LLM返回的不是有效的JSON格式")
                        
            except Exception as e:
                raise Exception(f"LLM分析失败: {str(e)}")
    
    def validate_xpath(self, html_content: str, xpath_dict: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """
        验证XPath的有效性（同步方法，因为lxml是同步的）
        
        Args:
            html_content: HTML内容
            xpath_dict: XPath字典
            
        Returns:
            dict: 验证结果
        """
        from lxml import html, etree
        
        try:
            tree = html.fromstring(html_content)
            results = {}
            
            for element_name, xpath in xpath_dict.items():
                try:
                    elements = tree.xpath(xpath)
                    if elements:
                        # 获取元素文本内容
                        if hasattr(elements[0], 'text_content'):
                            content = elements[0].text_content().strip()
                        else:
                            content = str(elements[0]).strip()
                        
                        results[element_name] = {
                            "xpath": xpath,
                            "found": True,
                            "content": content[:200] + "..." if len(content) > 200 else content,
                            "element_count": len(elements)
                        }
                    else:
                        results[element_name] = {
                            "xpath": xpath,
                            "found": False,
                            "content": None,
                            "element_count": 0
                        }
                except Exception as e:
                    results[element_name] = {
                        "xpath": xpath,
                        "found": False,
                        "content": None,
                        "error": str(e)
                    }
            
            return results
            
        except Exception as e:
            raise Exception(f"XPath验证失败: {str(e)}")
    
    async def extract_xpath_async(self, url: str, target_elements: List[str]) -> Dict[str, Any]:
        """
        异步主要提取方法
        
        Args:
            url: 目标URL
            target_elements: 要提取的元素列表
            
        Returns:
            dict: 完整的提取结果
        """
        async with self.global_semaphore:
            start_time = time.time()
            
            print(f"正在分析URL: {url}")
            print(f"目标元素: {', '.join(target_elements)}")
            print("-" * 50)
            
            # 创建aiohttp会话，配置连接池
            connector = aiohttp.TCPConnector(limit=self.connection_pool_size)
            async with aiohttp.ClientSession(connector=connector) as session:
                try:
                    # 1. 获取网页内容
                    raw_html, cleaned_html = await self.fetch_webpage_async(session, url)
                    print("✓ 网页内容获取成功")
                    
                    # 2. 使用LLM提取XPath
                    xpath_dict = await self.extract_xpath_with_llm_async(cleaned_html, target_elements)
                    print("✓ XPath提取完成")
                    
                    # 3. 验证XPath（同步操作，但很快）
                    validation_results = self.validate_xpath(cleaned_html, xpath_dict)
                    print("✓ XPath验证完成")
                    
                    processing_time = time.time() - start_time
                    
                    return {
                        "url": url,
                        "target_elements": target_elements,
                        "xpath_results": validation_results,
                        "processing_time": round(processing_time, 2),
                        "status": "success",
                        "summary": {
                            "total_elements": len(target_elements),
                            "successful_extractions": sum(1 for r in validation_results.values() if r.get("found", False)),
                            "failed_extractions": sum(1 for r in validation_results.values() if not r.get("found", False))
                        }
                    }
                    
                except Exception as e:
                    processing_time = time.time() - start_time
                    return {
                        "url": url,
                        "target_elements": target_elements,
                        "status": "error",
                        "error": str(e),
                        "processing_time": round(processing_time, 2),
                        "xpath_results": {},
                        "summary": {
                            "total_elements": len(target_elements),
                            "successful_extractions": 0,
                            "failed_extractions": len(target_elements)
                        }
                    }


async def main_async():
    """异步主函数"""
    if len(sys.argv) < 3:
        print("使用方法: python async_xpath_extractor.py <URL> <元素1> [元素2] [元素3] ...")
        print("示例: python async_xpath_extractor.py https://example.com 标题 正文")
        sys.exit(1)
    
    url = sys.argv[1]
    target_elements = sys.argv[2:]
    
    # 初始化提取器（需要配置API密钥）
    extractor = AsyncXPathExtractor()
    
    try:
        # 执行提取
        results = await extractor.extract_xpath_async(url, target_elements)
        
        # 输出结果
        print("\n" + "=" * 60)
        print("异步XPath 提取结果")
        print("=" * 60)
        print(f"URL: {results['url']}")
        print(f"提取成功: {results['summary']['successful_extractions']}/{results['summary']['total_elements']}")
        print(f"处理时间: {results.get('processing_time', 0):.2f}秒")
        print("-" * 60)
        
        # 按用户要求的格式输出：URL + 数据名称 + XPath
        print("\n📋 提取结果摘要:")
        for element_name, result in results['xpath_results'].items():
            if result['found']:
                print(f"{results['url']} + {element_name} + {result['xpath']}")
        
        print("\n📝 详细信息:")
        for element_name, result in results['xpath_results'].items():
            print(f"\n【{element_name}】")
            print(f"XPath: {result['xpath']}")
            print(f"状态: {'✓ 成功' if result['found'] else '✗ 失败'}")
            
            if result['found']:
                print(f"内容预览: {result['content']}")
                print(f"匹配元素数: {result['element_count']}")
            elif 'error' in result:
                print(f"错误: {result['error']}")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main_async())