#!/usr/bin/env python3
"""
XPath提取工具使用示例
"""

from xpath_extractor import XPathExtractor

def main():
    # 示例URL和要提取的元素
    url = "https://www.jiangsu.gov.cn/art/2025/7/16/art_46144_11602534.html"
    target_elements = ["标题", "正文"]
    
    print("🔧 XPath智能提取工具示例")
    print("=" * 50)
    print(f"目标URL: {url}")
    print(f"要提取的元素: {', '.join(target_elements)}")
    print("=" * 50)
    
    # 初始化提取器
    extractor = XPathExtractor()
    
    try:
        # 执行提取
        results = extractor.extract_xpath(url, target_elements)
        
        # 按要求输出格式：URL + 数据名称 + XPath
        print("\n🎯 提取结果（按要求格式）:")
        for element_name, result in results['xpath_results'].items():
            if result['found']:
                print(f"{url} + {element_name} + {result['xpath']}")
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")

if __name__ == "__main__":
    main()