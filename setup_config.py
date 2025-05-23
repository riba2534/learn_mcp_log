#!/usr/bin/env python3
"""
配置初始化脚本
帮助用户快速设置配置文件
"""

import json
import os
import shutil
from pathlib import Path


def setup_config():
    """设置配置文件"""
    print("🔧 配置初始化向导")
    print("=" * 50)
    
    # 检查是否已存在配置文件
    config_file = Path("config.json")
    if config_file.exists():
        print(f"⚠️  配置文件 {config_file} 已存在")
        overwrite = input("是否要覆盖现有配置？(y/N): ").lower().strip()
        if overwrite != 'y':
            print("❌ 取消配置初始化")
            return
    
    # 从示例文件复制
    example_file = Path("config.example.json")
    if not example_file.exists():
        print(f"❌ 示例配置文件 {example_file} 不存在")
        return
    
    # 读取示例配置
    with open(example_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    print("\n📝 请输入配置信息（直接回车使用默认值）:")
    
    # OpenAI API Key
    api_key = input(f"OpenAI API Key [{config['openai']['api_key']}]: ").strip()
    if api_key:
        config['openai']['api_key'] = api_key
    
    # OpenAI Base URL
    base_url = input(f"OpenAI Base URL [{config['openai']['base_url']}]: ").strip()
    if base_url:
        config['openai']['base_url'] = base_url
    
    # OpenAI Model
    model = input(f"OpenAI Model [{config['openai']['model']}]: ").strip()
    if model:
        config['openai']['model'] = model
    
    # 服务器配置
    host = input(f"服务器主机 [{config['server']['host']}]: ").strip()
    if host:
        config['server']['host'] = host
    
    port = input(f"服务器端口 [{config['server']['port']}]: ").strip()
    if port:
        try:
            config['server']['port'] = int(port)
        except ValueError:
            print("⚠️  端口必须是数字，使用默认值")
    
    # 保存配置
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 配置文件已保存到 {config_file}")
    
    # 检查 API Key 是否为示例值
    if config['openai']['api_key'] == 'your-openai-api-key-here':
        print("\n⚠️  警告: 你还没有设置真实的 OpenAI API Key")
        print("请编辑 config.json 文件或设置环境变量 OPENAI_API_KEY")
    
    print("\n🎉 配置初始化完成！")
    print("\n💡 提示:")
    print("1. 你可以直接编辑 config.json 文件来修改配置")
    print("2. 也可以通过环境变量来覆盖配置（如 OPENAI_API_KEY）")
    print("3. config.json 文件已被 .gitignore 忽略，不会提交到 Git")


def setup_env_file():
    """设置环境变量文件"""
    print("\n🌍 环境变量文件设置")
    print("=" * 30)
    
    env_file = Path(".env")
    example_env = Path("env.example")
    
    if env_file.exists():
        print(f"⚠️  环境变量文件 {env_file} 已存在")
        overwrite = input("是否要覆盖现有文件？(y/N): ").lower().strip()
        if overwrite != 'y':
            print("❌ 跳过环境变量文件设置")
            return
    
    if example_env.exists():
        shutil.copy(example_env, env_file)
        print(f"✅ 已复制 {example_env} 到 {env_file}")
        print("请编辑 .env 文件并填入真实的配置值")
    else:
        print(f"❌ 示例环境变量文件 {example_env} 不存在")


if __name__ == "__main__":
    try:
        setup_config()
        
        # 询问是否也要设置环境变量文件
        setup_env = input("\n是否也要设置环境变量文件？(y/N): ").lower().strip()
        if setup_env == 'y':
            setup_env_file()
        
        print("\n🚀 现在你可以运行项目了！")
        print("   uv run start_servers.py --mode both")
        
    except KeyboardInterrupt:
        print("\n\n👋 配置初始化已取消")
    except Exception as e:
        print(f"\n❌ 配置初始化失败: {e}") 