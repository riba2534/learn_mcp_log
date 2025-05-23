#!/usr/bin/env python3
"""MCP 服务器 - 提供工具和资源"""

import asyncio
import json
import os
from datetime import datetime

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# 加载环境变量
load_dotenv()

# 创建 MCP 服务器
mcp = FastMCP("simple-mcp-server")
LOG_FILE = "mcp_logs.jsonl"


def log_interaction(interaction_type, data):
    """记录 MCP 交互"""
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps({
            'timestamp': datetime.now().isoformat(),
            'type': interaction_type,
            'data': data
        }) + '\n')


@mcp.tool()
def read_file(path: str) -> str:
    """读取文件内容"""
    log_interaction('tool_call', {'tool': 'read_file', 'args': {'path': path}})
    try:
        with open(path, 'r') as f:
            content = f.read()
        log_interaction('tool_result', {'tool': 'read_file', 'success': True})
        return content
    except Exception as e:
        log_interaction('tool_result', {'tool': 'read_file', 'error': str(e)})
        return f"错误: {e}"


@mcp.tool()
def write_file(path: str, content: str) -> str:
    """写入文件"""
    log_interaction('tool_call', {'tool': 'write_file', 'args': {'path': path}})
    try:
        with open(path, 'w') as f:
            f.write(content)
        log_interaction('tool_result', {'tool': 'write_file', 'success': True})
        return f"文件已写入: {path}"
    except Exception as e:
        log_interaction('tool_result', {'tool': 'write_file', 'error': str(e)})
        return f"错误: {e}"


@mcp.tool()
def list_files(directory: str = ".") -> str:
    """列出目录内容"""
    log_interaction('tool_call', {'tool': 'list_files', 'args': {'directory': directory}})
    try:
        files = os.listdir(directory)
        log_interaction('tool_result', {'tool': 'list_files', 'success': True})
        return "\n".join(files)
    except Exception as e:
        log_interaction('tool_result', {'tool': 'list_files', 'error': str(e)})
        return f"错误: {e}"


@mcp.tool()
def get_time() -> str:
    """获取当前时间"""
    log_interaction('tool_call', {'tool': 'get_time', 'args': {}})
    current_time = datetime.now().isoformat()
    log_interaction('tool_result', {'tool': 'get_time', 'result': current_time})
    return current_time


def main():
    print("🔧 MCP 服务器启动")
    print(f"   日志: {LOG_FILE}")
    print("   工具: read_file, write_file, list_files, get_time")
    
    log_interaction('server_startup', {
        'server': 'simple-mcp-server',
        'tools': ['read_file', 'write_file', 'list_files', 'get_time']
    })
    
    # 运行服务器
    mcp.run()


if __name__ == "__main__":
    main() 