"""
MCP 天气查询服务端 - SSE 模式
实现 MCP 协议的 SSE 版本，提供天气查询功能并记录交互数据
"""
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import uuid
from pydantic import BaseModel
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# MCP 协议相关的数据模型
class MCPMessage(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[int] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

class Tool(BaseModel):
    name: str
    description: str
    inputSchema: Dict[str, Any]

class MCPInteractionLog(BaseModel):
    """MCP 交互日志"""
    session_id: str
    timestamp: datetime
    direction: str  # "request" or "response"
    message: Dict[str, Any]

class WeatherMCPServerSSE:
    def __init__(self, log_dir: Path = Path("logs/mcp_weather")):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.sessions = {}  # 存储会话信息
        
        # 定义工具
        self.tools = [
            Tool(
                name="get_weather",
                description="获取指定城市的天气信息",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "城市名称，例如：北京、上海、深圳"
                        }
                    },
                    "required": ["city"]
                }
            ),
            Tool(
                name="get_forecast",
                description="获取指定城市未来几天的天气预报",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "城市名称"
                        },
                        "days": {
                            "type": "integer",
                            "description": "预报天数，1-7天",
                            "minimum": 1,
                            "maximum": 7
                        }
                    },
                    "required": ["city"]
                }
            )
        ]
    
    def get_session_id(self, request: Request) -> str:
        """获取或创建会话ID"""
        session_id = request.headers.get("x-session-id")
        if not session_id:
            session_id = str(uuid.uuid4())
        
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "created_at": datetime.now(),
                "message_count": 0
            }
        
        return session_id
    
    async def log_interaction(self, session_id: str, direction: str, message: Dict[str, Any]):
        """记录交互数据"""
        log_entry = MCPInteractionLog(
            session_id=session_id,
            timestamp=datetime.now(),
            direction=direction,
            message=message
        )
        
        # 保存到日志文件
        log_file = self.log_dir / f"{session_id}.jsonl"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry.model_dump(), ensure_ascii=False, default=str) + '\n')
    
    async def handle_initialize(self, message: MCPMessage) -> MCPMessage:
        """处理初始化请求"""
        return MCPMessage(
            jsonrpc="2.0",
            id=message.id,
            result={
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "prompts": {}
                },
                "serverInfo": {
                    "name": "weather-mcp-server-sse",
                    "version": "1.0.0"
                }
            }
        )
    
    async def handle_list_tools(self, message: MCPMessage) -> MCPMessage:
        """处理列出工具请求"""
        tools_list = [tool.model_dump() for tool in self.tools]
        return MCPMessage(
            jsonrpc="2.0",
            id=message.id,
            result={"tools": tools_list}
        )
    
    async def handle_call_tool(self, message: MCPMessage) -> MCPMessage:
        """处理工具调用请求"""
        params = message.params or {}
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "get_weather":
            city = arguments.get("city", "未知")
            # 模拟天气数据
            weather_data = {
                "city": city,
                "temperature": "25°C",
                "weather": "晴天",
                "humidity": "65%",
                "wind": "东南风 3级",
                "air_quality": "良"
            }
            
            return MCPMessage(
                jsonrpc="2.0",
                id=message.id,
                result={
                    "content": [
                        {
                            "type": "text",
                            "text": f"{city}的天气信息：\n温度：{weather_data['temperature']}\n天气：{weather_data['weather']}\n湿度：{weather_data['humidity']}\n风力：{weather_data['wind']}\n空气质量：{weather_data['air_quality']}"
                        }
                    ]
                }
            )
        
        elif tool_name == "get_forecast":
            city = arguments.get("city", "未知")
            days = arguments.get("days", 3)
            
            # 模拟预报数据
            forecast = []
            weather_types = ["晴", "多云", "阴", "小雨", "中雨"]
            for i in range(days):
                forecast.append({
                    "date": f"第{i+1}天",
                    "weather": weather_types[i % len(weather_types)],
                    "temp_high": f"{20 + i}°C",
                    "temp_low": f"{15 + i}°C"
                })
            
            forecast_text = f"{city}未来{days}天天气预报：\n"
            for day in forecast:
                forecast_text += f"{day['date']}：{day['weather']}，{day['temp_low']} ~ {day['temp_high']}\n"
            
            return MCPMessage(
                jsonrpc="2.0",
                id=message.id,
                result={
                    "content": [
                        {
                            "type": "text",
                            "text": forecast_text
                        }
                    ]
                }
            )
        
        else:
            return MCPMessage(
                jsonrpc="2.0",
                id=message.id,
                error={
                    "code": -32601,
                    "message": f"Unknown tool: {tool_name}"
                }
            )
    
    async def handle_message(self, message: MCPMessage) -> MCPMessage:
        """处理单个消息"""
        method = message.method
        
        if method == "initialize":
            return await self.handle_initialize(message)
        elif method == "tools/list":
            return await self.handle_list_tools(message)
        elif method == "tools/call":
            return await self.handle_call_tool(message)
        else:
            return MCPMessage(
                jsonrpc="2.0",
                id=message.id,
                error={
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            )

# 创建 FastAPI 应用
app = FastAPI(title="Weather MCP Server SSE", version="1.0.0")

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建服务器实例
server = WeatherMCPServerSSE()

@app.get("/")
async def root():
    """根路径，返回服务器信息"""
    return {
        "name": "Weather MCP Server SSE",
        "version": "1.0.0",
        "protocol": "MCP over SSE",
        "endpoints": {
            "sse": "/sse",
            "message": "/message"
        }
    }

@app.get("/sse")
async def sse_endpoint(request: Request):
    """SSE 端点，用于建立 SSE 连接"""
    session_id = server.get_session_id(request)
    
    async def event_generator():
        # 发送连接建立事件
        yield f"data: {json.dumps({'type': 'connected', 'session_id': session_id})}\n\n"
        
        # 保持连接活跃
        try:
            while True:
                # 发送心跳
                yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.now().isoformat()})}\n\n"
                await asyncio.sleep(30)  # 每30秒发送一次心跳
        except asyncio.CancelledError:
            # 连接被取消
            yield f"data: {json.dumps({'type': 'disconnected'})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Session-ID": session_id
        }
    )

