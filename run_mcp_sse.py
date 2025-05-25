#!/usr/bin/env python3
"""
启动 MCP 天气服务器 - SSE 模式
"""
import argparse
import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from mcp.weather_server_sse import app
import uvicorn

def main():
    parser = argparse.ArgumentParser(description="启动 MCP 天气服务器 - SSE 模式")
    parser.add_argument("--host", default="127.0.0.1", help="绑定的主机地址")
    parser.add_argument("--port", type=int, default=8001, help="绑定的端口")
    parser.add_argument("--log-level", default="info", help="日志级别")
    parser.add_argument("--reload", action="store_true", help="启用自动重载")
    
    args = parser.parse_args()
    
    print(f"启动 Weather MCP Server SSE 在 http://{args.host}:{args.port}", flush=True)
    print(f"API 文档: http://{args.host}:{args.port}/docs", flush=True)
    print(f"SSE 端点: http://{args.host}:{args.port}/sse", flush=True)
    print(f"消息端点: http://{args.host}:{args.port}/message", flush=True)
    
    uvicorn.run(
        "mcp.weather_server_sse:app",
        host=args.host,
        port=args.port,
        log_level=args.log_level,
        reload=args.reload
    )

if __name__ == "__main__":
    main() 