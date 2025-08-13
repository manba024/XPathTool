#!/usr/bin/env python3
"""
配置文件处理模块
"""

import json
import os
import sys
from typing import Dict, Any, List, Optional
from pathlib import Path


class ConfigManager:
    """配置文件管理器"""
    
    def __init__(self):
        self.config_schema = {
            "required_fields": ["target_elements"],
            "optional_fields": [
                "max_concurrent", "request_timeout", "llm_timeout", 
                "retry_count", "output_file", "urls", "urls_file",
                "exclude_urls_file", "output_format", "api_key", 
                "api_base", "model", "use_async", "max_http_concurrent",
                "max_llm_concurrent", "max_global_concurrent", "batch_size", 
                "connection_pool_size", "max_tokens", "temperature", "batch_rest_time"
            ]
        }
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 验证配置
            self._validate_config(config)
            
            # 处理不同配置格式
            config = self._normalize_config(config, config_path)
            
            return config
            
        except FileNotFoundError:
            raise Exception(f"配置文件未找到: {config_path}")
        except json.JSONDecodeError as e:
            raise Exception(f"配置文件JSON格式错误: {str(e)}")
        except Exception as e:
            raise Exception(f"加载配置文件失败: {str(e)}")
    
    def _validate_config(self, config: Dict[str, Any]):
        """验证配置文件格式"""
        # 检查必需字段
        for field in self.config_schema["required_fields"]:
            if field not in config:
                raise Exception(f"配置文件缺少必需字段: {field}")
        
        # 验证字段类型
        if "target_elements" in config and not isinstance(config["target_elements"], list):
            raise Exception("target_elements 必须是列表")
        
        if "max_concurrent" in config and not isinstance(config["max_concurrent"], int):
            raise Exception("max_concurrent 必须是整数")
        
        if "max_concurrent" in config and config["max_concurrent"] < 1:
            raise Exception("max_concurrent 必须大于0")
        
        if "request_timeout" in config and not isinstance(config["request_timeout"], int):
            raise Exception("request_timeout 必须是整数")
        
        if "retry_count" in config and not isinstance(config["retry_count"], int):
            raise Exception("retry_count 必须是整数")
        
        # 验证异步配置参数
        if "use_async" in config and not isinstance(config["use_async"], bool):
            raise Exception("use_async 必须是布尔值")
        
        if "max_http_concurrent" in config and not isinstance(config["max_http_concurrent"], int):
            raise Exception("max_http_concurrent 必须是整数")
        
        if "max_http_concurrent" in config and config["max_http_concurrent"] < 1:
            raise Exception("max_http_concurrent 必须大于0")
        
        if "max_llm_concurrent" in config and not isinstance(config["max_llm_concurrent"], int):
            raise Exception("max_llm_concurrent 必须是整数")
        
        if "max_llm_concurrent" in config and config["max_llm_concurrent"] < 1:
            raise Exception("max_llm_concurrent 必须大于0")
        
        if "max_global_concurrent" in config and not isinstance(config["max_global_concurrent"], int):
            raise Exception("max_global_concurrent 必须是整数")
        
        if "max_global_concurrent" in config and config["max_global_concurrent"] < 1:
            raise Exception("max_global_concurrent 必须大于0")
        
        if "max_tokens" in config and not isinstance(config["max_tokens"], int):
            raise Exception("max_tokens 必须是整数")
        
        if "max_tokens" in config and config["max_tokens"] < 1:
            raise Exception("max_tokens 必须大于0")
        
        if "temperature" in config and not isinstance(config["temperature"], (int, float)):
            raise Exception("temperature 必须是数字")
        
        if "temperature" in config and (config["temperature"] < 0 or config["temperature"] > 2):
            raise Exception("temperature 必须在0-2之间")
        
        if "batch_rest_time" in config and not isinstance(config["batch_rest_time"], (int, float)):
            raise Exception("batch_rest_time 必须是数字")
        
        if "batch_rest_time" in config and config["batch_rest_time"] < 0:
            raise Exception("batch_rest_time 必须大于等于0")
        
        if "batch_size" in config and not isinstance(config["batch_size"], int):
            raise Exception("batch_size 必须是整数")
        
        if "batch_size" in config and config["batch_size"] < 1:
            raise Exception("batch_size 必须大于0")
    
    def _normalize_config(self, config: Dict[str, Any], config_path: str) -> Dict[str, Any]:
        """标准化配置格式"""
        # 设置默认值
        defaults = {
            "max_concurrent": 5,
            "request_timeout": 30,
            "llm_timeout": 60,
            "retry_count": 3,
            "output_file": "batch_results.csv",
            "model": "Pro/deepseek-ai/DeepSeek-R1",
            "api_base": "https://api.siliconflow.cn/v1",
            "use_async": True,
            "max_http_concurrent": 20,
            "max_llm_concurrent": 5,
            "max_global_concurrent": 50,
            "batch_size": 10,
            "connection_pool_size": 100,
            "max_tokens": 1000,
            "temperature": 0.1,
            "batch_rest_time": 0.1
        }
        
        # 应用默认值
        for key, value in defaults.items():
            if key not in config:
                # 如果有settings对象，优先从settings中获取
                if "settings" in config and key in config["settings"]:
                    config[key] = config["settings"][key]
                else:
                    config[key] = value
        
        # 处理settings对象中的配置
        if "settings" in config:
            settings = config["settings"]
            for key, value in settings.items():
                if key in defaults:
                    config[key] = value
        
        # 处理URL来源
        urls = []
        
        # 从配置文件中获取URL
        if "urls" in config:
            if isinstance(config["urls"], list):
                urls.extend(config["urls"])
            else:
                raise Exception("urls 必须是列表")
        
        # 从外部文件获取URL
        if "urls_file" in config:
            if isinstance(config["urls_file"], str):
                urls.extend(self._load_urls_from_file(config["urls_file"]))
            else:
                raise Exception("urls_file 必须是字符串")
        
        # 去重
        config["urls"] = list(set(urls))
        
        # 处理排除URL
        if "exclude_urls_file" in config:
            exclude_urls = self._load_urls_from_file(config["exclude_urls_file"])
            config["urls"] = [url for url in config["urls"] if url not in exclude_urls]
        
        # 验证URL格式
        config["urls"] = [url for url in config["urls"] if self._validate_url(url)]
        
        # 设置默认输出格式
        if "output_format" not in config:
            config["output_format"] = {
                "include_content_preview": True,
                "max_content_length": 200,
                "include_element_count": True,
                "include_processing_time": True
            }
        
        return config
    
    def _load_urls_from_file(self, file_path: str) -> List[str]:
        """从文件加载URL列表"""
        urls = []
        
        # 处理相对路径
        if not os.path.isabs(file_path):
            # 相对于配置文件所在目录
            config_dir = os.path.dirname(os.path.abspath(file_path))
            file_path = os.path.join(config_dir, file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if self._validate_url(line):
                            urls.append(line)
                        else:
                            print(f"警告: 第{line_num}行跳过无效URL: {line}")
        except FileNotFoundError:
            raise Exception(f"URL文件未找到: {file_path}")
        except Exception as e:
            raise Exception(f"读取URL文件失败: {str(e)}")
        
        return urls
    
    def _validate_url(self, url: str) -> bool:
        """验证URL格式"""
        try:
            from urllib.parse import urlparse
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def create_template_config(self, output_path: str):
        """创建配置文件模板"""
        template = {
            "settings": {
                "max_concurrent": 10,
                "request_timeout": 30,
                "llm_timeout": 60,
                "retry_count": 3,
                "output_file": "async_batch_results.csv",
                "model": "Pro/deepseek-ai/DeepSeek-R1",
                "use_async": True,
                "max_http_concurrent": 20,
                "max_llm_concurrent": 5,
                "max_global_concurrent": 50,
                "batch_size": 10,
                "connection_pool_size": 100,
                "max_tokens": 1000,
                "temperature": 0.1,
                "batch_rest_time": 0.1
            },
            "target_elements": [
                "标题",
                "正文",
                "作者",
                "发布时间"
            ],
            "urls": [
                "https://example.com/article1",
                "https://example.com/article2"
            ],
            "urls_file": "urls.txt",
            "output_format": {
                "include_content_preview": True,
                "max_content_length": 200,
                "include_element_count": True,
                "include_processing_time": True
            }
        }
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=2, ensure_ascii=False)
            print("配置文件模板已创建: {}".format(output_path))
        except Exception as e:
            raise Exception("创建配置文件模板失败: {}".format(str(e)))
    
    def validate_config_file(self, config_path: str) -> bool:
        """验证配置文件"""
        try:
            config = self.load_config(config_path)
            
            # 检查URL列表
            if not config.get("urls"):
                print("警告: 配置文件中没有有效的URL")
                return False
            
            # 检查目标元素
            if not config.get("target_elements"):
                print("警告: 配置文件中没有目标元素")
                return False
            
            # 检查输出目录
            output_file = config.get("output_file", "batch_results.csv")
            output_dir = os.path.dirname(output_file) if os.path.dirname(output_file) else "."
            if not os.path.exists(output_dir):
                print(f"警告: 输出目录不存在: {output_dir}")
            
            print("OK 配置文件验证通过")
            print(f"  - URL数量: {len(config['urls'])}")
            print(f"  - 目标元素: {len(config['target_elements'])}")
            print(f"  - 异步模式: {'启用' if config.get('use_async', True) else '禁用'}")
            print(f"  - 并发数: {config['max_concurrent']}")
            print(f"  - HTTP并发: {config.get('max_http_concurrent', 20)}")
            print(f"  - LLM并发: {config.get('max_llm_concurrent', 5)}")
            print(f"  - 批处理大小: {config.get('batch_size', 10)}")
            print(f"  - 输出文件: {config['output_file']}")
            
            return True
            
        except Exception as e:
            print("ERROR 配置文件验证失败: {}".format(str(e)))
            return False