@app.post("/message")
async def handle_message_endpoint(request: Request):
    """处理 MCP 消息的端点"""
    session_id = server.get_session_id(request)
    
    try:
        # 读取请求体
        body = await request.body()
        message_data = json.loads(body.decode('utf-8'))
        
        # 解析消息
        message = MCPMessage(**message_data)
        
        # 记录请求
        await server.log_interaction(session_id, "request", message_data)
        
        # 处理消息
        response = await server.handle_message(message)
        
        # 记录响应
        response_data = response.model_dump(exclude_none=True)
        await server.log_interaction(session_id, "response", response_data)
        
        # 返回响应
        return JSONResponse(content=response_data)
        
    except Exception as e:
        # 错误响应
        error_response = {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32700,
                "message": f"Parse error: {str(e)}"
            }
        }
        
        # 记录错误
        await server.log_interaction(session_id, "error", error_response)
        
        return JSONResponse(content=error_response, status_code=400)

@app.get("/sessions")
async def list_sessions():
    """列出所有会话"""
    return {
        "sessions": [
            {
                "session_id": sid,
                "created_at": info["created_at"].isoformat(),
                "message_count": info["message_count"]
            }
            for sid, info in server.sessions.items()
        ]
    }

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Weather MCP Server SSE")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8001, help="Port to bind to")
    parser.add_argument("--log-level", default="info", help="Log level")
    
    args = parser.parse_args()
    
    print(f"启动 Weather MCP Server SSE 在 http://{args.host}:{args.port}", flush=True)
    
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level=args.log_level
    ) 