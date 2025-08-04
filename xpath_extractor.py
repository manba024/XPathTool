#!/usr/bin/env python3
"""
XPath提取工具 - 使用LLM智能提取网页元素的XPath
"""

import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import json
import sys
import os
from urllib.parse import urljoin, urlparse
import re


class XPathExtractor:
    def __init__(self, api_key=None, api_base=None, model="Pro/deepseek-ai/DeepSeek-R1"):
        """
        初始化XPath提取器
        
        Args:
            api_key: API密钥（默认从环境变量SILICONFLOW_API_KEY获取）
            api_base: API基础URL（默认使用硅基流动）
            model: 使用的模型名称
        """
        self.api_key = api_key or os.getenv('SILICONFLOW_API_KEY')
        self.api_base = api_base or "https://api.siliconflow.cn/v1"
        self.model = model
        
        if not self.api_key:
            print("警告：未设置API密钥。请设置环境变量 SILICONFLOW_API_KEY 或在初始化时传入api_key参数")
            return
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_base
        )
    
    def fetch_webpage(self, url):
        """
        获取网页内容
        
        Args:
            url: 目标URL
            
        Returns:
            tuple: (html_content, cleaned_html)
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            response.encoding = response.apparent_encoding or 'utf-8'
            
            # 使用BeautifulSoup清理和格式化HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 移除script和style标签
            for script in soup(["script", "style"]):
                script.decompose()
            
            # 获取清理后的HTML
            cleaned_html = str(soup)
            print(cleaned_html)
            
            return response.text, cleaned_html
            
        except Exception as e:
            raise Exception(f"获取网页失败: {str(e)}")
    
    def create_dom_summary(self, html_content):
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
    
    def extract_xpath_with_llm(self, html_content, target_elements):
        """
        使用LLM提取XPath
        
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

        try:
            if not hasattr(self, 'client'):
                raise Exception("API客户端未初始化，请检查API密钥配置")
                
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的网页分析专家，擅长提取DOM元素的XPath选择器。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
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
    
    def validate_xpath(self, html_content, xpath_dict):
        """
        验证XPath的有效性
        
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
    
    def extract_xpath(self, url, target_elements):
        """
        主要提取方法
        
        Args:
            url: 目标URL
            target_elements: 要提取的元素列表
            
        Returns:
            dict: 完整的提取结果
        """
        print(f"正在分析URL: {url}")
        print(f"目标元素: {', '.join(target_elements)}")
        print("-" * 50)
        
        # 1. 获取网页内容
        raw_html, cleaned_html = self.fetch_webpage(url)
        print("✓ 网页内容获取成功")
        
        # 2. 使用LLM提取XPath
        xpath_dict = self.extract_xpath_with_llm(cleaned_html, target_elements)
        print("✓ XPath提取完成")
        
        # 3. 验证XPath
        validation_results = self.validate_xpath(cleaned_html, xpath_dict)
        print("✓ XPath验证完成")
        
        return {
            "url": url,
            "target_elements": target_elements,
            "xpath_results": validation_results,
            "summary": {
                "total_elements": len(target_elements),
                "successful_extractions": sum(1 for r in validation_results.values() if r.get("found", False)),
                "failed_extractions": sum(1 for r in validation_results.values() if not r.get("found", False))
            }
        }


def main():
    """主函数"""
    if len(sys.argv) < 3:
        print("使用方法: python xpath_extractor.py <URL> <元素1> [元素2] [元素3] ...")
        print("示例: python xpath_extractor.py https://example.com 标题 正文")
        sys.exit(1)
    
    url = sys.argv[1]
    target_elements = sys.argv[2:]
    
    # 初始化提取器（需要配置API密钥）
    extractor = XPathExtractor()
    
    try:
        # 执行提取
        results = extractor.extract_xpath(url, target_elements)
        
        # 输出结果
        print("\n" + "=" * 60)
        print("XPath 提取结果")
        print("=" * 60)
        print(f"URL: {results['url']}")
        print(f"提取成功: {results['summary']['successful_extractions']}/{results['summary']['total_elements']}")
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
    main()