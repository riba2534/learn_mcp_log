"""
Web 界面应用
用于展示 LLM 代理和 MCP 服务的交互数据
"""
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import aiofiles

class LogEntry(BaseModel):
    """日志条目"""
    id: str
    timestamp: datetime
    type: str  # "llm" or "mcp"
    summary: str
    details: Dict[str, Any]

class WebApp:
    def __init__(self):
        self.app = FastAPI(title="MCP Proxy Logger Web Interface")
        self.templates = Jinja2Templates(directory="templates")
        
        # 挂载静态文件
        self.app.mount("/static", StaticFiles(directory="static"), name="static")
        
        # 设置路由
        self.setup_routes()
    
    def setup_routes(self):
        """设置路由"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def index(request: Request):
            """首页"""
            return self.templates.TemplateResponse(
                "index.html",
                {"request": request}
            )
        
        @self.app.get("/api/logs/llm")
        async def get_llm_logs():
            """获取 LLM 代理日志"""
            log_dir = Path("logs/llm_proxy")
            logs = []
            
            if log_dir.exists():
                for log_file in sorted(log_dir.glob("*.json"), reverse=True):
                    try:
                        async with aiofiles.open(log_file, 'r', encoding='utf-8') as f:
                            content = await f.read()
                            data = json.loads(content)
                            
                            # 创建摘要
                            summary = f"{data['method']} {data['path']}"
                            if data.get('body') and isinstance(data['body'], dict):
                                if 'model' in data['body']:
                                    summary += f" (model: {data['body']['model']})"
                            
                            logs.append(LogEntry(
                                id=data['id'],
                                timestamp=data['timestamp'],
                                type="llm",
                                summary=summary,
                                details=data
                            ))
                    except Exception as e:
                        print(f"Error reading log file {log_file}: {e}")
            
            return [log.model_dump() for log in logs[:50]]  # 最多返回50条
        
        @self.app.get("/api/logs/mcp")
        async def get_mcp_logs():
            """获取 MCP 服务日志"""
            log_dir = Path("logs/mcp_weather")
            logs = []
            sessions = {}
            
            if log_dir.exists():
                for log_file in sorted(log_dir.glob("*.jsonl"), reverse=True):
                    try:
                        async with aiofiles.open(log_file, 'r', encoding='utf-8') as f:
                            lines = await f.readlines()
                            
                        session_logs = []
                        for line in lines:
                            if line.strip():
                                entry = json.loads(line)
                                session_logs.append(entry)
                        
                        if session_logs:
                            session_id = session_logs[0]['session_id']
                            sessions[session_id] = session_logs
                    except Exception as e:
                        print(f"Error reading log file {log_file}: {e}")
            
            # 转换为日志条目
            for session_id, session_logs in sessions.items():
                # 按时间戳分组请求和响应
                interactions = []
                i = 0
                while i < len(session_logs):
                    if session_logs[i]['direction'] == 'request':
                        request = session_logs[i]
                        response = None
                        if i + 1 < len(session_logs) and session_logs[i + 1]['direction'] == 'response':
                            response = session_logs[i + 1]
                            i += 1
                        
                        # 创建交互摘要
                        method = request['message'].get('method', 'unknown')
                        summary = f"MCP: {method}"
                        if method == 'tools/call':
                            tool_name = request['message'].get('params', {}).get('name', '')
                            summary = f"MCP: Call {tool_name}"
                        
                        logs.append(LogEntry(
                            id=f"{session_id}_{i}",
                            timestamp=request['timestamp'],
                            type="mcp",
                            summary=summary,
                            details={
                                "session_id": session_id,
                                "request": request['message'],
                                "response": response['message'] if response else None
                            }
                        ))
                    i += 1
            
            return [log.model_dump() for log in sorted(logs, key=lambda x: x.timestamp, reverse=True)[:50]]
        
        @self.app.get("/api/log/{log_type}/{log_id}")
        async def get_log_detail(log_type: str, log_id: str):
            """获取日志详情"""
            if log_type == "llm":
                log_file = Path(f"logs/llm_proxy/{log_id}.json")
                if log_file.exists():
                    async with aiofiles.open(log_file, 'r', encoding='utf-8') as f:
                        content = await f.read()
                        return json.loads(content)
            
            return {"error": "Log not found"}
        
        @self.app.get("/api/log/{log_type}/{log_id}/parse")
        async def parse_log_detail(log_type: str, log_id: str):
            """解析日志详情，提取关键信息"""
            if log_type == "llm":
                log_file = Path(f"logs/llm_proxy/{log_id}.json")
                if log_file.exists():
                    async with aiofiles.open(log_file, 'r', encoding='utf-8') as f:
                        content = await f.read()
                        data = json.loads(content)
                        return self.parse_llm_log(data)
            elif log_type == "mcp":
                # 从现有日志数据中查找
                log_dir = Path("logs/mcp_weather")
                if log_dir.exists():
                    for log_file in log_dir.glob("*.jsonl"):
                        try:
                            async with aiofiles.open(log_file, 'r', encoding='utf-8') as f:
                                lines = await f.readlines()
                            
                            for line in lines:
                                if line.strip():
                                    entry = json.loads(line)
                                    if f"{entry['session_id']}_" in log_id:
                                        return self.parse_mcp_log(entry)
                        except Exception:
                            continue
            
            return {"error": "Log not found"}
    
    def parse_llm_log(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """解析 LLM 日志，提取关键信息"""
        parsed = {
            "basic_info": {
                "id": data.get("id"),
                "timestamp": data.get("timestamp"),
                "method": data.get("method"),
                "path": data.get("path"),
                "duration_ms": data.get("duration_ms"),
                "status": data.get("response_status")
            },
            "request_info": {},
            "response_info": {},
            "conversation": [],
            "model_info": {},
            "streaming_info": {},
            "error_info": {}
        }
        
        # 解析请求信息
        if data.get("body"):
            body = data["body"]
            parsed["request_info"] = {
                "model": body.get("model"),
                "temperature": body.get("temperature"),
                "max_tokens": body.get("max_tokens"),
                "stream": body.get("stream", False),
                "tools": len(body.get("tools", [])) if body.get("tools") else 0
            }
            
            # 解析对话内容
            if body.get("messages"):
                for msg in body["messages"]:
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    
                    # 处理复杂内容格式
                    if isinstance(content, list):
                        text_parts = []
                        for part in content:
                            if isinstance(part, dict) and part.get("type") == "text":
                                text_parts.append(part.get("text", ""))
                        content = "\n".join(text_parts)
                    
                    parsed["conversation"].append({
                        "role": role,
                        "content": content,  # 显示完整内容，不省略
                        "content_length": len(str(content))
                    })
        
        # 解析响应信息
        if data.get("response_status"):
            parsed["response_info"]["status"] = data["response_status"]
            parsed["response_info"]["headers"] = data.get("response_headers", {})
        
        # 解析流式响应
        if data.get("response_chunks"):
            chunks = data["response_chunks"]
            parsed["streaming_info"] = {
                "total_chunks": len(chunks),
                "first_chunk_time": "处理中..." if chunks else "无",
                "last_chunk_time": "处理中..." if chunks else "无",
                "total_content_length": 0
            }
            
            # 提取实际内容
            content_parts = []
            for chunk in chunks:
                if chunk.startswith("data: ") and not chunk.startswith("data: [DONE]"):
                    try:
                        chunk_data = json.loads(chunk[6:])  # 去掉 "data: " 前缀
                        if "choices" in chunk_data and chunk_data["choices"]:
                            delta = chunk_data["choices"][0].get("delta", {})
                            if "content" in delta and delta["content"]:
                                content_parts.append(delta["content"])
                    except:
                        continue
            
            full_content = "".join(content_parts)
            parsed["streaming_info"]["total_content_length"] = len(full_content)
            parsed["streaming_info"]["generated_content"] = full_content  # 显示完整生成内容
        
        # 解析模型信息
        if data.get("body", {}).get("model"):
            model = data["body"]["model"]
            parsed["model_info"] = {
                "model_name": model,
                "provider": self.detect_provider(model),
                "model_type": self.detect_model_type(model)
            }
        
        return parsed
    
    def parse_mcp_log(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """解析 MCP 日志，提取关键信息"""
        parsed = {
            "basic_info": {
                "session_id": data.get("session_id"),
                "timestamp": data.get("timestamp"),
                "direction": data.get("direction")
            },
            "message_info": {},
            "tool_info": {},
            "error_info": {}
        }
        
        message = data.get("message", {})
        
        # 基本消息信息
        parsed["message_info"] = {
            "method": message.get("method"),
            "id": message.get("id"),
            "jsonrpc": message.get("jsonrpc")
        }
        
        # 工具调用信息
        if message.get("method") == "tools/call":
            params = message.get("params", {})
            parsed["tool_info"] = {
                "tool_name": params.get("name"),
                "arguments": params.get("arguments", {}),
                "arguments_summary": self.summarize_tool_arguments(params.get("arguments", {}))
            }
        
        # 工具列表信息
        elif message.get("method") == "tools/list":
            result = message.get("result", {})
            if "tools" in result:
                parsed["tool_info"] = {
                    "available_tools": [tool.get("name") for tool in result["tools"]],
                    "tool_count": len(result["tools"])
                }
        
        # 错误信息
        if "error" in message:
            error = message["error"]
            parsed["error_info"] = {
                "code": error.get("code"),
                "message": error.get("message"),
                "data": error.get("data")
            }
        
        return parsed
    
    def detect_provider(self, model: str) -> str:
        """检测模型提供商"""
        if "anthropic" in model.lower() or "claude" in model.lower():
            return "Anthropic"
        elif "openai" in model.lower() or "gpt" in model.lower():
            return "OpenAI"
        elif "google" in model.lower() or "gemini" in model.lower():
            return "Google"
        elif "meta" in model.lower() or "llama" in model.lower():
            return "Meta"
        else:
            return "Unknown"
    
    def detect_model_type(self, model: str) -> str:
        """检测模型类型"""
        model_lower = model.lower()
        if "sonnet" in model_lower:
            return "Claude Sonnet"
        elif "haiku" in model_lower:
            return "Claude Haiku"
        elif "opus" in model_lower:
            return "Claude Opus"
        elif "gpt-4" in model_lower:
            return "GPT-4"
        elif "gpt-3.5" in model_lower:
            return "GPT-3.5"
        else:
            return "Unknown"
    
    def summarize_tool_arguments(self, args: Dict[str, Any]) -> str:
        """总结工具参数"""
        if not args:
            return "无参数"
        
        summary_parts = []
        for key, value in args.items():
            if isinstance(value, str) and len(value) > 50:
                summary_parts.append(f"{key}: {value[:50]}...")
            else:
                summary_parts.append(f"{key}: {value}")
        
        return "; ".join(summary_parts[:3])  # 最多显示3个参数

# 创建应用实例
web_app = WebApp()
app = web_app.app 