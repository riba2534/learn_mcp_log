#!/usr/bin/env python
"""
启动 Web 界面服务
"""
import uvicorn
import sys
import os
import argparse

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.web.app import app

if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="Web 界面服务")
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("WEB_PORT", 8080)),
        help="Web 服务端口 (默认: 8080)"
    )
    args = parser.parse_args()
    
    print("🌐 启动 Web 界面服务...", flush=True)
    print(f"🔗 访问地址: http://localhost:{args.port}", flush=True)
    print("\n📊 功能说明:", flush=True)
    print("   - 查看 LLM API 交互记录", flush=True)
    print("   - 查看 MCP 服务交互记录", flush=True)
    print("   - 实时更新，自动刷新\n", flush=True)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=args.port,
        log_level="info"
    ) 