#!/usr/bin/env python3
"""
服务器启动脚本
可以同时启动 OpenAI API 代理服务器和 MCP 服务器，或者单独启动其中一个
"""

import argparse
import asyncio
import subprocess
import sys
import time
from pathlib import Path


def start_openai_proxy(host="127.0.0.1", port=8000, target="https://api.openai.com", log_file="openai_interactions.jsonl"):
    """启动 OpenAI API 代理服务器"""
    cmd = [
        "uv", "run", "openai_proxy.py",
        "--host", host,
        "--port", str(port),
        "--target", target,
        "--log-file", log_file
    ]
    
    print(f"🚀 启动 OpenAI API 代理服务器...")
    print(f"   监听地址: http://{host}:{port}")
    print(f"   目标 API: {target}")
    print(f"   日志文件: {log_file}")
    
    return subprocess.Popen(cmd)


def start_mcp_server():
    """启动 MCP 服务器"""
    cmd = ["uv", "run", "mcp_server.py"]
    
    print(f"🔧 启动 MCP 学习服务器...")
    print(f"   日志文件: mcp_interactions.jsonl")
    
    return subprocess.Popen(cmd)


async def main():
    parser = argparse.ArgumentParser(description='启动 Cline 学习工具服务器')
    parser.add_argument('--mode', choices=['proxy', 'mcp', 'both'], default='both',
                       help='启动模式：proxy(仅API代理), mcp(仅MCP服务器), both(同时启动)')
    
    # OpenAI 代理服务器参数
    parser.add_argument('--proxy-host', default='127.0.0.1', help='API代理监听主机')
    parser.add_argument('--proxy-port', type=int, default=8000, help='API代理监听端口')
    parser.add_argument('--target-api', default='https://api.openai.com', help='目标API URL')
    parser.add_argument('--proxy-log', default='openai_interactions.jsonl', help='API代理日志文件')
    
    args = parser.parse_args()
    
    # 检查 uv 是否可用
    try:
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ 错误：uv 未安装或不可用")
        print("请先安装 uv：")
        print("  curl -LsSf https://astral.sh/uv/install.sh | sh")
        print("  或者使用 brew install uv")
        sys.exit(1)
    
    processes = []
    
    try:
        if args.mode in ['proxy', 'both']:
            proxy_process = start_openai_proxy(
                host=args.proxy_host,
                port=args.proxy_port,
                target=args.target_api,
                log_file=args.proxy_log
            )
            processes.append(('OpenAI API 代理', proxy_process))
            time.sleep(2)  # 等待代理服务器启动
        
        if args.mode in ['mcp', 'both']:
            mcp_process = start_mcp_server()
            processes.append(('MCP 服务器', mcp_process))
            time.sleep(2)  # 等待MCP服务器启动
        
        print("\n" + "="*60)
        print("🎉 服务器启动完成！")
        print("="*60)
        
        if args.mode in ['proxy', 'both']:
            print(f"\n📡 OpenAI API 代理服务器")
            print(f"   地址: http://{args.proxy_host}:{args.proxy_port}")
            print(f"   健康检查: http://{args.proxy_host}:{args.proxy_port}/health")
            print(f"   在 Cline 中配置 API 端点为: http://{args.proxy_host}:{args.proxy_port}")
        
        if args.mode in ['mcp', 'both']:
            print(f"\n🔧 MCP 学习服务器")
            print(f"   在 Cline 中配置 MCP 服务器:")
            print(f"   命令: uv")
            print(f"   参数: [\"run\", \"mcp_server.py\"]")
            print(f"   工作目录: {Path.cwd()}")
            print(f"   或者使用: [\"--directory\", \"{Path.cwd()}\", \"run\", \"mcp_server.py\"]")
        
        print(f"\n📝 日志文件:")
        if args.mode in ['proxy', 'both']:
            print(f"   • {args.proxy_log} - API 交互日志")
        if args.mode in ['mcp', 'both']:
            print(f"   • mcp_interactions.jsonl - MCP 交互日志")
            print(f"   • mcp_server.log - MCP 服务器运行日志")
        
        print(f"\n💡 使用提示:")
        print(f"   • 按 Ctrl+C 停止所有服务器")
        print(f"   • 使用 'tail -f <日志文件>' 查看实时日志")
        print(f"   • 使用 'uv run log_viewer.py' 查看格式化日志")
        print(f"   • 使用 'uv run log_viewer.py --stats' 查看统计信息")
        
        print("\n⏳ 服务器运行中，按 Ctrl+C 停止...")
        
        # 等待所有进程
        while True:
            # 检查是否有进程意外退出
            for name, process in processes:
                if process.poll() is not None:
                    print(f"\n❌ {name} 意外退出，退出码: {process.returncode}")
                    return
            
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n👋 正在停止服务器...")
        
    finally:
        # 清理所有进程
        for name, process in processes:
            if process.poll() is None:
                print(f"  停止 {name}...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"  强制停止 {name}...")
                    process.kill()
        
        print("✅ 所有服务器已停止")


if __name__ == "__main__":
    asyncio.run(main()) 