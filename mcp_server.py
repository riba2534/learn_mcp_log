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
from typing import Any, Dict, List, Optional, Sequence

from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.models import InitializationOptions


class MCPLogger:
    """MCP 交互日志记录器"""
    
    def __init__(self, log_file: str = "mcp_interactions.jsonl"):
        self.log_file = log_file
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
            
        self.logger.info(f"MCP {interaction_type}: {json.dumps(data, ensure_ascii=False)}")


# 创建 MCP 服务器和日志记录器
server = Server("learning-mcp-server")
mcp_logger = MCPLogger()


@server.list_resources()
async def handle_list_resources() -> List[types.Resource]:
    """列出可用资源"""
    mcp_logger.log_interaction("list_resources", {"action": "获取资源列表"})
    
    resources = [
        types.Resource(
            uri="file://README.md",
            name="项目说明文档",
            description="关于这个 MCP 学习服务器的说明文档",
            mimeType="text/markdown"
        ),
        types.Resource(
            uri="config://server-info", 
            name="服务器信息",
            description="MCP 服务器的配置和状态信息",
            mimeType="application/json"
        ),
        types.Resource(
            uri="log://interactions",
            name="交互日志",
            description="MCP 客户端与服务器的交互历史记录",
            mimeType="application/json"
        )
    ]
    
    return resources


@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """读取资源内容"""
    mcp_logger.log_interaction("read_resource", {"uri": uri})
    
    if uri == "file://README.md":
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
    
    elif uri == "config://server-info":
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
    
    elif uri == "log://interactions":
        # 读取最近的交互日志
        try:
            with open(mcp_logger.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                recent_logs = lines[-10:]  # 获取最近 10 条记录
                return ''.join(recent_logs)
        except FileNotFoundError:
            return "暂无交互日志"
    
    else:
        raise ValueError(f"未知的资源 URI: {uri}")


@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """列出可用工具"""
    mcp_logger.log_interaction("list_tools", {"action": "获取工具列表"})
    
    tools = [
        types.Tool(
            name="read_file",
            description="读取本地文件内容",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "要读取的文件路径"
                    }
                },
                "required": ["file_path"]
            }
        ),
        types.Tool(
            name="write_file",
            description="将内容写入本地文件",
            inputSchema={
                "type": "object", 
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "要写入的文件路径"
                    },
                    "content": {
                        "type": "string",
                        "description": "要写入的内容"
                    }
                },
                "required": ["file_path", "content"]
            }
        ),
        types.Tool(
            name="list_directory",
            description="列出目录中的文件和子目录",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory_path": {
                        "type": "string", 
                        "description": "要列出的目录路径，默认为当前目录",
                        "default": "."
                    }
                }
            }
        ),
        types.Tool(
            name="get_system_info",
            description="获取系统信息（操作系统、Python版本等）",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="calculate",
            description="执行简单的数学计算",
            inputSchema={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "要计算的数学表达式，例如：2+3*4"
                    }
                },
                "required": ["expression"]
            }
        )
    ]
    
    return tools


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """处理工具调用"""
    mcp_logger.log_interaction("call_tool", {
        "tool_name": name,
        "arguments": arguments
    })
    
    try:
        if name == "read_file":
            file_path = arguments["file_path"]
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return [types.TextContent(
                    type="text",
                    text=f"文件 '{file_path}' 的内容:\n\n{content}"
                )]
            except FileNotFoundError:
                return [types.TextContent(
                    type="text", 
                    text=f"错误：文件 '{file_path}' 不存在"
                )]
            except Exception as e:
                return [types.TextContent(
                    type="text",
                    text=f"读取文件时发生错误：{str(e)}"
                )]
        
        elif name == "write_file":
            file_path = arguments["file_path"]
            content = arguments["content"]
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return [types.TextContent(
                    type="text",
                    text=f"成功将内容写入文件 '{file_path}'"
                )]
            except Exception as e:
                return [types.TextContent(
                    type="text",
                    text=f"写入文件时发生错误：{str(e)}"
                )]
        
        elif name == "list_directory":
            directory_path = arguments.get("directory_path", ".")
            try:
                path = Path(directory_path)
                if not path.exists():
                    return [types.TextContent(
                        type="text",
                        text=f"错误：目录 '{directory_path}' 不存在"
                    )]
                
                items = []
                for item in path.iterdir():
                    if item.is_dir():
                        items.append(f"📁 {item.name}/")
                    else:
                        size = item.stat().st_size
                        items.append(f"📄 {item.name} ({size} bytes)")
                
                return [types.TextContent(
                    type="text",
                    text=f"目录 '{directory_path}' 的内容:\n\n" + "\n".join(items)
                )]
            except Exception as e:
                return [types.TextContent(
                    type="text",
                    text=f"列出目录时发生错误：{str(e)}"
                )]
        
        elif name == "get_system_info":
            import platform
            import sys
            
            info = {
                "操作系统": platform.system(),
                "系统版本": platform.release(),
                "架构": platform.machine(),
                "Python版本": sys.version,
                "当前工作目录": os.getcwd(),
                "环境变量数量": len(os.environ)
            }
            
            info_text = "\n".join([f"{key}: {value}" for key, value in info.items()])
            
            return [types.TextContent(
                type="text",
                text=f"系统信息:\n\n{info_text}"
            )]
        
        elif name == "calculate":
            expression = arguments["expression"]
            try:
                # 安全的数学表达式求值（仅支持基本数学运算）
                allowed_chars = "0123456789+-*/.() "
                if not all(c in allowed_chars for c in expression):
                    return [types.TextContent(
                        type="text",
                        text="错误：表达式包含不允许的字符"
                    )]
                
                result = eval(expression)
                return [types.TextContent(
                    type="text",
                    text=f"计算结果: {expression} = {result}"
                )]
            except Exception as e:
                return [types.TextContent(
                    type="text",
                    text=f"计算错误：{str(e)}"
                )]
        
        else:
            return [types.TextContent(
                type="text",
                text=f"错误：未知的工具 '{name}'"
            )]
            
    except Exception as e:
        mcp_logger.log_interaction("tool_error", {
            "tool_name": name,
            "arguments": arguments,
            "error": str(e)
        })
        return [types.TextContent(
            type="text",
            text=f"工具执行错误：{str(e)}"
        )]


