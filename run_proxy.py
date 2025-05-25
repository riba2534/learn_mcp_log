#!/usr/bin/env python
"""
启动 LLM 代理服务
"""
import uvicorn
import sys
import os
import argparse

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.proxy.llm_proxy import app

if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="LLM API 代理服务")
    parser.add_argument(
        "--target-url", 
        default=os.getenv("TARGET_BASE_URL", "https://api.openai.com"),
        help="目标 API 的 base URL (默认: https://api.openai.com)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="代理服务端口 (默认: 8000)"
    )
    args = parser.parse_args()
    
    # 设置环境变量
    os.environ["TARGET_BASE_URL"] = args.target_url
    
    print("🚀 启动 LLM 代理服务...", flush=True)
    print(f"📡 代理地址: http://localhost:{args.port}", flush=True)
    print(f"🎯 目标 API: {args.target_url}", flush=True)
    print("\n💡 使用方法:", flush=True)
    print(f"   在客户端设置 API Base URL 为: http://localhost:{args.port}/v1", flush=True)
    print("   保持 API Key 不变\n", flush=True)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=args.port,
        log_level="info"
    ) 