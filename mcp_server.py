#!/usr/bin/env python3
"""
MCP 服务器 - 学习版本
接受 Cline 作为 MCP 客户端的请求，记录交互过程，并提供一些示例工具
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from config import get_config


class MCPLogger:
    """MCP 交互日志记录器"""

    def __init__(self, log_file: Optional[str] = None):
        # 获取配置
        config = get_config()
        logging_config = config.get_logging_config()
        
        self.log_file = log_file or logging_config.get('interactions_file', 'mcp_interactions.jsonl')
        self.setup_logging()

    def setup_logging(self):
        """设置日志记录"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stderr),  # 输出到标准错误流，避免与 MCP 通信冲突
                logging.FileHandler('mcp_server.log')
            ]
        )
        self.logger = logging.getLogger(__name__)

    def log_interaction(self, interaction_type: str, data: Dict[str, Any]):
        """记录交互数据"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": interaction_type,
            "data": data
        }

        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

        self.logger.info(
            f"MCP {interaction_type}: {json.dumps(data, ensure_ascii=False)}")


# 创建 FastMCP 服务器和日志记录器
mcp = FastMCP("learning-mcp-server")
mcp_logger = MCPLogger()


@mcp.resource("file://README.md")
def get_readme() -> str:
    """获取项目说明文档"""
    mcp_logger.log_interaction("read_resource", {"uri": "file://README.md"})

    return """# MCP 学习服务器

这是一个用于学习 Model Context Protocol (MCP) 的示例服务器。

## 功能特性

- 📝 记录所有 MCP 交互过程
- 🛠️ 提供示例工具（文件操作、系统信息等）
- 📊 展示资源管理功能
- 💬 支持自定义提示模板

## 使用方法

1. 启动服务器：`python mcp_server.py`
2. 配置 Cline 连接到此服务器
3. 查看 `mcp_interactions.jsonl` 了解交互过程

## 学习资源

通过查看日志文件，你可以学习：
- MCP 协议的消息格式
- 客户端和服务器之间的通信流程
- 工具调用的参数传递方式
- 资源访问的实现机制
"""


@mcp.resource("config://server-info")
def get_server_info() -> str:
    """获取服务器配置信息"""
    mcp_logger.log_interaction(
        "read_resource", {"uri": "config://server-info"})

    server_info = {
        "name": "learning-mcp-server",
        "version": "1.0.0",
        "capabilities": [
            "resources",
            "tools",
            "prompts"
        ],
        "supported_features": {
            "file_operations": True,
            "system_info": True,
            "logging": True,
            "custom_prompts": True
        },
        "status": "运行中",
        "start_time": datetime.now().isoformat()
    }
    return json.dumps(server_info, indent=2, ensure_ascii=False)


@mcp.tool()
def read_file(file_path: str) -> str:
    """读取本地文件内容

    Args:
        file_path: 要读取的文件路径
    """
    mcp_logger.log_interaction("call_tool", {
        "tool_name": "read_file",
        "arguments": {"file_path": file_path}
    })

    try:
        path = Path(file_path)
        if not path.exists():
            return f"错误：文件 '{file_path}' 不存在"

        if not path.is_file():
            return f"错误：'{file_path}' 不是一个文件"

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        return f"文件内容 ({file_path}):\n\n{content}"

    except Exception as e:
        return f"读取文件时出错: {str(e)}"


@mcp.tool()
def write_file(file_path: str, content: str) -> str:
    """将内容写入本地文件

    Args:
        file_path: 要写入的文件路径
        content: 要写入的内容
    """
    mcp_logger.log_interaction("call_tool", {
        "tool_name": "write_file",
        "arguments": {"file_path": file_path, "content": content}
    })

    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

        return f"成功写入文件: {file_path}"

    except Exception as e:
        return f"写入文件时出错: {str(e)}"


@mcp.tool()
def list_directory(directory_path: str) -> str:
    """列出目录中的文件和子目录

    Args:
        directory_path: 要列出的目录路径
    """
    mcp_logger.log_interaction("call_tool", {
        "tool_name": "list_directory",
        "arguments": {"directory_path": directory_path}
    })

    try:
        path = Path(directory_path)
        if not path.exists():
            return f"错误：目录 '{directory_path}' 不存在"

        if not path.is_dir():
            return f"错误：'{directory_path}' 不是一个目录"

        items = []
        for item in sorted(path.iterdir()):
            item_type = "目录" if item.is_dir() else "文件"
            size = item.stat().st_size if item.is_file() else "-"
            items.append(f"{item_type}: {item.name} ({size} bytes)" if size !=
                         "-" else f"{item_type}: {item.name}")

        if not items:
            return f"目录 '{directory_path}' 为空"

        return f"目录内容 ({directory_path}):\n\n" + "\n".join(items)

    except Exception as e:
        return f"列出目录时出错: {str(e)}"


@mcp.tool()
def get_system_info() -> str:
    """获取系统信息"""
    mcp_logger.log_interaction("call_tool", {
        "tool_name": "get_system_info",
        "arguments": {}
    })

    import platform
    import psutil

    try:
        info = {
            "操作系统": platform.system(),
            "系统版本": platform.release(),
            "处理器": platform.processor(),
            "Python版本": platform.python_version(),
            "当前工作目录": str(Path.cwd()),
            "CPU核心数": psutil.cpu_count(),
            "内存使用": f"{psutil.virtual_memory().percent}%",
            "磁盘使用": f"{psutil.disk_usage('/').percent}%"
        }

        result = "系统信息:\n\n"
        for key, value in info.items():
            result += f"{key}: {value}\n"

        return result

    except Exception as e:
        return f"获取系统信息时出错: {str(e)}"


@mcp.tool()
def calculate(expression: str) -> str:
    """执行简单的数学计算

    Args:
        expression: 数学表达式（如 "2 + 3 * 4"）
    """
    mcp_logger.log_interaction("call_tool", {
        "tool_name": "calculate",
        "arguments": {"expression": expression}
    })

    try:
        # 安全的数学计算，只允许基本运算符
        allowed_chars = set('0123456789+-*/()., ')
        if not all(c in allowed_chars for c in expression):
            return "错误：表达式包含不允许的字符"

        result = eval(expression)
        return f"{expression} = {result}"

    except Exception as e:
        return f"计算错误: {str(e)}"


if __name__ == "__main__":
    print("""
🔧 MCP 学习服务器
====================

这是一个用于学习 Model Context Protocol (MCP) 的示例服务器。

📋 功能特性：
  • 完整的交互日志记录
  • 文件操作工具
  • 系统信息查询
  • 自定义提示模板
  • 资源管理功能

📝 日志文件：
  • mcp_interactions.jsonl - MCP 协议交互记录
  • mcp_server.log - 服务器运行日志

🔗 连接方法：
  在 Cline 中配置此服务器的启动命令：
  python mcp_server.py

📚 学习建议：
  1. 查看日志文件了解 MCP 协议格式
  2. 尝试不同的工具调用
  3. 观察客户端和服务器的交互流程
""", file=sys.stderr)

    mcp_logger.logger.info("🚀 MCP 学习服务器启动中...")

    try:
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        print("\n👋 MCP 服务器已关闭", file=sys.stderr)
    except Exception as e:
        print(f"\n❌ 服务器错误: {e}", file=sys.stderr)
        sys.exit(1)