@server.list_prompts()
async def handle_list_prompts() -> List[types.Prompt]:
    """列出可用的提示模板"""
    mcp_logger.log_interaction("list_prompts", {"action": "获取提示模板列表"})
    
    prompts = [
        types.Prompt(
            name="analyze_code",
            description="代码分析提示模板",
            arguments=[
                types.PromptArgument(
                    name="code",
                    description="要分析的代码",
                    required=True
                ),
                types.PromptArgument(
                    name="language",
                    description="编程语言",
                    required=False
                )
            ]
        ),
        types.Prompt(
            name="file_summary",
            description="文件内容摘要提示模板",
            arguments=[
                types.PromptArgument(
                    name="file_path",
                    description="文件路径",
                    required=True
                )
            ]
        ),
        types.Prompt(
            name="debug_help",
            description="调试帮助提示模板",
            arguments=[
                types.PromptArgument(
                    name="error_message",
                    description="错误信息",
                    required=True
                ),
                types.PromptArgument(
                    name="context",
                    description="错误上下文",
                    required=False
                )
            ]
        )
    ]
    
    return prompts


@server.get_prompt()
async def handle_get_prompt(name: str, arguments: Dict[str, str]) -> types.GetPromptResult:
    """获取特定的提示模板内容"""
    mcp_logger.log_interaction("get_prompt", {
        "prompt_name": name,
        "arguments": arguments
    })
    
    if name == "analyze_code":
        code = arguments.get("code", "")
        language = arguments.get("language", "未指定")
        
        prompt_text = f"""请分析以下{language}代码：

```{language.lower() if language != "未指定" else ""}
{code}
```

请从以下几个方面进行分析：
1. 代码功能和目的
2. 代码结构和组织
3. 潜在的问题或改进建议
4. 最佳实践的应用情况
5. 性能考虑因素

请提供详细的分析和具体的改进建议。"""

        return types.GetPromptResult(
            description="代码分析提示",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(type="text", text=prompt_text)
                )
            ]
        )
    
    elif name == "file_summary":
        file_path = arguments.get("file_path", "")
        
        prompt_text = f"""请阅读并总结文件 '{file_path}' 的内容。

请使用 read_file 工具读取文件内容，然后提供：
1. 文件类型和格式
2. 主要内容摘要
3. 关键信息点
4. 如果是代码文件，请说明其功能
5. 如果是文档文件，请提取主要观点

请先读取文件，然后提供全面的摘要。"""

        return types.GetPromptResult(
            description="文件内容摘要提示",
            messages=[
                types.PromptMessage(
                    role="user", 
                    content=types.TextContent(type="text", text=prompt_text)
                )
            ]
        )
    
    elif name == "debug_help":
        error_message = arguments.get("error_message", "")
        context = arguments.get("context", "")
        
        context_text = f"\n\n上下文信息：\n{context}" if context else ""
        
        prompt_text = f"""我遇到了以下错误，请帮助我调试：

错误信息：
{error_message}{context_text}

请提供：
1. 错误的可能原因分析
2. 具体的解决步骤
3. 预防类似错误的建议
4. 相关的最佳实践

如果需要查看代码或配置文件，请使用可用的工具进行检查。"""

        return types.GetPromptResult(
            description="调试帮助提示",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(type="text", text=prompt_text)
                )
            ]
        )
    
    else:
        raise ValueError(f"未知的提示模板: {name}")


async def run_server():
    """运行 MCP 服务器"""
    mcp_logger.logger.info("🚀 MCP 学习服务器启动中...")
    
    # 创建初始化选项
    init_options = InitializationOptions(
        server_name="learning-mcp-server",
        server_version="1.0.0",
        capabilities=server.get_capabilities(
            notification_options=types.NotificationOptions(),
            experimental_capabilities={}
        )
    )
    
    mcp_logger.log_interaction("server_startup", {
        "server_name": init_options.server_name,
        "server_version": init_options.server_version,
        "capabilities": [
            "resources",
            "tools", 
            "prompts"
        ]
    })
    
    mcp_logger.logger.info("✅ MCP 服务器已启动，等待客户端连接...")
    mcp_logger.logger.info(f"📝 交互日志将保存到: {mcp_logger.log_file}")
    
    # 使用 stdio 传输运行服务器
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            init_options
        )


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
    
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        print("\n👋 MCP 服务器已关闭", file=sys.stderr)
    except Exception as e:
        print(f"\n❌ 服务器错误: {e}", file=sys.stderr)
        sys.exit(1) 