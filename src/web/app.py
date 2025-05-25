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

# 创建应用实例
web_app = WebApp()
app = web_app.app 