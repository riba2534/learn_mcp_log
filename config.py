#!/usr/bin/env python3
"""
配置管理模块
用于加载和管理应用程序配置，支持从文件和环境变量读取
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """配置管理类"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config_data = {}
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        config_path = Path(self.config_file)
        
        # 如果配置文件不存在，尝试从示例文件复制
        if not config_path.exists():
            example_path = Path("config.example.json")
            if example_path.exists():
                print(f"⚠️  配置文件 {self.config_file} 不存在")
                print(f"📋 请复制 {example_path} 到 {self.config_file} 并填入真实配置")
                print(f"💡 命令: cp {example_path} {self.config_file}")
                # 加载示例配置作为默认值
                with open(example_path, 'r', encoding='utf-8') as f:
                    self.config_data = json.load(f)
            else:
                raise FileNotFoundError(f"配置文件 {self.config_file} 和示例文件 {example_path} 都不存在")
        else:
            # 加载实际配置文件
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config_data = json.load(f)
        
        # 从环境变量覆盖配置
        self._load_from_env()
    
    def _load_from_env(self):
        """从环境变量加载配置"""
        # OpenAI 配置
        if os.getenv('OPENAI_API_KEY'):
            self.config_data.setdefault('openai', {})['api_key'] = os.getenv('OPENAI_API_KEY')
        
        if os.getenv('OPENAI_BASE_URL'):
            self.config_data.setdefault('openai', {})['base_url'] = os.getenv('OPENAI_BASE_URL')
        
        if os.getenv('OPENAI_MODEL'):
            self.config_data.setdefault('openai', {})['model'] = os.getenv('OPENAI_MODEL')
        
        # 服务器配置
        if os.getenv('SERVER_HOST'):
            self.config_data.setdefault('server', {})['host'] = os.getenv('SERVER_HOST')
        
        if os.getenv('SERVER_PORT'):
            self.config_data.setdefault('server', {})['port'] = int(os.getenv('SERVER_PORT'))
        
        if os.getenv('DEBUG'):
            self.config_data.setdefault('server', {})['debug'] = os.getenv('DEBUG').lower() == 'true'
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔的嵌套键"""
        keys = key.split('.')
        value = self.config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_openai_config(self) -> Dict[str, Any]:
        """获取 OpenAI 配置"""
        return self.config_data.get('openai', {})
    
    def get_server_config(self) -> Dict[str, Any]:
        """获取服务器配置"""
        return self.config_data.get('server', {})
    
    def get_mcp_config(self) -> Dict[str, Any]:
        """获取 MCP 配置"""
        return self.config_data.get('mcp', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return self.config_data.get('logging', {})
    
    def validate_config(self) -> bool:
        """验证配置是否完整"""
        required_keys = [
            'openai.api_key',
            'server.host',
            'server.port'
        ]
        
        missing_keys = []
        for key in required_keys:
            if self.get(key) is None or self.get(key) == "your-openai-api-key-here":
                missing_keys.append(key)
        
        if missing_keys:
            print(f"❌ 配置验证失败，缺少以下配置项: {', '.join(missing_keys)}")
            return False
        
        print("✅ 配置验证通过")
        return True


# 全局配置实例
config = Config()


def get_config() -> Config:
    """获取全局配置实例"""
    return config


if __name__ == "__main__":
    # 测试配置加载
    print("🔧 测试配置加载...")
    
    print(f"OpenAI API Key: {config.get('openai.api_key', 'Not set')}")
    print(f"Server Host: {config.get('server.host', 'Not set')}")
    print(f"Server Port: {config.get('server.port', 'Not set')}")
    
    config.validate_config() 